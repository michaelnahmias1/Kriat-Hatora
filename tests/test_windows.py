# -*- coding: utf-8 -*-
"""בדיקות לחלונות היישור: בנייה, retry, אינטרפולציה ותפירה — בלי רשת/GPU."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner.windows import (  # noqa: E402
    align_windows,
    build_windows,
    interpolate_words,
    merge_windows,
    stitch,
)


def _anchor(ref, start, sim=0.9):
    return {"ref": ref, "asr": ref, "start": start, "end": start + 0.4,
            "sim": sim}


class TestBuildWindows(unittest.TestCase):
    def test_no_anchors_single_window(self):
        ws = build_windows([], 10, 60.0)
        self.assertEqual(len(ws), 1)
        self.assertEqual((ws[0]["word_lo"], ws[0]["word_hi"]), (0, 9))
        self.assertEqual((ws[0]["t_lo"], ws[0]["t_hi"]), (0.0, 60.0))

    def test_full_coverage_and_anchor_overlap(self):
        anchors = [_anchor(5, 20.0), _anchor(12, 45.0)]
        ws = build_windows(anchors, 20, 80.0)
        self.assertEqual(ws[0]["word_lo"], 0)
        self.assertEqual(ws[-1]["word_hi"], 19)
        # חלונות שכנים חופפים במילת העוגן
        for w1, w2 in zip(ws, ws[1:]):
            self.assertEqual(w1["word_hi"], w2["word_lo"])

    def test_short_windows_merged(self):
        # שני עוגנים במרחק שנייה — החלון ביניהם קצר מ-min_dur וממוזג
        anchors = [_anchor(3, 10.0), _anchor(4, 11.0), _anchor(10, 40.0)]
        ws = build_windows(anchors, 15, 60.0, min_dur=8.0)
        for w in ws:
            self.assertGreaterEqual(w["t_hi"] - w["t_lo"], 8.0)
        self.assertEqual(ws[0]["word_lo"], 0)
        self.assertEqual(ws[-1]["word_hi"], 14)

    def test_padding_clipped_to_audio(self):
        anchors = [_anchor(2, 0.1), _anchor(8, 59.9)]
        ws = build_windows(anchors, 10, 60.0)
        for w in ws:
            self.assertGreaterEqual(w["t_lo"], 0.0)
            self.assertLessEqual(w["t_hi"], 60.0)


class TestInterpolate(unittest.TestCase):
    def test_letter_weighted(self):
        spans = interpolate_words(0.0, 10.0, ["אב", "אבאבאבאב"])  # 2 מול 8
        self.assertAlmostEqual(spans[0][1], 2.0)
        self.assertAlmostEqual(spans[1][0], 2.0)
        self.assertAlmostEqual(spans[1][1], 10.0)

    def test_contiguous_and_scored_zero(self):
        spans = interpolate_words(5.0, 8.0, ["אאא", "בבב", "גגג"])
        self.assertEqual(len(spans), 3)
        for (s1, e1, sc), (s2, _, _) in zip(spans, spans[1:]):
            self.assertAlmostEqual(e1, s2)
            self.assertEqual(sc, 0.0)


def _linear_align_fn(window):
    """‏stub: מפזר את מילות החלון שווה-בשווה על טווח הזמן שלו, ציון 0.8."""
    n = window["word_hi"] - window["word_lo"] + 1
    step = (window["t_hi"] - window["t_lo"]) / n
    return [(window["t_lo"] + i * step, window["t_lo"] + (i + 1) * step, 0.8)
            for i in range(n)]


class TestAlignWindows(unittest.TestCase):
    def _windows(self):
        anchors = [_anchor(4, 20.0, sim=0.9), _anchor(9, 40.0, sim=0.95)]
        return build_windows(anchors, 15, 60.0)

    def test_all_success(self):
        ws = self._windows()
        out = align_windows(ws, _linear_align_fn, ["אבג"] * 15)
        self.assertEqual(len(out), len(ws))
        self.assertFalse(any(o["interpolated"] for o in out))

    def test_failed_window_merges_with_neighbor(self):
        ws = self._windows()
        calls = []

        def flaky(w):
            calls.append((w["word_lo"], w["word_hi"]))
            if (w["word_lo"], w["word_hi"]) == (ws[1]["word_lo"],
                                                ws[1]["word_hi"]):
                return None  # החלון האמצעי נכשל בפני עצמו
            return _linear_align_fn(w)

        out = align_windows(ws, flaky, ["אבג"] * 15)
        self.assertFalse(any(o["interpolated"] for o in out))
        covered = [(o["window"]["word_lo"], o["window"]["word_hi"])
                   for o in out]
        self.assertEqual(covered[0][0], 0)
        self.assertEqual(covered[-1][1], 14)

    def test_all_failed_interpolates(self):
        ws = self._windows()
        out = align_windows(ws, lambda w: None, ["אבג"] * 15)
        self.assertTrue(all(o["interpolated"] for o in out))
        spans, flags = stitch(out, 15)
        self.assertEqual(len(spans), 15)
        self.assertTrue(all(flags))


class TestStitch(unittest.TestCase):
    def test_overlap_deduped_and_monotonic(self):
        anchors = [_anchor(4, 20.0)]
        ws = build_windows(anchors, 10, 60.0)
        out = align_windows(ws, _linear_align_fn, ["אבג"] * 10)
        spans, flags = stitch(out, 10)
        self.assertEqual(len(spans), 10)
        for (s1, _, _), (s2, _, _) in zip(spans, spans[1:]):
            self.assertLess(s1, s2)

    def test_count_mismatch_raises(self):
        ws = build_windows([], 10, 60.0)
        out = align_windows(ws, _linear_align_fn, ["אבג"] * 10)
        with self.assertRaises(RuntimeError):
            stitch(out, 11)

    def test_merge_windows_spans_union(self):
        w1 = {"word_lo": 0, "word_hi": 4, "t_lo": 0.0, "t_hi": 20.0,
              "sim_left": None, "sim_right": 0.9}
        w2 = {"word_lo": 4, "word_hi": 9, "t_lo": 19.5, "t_hi": 60.0,
              "sim_left": 0.9, "sim_right": None}
        m = merge_windows(w1, w2)
        self.assertEqual((m["word_lo"], m["word_hi"]), (0, 9))
        self.assertEqual((m["t_lo"], m["t_hi"]), (0.0, 60.0))
        self.assertIsNone(m["sim_left"])
        self.assertIsNone(m["sim_right"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
