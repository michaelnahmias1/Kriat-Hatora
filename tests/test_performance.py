# -*- coding: utf-8 -*-
"""סדר ביצוע (PLAN_TEFILA.md 3.2, ‏4.3.2) ו"כנראה דולג" (4.3.4) — בלי מודלים.

- expand_performance: פריסה, דילוג, חזרה, פזמון אחרי כל בית, ספירות, תוויות,
  ולידציה (טווח אחרי החיתוך/‏splits, תקרות).
- דגלי תחילת יחידה על הרצף הפרוס: כל קפיצה פותחת הופעה חדשה.
- צינור מלא עם mocks: ביצוע לינארי = בלי performance (אותו SRT ודוח, בשני
  הפרופילים); פזמון — כתובית לכל הופעה; עוגן-דמה וכוכב על הופעה חוזרת;
  "כנראה דולג" בדוח (תפילה בלבד); אינדקס מחוץ לטווח נכשל לפני טעינת ההקלטה.
- ניתוב params ⇐ pipeline_call ⇐ run_hybrid_units עם performance.
"""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "tests"))
sys.path.insert(0, str(_REPO / "tools"))

from aligner import hybrid as H  # noqa: E402
from aligner.confidence import format_report  # noqa: E402
from aligner.pipeline import units_to_segments  # noqa: E402
from test_singing import StarFake  # noqa: E402
from test_tanakh_golden import FakeWave, _fake_romanize  # noqa: E402
import run_local  # noqa: E402

_SPEC = importlib.util.spec_from_file_location(
    "modal_params_perf", _REPO / "modal_worker" / "params.py")
params = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(params)

# לכה דודי מקוצרת: פזמון (2 כתוביות) ושני בתים (2 כתוביות כל אחד)
UNITS = [
    {"text": "לְכָה דוֹדִי לִקְרַאת כַּלָּה, פְּנֵי שַׁבָּת נְקַבְּלָה:",
     "label": "פזמון", "kind": "refrain"},
    {"text": "שָׁמוֹר וְזָכוֹר בְּדִבּוּר אֶחָד, הִשְׁמִיעָנוּ אֵל הַמְיֻחָד:",
     "label": "בית 1", "kind": "stanza"},
    {"text": "לִקְרַאת שַׁבָּת לְכוּ וְנֵלְכָה, כִּי הִיא מְקוֹר הַבְּרָכָה:",
     "label": "בית 2", "kind": "stanza"},
]
# פזמון בהתחלה ואחרי כל בית
REFRAIN_ORDER = [0, 1, 2, 3, 0, 1, 4, 5, 0, 1]


def _segs():
    return units_to_segments(UNITS, 4, mode="tefila")


class TestExpand(unittest.TestCase):
    def test_base_segments(self):
        segs = _segs()
        self.assertEqual([s["unit"] for s in segs], [0, 0, 1, 1, 2, 2])

    def test_none_is_identity(self):
        segs = _segs()
        self.assertIs(H.expand_performance(segs, None), segs)

    def test_linear(self):
        segs = _segs()
        out = H.expand_performance(segs, list(range(len(segs))))
        self.assertEqual([s["display"] for s in out],
                         [s["display"] for s in segs])
        self.assertEqual([s["label"] for s in out], [s["label"] for s in segs])
        self.assertTrue(all(s["occurrence"] == 1 for s in out))
        self.assertEqual(H._unit_start_flags(out), H._unit_start_flags(segs))

    def test_skip(self):
        segs = _segs()
        out = H.expand_performance(segs, [0, 1, 4, 5])  # בית 1 דולג
        self.assertEqual([s["unit"] for s in out], [0, 0, 2, 2])
        self.assertEqual([s["seg_index"] for s in out], [0, 1, 4, 5])
        self.assertEqual(H._unit_start_flags(out), [True, False, True, False])

    def test_refrain_after_every_stanza(self):
        segs = _segs()
        out = H.expand_performance(segs, REFRAIN_ORDER)
        self.assertEqual(len(out), len(REFRAIN_ORDER))
        self.assertEqual([s["occurrence"] for s in out],
                         [1, 1, 1, 1, 2, 2, 1, 1, 3, 3])
        self.assertEqual([s["label"] for s in out],
                         ["פזמון", "פזמון", "בית 1", "בית 1",
                          "פזמון · חזרה 2", "פזמון · חזרה 2", "בית 2", "בית 2",
                          "פזמון · חזרה 3", "פזמון · חזרה 3"])
        self.assertEqual(H._unit_start_flags(out),
                         [True, False] * 5)
        n_words = sum(len(segs[i]["align_plain"]) for i in REFRAIN_ORDER)
        self.assertEqual(sum(len(s["align_plain"]) for s in out), n_words)
        self.assertEqual(H._unit_start_words(out),
                         [0, 7, 14, 21, 29])  # 7 מילים בשורה, בבית 2 — 8
        # הבסיס לא השתנה (העתקים, לא עריכה במקום)
        self.assertEqual(segs[0]["label"], "פזמון")
        self.assertNotIn("seg_index", segs[0])

    def test_repeat_same_line_back_to_back(self):
        """שורה אחת (מקטע יחיד) פעמיים ברצף — שתי הופעות, שתיהן תחילת שורה."""
        segs = units_to_segments([{"text": "אָמֵן אָמֵן", "label": "ש"}], 4,
                                 mode="tefila")
        out = H.expand_performance(segs, [0, 0])
        self.assertEqual(H._unit_start_flags(out), [True, True])
        # גם חזרה אחורה בתוך אותה יחידה פותחת הופעה
        out = H.expand_performance(_segs(), [0, 1, 0, 1])
        self.assertEqual(H._unit_start_flags(out), [True, False, True, False])

    def test_validation(self):
        segs = _segs()
        for bad in ([], [0, 6], [-1], [0, True], [0, 1.0], "0,1", {}):
            with self.assertRaises(ValueError, msg=repr(bad)) as cm:
                H.expand_performance(segs, bad)
            self.assertRegex(str(cm.exception), "סדר הביצוע")
        with self.assertRaisesRegex(ValueError, "6 כתוביות"):
            H.expand_performance(segs, [6])
        with self.assertRaisesRegex(ValueError, "ארוך מדי"):
            H.expand_performance(segs, [0] * (H.MAX_PERFORMANCE + 1))
        with mock.patch.object(H, "MAX_PERFORMED_WORDS", 20):
            with self.assertRaisesRegex(ValueError, "מילים"):
                H.expand_performance(segs, [0, 1, 0, 1, 0, 1])  # 21 מילים

    def test_range_is_after_splits(self):
        """הטווח נמדד אחרי החלוקה הידנית — לא מול החיתוך האוטומטי."""
        segs = units_to_segments(UNITS, 4, splits=[7, 7, 8], mode="tefila")
        self.assertEqual(len(segs), 3)
        H.expand_performance(segs, [0, 1, 0, 2])
        with self.assertRaises(ValueError):
            H.expand_performance(segs, [3])

    def test_range_is_after_merge(self):
        """הדפדפן שולח אינדקסים לכתוביות אחרי מיזוג כתובית בלי מילה נשמעת
        (כתיב, 8.22) — ‏len(splits) גדול מהן, והצינור בודק מול הספירה האמיתית."""
        units = [{"text": "כִּי הִשְׁקִיף מִמְּרוֹם הביט [הַבִּיטָה]",
                  "label": "ש"}]
        segs = units_to_segments(units, 4, splits=[3, 1, 1], mode="tefila")
        self.assertEqual(len(segs), 2)  # "הביט" התמזג לכתובית שלפניו
        self.assertEqual(len(H.expand_performance(segs, [0, 1, 0, 1])), 4)
        with self.assertRaisesRegex(ValueError, "2 כתוביות"):
            H.expand_performance(segs, [2])

    def test_report_labels(self):
        out = H.expand_performance(_segs(), REFRAIN_ORDER)
        report = format_report(out, [0.1] * len(out), [{}] * len(out),
                               [float(i) for i in range(len(out))])
        self.assertIn("פזמון · חזרה 2 |", report)
        self.assertIn("פזמון · חזרה 3 |", report)


class TestProbablySkipped(unittest.TestCase):
    def test_flags_long_unmatched_occurrence(self):
        out = H.expand_performance(_segs(), REFRAIN_ORDER)
        flags = H._unit_start_flags(out)
        # כל המילים זוהו חוץ מההופעה השנייה של הפזמון (מילים 14–20)
        matches = [{"ref": r, "sim": 1.0} for r in range(36)
                   if not 14 <= r <= 20]
        matches.append({"ref": 16, "sim": 0.6})  # מתחת לסף — לא נחשבת
        got = H._probably_skipped(out, flags, matches)
        self.assertEqual([(k["seg"], k["label"], k["words"]) for k in got],
                         [(4, "פזמון · חזרה 2", 7)])
        lines = H._skipped_lines(got)
        self.assertIn("כנראה דולג", lines[0])
        self.assertIn("כתובית 5 · פזמון · חזרה 2 | 7 מילים", lines[1])

    def test_short_or_matched_not_flagged(self):
        segs = _segs()
        flags = H._unit_start_flags(segs)
        self.assertEqual(H._probably_skipped(segs, flags, []), [
            {"seg": 0, "label": "פזמון", "words": 7,
             "display": segs[0]["display"] + " " + segs[1]["display"]},
            {"seg": 2, "label": "בית 1", "words": 7,
             "display": segs[2]["display"] + " " + segs[3]["display"]},
            {"seg": 4, "label": "בית 2", "words": 8,
             "display": segs[4]["display"] + " " + segs[5]["display"]}])
        self.assertEqual(H._probably_skipped(segs, flags, [], min_words=9), [])
        one = [{"ref": 3, "sim": 0.9}]
        self.assertEqual(len(H._probably_skipped(segs, flags, one)), 2)
        self.assertEqual(H._skipped_lines([]), [])


# --- צינור מלא עם mocks -----------------------------------------------------------

def _asr(segments, omit_segs=(), sec_per_word=0.9, lead=1.0, intro=None,
         garble=()):
    """תמלול מדומה של הרצף (הפרוס): מילה כל sec_per_word; מקטעים ב-omit_segs
    "נאמרו" (תופסים זמן) אבל לא תומללו. ‏intro — מילות דיבור קצרות לפני
    המקטע שאינדקסו intro[0] (פרופיל שירה: דיבור שאינו בטקסט). ‏garble —
    מקטעים שהמילה הראשונה שלהם משובשת בתמלול (לא תהיה עוגן)."""
    asr, t = [], lead
    for i, seg in enumerate(segments):
        if intro and i == intro[0]:
            t += 1.0
            for w in intro[1]:
                asr.append({"word": w, "start": t, "end": t + .3, "prob": .9})
                t += .35
            t += 1.0
        for k, w in enumerate(seg["align_plain"]):
            if i in garble and k == 0:
                w = "מינשמע"
            if i not in omit_segs:
                asr.append({"word": w, "start": t, "end": t + .8 * sec_per_word,
                            "prob": .9})
            t += sec_per_word
    return asr, int((t + 2) * 16000)


def _run(units, *, performance=None, profile="reading", asr_segments=None,
         omit_segs=(), intro=None, garble=(), mode="tefila", splits=None,
         **extra):
    base = units_to_segments(units, 4, splits, mode)
    expanded = H.expand_performance(base, performance) if performance else base
    asr, n_audio = _asr(asr_segments or expanded, omit_segs, intro=intro,
                        garble=garble)
    StarFake.inits, StarFake.calls = [], []
    debug, out = {}, io.StringIO()
    with tempfile.TemporaryDirectory() as td, \
            mock.patch.object(H, "load_audio_16k_mono",
                              return_value=FakeWave(n_audio)) as load, \
            mock.patch.object(H, "MmsAligner", StarFake), \
            mock.patch.object(H, "romanize_words", _fake_romanize), \
            mock.patch.object(H.asr_mod, "transcribe",
                              return_value=(asr, "fake")), \
            mock.patch.object(H.vad_mod, "detect_speech",
                              return_value=[(0.0, n_audio / 16000)]), \
            contextlib.redirect_stdout(out):
        srt_path = Path(td) / "o.srt"
        kw = dict(mode=mode, profile=profile, work_dir=td, debug=debug,
                  splits=splits, **extra)
        if performance is not None:
            kw["performance"] = performance
        H.run_hybrid_units(units, "a.m4a", str(srt_path), **kw)
        srt = srt_path.read_text(encoding="utf-8-sig")
        report = srt_path.with_suffix(".report.txt").read_text(
            encoding="utf-8")
    return dict(srt=srt, report=report, log=out.getvalue(), debug=debug,
                cues=run_local.parse_srt(srt), load=load)


class TestPerformancePipeline(unittest.TestCase):
    def test_linear_equals_no_performance(self):
        n = len(_segs())
        for profile in ("reading", "singing"):
            a = _run(UNITS, profile=profile)
            b = _run(UNITS, profile=profile, performance=list(range(n)))
            self.assertEqual(a["srt"], b["srt"], profile)
            self.assertEqual(a["report"], b["report"], profile)
            self.assertIn("סדר ביצוע: 6 הופעות של 6 כתוביות (חזרות: 0, "
                          "דילוגים: 0)", b["log"])

    def test_refrain_one_cue_per_occurrence(self):
        segs = _segs()
        r = _run(UNITS, performance=REFRAIN_ORDER)
        self.assertEqual([c["text"] for c in r["cues"]],
                         [segs[i]["display"] for i in REFRAIN_ORDER])
        starts = [c["start"] for c in r["cues"]]
        self.assertEqual(starts, sorted(starts))
        self.assertIn("(חזרות: 4, דילוגים: 0)", r["log"])
        flat = r["debug"]["flat_plain"]
        self.assertEqual(len(flat), 36)
        self.assertEqual(r["debug"]["unit_flags"], [True, False] * 5)
        # הופעה שנייה של הפזמון — בזמן שלה (0.9 ש׳ למילה מ-1.0), לא של הראשונה
        self.assertAlmostEqual(r["cues"][4]["start"], 1.0 + 14 * 0.9, delta=1.0)
        self.assertEqual(r["debug"]["probably_skipped"], [])

    def test_skip_drops_cues(self):
        segs = _segs()
        r = _run(UNITS, performance=[0, 1, 4, 5])
        self.assertEqual([c["text"] for c in r["cues"]],
                         [segs[i]["display"] for i in (0, 1, 4, 5)])
        self.assertIn("(חזרות: 0, דילוגים: 2)", r["log"])

    def test_singing_pseudo_anchor_and_stars_on_repeat(self):
        """דיבור לפני הופעה חוזרת של הפזמון ⇐ חסם תחתון לתחילת ההופעה
        (מילה 14), וכוכב לפני כל תחילת הופעה."""
        base = H.expand_performance(_segs(), REFRAIN_ORDER)
        r = _run(UNITS, performance=REFRAIN_ORDER, profile="singing",
                 intro=(4, ["עכשיו", "כולם", "ביחד", "בבקשה"]), garble={4})
        runs = r["debug"]["nontext_runs"]
        self.assertEqual([x["pseudo_ref"] for x in runs], [14])
        self.assertGreaterEqual(r["cues"][4]["start"], runs[0]["end"] - 1e-3)
        self.assertLessEqual(r["cues"][3]["end"], runs[0]["start"] + 1e-3)
        self.assertEqual(len(r["cues"]), len(base))
        # כל קריאה: כוכב בתחילה ובסוף, ובאמצע לפני כל תחילת הופעה שבחלון
        attempts = [x["window"] for x in r["debug"]["window_attempts"]
                    if x["status"] != "too_few_frames"]
        self.assertEqual(len(attempts), len(StarFake.calls))
        starts = set(H._unit_start_words(base))
        inner = 0
        for w, (n, st) in zip(attempts, StarFake.calls):
            self.assertEqual(st, [k == 0 or w["word_lo"] + k in starts
                                  for k in range(n)] + [True])
            inner += sum(st[1:-1])
        self.assertGreater(inner, 0)  # לפחות הופעה אחת באמצע חלון

    def test_probably_skipped_in_report_tefila_only(self):
        segs = _segs()
        expanded = H.expand_performance(segs, REFRAIN_ORDER)
        r = _run(UNITS, performance=REFRAIN_ORDER, asr_segments=expanded,
                 omit_segs={6, 7})  # בית 2 "לא נשמע" בתמלול
        self.assertEqual([(k["seg"], k["label"])
                          for k in r["debug"]["probably_skipped"]],
                         [(6, "בית 2")])
        self.assertIn("כנראה דולג", r["report"])
        self.assertIn("כתובית 7 · בית 2 | 8 מילים", r["report"])
        self.assertIn("כנראה דולג", r["log"])

    def test_out_of_range_fails_before_audio(self):
        for perf in ([0, 6], [0, -1]):
            with self.assertRaisesRegex(ValueError, "סדר הביצוע"), \
                    mock.patch.object(H, "load_audio_16k_mono") as load, \
                    contextlib.redirect_stdout(io.StringIO()):
                H.run_hybrid_units(UNITS, "a", "o.srt", mode="tefila",
                                   performance=perf)
            load.assert_not_called()

    def test_tanakh_mode_rejects_performance(self):
        with self.assertRaises(NotImplementedError):
            H.run_hybrid_units(UNITS, "a", "o.srt", performance=[0])


class TestParamsRouting(unittest.TestCase):
    """טופס ה-worker עם performance ⇐ pipeline_call ⇐ run_hybrid_units."""

    def _form(self, **extra):
        form = {"source": "siddur", "title": "לכה דודי",
                "units": json.dumps(UNITS, ensure_ascii=False)}
        form.update(extra)
        return form

    def _call(self, form):
        p = params.parse_params(form)
        name, kw = params.pipeline_call(p, "a.m4a", "o.srt", ".")
        self.assertEqual(name, "run_hybrid_units")
        return kw

    def test_routes_and_runs(self):
        kw = self._call(self._form(performance=json.dumps(REFRAIN_ORDER),
                                   profile="singing"))
        self.assertEqual(kw["performance"], REFRAIN_ORDER)
        units = kw.pop("units")
        for k in ("audio_path", "out_srt_path", "work_dir"):
            kw.pop(k)
        r = _run(units, **kw)
        self.assertEqual(len(r["cues"]), len(REFRAIN_ORDER))
        self.assertIn("פרופיל: שירה", r["report"])

    def test_splits_and_performance(self):
        kw = self._call(self._form(splits="[7, 7, 8]",
                                   performance="[0, 1, 0, 2, 0]"))
        units, splits, perf = kw["units"], kw["splits"], kw["performance"]
        r = _run(units, splits=splits, performance=perf)
        base = units_to_segments(units, 4, splits, "tefila")
        self.assertEqual([c["text"] for c in r["cues"]],
                         [base[i]["display"] for i in perf])

    def test_range_checked_in_pipeline_without_splits(self):
        """בלי splits ה-worker מעביר כל אינדקס; הצינור דוחה בעברית."""
        kw = self._call(self._form(performance="[0, 99]"))
        with self.assertRaisesRegex(ValueError, "מפנה לכתובית 99"), \
                contextlib.redirect_stdout(io.StringIO()):
            H.run_hybrid_units(kw["units"], "a", "o.srt", mode=kw["mode"],
                               performance=kw["performance"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
