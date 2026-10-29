# -*- coding: utf-8 -*-
"""tools/run_local.py ווו הדיבאג של run_hybrid_units — בלי מודלים, torch או רשת.

אותו סגנון mocks כמו test_tanakh_golden.py (ASR / ‏MmsAligner / ‏VAD מדומים):
1. ‏debug=None (ברירת המחדל) ומילון debug — אותו SRT, דוח ויומן בדיוק.
2. ‏run_local.main כותב SRT, דוח, יומן, asr.json ו-debug.json, והדאמפ מכיל
   תמלול, עוגנים, חלונות + סטטוס ניסיונות, זמני מילים, VAD והערכה מול
   ground truth.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "tools"))
sys.path.insert(0, str(_REPO / "tests"))

from aligner import hybrid as H  # noqa: E402
import run_local  # noqa: E402
from test_tanakh_golden import FakeAligner, FakeWave, _fake_romanize  # noqa: E402

TEXT = (
    "כִּי לה' הַמְּלוּכָה. וּמושֵׁל בַּגּויִם:\n"
    "וְהָיָה ה' לְמֶלֶךְ עַל כָּל הָאָרֶץ. בַּיּום הַהוּא יִהְיֶה ה' אֶחָד וּשְׁמו אֶחָד:\n"
    "נִשְׁמַת כָּל חַי תְּבָרֵךְ אֶת שִׁמְךָ ה' אֱלהֵינוּ וְרוּחַ כָּל בָּשָׂר"
    " תְּפָאֵר. וּמִבַּלְעֲדֶיךָ אֵין לָנוּ (מֶלֶךְ) גּואֵל וּמושִׁיעַ:\n\n"
)
SEC_PER_WORD = 0.7
INTRO = 5.0  # "הקדמה" שאינה בטקסט — המילים מתחילות אחריה


def _flat_plain():
    payload = run_local._load_pipeline()[1]({"text": TEXT, "mode": "tefila"})
    segs = H.units_to_segments(payload["units"], payload["max_words"],
                               mode="tefila")
    return [w for s in segs for w in s["align_plain"]]


def _fakes():
    plain = _flat_plain()
    # ‏ASR מדומה: הקדמה ("שלום לכולם") ואז הטקסט, כשכל מילה רביעית נבלעה
    asr = [{"word": "שלום", "start": 1.0, "end": 1.4, "prob": 0.9},
           {"word": "לכולם", "start": 1.5, "end": 2.0, "prob": 0.9}]
    asr += [{"word": w, "start": INTRO + i * SEC_PER_WORD,
             "end": INTRO + i * SEC_PER_WORD + 0.5, "prob": 0.9}
            for i, w in enumerate(plain) if i % 4 != 3]
    audio_n = int((INTRO + len(plain) * SEC_PER_WORD + 2) * 16000)
    speech = [(INTRO + i * SEC_PER_WORD - 0.1, INTRO + i * SEC_PER_WORD + 0.6)
              for i in range(0, len(plain), 3)]
    return asr, audio_n, speech


@contextlib.contextmanager
def _patched():
    asr, audio_n, speech = _fakes()
    FakeAligner.calls = []
    with mock.patch.object(H, "load_audio_16k_mono",
                           return_value=FakeWave(audio_n)), \
            mock.patch.object(H, "MmsAligner", FakeAligner), \
            mock.patch.object(H, "romanize_words", _fake_romanize), \
            mock.patch.object(H.asr_mod, "transcribe",
                              return_value=(asr, "fake-asr")), \
            mock.patch.object(H.vad_mod, "detect_speech",
                              return_value=speech):
        yield asr


class TestDebugHookIsInert(unittest.TestCase):
    def _run(self, debug):
        payload = run_local._load_pipeline()[1]({"text": TEXT, "mode": "tefila"})
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as td, _patched(), \
                contextlib.redirect_stdout(out):
            srt_path = str(Path(td) / "o.srt")
            H.run_hybrid_units(payload["units"], "a.m4a", srt_path,
                               max_words=payload["max_words"], mode="tefila",
                               work_dir=td, debug=debug)
            srt = Path(srt_path).read_text(encoding="utf-8-sig")
            report = Path(srt_path).with_suffix(".report.txt").read_text(
                encoding="utf-8")
            log = out.getvalue().replace(td, "<td>")
        return srt, report, log, list(FakeAligner.calls)

    def test_same_output_with_and_without_debug(self):
        debug = {}
        self.assertEqual(self._run(None), self._run(debug))
        for key in ("segments", "asr_words", "anchors", "coverage", "windows",
                    "window_attempts", "aligned", "word_spans", "starts_raw",
                    "speech", "starts", "snap_dists", "confidences"):
            self.assertIn(key, debug)
        statuses = {a["status"] for a in debug["window_attempts"]}
        self.assertIn("ok", statuses)


class TestRunLocal(unittest.TestCase):
    def test_main_writes_outputs_and_dump(self):
        with tempfile.TemporaryDirectory() as td, _patched():
            text_file = Path(td) / "text.txt"
            text_file.write_text(TEXT, encoding="utf-8")
            truth_file = Path(td) / "gt.json"
            truth_file.write_text(json.dumps({
                "line_starts": [{"line": 1, "start": INTRO},
                                {"line": 3, "start": 30.0}],
                "non_text_speech": [{"start": 0.0, "end": INTRO}]}),
                encoding="utf-8")
            out_dir = Path(td) / "out"
            with contextlib.redirect_stdout(io.StringIO()):
                dump = run_local.main([
                    "--audio", str(Path(td) / "rec.m4a"),
                    "--text-file", str(text_file), "--out-dir", str(out_dir),
                    "--ground-truth", str(truth_file)])
            for name in ("rec.srt", "rec.report.txt", "run.log", "asr.json",
                         "debug.json"):
                self.assertTrue((out_dir / name).exists(), name)
            self.assertIn("6/8", (out_dir / "run.log").read_text(encoding="utf-8"))
            saved = json.loads((out_dir / "debug.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["meta"]["mode"], "tefila")

        self.assertEqual(dump["transcription"][0]["word"], "שלום")
        self.assertEqual(len(dump["words"]), dump["n_text_words"])
        self.assertTrue(dump["anchors"])
        a = dump["anchors"][0]
        self.assertEqual(a["asr_word"], dump["words"][a["ref"]]["plain"])
        self.assertEqual(len(dump["anchor_coverage_per_unit"]), 3)
        self.assertTrue(dump["windows_initial"])
        self.assertTrue(dump["window_attempts"])
        self.assertIn("status", dump["window_attempts"][0])
        self.assertTrue(dump["windows_final"])
        # לה' ממופה לשם ה׳ במצב תפילה (8.21)
        self.assertEqual(dump["words"][1]["plain"], "לאדני")
        seg = dump["segments"][0]
        for key in ("start_raw", "start", "vad_snap", "confidence", "label"):
            self.assertIn(key, seg)
        self.assertTrue(dump["vad"]["ran"])
        ev = dump["evaluation"]["line_starts"]
        self.assertEqual([r["line"] for r in ev], [1, 3])
        self.assertIsNotNone(ev[0]["error"])
        self.assertIn("text_words_inside", dump["evaluation"]["non_text_speech"][0])

    def test_asr_json_reused(self):
        asr = [{"word": "כי", "start": 0.1, "end": 0.3, "prob": 1.0}]
        with tempfile.TemporaryDirectory() as td, _patched():
            text_file = Path(td) / "t.txt"
            text_file.write_text(TEXT, encoding="utf-8")
            cache = Path(td) / "asr.json"
            cache.write_text(json.dumps({"model": "cached", "words": asr}),
                             encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                dump = run_local.main([
                    "--audio", "rec.m4a", "--text-file", str(text_file),
                    "--out-dir", str(Path(td) / "o"), "--asr-json", str(cache),
                    "--max-word-sec", "30", "--rate-range", "0.05", "10"])
        self.assertEqual(dump["asr_name"], "cached")
        self.assertEqual(dump["meta"]["overrides"],
                         {"rate_range": (0.05, 10.0), "max_word_sec": 30.0})
        self.assertEqual(H._MAX_WORD_SEC, 12.0)  # הוחזר אחרי הריצה


class TestPureHelpers(unittest.TestCase):
    def test_parse_srt_and_compare(self):
        srt = ("﻿1\n00:00:05,410 --> 00:00:07,667\nכִּי\n\n"
               "2\n00:01:01,000 --> 00:01:02,500\nא ב\n")
        cues = run_local.parse_srt(srt)
        self.assertEqual([c["start"] for c in cues], [5.41, 61.0])
        self.assertEqual(cues[1]["text"], "א ב")
        cmp = run_local.compare_srts(cues, [{"start": 5.0}, {"start": 60.0}])
        self.assertEqual(cmp["start_diffs"], [0.41, 1.0])

    def test_received_v1_parses(self):
        p = _REPO / "samples" / "nishmat" / "received_v1.srt"
        if not p.exists():
            self.skipTest("אין דגימה")
        cues = run_local.parse_srt(p.read_text(encoding="utf-8-sig"))
        self.assertEqual(len(cues), 21)
        self.assertAlmostEqual(cues[9]["start"], 50.131)


if __name__ == "__main__":
    unittest.main(verbosity=2)
