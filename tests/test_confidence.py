# -*- coding: utf-8 -*-
"""בדיקות לניקוד הביטחון, להצמדת ה-VAD ולעזרי ההיברידי — בלי רשת/GPU."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner.confidence import (  # noqa: E402
    format_report,
    score_segment,
)
from aligner.hybrid import (  # noqa: E402
    _anchor_dists,
    _asr_gaps,
    _segment_word_ranges,
    _verse_start_flags,
)
from aligner.vad import snap_boundaries  # noqa: E402


class TestScoreSegment(unittest.TestCase):
    def test_perfect_segment(self):
        conf = score_segment({"ctc_score": 1.0, "anchor_dist": 0,
                              "interpolated": False, "asr_gap": 0.1,
                              "vad_snapped": True})
        self.assertGreaterEqual(conf, 0.95)

    def test_interpolated_capped(self):
        conf = score_segment({"ctc_score": 1.0, "anchor_dist": 0,
                              "interpolated": True, "asr_gap": 0.1,
                              "vad_snapped": True})
        self.assertLessEqual(conf, 0.3)

    def test_missing_signals_middle_ground(self):
        conf = score_segment({"ctc_score": None, "anchor_dist": None,
                              "interpolated": False, "asr_gap": None,
                              "vad_snapped": None})
        self.assertGreater(conf, 0.2)
        self.assertLess(conf, 0.6)

    def test_disagreement_lowers(self):
        base = {"ctc_score": 0.8, "anchor_dist": 5, "interpolated": False,
                "vad_snapped": True}
        agree = score_segment({**base, "asr_gap": 0.2})
        disagree = score_segment({**base, "asr_gap": 3.0})
        self.assertGreater(agree, disagree)


class TestReport(unittest.TestCase):
    def test_low_confidence_listed_with_verse(self):
        segments = [{"display": "בְּרֵאשִׁ֖ית בָּרָ֣א", "verse": 1},
                    {"display": "אֵ֥ת הַשָּׁמַ֖יִם", "verse": 1}]
        infos = [{"interpolated": False, "anchor_dist": 0},
                 {"interpolated": True, "anchor_dist": None}]
        report = format_report(segments, [0.9, 0.2], infos, [0.0, 65.0])
        self.assertIn("אֵ֥ת הַשָּׁמַ֖יִם", report)
        self.assertNotIn("בְּרֵאשִׁ֖ית בָּרָ֣א", report.split("לבדיקה")[1])
        self.assertIn("[01:05]", report)
        self.assertIn("זמן משוער", report)

    def test_all_good(self):
        segments = [{"display": "אבג", "verse": 1}]
        report = format_report(segments, [0.9], [{}], [0.0])
        self.assertIn("כל המקטעים", report)


class TestSnapBoundaries(unittest.TestCase):
    def test_snap_within_radius(self):
        speech = [(0.0, 4.8), (5.2, 9.7), (10.3, 20.0)]
        starts = [0.1, 5.0, 10.0]
        flags = [True, False, False]
        new, dists = snap_boundaries(starts, speech, flags)
        self.assertAlmostEqual(new[1], 5.2)
        self.assertAlmostEqual(new[2], 10.3)
        self.assertIsNotNone(dists[1])

    def test_verse_radius_larger(self):
        speech = [(0.0, 4.0), (5.6, 9.0)]
        starts = [0.0, 5.0]
        # 0.6 שניות: מעבר לרדיוס רגיל (0.35) אך בתוך רדיוס-פסוק (0.7)
        _, d_regular = snap_boundaries(starts, speech, [True, False])
        self.assertIsNone(d_regular[1])
        new, d_verse = snap_boundaries(starts, speech, [True, True])
        self.assertAlmostEqual(new[1], 5.6)

    def test_monotonicity_enforced(self):
        speech = [(0.0, 1.0), (1.2, 9.0)]
        starts = [1.15, 1.25]
        new, _ = snap_boundaries(starts, speech, [False, False])
        self.assertLess(new[0], new[1])

    def test_no_speech_regions(self):
        starts = [1.0, 2.0]
        new, dists = snap_boundaries(starts, [], [False, False])
        self.assertEqual(new, starts)
        self.assertEqual(dists, [None, None])


class TestHybridHelpers(unittest.TestCase):
    def _segments(self):
        return [
            {"align_vocalized": ["א", "ב"], "align_plain": ["א", "ב"],
             "verse": 1},
            {"align_vocalized": ["ג"], "align_plain": ["ג"], "verse": 1},
            {"align_vocalized": ["ד", "ה"], "align_plain": ["ד", "ה"],
             "verse": 2},
        ]

    def test_word_ranges(self):
        self.assertEqual(_segment_word_ranges(self._segments()),
                         [(0, 1), (2, 2), (3, 4)])

    def test_verse_flags(self):
        self.assertEqual(_verse_start_flags(self._segments()),
                         [True, False, True])

    def test_anchor_dists(self):
        ranges = [(0, 1), (2, 2), (3, 4)]
        self.assertEqual(_anchor_dists(ranges, [2]), [1, 0, 1])
        self.assertEqual(_anchor_dists(ranges, []), [None, None, None])

    def test_asr_gaps_median(self):
        ranges = [(0, 2)]
        matches = [{"ref": 0, "asr_start": 1.0},
                   {"ref": 1, "asr_start": 2.0},
                   {"ref": 2, "asr_start": 9.0}]
        word_starts = [1.1, 2.1, 3.0]
        gaps = _asr_gaps(ranges, matches, word_starts)
        self.assertAlmostEqual(gaps[0], 0.1, places=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
