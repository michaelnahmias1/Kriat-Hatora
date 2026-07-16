# -*- coding: utf-8 -*-
"""בדיקות למנגנון העוגנים (הצלבת ASR עם טקסט ידוע) — בלי רשת/GPU."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner.anchors import (  # noqa: E402
    align_sequences,
    find_anchors,
    normalize_word,
    select_anchors,
    word_similarity,
)


class TestNormalize(unittest.TestCase):
    def test_strips_niqqud_and_punct(self):
        self.assertEqual(normalize_word("בְּרֵאשִׁ֖ית,"), "בראשית")

    def test_finals_folded(self):
        self.assertEqual(normalize_word("הארץ"), "הארצ")
        self.assertEqual(normalize_word("שמים"), "שמימ")

    def test_qere_substitution(self):
        self.assertEqual(normalize_word("אדוני"), "אדני")

    def test_non_hebrew_dropped(self):
        self.assertEqual(normalize_word("hello 123 ..."), "")


class TestSimilarity(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(word_similarity("בראשית", "בראשית"), 1.0)

    def test_ktiv_male_vs_haser_is_cheap(self):
        # כוהנים (תמלול, כתיב מלא) מול כהנים (תורה, כתיב חסר)
        self.assertGreaterEqual(word_similarity("כוהנימ", "כהנימ"), 0.9)

    def test_real_edit_is_expensive(self):
        self.assertLess(word_similarity("בראשית", "ברכשית"), 0.9)

    def test_unrelated_words(self):
        self.assertLess(word_similarity("בראשית", "והארצ"), 0.5)

    def test_length_gap_short_circuits(self):
        self.assertEqual(word_similarity("אב", "אבגדהוזחט"), 0.0)


class TestAlignSequences(unittest.TestCase):
    def test_perfect_match(self):
        ref = ["בראשית", "ברא", "אלהימ", "את", "השמימ"]
        pairs = align_sequences(list(ref), ref)
        matched = [(a, r) for a, r, s in pairs if a is not None and r is not None]
        self.assertEqual(matched, [(i, i) for i in range(5)])

    def test_asr_omission(self):
        ref = ["בראשית", "ברא", "אלהימ", "את", "השמימ"]
        asr = ["בראשית", "אלהימ", "את", "השמימ"]  # "ברא" נבלע
        pairs = align_sequences(asr, ref)
        matched = {r: a for a, r, s in pairs
                   if a is not None and r is not None and s >= 0.9}
        self.assertEqual(matched[0], 0)
        self.assertEqual(matched[4], 3)
        self.assertNotIn(1, matched)

    def test_asr_hallucinated_insertion(self):
        ref = ["בראשית", "ברא", "אלהימ"]
        asr = ["בראשית", "אממ", "ברא", "אלהימ"]
        pairs = align_sequences(asr, ref)
        matched = {r: a for a, r, s in pairs
                   if a is not None and r is not None and s >= 0.9}
        self.assertEqual(matched[1], 2)
        self.assertEqual(matched[2], 3)

    def test_monotonic(self):
        ref = ["אלף", "בית", "גימל", "דלת", "הא"]
        asr = ["בית", "אלף", "גימל", "דלת"]  # סדר הפוך בתחילת התמלול
        pairs = align_sequences(asr, ref)
        matched = [(a, r) for a, r, s in pairs
                   if a is not None and r is not None]
        # ההתאמות תמיד מונוטוניות בשני הצירים
        for (a1, r1), (a2, r2) in zip(matched, matched[1:]):
            self.assertLess(a1, a2)
            self.assertLess(r1, r2)


def _times(n, step=1.0, dur=0.4):
    return [(i * step, i * step + dur) for i in range(n)]


class TestSelectAnchors(unittest.TestCase):
    def _pairs_identity(self, words):
        return [(i, i, 1.0) for i in range(len(words))]

    def test_selects_confident_words(self):
        ref = ["בראשית", "ברא", "אלהימ", "את", "השמימ", "ואת", "הארצ"]
        anchors, coverage = select_anchors(
            self._pairs_identity(ref), _times(len(ref)), ref)
        self.assertGreaterEqual(len(anchors), 3)
        self.assertEqual(coverage, 1.0)
        # "את" קצרה מדי (2 אותיות) — לא עוגן
        self.assertNotIn(3, [a["ref"] for a in anchors])

    def test_repeated_word_rejected(self):
        ref = ["ויאמר", "אלהימ", "יהי", "אור", "ויאמר", "אלהימ", "יהי", "רקיע"]
        anchors, _ = select_anchors(
            self._pairs_identity(ref), _times(len(ref)), ref)
        refs = [a["ref"] for a in anchors]
        # מילים שחוזרות בסביבה (ויאמר, אלהימ, יהי) נפסלות
        for j in (0, 1, 2, 4, 5, 6):
            self.assertNotIn(j, refs)

    def test_out_of_order_times_pruned(self):
        ref = ["בראשית", "ברא", "אלהימ", "השמימ", "והארצ"]
        times = [(0.0, 0.4), (1.0, 1.4), (99.0, 99.4), (3.0, 3.4), (4.0, 4.4)]
        anchors, _ = select_anchors(self._pairs_identity(ref), times, ref)
        ends = [a["end"] for a in anchors]
        self.assertEqual(ends, sorted(ends))
        self.assertNotIn(2, [a["ref"] for a in anchors])

    def test_insane_rate_drops_weaker(self):
        ref = ["בראשית", "ברא", "אלהימ"]
        pairs = [(0, 0, 1.0), (1, 1, 0.86), (2, 2, 1.0)]
        # מילה אחת ביניהן אבל 60 שניות פער → קצב בלתי-אפשרי
        times = [(0.0, 0.4), (60.0, 60.4), (61.0, 61.4)]
        anchors, _ = select_anchors(pairs, times, ref)
        # העוגן החלש (sim 0.86) בקצה הקצב הבלתי-סביר הופל
        self.assertNotIn(1, [a["ref"] for a in anchors])


class TestFindAnchors(unittest.TestCase):
    def test_end_to_end_with_raw_words(self):
        ref_plain = ["בראשית", "ברא", "אלהים", "את", "השמים", "ואת", "הארץ"]
        asr_words = [
            {"word": "בראשית,", "start": 0.0, "end": 0.8},
            {"word": "ברא", "start": 1.0, "end": 1.5},
            {"word": "אלוהים", "start": 2.0, "end": 2.6},  # כתיב מלא
            {"word": "את", "start": 3.0, "end": 3.2},
            {"word": "השמיים", "start": 3.5, "end": 4.2},  # כתיב מלא
            {"word": "ואת", "start": 4.5, "end": 4.8},
            {"word": "הארץ", "start": 5.0, "end": 5.6},
        ]
        found = find_anchors(asr_words, ref_plain)
        refs = [a["ref"] for a in found["anchors"]]
        self.assertIn(0, refs)   # בראשית
        self.assertIn(2, refs)   # אלוהים↔אלהים למרות כתיב מלא
        self.assertIn(6, refs)   # הארץ
        self.assertGreaterEqual(found["coverage"], 0.9)
        a0 = next(a for a in found["anchors"] if a["ref"] == 0)
        self.assertEqual(a0["start"], 0.0)

    def test_empty_asr(self):
        found = find_anchors([], ["בראשית", "ברא"])
        self.assertEqual(found["anchors"], [])
        self.assertEqual(found["coverage"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
