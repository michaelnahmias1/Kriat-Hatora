# -*- coding: utf-8 -*-
"""בדיקות לחותך הטקסט הלא-מוטעם (src/chunker/prose.py) — בלי רשת ובלי תלויות.

PLAN_TEFILA.md משימה 4.1.1: שורות, פיסוק, מקף, פולבק, יחידה מוטעמת
שעוברת לחותך הישן, טקסט ריק/בלי עברית.

הרצה:  python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner.pipeline import units_to_segments  # noqa: E402
from chunker import (  # noqa: E402
    prose_lines,
    prose_segments,
    prose_tokens,
    segments_for_pipeline,
    split_prose,
)
from chunker.prose import RANK_STRONG, RANK_WEAK, break_rank  # noqa: E402

NBSP = "\u00a0"
MAQAF = "־"

ASHREI = ("אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ, עוֹד יְהַלְלוּךָ סֶּלָה׃\n"
          "אַשְׁרֵי הָעָם שֶׁכָּכָה לּוֹ, אַשְׁרֵי הָעָם שֶׁיְהֹוָה אֱלֹהָיו׃")


def displays(segs):
    return [s["display"] for s in segs]


def sizes(chunks):
    return [len(c) for c in chunks]


class TestLines(unittest.TestCase):
    def test_lines_kept_separate(self):
        lines = prose_lines(ASHREI)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0][0], "אַשְׁרֵי")
        self.assertEqual(lines[1][-1], "אֱלֹהָיו׃")

    def test_br_tag_is_a_line_break(self):
        self.assertEqual(len(prose_lines("אָבָא<br>אִמָּא")), 2)
        self.assertEqual(len(prose_lines("אָבָא<br/>אִמָּא\r\nדָּוִד")), 3)

    def test_blank_and_non_hebrew_lines_dropped(self):
        self.assertEqual(prose_lines("\n\n  \n---\n123\n"), [])
        self.assertEqual(len(prose_lines("אָבָא\n\n***\nאִמָּא")), 2)

    def test_segment_never_crosses_a_line(self):
        segs = prose_segments("אָבָא אִמָּא\nדָּוִד", max_words=8)
        self.assertEqual(displays(segs), ["אָבָא אִמָּא", "דָּוִד"])

    def test_footnote_spanning_lines_removed(self):
        lines = prose_lines("אָבָא<sup>הערה\nשנייה</sup> אִמָּא")
        self.assertEqual(lines, [["אָבָא", "אִמָּא"]])


class TestTokens(unittest.TestCase):
    def test_standalone_punctuation_glued_not_dropped(self):
        self.assertEqual(prose_tokens("אָבָא – אִמָּא"),
                         ["אָבָא" + NBSP + "–", "אִמָּא"])

    def test_opening_bracket_glued_forward(self):
        self.assertEqual(prose_tokens("אָבָא ( אִמָּא )"),
                         ["אָבָא", "(" + NBSP + "אִמָּא" + NBSP + ")"])

    def test_tokens_have_no_plain_space(self):
        """הדפדפן מפצל תצוגה ב-" " — כל טוקן חייב להיות מילה אחת אצלו."""
        for t in prose_tokens("אָבָא , ; אִמָּא : 3 דָּוִד"):
            self.assertNotIn(" ", t)

    def test_display_joins_tokens_exactly(self):
        segs = prose_segments(ASHREI, max_words=3)
        joined = " ".join(displays(segs)).split(" ")
        self.assertEqual(joined, prose_tokens(ASHREI))

    def test_html_and_entities_cleaned(self):
        self.assertEqual(prose_tokens("<b>אָבָא</b>&nbsp;אִמָּא"),
                         ["אָבָא", "אִמָּא"])


class TestBreakRank(unittest.TestCase):
    def test_strong_marks(self):
        for mark in ".:;?!׃":
            self.assertEqual(break_rank("אָבָא" + mark), RANK_STRONG, mark)

    def test_weak_marks(self):
        for mark in [",", NBSP + "–", NBSP + "—", NBSP + "-"]:
            self.assertEqual(break_rank("אָבָא" + mark), RANK_WEAK, mark)

    def test_quote_after_period_still_strong(self):
        self.assertEqual(break_rank('אָבָא."'), RANK_STRONG)

    def test_no_punct_and_geresh(self):
        self.assertIsNone(break_rank("אָבָא"))
        self.assertIsNone(break_rank("ה'"))
        self.assertIsNone(break_rank("אָבָא" + MAQAF))


class TestSplit(unittest.TestCase):
    def test_short_line_whole(self):
        self.assertEqual(split_prose(["א", "ב", "ג"], 4), [["א", "ב", "ג"]])

    def test_strong_beats_weak(self):
        words = ["א,", "ב", "ג.", "ד", "ה", "ו"]
        self.assertEqual(sizes(split_prose(words, 4)), [3, 3])
        words = ["א.", "ב,", "ג", "ד", "ה", "ו"]
        self.assertEqual(sizes(split_prose(words, 4)), [1, 1, 4])

    def test_tie_break_nearest_middle(self):
        words = ["א,", "ב", "ג,", "ד", "ה,", "ו", "ז"]
        self.assertEqual(sizes(split_prose(words, 4)), [3, 4])

    def test_punct_on_last_word_is_not_internal(self):
        words = ["א", "ב", "ג", "ד", "ה."]
        self.assertEqual(sizes(split_prose(words, 4)), [2, 3])

    def test_fallback_equal_split(self):
        self.assertEqual(sizes(split_prose(list("אבגדהוזח"), 4)), [4, 4])
        self.assertEqual(sizes(split_prose(list("אבגדה"), 4)), [2, 3])

    def test_recursive_split(self):
        words = ["א", "ב,", "ג", "ד", "ה.", "ו", "ז", "ח,", "ט", "י"]
        chunks = split_prose(words, 3)
        self.assertTrue(all(len(c) <= 3 for c in chunks))
        self.assertEqual(sum(chunks, []), words)
        self.assertEqual(sizes(chunks)[:2], [2, 3])  # ה. ואז ב,

    def test_never_cut_at_spaced_maqaf(self):
        """מקף שהוקלד עם רווח: אסור לחתוך משני צדיו."""
        words = ["א", "ב", "ג" + MAQAF, "ד", "ה", "ו"]
        chunks = split_prose(words, 3)
        for c in chunks[:-1]:
            self.assertFalse(c[-1].endswith(MAQAF))
        words = ["א", "ב", "ג", MAQAF + "ד", "ה", "ו"]
        for c in split_prose(words, 3)[1:]:
            self.assertFalse(c[0].startswith(MAQAF))

    def test_maqaf_chain_is_one_word(self):
        self.assertEqual(prose_tokens("כָּל" + MAQAF + "הָעָם"),
                         ["כָּל" + MAQAF + "הָעָם"])

    def test_unsplittable_chain_stays_whole(self):
        words = ["א" + MAQAF, "ב" + MAQAF, "ג" + MAQAF, "ד" + MAQAF, "ה"]
        self.assertEqual(split_prose(words, 2), [words])


class TestProseSegments(unittest.TestCase):
    def test_ashrei(self):
        segs = prose_segments(ASHREI)
        self.assertEqual(displays(segs), [
            "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ,", "עוֹד יְהַלְלוּךָ סֶּלָה׃",
            "אַשְׁרֵי הָעָם שֶׁכָּכָה לּוֹ,", "אַשְׁרֵי הָעָם שֶׁיְהֹוָה אֱלֹהָיו׃"])
        self.assertEqual(segs[0]["align_plain"], ["אשרי", "יושבי", "ביתך"])
        self.assertEqual(segs[3]["align_plain"][2], "שיהוה")

    def test_same_shape_as_taamim_segments(self):
        (seg,) = prose_segments("אָבָא")
        self.assertEqual(set(seg),
                         set(segments_for_pipeline("אָ֣בָא")[0]))

    def test_unvocalized_text_needs_tefila_mode(self):
        text = "ברוך אתה ה' אלהינו מלך העולם"
        self.assertEqual(prose_segments(text), [])  # תנ״ך: הכול כתיב
        segs = prose_segments(text, mode="tefila")
        self.assertEqual(sizes([s["display"].split(" ") for s in segs]),
                         [3, 3])
        self.assertEqual(segs[0]["align_plain"], ["ברוך", "אתה", "אדני"])

    def test_empty_and_non_hebrew(self):
        self.assertEqual(prose_segments(""), [])
        self.assertEqual(prose_segments("hello, world. 123"), [])


class TestRoutingInPipeline(unittest.TestCase):
    """זיהוי אוטומטי של מצב החיתוך ביחידה, ועקביות עם החלוקה המותאמת."""

    VERSE = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"

    def test_accented_unit_goes_to_taamim_chunker(self):
        segs = units_to_segments([{"text": self.VERSE, "kind": "line"}])
        self.assertEqual(displays(segs),
                         displays(segments_for_pipeline(self.VERSE)))

    def test_unaccented_unit_goes_to_prose_chunker(self):
        segs = units_to_segments([{"text": ASHREI, "kind": "paragraph"}])
        self.assertEqual(displays(segs), displays(prose_segments(ASHREI)))

    def test_sof_pasuq_alone_is_not_taamim(self):
        """‏׃ בסוף שורת סידור אינו טעם — הפסיק עדיין חותך."""
        text = "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ, עוֹד יְהַלְלוּךָ סֶּלָה׃"
        segs = units_to_segments([{"text": text, "kind": "line"}])
        self.assertEqual(segs[0]["display"], "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ,")

    def test_forced_punct_on_accented_text(self):
        segs = units_to_segments(
            [{"text": self.VERSE, "kind": "line", "chunk": "punct"}],
            max_words=8)
        self.assertEqual(len(segs), 1)

    def test_splits_use_the_same_words_as_the_display(self):
        text = "אָבָא – אִמָּא, דָּוִד\nשָׁלוֹם"
        units = [{"text": text, "kind": "line", "label": "ש"}]
        auto = units_to_segments(units)
        n = sum(len(s["display"].split(" ")) for s in auto)
        regrouped = units_to_segments(units, splits=[1, n - 1])
        self.assertEqual(" ".join(displays(regrouped)),
                         " ".join(displays(auto)))
        self.assertEqual(regrouped[0]["display"], "אָבָא" + NBSP + "–")


if __name__ == "__main__":
    unittest.main(verbosity=2)
