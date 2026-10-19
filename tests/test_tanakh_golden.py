# -*- coding: utf-8 -*-
"""בדיקת "זהב" לתנ״ך: הרפקטור ליחידות טקסט (PLAN_TEFILA.md 4.1.3) לא שינה דבר.

המימושים הישנים (לפני הרפקטור) מוקפאים כאן כלשונם — verses_to_segments,
‏_verse_start_flags, ‏format_report ו-run_hybrid — ומושווים מול המסלול החדש:
‏1. אותם מקטעים (display / align_vocalized / align_plain) ואותם דגלי פסוק.
‏2. ‏run_hybrid מלא עם mocks של ASR / ‏MmsAligner / ‏VAD (בלי torch, רשת או
   GPU): אותם קלטים למיישר, לעוגנים ול-VAD, ואותו SRT, דוח ויומן.

**אסור למזג שינוי בצינור בלי שהבדיקה הזו ירוקה.**

הרצה:  python3 -m unittest discover -s tests -v
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner import hybrid as H  # noqa: E402
from aligner.pipeline import (  # noqa: E402
    units_to_segments,
    verse_units,
    verses_to_segments,
)
from chunker import (  # noqa: E402
    clean_sefaria_text,
    regroup_words,
    segments_for_pipeline,
    tokenize,
)


# --- המימושים הישנים, מוקפאים (קומיט eb28576) -----------------------------------

def old_verses_to_segments(verses: list, max_words: int = 4, splits=None) -> list:
    if splits:
        words, verse_of = [], []
        for vi, verse in enumerate(verses, 1):
            toks = tokenize(clean_sefaria_text(verse))
            words.extend(toks)
            verse_of.extend([vi] * len(toks))
        return regroup_words(words, splits, verse_of)
    segments = []
    for vi, verse in enumerate(verses, 1):
        for seg in segments_for_pipeline(verse, max_words):
            seg["verse"] = vi
            segments.append(seg)
    return segments


def old_verse_start_flags(segments: list) -> list:
    flags, prev = [], None
    for seg in segments:
        flags.append(seg.get("verse") != prev)
        prev = seg.get("verse")
    return flags


def old_format_report(segments: list, confidences: list, infos: list,
                      starts: list, threshold: float = 0.5) -> str:
    _reasons = H.conf_mod._reasons
    low = [i for i, c in enumerate(confidences) if c < threshold]
    lines = [
        "דוח איכות הסנכרון",
        "=" * 40,
        f"מקטעים: {len(segments)} | ביטחון חציוני: "
        f"{sorted(confidences)[len(confidences) // 2]:.2f} | "
        f"לבדיקה ידנית: {len(low)}",
        "",
    ]
    if not low:
        lines.append("כל המקטעים בביטחון סביר — ייבא ל-CapCut ובדוק בעין.")
    else:
        lines.append(f"מקטעים בביטחון נמוך (<{threshold}) — מומלץ לגרור ידנית:")
        for i in low:
            seg = segments[i]
            m, s = divmod(int(starts[i]), 60)
            lines.append(
                f"  [{m:02d}:{s:02d}] פסוק {seg.get('verse', '?')} | "
                f"ביטחון {confidences[i]:.2f} | {seg['display']}")
            lines.append(f"        סיבה: {_reasons(infos[i])}")
    return "\n".join(lines)


def old_run_hybrid(book, chapter, audio_path, out_srt_path,
                   verse_start=None, chapter_end=None, verse_end=None,
                   max_words=4, asr_model=None, work_dir=".", splits=None):
    """run_hybrid כפי שהיה — כל שם מודול נשלף דרך H כדי שה-mocks יחולו."""
    book = H.to_english(book)
    print(f"1/8 מאתר את גרסת MAM עבור {book}…")
    version = H.find_mam_version(book)
    ref = H.build_ref(book, chapter, verse_start, chapter_end, verse_end)
    print(f"    גרסה: «{version}» | טווח: {ref}")

    print("2/8 מושך את הטקסט וחותך לפי טעמים…")
    verses = H.fetch_verses(ref, version)
    segments = old_verses_to_segments(verses, max_words, splits)
    if splits:
        print("    חלוקת הכתוביות נלקחה מהעריכה הידנית בממשק")
    flat_vocalized = [w for s in segments for w in s["align_vocalized"]]
    flat_plain = [w for s in segments for w in s["align_plain"]]
    print(f"    {len(verses)} פסוקים → {len(segments)} מקטעים "
          f"({len(flat_plain)} מילים)")

    print("3/8 טוען וממיר את ההקלטה (16kHz מונו)…")
    waveform = H.load_audio_16k_mono(audio_path, work_dir)
    wav_path = str(Path(work_dir) / H.WAV16K_NAME)
    audio_dur = waveform.size(1) / H._SAMPLE_RATE
    print(f"    משך: {audio_dur / 60:.1f} דקות")

    print("4/8 תמלול עברי (עוגנים בלבד — לא התזמון הסופי)…")
    asr_words, asr_name = H.asr_mod.transcribe(wav_path, model_name=asr_model)

    print("5/8 הצלבת התמלול עם טקסט Sefaria — איתור עוגנים…")
    found = H.anchors_mod.find_anchors(asr_words, flat_plain)
    anchor_list, coverage = found["anchors"], found["coverage"]
    print(f"    כיסוי התאמה: {coverage:.0%} | עוגנים: {len(anchor_list)}")
    if coverage < 0.4:
        print("    ⚠️ כיסוי נמוך — התמלול מתקשה בקריאה הזו. ממשיכים עם "
              "חלונות גדולים; בדוק את הדוח בסוף.")

    print("6/8 יישור מאולץ ממושכן (MMS על כל חלון בין עוגנים)…")
    window_list = H.win_mod.build_windows(anchor_list, len(flat_plain),
                                          audio_dur)
    print(f"    {len(window_list)} חלונות")
    aligner = H.MmsAligner()

    def align_fn(w):
        words = flat_vocalized[w["word_lo"]:w["word_hi"] + 1]
        roman = H.romanize_words(words)
        s0 = int(w["t_lo"] * H._SAMPLE_RATE)
        s1 = int(w["t_hi"] * H._SAMPLE_RATE)
        piece = waveform[:, s0:s1]
        n_tokens = sum(len(r) for r in roman)
        if piece.size(1) / H._FRAME_STRIDE < n_tokens * 1.1 + 4:
            return None
        try:
            spans = aligner.align(piece, roman, offset_sec=w["t_lo"])
        except Exception as e:
            print(f"    ⚠️ חלון מילים {w['word_lo']}–{w['word_hi']} נכשל "
                  f"({type(e).__name__}) — מנסה מיזוג/אינטרפולציה")
            return None
        if any(e - s > H._MAX_WORD_SEC for s, e, _ in spans):
            return None
        return spans

    aligned = H.win_mod.align_windows(window_list, align_fn, flat_plain)
    spans, interp_flags = H.win_mod.stitch(aligned, len(flat_plain))
    n_interp = sum(interp_flags)
    if n_interp:
        print(f"    {n_interp} מילים קיבלו זמן משוער (אינטרפולציה) — יסומנו בדוח")

    print("7/8 הצמדת גבולות לנשימות (VAD)…")
    word_spans = [(s, e) for s, e, _ in spans]
    starts, _ends = H.segment_bounds(segments, word_spans)
    verse_flags = old_verse_start_flags(segments)
    vad_ran = True
    try:
        speech = H.vad_mod.detect_speech(wav_path)
        starts, snap_dists = H.vad_mod.snap_boundaries(starts, speech,
                                                       verse_flags)
        print(f"    הוצמדו {sum(1 for d in snap_dists if d is not None)}"
              f"/{len(starts)} גבולות")
    except Exception as e:
        vad_ran = False
        snap_dists = [None] * len(starts)
        print(f"    ⚠️ VAD לא רץ ({type(e).__name__}) — ממשיכים בלי הצמדה")

    print("8/8 ניקוד ביטחון, SRT ודוח…")
    word_ranges = H._segment_word_ranges(segments)
    word_starts = [s for s, _, _ in spans]
    ctc_scores = H._segment_ctc_scores(word_ranges, spans)
    anchor_dists = H._anchor_dists(word_ranges,
                                   [a["ref"] for a in anchor_list])
    interp_segs = H._segment_interpolated(word_ranges, interp_flags)
    asr_gaps = H._asr_gaps(word_ranges, found["matches"], word_starts)
    infos = [{
        "ctc_score": ctc_scores[i],
        "anchor_dist": anchor_dists[i],
        "interpolated": interp_segs[i],
        "asr_gap": asr_gaps[i],
        "vad_snapped": (snap_dists[i] is not None) if vad_ran else None,
    } for i in range(len(segments))]
    confs = H.conf_mod.score_segments(infos)

    srt = H.build_srt(segments, word_spans, starts_override=starts)
    Path(out_srt_path).write_text(srt, encoding="utf-8-sig")
    report = old_format_report(segments, confs, infos, starts)
    report_path = str(Path(out_srt_path).with_suffix(".report.txt"))
    Path(report_path).write_text(
        f"מודל תמלול: {asr_name} | כיסוי: {coverage:.0%} | "
        f"עוגנים: {len(anchor_list)} | חלונות: {len(window_list)}\n\n" + report,
        encoding="utf-8")
    print(f"✅ נוצר: {out_srt_path}")
    print(f"📋 דוח איכות: {report_path}")
    return out_srt_path


# --- פסוקים סינתטיים (כמו ב-test_chunker.py) ------------------------------------

BERESHIT_1 = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
BERESHIT_2 = "וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֙הוּ֙ וָבֹ֑הוּ"
KETIV_QERE = "וְקָרְב֣וּ (ידו) יָדָ֔יו אֶל־הָעָֽם׃"
KETIV_SEG = "יָדָ֥יו (ידו) חָזָֽק׃"
SHEM = "וַיֹּ֥אמֶר יְהוָ֖ה אֶל־מֹשֶׁ֣ה לֵּאמֹ֑ר"
EMET = "בִּנְא֣וֹת דֶּ֭שֶׁא יַרְבִּיצֵ֑נִי עַל־מֵ֖י מְנֻח֣וֹת יְנַהֲלֵֽנִי׃"
TAGGED = "<big>בְּ</big>רֵאשִׁ֖ית בָּרָ֣א&nbsp;אֱלֹהִ֑ים {פ}"
ALL_KETIV = "(ידו)"  # פסוק שכולו בלתי-נשמע — נעלם בחיתוך, מוזג בחלוקה

VERSE_SETS = {
    "single": [BERESHIT_1],
    "two": [BERESHIT_1, BERESHIT_2],
    "ketiv_qere": [KETIV_QERE, KETIV_SEG, SHEM],
    "emet": [EMET, BERESHIT_2],
    "tagged": [TAGGED, BERESHIT_1],
    "all_ketiv_inside": [BERESHIT_1, ALL_KETIV, BERESHIT_2],
    "all_ketiv_first": [ALL_KETIV, BERESHIT_2],
    "mixed": [BERESHIT_1, BERESHIT_2, KETIV_QERE, KETIV_SEG, SHEM, EMET],
}


def _n_words(verses):
    return sum(len(tokenize(clean_sefaria_text(v))) for v in verses)


def _split_cases(verses):
    """כמה חלוקות ידניות תקינות: מילה-מילה, זוגות, הכול-אחד, וחוצת-פסוק."""
    n = _n_words(verses)
    pairs = [2] * (n // 2) + ([1] if n % 2 else [])
    cases = [[1] * n, pairs, [n]]
    if n >= 3:
        cases.append([1, n - 2, 1])
    return cases


def _lists(segments):
    return ([s["display"] for s in segments],
            [s["align_vocalized"] for s in segments],
            [s["align_plain"] for s in segments])


class TestSegmentsGolden(unittest.TestCase):
    """המקטעים ודגלי הפסוק — זהים לחלוטין למימוש הישן."""

    def _check(self, verses, max_words=4, splits=None):
        old = old_verses_to_segments(verses, max_words, splits)
        # verses_to_segments נשאר בחתימתו ובפלטו המדויק (כולל "verse")
        self.assertEqual(verses_to_segments(verses, max_words, splits), old)
        # המסלול החדש: יחידות verse/taamim
        new = units_to_segments(verse_units(verses), max_words, splits)
        self.assertEqual(_lists(new), _lists(old))
        self.assertEqual(H._unit_start_flags(new), old_verse_start_flags(old))
        self.assertEqual(H._verse_start_flags(old), old_verse_start_flags(old))
        self.assertEqual([s["label"] for s in new],
                         [f"פסוק {s['verse']}" for s in old])

    def test_taamim_cut_all_sets_and_max_words(self):
        for name, verses in VERSE_SETS.items():
            for max_words in (1, 2, 3, 4, 6, 8):
                with self.subTest(set=name, max_words=max_words):
                    self._check(verses, max_words)

    def test_custom_splits_all_sets(self):
        for name, verses in VERSE_SETS.items():
            for splits in _split_cases(verses):
                with self.subTest(set=name, splits=splits):
                    self._check(verses, splits=splits)

    def test_bad_splits_raise_the_same(self):
        verses = VERSE_SETS["two"]
        for splits in ([2], [_n_words(verses) - 1, 0, 1]):
            with self.assertRaises(ValueError):
                old_verses_to_segments(verses, splits=splits)
            with self.assertRaises(ValueError):
                units_to_segments(verse_units(verses), splits=splits)

    def test_report_text_identical(self):
        verses = VERSE_SETS["mixed"]
        old = old_verses_to_segments(verses)
        new = units_to_segments(verse_units(verses))
        confs = [0.2 if i % 2 else 0.9 for i in range(len(old))]
        infos = [{"interpolated": bool(i % 3), "anchor_dist": i}
                 for i in range(len(old))]
        starts = [i * 7.3 for i in range(len(old))]
        expected = old_format_report(old, confs, infos, starts)
        self.assertEqual(H.conf_mod.format_report(new, confs, infos, starts),
                         expected)
        self.assertEqual(H.conf_mod.format_report(old, confs, infos, starts),
                         expected)


class TestUnits(unittest.TestCase):
    """חוזה היחידות: instruction מחוץ ליישור, unit/label, נקודות החיבור."""

    def test_instruction_units_excluded(self):
        units = [
            {"text": BERESHIT_1, "label": "א", "kind": "verse", "chunk": "taamim"},
            {"text": "בַּעֲשֶׂ֖רֶת יְמֵ֥י תְשׁוּבָֽה׃", "label": "הוראה",
             "kind": "instruction", "chunk": "taamim"},
            {"text": BERESHIT_2, "label": "ב", "kind": "verse", "chunk": "taamim"},
        ]
        segs = units_to_segments(units)
        self.assertEqual(_lists(segs),
                         _lists(old_verses_to_segments([BERESHIT_1, BERESHIT_2])))
        self.assertEqual(sorted({s["unit"] for s in segs}), [0, 2])
        self.assertEqual(sorted({s["label"] for s in segs}), ["א", "ב"])
        n = _n_words([BERESHIT_1, BERESHIT_2])
        split_segs = units_to_segments(units, splits=[n])
        self.assertEqual(len(split_segs), 1)
        self.assertEqual(split_segs[0]["unit"], 0)

    def test_chunk_detected_from_taamim(self):
        units = [{"text": BERESHIT_1, "label": "x", "kind": "line"}]
        self.assertEqual(_lists(units_to_segments(units)),
                         _lists(old_verses_to_segments([BERESHIT_1])))

    def test_punct_chunk_routed_to_prose_chunker(self):
        """יחידה בלי טעמים ⇒ החותך לפי פיסוק (4.1.1) — חותך בפסיק."""
        units = [{"text": "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ, עוֹד יְהַלְלוּךָ",
                  "label": "אשרי · 1", "kind": "line"}]
        segs = units_to_segments(units)
        self.assertEqual([s["display"] for s in segs],
                         ["אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ,", "עוֹד יְהַלְלוּךָ"])
        self.assertEqual({s["label"] for s in segs}, {"אשרי · 1"})

    def test_unknown_chunk_rejected(self):
        with self.assertRaises(ValueError):
            units_to_segments([{"text": BERESHIT_1, "chunk": "rhyme"}])

    def test_tefila_mode_same_on_verse_without_ketiv(self):
        """מצב תפילה (4.1.2) על פסוק בלי כתיב — אותן מילות יישור כמו בתנ״ך."""
        units = verse_units([BERESHIT_1, BERESHIT_2])
        self.assertEqual(_lists(units_to_segments(units, mode="tefila")),
                         _lists(units_to_segments(units)))

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            units_to_segments(verse_units([BERESHIT_1]), mode="tanach")

    def test_unit_start_flags_follow_units(self):
        segs = [{"unit": 0}, {"unit": 0}, {"unit": 3}, {"unit": 4}]
        self.assertEqual(H._unit_start_flags(segs), [True, False, True, True])

    def test_report_uses_label(self):
        segs = [{"display": "אבג", "label": "אשרי · 3"}]
        report = H.conf_mod.format_report(segs, [0.1], [{}], [0.0])
        self.assertIn("אשרי · 3 |", report)
        self.assertNotIn("פסוק", report)


# --- run_hybrid מלא עם mocks -------------------------------------------------

class FakeWave:
    """מחקה tensor בצורה [1, n] — רק מה שהצינור נוגע בו."""

    def __init__(self, n):
        self.n = n

    def size(self, dim):
        return self.n if dim == 1 else 1

    def __getitem__(self, key):
        return FakeWave(len(range(self.n)[key[1]]))


class FakeAligner:
    """מיישר דטרמיניסטי שרושם כל קריאה; כל קריאה שלישית נכשלת."""

    calls = []

    def __init__(self, *a, **kw):
        pass

    def align(self, piece, roman, offset_sec=0.0):
        FakeAligner.calls.append((piece.n, tuple(roman), round(offset_sec, 6)))
        if len(FakeAligner.calls) % 3 == 0:
            raise RuntimeError("כשל מדומה")
        dur = piece.n / 16000
        step = dur / len(roman)
        return [(offset_sec + i * step, offset_sec + (i + 0.8) * step,
                 0.3 + 0.1 * (i % 7)) for i in range(len(roman))]


def _fake_romanize(words):
    return ["ab"[:1 + len(w) % 2] for w in words]


class TestRunHybridGolden(unittest.TestCase):
    """run_hybrid החדש מול הישן: אותם קלטים למיישר, ל-VAD, ואותו פלט."""

    SEC_PER_WORD = 0.6

    def _run(self, fn, verses, splits=None, max_words=4, vad_fails=False):
        flat_plain = [w for s in old_verses_to_segments(verses, max_words,
                                                        splits)
                      for w in s["align_plain"]]
        # ‏ASR מדומה: כל מילה רביעית "נבלעה", כך שיש עוגנים וגם פערים
        asr_words = [{"word": w, "start": i * self.SEC_PER_WORD,
                      "end": i * self.SEC_PER_WORD + 0.4, "prob": 0.9}
                     for i, w in enumerate(flat_plain) if i % 4 != 3]
        audio_n = int((len(flat_plain) * self.SEC_PER_WORD + 1.5) * 16000)
        speech = [(i * self.SEC_PER_WORD - 0.1, i * self.SEC_PER_WORD + 0.5)
                  for i in range(0, len(flat_plain), 3)]
        anchor_calls, snap_calls = [], []
        real_find, real_snap = (H.anchors_mod.find_anchors,
                                H.vad_mod.snap_boundaries)

        def find_spy(asr, plain, *a, **kw):
            anchor_calls.append((list(asr), list(plain)))
            return real_find(asr, plain, *a, **kw)

        def snap_spy(starts, regions, flags, *a, **kw):
            snap_calls.append((list(starts), list(regions), list(flags)))
            return real_snap(starts, regions, flags, *a, **kw)

        def detect(_wav):
            if vad_fails:
                raise ImportError("אין silero")
            return speech

        FakeAligner.calls = []
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as td, \
                mock.patch.object(H, "find_mam_version",
                                  return_value="Miqra according to the Masorah"), \
                mock.patch.object(H, "fetch_verses", return_value=list(verses)), \
                mock.patch.object(H, "load_audio_16k_mono",
                                  return_value=FakeWave(audio_n)), \
                mock.patch.object(H, "MmsAligner", FakeAligner), \
                mock.patch.object(H, "romanize_words", _fake_romanize), \
                mock.patch.object(H.asr_mod, "transcribe",
                                  return_value=(asr_words, "fake-asr")), \
                mock.patch.object(H.anchors_mod, "find_anchors", find_spy), \
                mock.patch.object(H.vad_mod, "detect_speech", detect), \
                mock.patch.object(H.vad_mod, "snap_boundaries", snap_spy), \
                contextlib.redirect_stdout(out):
            srt_path = str(Path(td) / "out.srt")
            ret = fn("בראשית", 1, "rec.m4a", srt_path, verse_start=1,
                     verse_end=len(verses), max_words=max_words,
                     work_dir=td, splits=splits)
            srt = Path(srt_path).read_text(encoding="utf-8-sig")
            report = Path(srt_path).with_suffix(".report.txt").read_text(
                encoding="utf-8")
            log = out.getvalue().replace(td, "<td>")
            ret = ret.replace(td, "<td>")
        return {"aligner": list(FakeAligner.calls), "anchors": anchor_calls,
                "snap": snap_calls, "srt": srt, "report": report,
                "log": log, "ret": ret}

    def _compare(self, verses, **kw):
        old = self._run(old_run_hybrid, verses, **kw)
        new = self._run(H.run_hybrid, verses, **kw)
        self.assertTrue(old["aligner"], "המיישר לא נקרא — הבדיקה ריקה")
        for key in ("aligner", "anchors", "snap", "srt", "report", "log",
                    "ret"):
            self.assertEqual(new[key], old[key], key)
        return old

    def test_same_aligner_inputs_taamim_cut(self):
        verses = VERSE_SETS["mixed"] * 3
        old = self._compare(verses)
        self.assertTrue(old["snap"])  # ה-VAD קיבל דגלי פסוק
        self.assertIn("נכשל", old["log"])  # מסלול הכשל/אינטרפולציה נבדק

    def test_same_aligner_inputs_custom_splits(self):
        verses = VERSE_SETS["mixed"] * 2
        n = _n_words(verses)
        self._compare(verses, splits=[3] * (n // 3) + ([n % 3] if n % 3 else []))

    def test_same_aligner_inputs_small_max_words(self):
        self._compare(VERSE_SETS["all_ketiv_inside"] * 4, max_words=2)

    def test_same_when_vad_fails(self):
        self._compare(VERSE_SETS["ketiv_qere"] * 3, vad_fails=True)


class TestRunHybridUnits(unittest.TestCase):
    """run_hybrid_units: רק ערכי ברירת המחדל של performance/profile בינתיים."""

    def test_non_default_performance_rejected(self):
        with self.assertRaises(NotImplementedError):
            H.run_hybrid_units(verse_units([BERESHIT_1]), "a.m4a", "o.srt",
                               performance=[0, 0])

    def test_non_default_profile_rejected(self):
        with self.assertRaises(NotImplementedError):
            H.run_hybrid_units(verse_units([BERESHIT_1]), "a.m4a", "o.srt",
                               profile="singing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
