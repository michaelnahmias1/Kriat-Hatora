# -*- coding: utf-8 -*-
"""פרופיל שירה (PLAN_TEFILA.md 4.3.3, ‏4.3.5, ‏8.26) — בלי מודלים, torch או רשת.

- פרופילים: קריאה = הכל כבוי; ערכי השירה במקום אחד.
- ב: זיהוי דיבור שאינו בטקסט (nontext_runs) והחלתו (apply_nontext_runs).
- גבול קשיח בחלונות: עוגן-דמה עם חסם תחתון, בלי מיזוג מעליו.
- ה: אינטרפולציה שמדלגת על דיבור שזוהה; חלון עם מרווח תחילות > 20 ש׳ נכשל.
- ד: גיוס שני עם דרישת הקשר.
- ג: כוכב ב-MmsAligner.align (עם מודל מדומה) ובקריאות הצינור.
- צינור מלא עם mocks: ‏vad_filter=False, דוח, דאמפ, חסם, קטיעת כתובית, VAD.
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "tests"))

from aligner import anchors as A  # noqa: E402
from aligner import hybrid as H  # noqa: E402
from aligner import profiles as P  # noqa: E402
from aligner import windows as W  # noqa: E402
from aligner.pipeline import MmsAligner, build_srt, units_to_segments  # noqa: E402
from test_tanakh_golden import FakeWave, _fake_romanize  # noqa: E402


class TestProfiles(unittest.TestCase):
    def test_reading_is_all_off(self):
        r = P.get_profile("reading")
        self.assertTrue(r.asr_vad_filter)
        self.assertIsNone(r.nontext)
        self.assertFalse(r.star or r.recruit_context)
        self.assertIsNone(r.max_start_gap_sec)
        self.assertIsNone(r.max_word_sec)
        self.assertEqual(r.vad_snap_min_speech, 0.0)

    def test_singing_values(self):
        s = P.get_profile("singing")
        self.assertFalse(s.asr_vad_filter)
        self.assertTrue(s.star and s.recruit_context)
        self.assertEqual((s.max_start_gap_sec, s.max_word_sec), (20.0, 20.0))
        self.assertEqual(s.vad_snap_min_speech, 0.5)
        self.assertEqual(s.nontext.max_word_sec, 0.6)
        self.assertEqual(set(s.nontext.detect_kwargs()) | set(s.nontext.apply_kwargs()),
                         set(P.NonTextParams.__dataclass_fields__))

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):
            P.get_profile("shouting")

    def test_run_hybrid_units_guards(self):
        units = [{"text": "שָׁלוֹם", "label": "א", "kind": "line"}]
        with self.assertRaises(ValueError):
            H.run_hybrid_units(units, "a", "o", profile="shouting")
        with self.assertRaises(NotImplementedError):  # אין שירה לתנ״ך
            H.run_hybrid_units(units, "a", "o", profile="singing")


# --- ב: ריצות דיבור שאינו בטקסט ------------------------------------------------

def _times(spec):
    """[(start, dur)] → [(start, end)]."""
    return [(s, s + d) for s, d in spec]


class TestNontextRuns(unittest.TestCase):
    def test_short_unmatched_words_form_a_run(self):
        # 0–3: דיבור (קצר, לא-טקסט); 4–5: טקסט מושר (מותאם); 6: מילה מושרת ארוכה
        times = _times([(1.0, .3), (1.4, .3), (1.8, .3), (2.2, .3),
                        (5.0, .5), (6.0, .5), (8.0, 1.5)])
        words = ["שלום", "לכולם", "בוקר", "טוב", "כי", "לאדני", "אהה"]
        pairs = [(4, 0, 1.0), (5, 1, 0.9), (6, 2, 0.2)]
        runs = A.nontext_runs(pairs, times, words)
        self.assertEqual(len(runs), 1)
        self.assertEqual((runs[0]["start"], runs[0]["end"]), (1.0, 2.5))
        self.assertEqual(runs[0]["text"], "שלום לכולם בוקר טוב")

    def test_sung_or_short_runs_ignored(self):
        times = _times([(0, .9), (1, .9), (2, .9), (3, .9)])  # מושר — ארוך
        self.assertEqual(A.nontext_runs([], times, ["א"] * 4), [])
        times = _times([(0, .2), (0.3, .2)])                 # רק 2 מילים
        self.assertEqual(A.nontext_runs([], times, ["א"] * 2), [])

    def test_split_on_gap_and_merge_without_text_between(self):
        # שתי ריצות במרחק 2 ש׳ בלי טקסט ביניהן — מתאחדות; מרחק 5 ש׳ — לא
        times = _times([(0, .3), (.4, .3), (.8, .3),
                        (3.1, .3), (3.5, .3), (3.9, .3),
                        (9.2, .3), (9.6, .3), (10.0, .3)])
        runs = A.nontext_runs([], times, ["x"] * 9)
        self.assertEqual([(r["start"], r["end"]) for r in runs],
                         [(0, 4.2), (9.2, 10.3)])

    def test_text_word_between_prevents_merge(self):
        times = _times([(0, .3), (.4, .3), (.8, .3), (1.5, .3),
                        (2.2, .3), (2.6, .3), (3.0, .3)])
        runs = A.nontext_runs([(3, 0, 1.0)], times, ["x"] * 7)
        self.assertEqual(len(runs), 2)


def _anchor(ref, start, sim=1.0):
    return {"ref": ref, "asr": 0, "start": start, "end": start + 0.4,
            "sim": sim}


class TestApplyNontextRuns(unittest.TestCase):
    UNIT_STARTS = [0, 10, 20]

    def test_drops_anchor_in_run_and_bounds_next_line(self):
        anchors = [_anchor(2, 3.0), _anchor(8, 9.0),
                   _anchor(15, 56.9),   # "אני"~"אין" בתוך שם הניגון
                   _anchor(25, 80.0)]
        runs = [{"start": 57.5, "end": 58.4, "text": "לקראת דודי ארוץ"}]
        out = A.apply_nontext_runs(anchors, runs, self.UNIT_STARTS, 30, 120.0)
        self.assertNotIn(15, [a["ref"] for a in out])
        pseudo = [a for a in out if a.get("lower_bound")]
        self.assertEqual(len(pseudo), 1)
        self.assertEqual((pseudo[0]["ref"], pseudo[0]["start"],
                          pseudo[0]["run_start"]), (10, 58.4, 57.5))
        self.assertEqual(runs[0]["pseudo_ref"], 10)
        self.assertEqual([a["ref"] for a in out], sorted(a["ref"] for a in out))

    def test_intro_bounds_first_word(self):
        out = A.apply_nontext_runs([_anchor(3, 15.0)],
                                   [{"start": 3.6, "end": 9.4, "text": "x"}],
                                   self.UNIT_STARTS, 30, 120.0)
        self.assertEqual(out[0]["ref"], 0)
        self.assertTrue(out[0]["lower_bound"])
        self.assertEqual(out[0]["start"], 9.4)

    def test_no_room_no_pseudo_anchor(self):
        """דיבור בסוף ההקלטה ("תודה רבה") לא מושך את השורה האחרונה אחריו."""
        runs = [{"start": 118.0, "end": 119.5, "text": "תודה רבה לכולם"}]
        out = A.apply_nontext_runs([_anchor(5, 10.0)], runs, self.UNIT_STARTS,
                                   30, 120.0)
        self.assertFalse(any(a.get("lower_bound") for a in out))
        self.assertIsNone(runs[0]["pseudo_ref"])

    def test_no_line_start_between_bounding_anchors(self):
        runs = [{"start": 20.0, "end": 21.0, "text": "x"}]
        out = A.apply_nontext_runs([_anchor(11, 15.0), _anchor(14, 25.0)],
                                   runs, self.UNIT_STARTS, 30, 120.0)
        self.assertEqual([a["ref"] for a in out], [11, 14])

    def test_find_anchors_reports_runs_only_when_asked(self):
        asr = [{"word": w, "start": i * .3, "end": i * .3 + .25}
               for i, w in enumerate(["שלום", "לכולם", "בוקר", "טוב"])]
        asr += [{"word": "בראשית", "start": 5.0, "end": 5.8},
                {"word": "ברא", "start": 6.0, "end": 6.8}]
        ref = ["בראשית", "ברא"]
        self.assertNotIn("nontext_runs", A.find_anchors(asr, ref))
        found = A.find_anchors(asr, ref,
                               nontext=P.NonTextParams().detect_kwargs())
        self.assertEqual([r["text"] for r in found["nontext_runs"]],
                         ["שלום לכולם בוקר טוב"])


class TestRecruitContext(unittest.TestCase):
    def test_recruit_without_context_needs_flag(self):
        ref = ["אב" + a + b for a in "גדהזחטכלמנ" for b in "סעפצקרשת"][:70]
        # עוגן אחד בהקשר בתחילה, ומילה בודדת (בלי הקשר) רחוק — רק גיוס שני
        pairs = ([(0, 0, 1.0), (1, 1, 1.0), (2, 2, 1.0)]
                 + [(None, j, 0.0) for j in range(3, 60)] + [(3, 60, 0.8)])
        times = [(0.0, .4), (.5, .9), (1.0, 1.4), (200.0, 200.4)]
        with_recruit, _ = A.select_anchors(pairs, times, ref)
        guarded, _ = A.select_anchors(pairs, times, ref, recruit_context=True)
        self.assertIn(60, [a["ref"] for a in with_recruit])
        self.assertNotIn(60, [a["ref"] for a in guarded])


# --- גבול קשיח בחלונות ----------------------------------------------------------

def _pseudo(ref, t1, t0):
    return {"ref": ref, "asr": None, "start": t1, "end": t1, "sim": None,
            "lower_bound": True, "run_start": t0}


class TestHardBoundaryWindows(unittest.TestCase):
    def test_split_at_lower_bound(self):
        anchors = [_anchor(0, 1.0), _pseudo(10, 58.4, 57.5), _anchor(20, 90.0)]
        ws = W.build_windows(anchors, 25, 120.0)
        self.assertEqual([(w["word_lo"], w["word_hi"]) for w in ws],
                         [(0, 9), (10, 20), (20, 24)])
        self.assertEqual(ws[0]["t_hi"], 57.5 + 0.5)   # נגמר בתחילת הדיבור
        self.assertEqual(ws[1]["t_lo"], 58.4)         # בלי ריפוד לאחור
        self.assertTrue(ws[1]["hard_left"])
        self.assertFalse(ws[0].get("hard_left") or ws[2].get("hard_left"))

    def test_pseudo_first_and_last(self):
        ws = W.build_windows([_pseudo(0, 9.4, 3.6)], 5, 30.0)
        self.assertEqual([(w["word_lo"], w["word_hi"], w["t_lo"]) for w in ws],
                         [(0, 4, 9.4)])
        ws = W.build_windows([_anchor(0, 1.0), _pseudo(4, 20.0, 18.0)], 5, 30.0)
        self.assertEqual([(w["word_lo"], w["word_hi"]) for w in ws],
                         [(0, 3), (4, 4)])

    def test_short_windows_never_merge_across_bound(self):
        anchors = [_anchor(0, 1.0), _anchor(3, 3.0), _pseudo(6, 5.0, 4.0),
                   _anchor(9, 6.0), _anchor(12, 30.0)]
        ws = W.build_windows(anchors, 15, 40.0)
        for w in ws:
            if w["word_lo"] < 6 <= w["word_hi"]:
                self.assertEqual(w["word_lo"], 6, "מוזג מעל הגבול הקשיח")
        self.assertTrue(any(w["word_lo"] == 6 and w.get("hard_left")
                            for w in ws))

    def test_stitch_and_retry_respect_bound(self):
        anchors = [_anchor(0, 1.0), _pseudo(5, 20.0, 18.0), _anchor(10, 40.0)]
        ws = W.build_windows(anchors, 12, 50.0)
        plain = ["אבג"] * 12

        def align_fn(w):
            if w.get("hard_left"):
                return None  # החלון שאחרי הגבול נכשל — ולא ימוזג שמאלה
            n = w["word_hi"] - w["word_lo"] + 1
            step = (w["t_hi"] - w["t_lo"]) / n
            return [(w["t_lo"] + i * step, w["t_lo"] + (i + .5) * step, .5)
                    for i in range(n)]

        out = W.align_windows(ws, align_fn, plain, exclude=[(18.0, 20.0)])
        self.assertTrue(any(o["interpolated"] and o["window"]["word_lo"] == 5
                            for o in out))
        spans, _ = W.stitch(out, 12)
        self.assertGreaterEqual(spans[5][0], 20.0)        # החסם התחתון
        self.assertLessEqual(spans[4][1], 18.0 + 0.5)     # לפני הדיבור (+ריפוד)


class TestInterpolationExclude(unittest.TestCase):
    def test_skips_excluded_time(self):
        # 1/3 מהזמן הפנוי לפני הקטע; משקלות 1,1,1,3 ⇒ מילה 2 מתחילה בגבול
        spans = W.interpolate_words(0.0, 10.0, ["א", "ב", "ג", "דהו"],
                                    exclude=[(2.0, 6.0)])
        self.assertEqual(len(spans), 4)
        for s, e, _ in spans:  # מילה יכולה "לגשר" על הקטע, אבל לא להתחיל/להיגמר בו
            self.assertFalse(2.0 < s < 6.0)
            self.assertFalse(2.0 < e < 6.0)
        self.assertAlmostEqual(spans[1][1], 2.0)  # נגמרת בגבול — לפני הקטע
        self.assertAlmostEqual(spans[2][0], 6.0)  # מתחילה בגבול — אחרי הקטע
        self.assertAlmostEqual(spans[0][0], 0.0)
        self.assertAlmostEqual(spans[-1][1], 10.0)

    def test_no_exclude_is_unchanged(self):
        words = ["אבג", "ד", "הוזח"]
        self.assertEqual(W.interpolate_words(1.0, 9.0, words),
                         W.interpolate_words(1.0, 9.0, words, exclude=None))
        self.assertEqual(W.interpolate_words(1.0, 9.0, words, exclude=[]),
                         W.interpolate_words(1.0, 9.0, words))


# --- ג: כוכב ב-MmsAligner (מודל מדומה) ------------------------------------------

class _Span:
    def __init__(self, start, end):
        self.start, self.end, self.score = start, end, 0.5


class _Emission:
    def __init__(self, n):
        self.n = n

    def size(self, dim):
        return self.n

    def __getitem__(self, i):
        return self


class TestStarAlign(unittest.TestCase):
    def _aligner(self, seen):
        al = MmsAligner.__new__(MmsAligner)
        al._torch = mock.MagicMock()
        al.device = "cpu"
        al.sample_rate = 16000
        wave = mock.MagicMock()
        wave.to.return_value = wave
        wave.size.return_value = 16000
        al.model = lambda w: (_Emission(50), None)
        al.tokenizer = lambda words: (seen.append(list(words)) or
                                      [[1] for _ in words])
        al.aligner = lambda em, toks: [[_Span(i * 2, i * 2 + 1)]
                                       for i in range(len(toks))]
        return al, wave

    def test_stars_inserted_and_dropped(self):
        seen = []
        al, wave = self._aligner(seen)
        spans = al.align(wave, ["ki", "ladonai", "hamelukha"], 10.0,
                         stars=[True, False, True, True])
        self.assertEqual(seen[0], ["*", "ki", "ladonai", "*", "hamelukha", "*"])
        self.assertEqual(len(spans), 3)
        # מילה 0 היא הטוקן השני (אחרי הכוכב) — הזמנים שלה, לא של הכוכב
        self.assertAlmostEqual(spans[0][0], 10.0 + 2 * 0.02)

    def test_no_stars_unchanged(self):
        seen = []
        al, wave = self._aligner(seen)
        al.align(wave, ["a", "b"], 0.0)
        self.assertEqual(seen[0], ["a", "b"])


# --- צינור מלא עם mocks -----------------------------------------------------------

TEXT_UNITS = [
    {"text": "כִּי לה' הַמְּלוּכָה. וּמושֵׁל בַּגּויִם:", "label": "שורה 1",
     "kind": "line"},
    {"text": "וְהָיָה ה' לְמֶלֶךְ עַל כָּל הָאָרֶץ:", "label": "שורה 2",
     "kind": "line"},
    {"text": "נִשְׁמַת כָּל חַי תְּבָרֵךְ אֶת שִׁמְךָ ה' אֱלהֵינוּ וְרוּחַ כָּל בָּשָׂר"
             " תְּפָאֵר:", "label": "שורה 3", "kind": "line"},
]
INTRO = ["שלום", "לכולם", "אני", "רוצה", "להקריא", "לכם"]
MELODY = ["עכשיו", "בניגון", "של", "קרליבך"]


class StarFake:
    inits, calls = [], []

    def __init__(self, *a, **kw):
        StarFake.inits.append(kw)

    def align(self, piece, roman, offset_sec=0.0, stars=None):
        StarFake.calls.append((len(roman), stars))
        dur = piece.n / 16000
        step = dur / len(roman)
        return [(offset_sec + i * step, offset_sec + (i + .8) * step, .5)
                for i in range(len(roman))]


class GapFake(StarFake):
    """מדמה CTC על מליסמה: מילה ראשונה בתחילה, כל השאר דחוסות בסוף."""

    def align(self, piece, roman, offset_sec=0.0, stars=None):
        dur = piece.n / 16000
        if dur < 25 or len(roman) < 3:
            return super().align(piece, roman, offset_sec, stars)
        StarFake.calls.append((len(roman), stars))
        end = offset_sec + dur
        return ([(offset_sec, offset_sec + .5, .5)]
                + [(end - (len(roman) - i) * .2, end - (len(roman) - i) * .2 + .1,
                    .5) for i in range(1, len(roman))])


def _scenario(line3_sparse=False):
    segs = units_to_segments(TEXT_UNITS, 4, mode="tefila")
    plain = [w for s in segs for w in s["align_plain"]]
    starts = [0]
    for s in segs:
        starts.append(starts[-1] + len(s["align_plain"]))
    line3 = next(i for i, s in enumerate(segs) if s["unit"] == 2)
    w3 = starts[line3]
    asr, t = [], 1.0
    for w in INTRO:                      # דיבור: 0.3 ש׳ למילה
        asr.append({"word": w, "start": t, "end": t + .3, "prob": .9})
        t += .35
    intro_end = asr[-1]["end"]
    t = 6.0
    for i, w in enumerate(plain[:w3]):    # שירה: 1.2 ש׳ למילה
        asr.append({"word": w, "start": t, "end": t + 1.0, "prob": .9})
        t += 1.2
    t += 1.0
    mel_start = t
    for w in MELODY:
        asr.append({"word": w, "start": t, "end": t + .3, "prob": .9})
        t += .35
    mel_end = asr[-1]["end"]
    t += 1.5
    line3_start = t
    tail = plain[w3:]
    for i, w in enumerate(tail):
        if i == 0:  # המילה הראשונה מושרת ומשובשת בתמלול ("מי נשמע" בנשמת)
            asr.append({"word": "מינשמע", "start": t, "end": t + 1.5,
                        "prob": .5})
            t += 1.7
            continue
        if line3_sparse and i not in (len(tail) - 2, len(tail) - 1):
            t += 3.0                       # מליסמה: אין תמלול באמצע השורה
            continue
        asr.append({"word": w, "start": t, "end": t + 1.0, "prob": .9})
        t += 1.2
    audio = int((t + 2) * 16000)
    return dict(asr=asr, audio=audio, intro_end=intro_end,
                mel=(mel_start, mel_end), line3_start=line3_start,
                line3_seg=line3, w3=w3)


class TestSingingPipeline(unittest.TestCase):
    def _run(self, aligner=StarFake, speech=((0.5, 3.0),), line3_sparse=False):
        sc = _scenario(line3_sparse)
        StarFake.inits, StarFake.calls = [], []
        debug, out = {}, io.StringIO()
        with tempfile.TemporaryDirectory() as td, \
                mock.patch.object(H, "load_audio_16k_mono",
                                  return_value=FakeWave(sc["audio"])), \
                mock.patch.object(H, "MmsAligner", aligner), \
                mock.patch.object(H, "romanize_words", _fake_romanize), \
                mock.patch.object(H.asr_mod, "transcribe",
                                  return_value=(sc["asr"], "fake")) as tr, \
                mock.patch.object(H.vad_mod, "detect_speech",
                                  return_value=list(speech)), \
                contextlib.redirect_stdout(out):
            srt_path = Path(td) / "o.srt"
            H.run_hybrid_units(TEXT_UNITS, "a.m4a", str(srt_path),
                               mode="tefila", profile="singing", work_dir=td,
                               debug=debug)
            srt = srt_path.read_text(encoding="utf-8-sig")
            report = srt_path.with_suffix(".report.txt").read_text(
                encoding="utf-8")
        sys.path.insert(0, str(_REPO / "tools"))
        import run_local
        return dict(sc=sc, debug=debug, log=out.getvalue(), report=report,
                    cues=run_local.parse_srt(srt), transcribe=tr)

    def test_end_to_end(self):
        r = self._run()
        sc, cues = r["sc"], r["cues"]
        self.assertEqual(r["transcribe"].call_args.kwargs.get("vad_filter"),
                         False)
        self.assertEqual(StarFake.inits, [{"with_star": True}])
        self.assertTrue(all(st is not None and st[0] and st[-1]
                             for _, st in StarFake.calls))
        runs = r["debug"]["nontext_runs"]
        self.assertEqual([x["text"] for x in runs],
                         [" ".join(INTRO), " ".join(MELODY)])
        self.assertEqual([x["pseudo_ref"] for x in runs], [0, sc["w3"]])
        self.assertIn("זוהה דיבור שאינו בטקסט", r["report"])
        self.assertIn("«" + " ".join(MELODY) + "»", r["report"])
        self.assertIn("פרופיל: שירה", r["report"])
        # ההקדמה לא מכוסה; שורה 3 מתחילה אחרי שם הניגון; הכתובית שלפניה נקטעת
        self.assertGreaterEqual(cues[0]["start"], sc["intro_end"] - 1e-3)
        i3 = sc["line3_seg"]
        self.assertGreaterEqual(cues[i3]["start"], sc["mel"][1] - 1e-3)
        self.assertLessEqual(cues[i3 - 1]["end"], sc["mel"][0] + 1e-3)
        # VAD זיהה מעט דיבור ⇒ בלי הצמדה
        self.assertIn("בלי הצמדה", r["log"])
        self.assertFalse(r["debug"]["vad_ran"])

    def test_vad_snaps_when_mostly_speech(self):
        sc = _scenario()
        r = self._run(speech=[(0.0, sc["audio"] / 16000)])
        self.assertTrue(r["debug"]["vad_ran"])
        self.assertIn("הוצמדו", r["log"])

    def test_start_gap_fails_window_and_interpolates_outside_runs(self):
        r = self._run(aligner=GapFake, line3_sparse=True)
        statuses = [a["status"] for a in r["debug"]["window_attempts"]]
        self.assertIn("start_gap_too_long", statuses)
        mel = r["sc"]["mel"]
        spans = r["debug"]["word_spans"]
        w3 = r["sc"]["w3"]
        self.assertTrue(any(r["debug"]["interpolated"][w3:]))
        for s, e, _ in spans[w3:]:
            self.assertGreaterEqual(s, mel[1])  # לא בתוך שם הניגון


class TestBuildSrtGaps(unittest.TestCase):
    def test_cue_cut_at_gap(self):
        segs = [{"display": "א", "align_vocalized": ["א"]},
                {"display": "ב", "align_vocalized": ["ב"]}]
        spans = [(1.0, 2.0), (10.0, 11.0)]
        self.assertIn("00:00:01,000 --> 00:00:10,000", build_srt(segs, spans))
        self.assertIn("00:00:01,000 --> 00:00:07,000",
                      build_srt(segs, spans, gaps=[(7.0, 9.5)]))
        # קטע שחוצה את תחילת הכתובית הבאה — לא קוטע
        self.assertIn("00:00:01,000 --> 00:00:10,000",
                      build_srt(segs, spans, gaps=[(9.0, 10.5)]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
