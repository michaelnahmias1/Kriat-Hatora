# -*- coding: utf-8 -*-
"""בדיקות לחלקים של ה-aligner שאינם דורשים רשת/GPU.

הרצה:  python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner.pipeline import (  # noqa: E402
    _fmt_ts,
    build_ref,
    build_srt,
    verses_to_segments,
)


class TestBuildRef(unittest.TestCase):
    def test_whole_chapter(self):
        self.assertEqual(build_ref("Genesis", 1), "Genesis 1")

    def test_verse_range_within_chapter(self):
        self.assertEqual(build_ref("Genesis", 1, 1, None, 13), "Genesis 1:1-13")

    def test_aliyah_crossing_chapters(self):
        self.assertEqual(build_ref("Genesis", 1, 1, 2, 3), "Genesis 1:1-2:3")


class TestSrtFormat(unittest.TestCase):
    def test_timestamp_format(self):
        self.assertEqual(_fmt_ts(0), "00:00:00,000")
        self.assertEqual(_fmt_ts(3661.5), "01:01:01,500")

    def test_build_srt_continuous_and_utf8(self):
        verse = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
        segments = verses_to_segments([verse])
        n_words = sum(len(s["align_vocalized"]) for s in segments)
        spans = [(i * 0.5, i * 0.5 + 0.4) for i in range(n_words)]
        srt = build_srt(segments, spans)
        blocks = srt.strip().split("\n\n")
        self.assertEqual(len(blocks), len(segments))
        # רציפות: סוף מקטע 1 = תחילת מקטע 2
        end_1 = blocks[0].split("\n")[1].split(" --> ")[1]
        start_2 = blocks[1].split("\n")[1].split(" --> ")[0]
        self.assertEqual(end_1, start_2)
        # הטקסט המוצג נשאר מנוקד ומוטעם
        self.assertIn("בְּרֵאשִׁ֖ית", srt)

    def test_word_count_mismatch_raises(self):
        segments = verses_to_segments(["בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים"])
        with self.assertRaises(RuntimeError):
            build_srt(segments, [(0.0, 0.4)] * 99)


class TestVersesToSegments(unittest.TestCase):
    def test_segments_carry_verse_numbers(self):
        verses = ["בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים",
                  "וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֙הוּ֙ וָבֹ֑הוּ"]
        segs = verses_to_segments(verses)
        self.assertEqual(segs[0]["verse"], 1)
        self.assertEqual(segs[-1]["verse"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
