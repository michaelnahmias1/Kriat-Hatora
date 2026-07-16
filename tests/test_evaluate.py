# -*- coding: utf-8 -*-
"""בדיקות לרתמת ההערכה — בלי רשת/GPU."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner.evaluate import (  # noqa: E402
    boundary_errors,
    comparison_table,
    equal_split_baseline,
    error_metrics,
)


class TestMetrics(unittest.TestCase):
    def test_boundary_errors_sign(self):
        errs = boundary_errors([1.0, 5.5], [1.2, 5.0])
        self.assertAlmostEqual(errs[0], -0.2)  # מקדים
        self.assertAlmostEqual(errs[1], 0.5)   # מאחר

    def test_length_mismatch_raises(self):
        with self.assertRaises(RuntimeError):
            boundary_errors([1.0], [1.0, 2.0])

    def test_error_metrics(self):
        m = error_metrics([-0.1, 0.3, 1.5, -0.05])
        self.assertEqual(m["n"], 4)
        self.assertEqual(m["early"], 0)   # רק מתחת ל-0.2-
        self.assertEqual(m["late"], 2)
        self.assertAlmostEqual(m["pct_within_05"], 75.0)
        self.assertAlmostEqual(m["pct_within_10"], 75.0)

    def test_comparison_table_contains_methods(self):
        truth = [0.0, 10.0, 20.0]
        table = comparison_table(
            {"היברידי": [0.1, 10.2, 19.8], "baseline": [0.0, 13.0, 25.0]},
            truth)
        self.assertIn("היברידי", table)
        self.assertIn("baseline", table)
        self.assertIn("%", table)


class TestBaseline(unittest.TestCase):
    def test_letter_weighted_split(self):
        segments = [{"align_plain": ["אב"]}, {"align_plain": ["אבגדוזחט"]}]
        starts = equal_split_baseline(segments, 10.0)
        self.assertAlmostEqual(starts[0], 0.0)
        self.assertAlmostEqual(starts[1], 2.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
