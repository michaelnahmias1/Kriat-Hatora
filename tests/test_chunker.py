# -*- coding: utf-8 -*-
"""בדיקות יחידה לפונקציית החיתוך — רצות בלי רשת ובלי תלויות.

רוב הבדיקות בונות מילים סינתטיות עם קודפוינטים מפורשים (\\uXXXX) כדי
שהכוונה תהיה חד-משמעית. פסוק הדוגמה (בראשית א:א) משוחזר מזיכרון —
האימות הסופי מול טקסט MAM האמיתי רץ ב-notebook האימותים ב-Colab.

הרצה:  python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chunker import (  # noqa: E402
    clean_sefaria_text,
    segments_for_pipeline,
    split_unit,
    taamim,
    to_alignment_words,
    tokenize,
    verse_to_segments,
    word_accents,
    word_rank,
)

# --- כלי עזר לבניית מילים סינתטיות ----------------------------------------

ETNAHTA = "֑"
TIPEHA = "֖"
ZAQEF_QATAN = "֔"
PASHTA = "֙"
ZARQA_0598 = "֘"
ZINOR_05AE = "֮"
MUNAH = "֣"
METEG = "ֽ"
MAQAF = "־"


def w(base="אבג", *accents):
    """מילה סינתטית: אותיות בסיס + טעמים אחרי האות הראשונה."""
    return base[0] + "".join(accents) + base[1:]


class TestClean(unittest.TestCase):
    def test_strips_html_entities_and_parasha_marks(self):
        raw = "וַיֹּאמֶר&nbsp;<b>אֱלֹהִים</b>  {פ} <br/>"
        self.assertEqual(clean_sefaria_text(raw), "וַיֹּאמֶר אֱלֹהִים")

    def test_normalizes_whitespace_and_invisibles(self):
        raw = "אבג‏    דהו‎"
        self.assertEqual(clean_sefaria_text(raw), "אבג דהו")


class TestTokenize(unittest.TestCase):
    def test_maqaf_chain_is_one_prosodic_word(self):
        verse = "עַל" + MAQAF + "פְּנֵי תְהוֹם"
        self.assertEqual(len(tokenize(verse)), 2)

    def test_tokens_without_hebrew_letters_are_dropped(self):
        self.assertEqual(tokenize("אבג ׀ דהו"), ["אבג", "דהו"])


class TestAccents(unittest.TestCase):
    def test_mam_double_helper_accent_is_deduped(self):
        word = "א" + PASHTA + "ב" + PASHTA + "ג"  # פשטא כפולה (עזר של MAM)
        self.assertEqual(word_accents(word), {PASHTA})

    def test_meteg_is_not_an_accent(self):
        self.assertEqual(word_accents(w("אבג", METEG)), set())
        self.assertIsNone(word_rank(w("אבג", METEG)))

    def test_servant_has_no_rank(self):
        self.assertIsNone(word_rank(w("אבג", MUNAH)))

    def test_both_zarqa_variants_are_rank_3(self):
        self.assertEqual(word_rank(w("אבג", ZARQA_0598)), 3)
        self.assertEqual(word_rank(w("אבג", ZINOR_05AE)), 3)

    def test_etnahta_is_rank_1(self):
        self.assertEqual(word_rank(w("אבג", ETNAHTA)), 1)


class TestSplit(unittest.TestCase):
    def test_short_unit_is_returned_whole(self):
        words = [w() for _ in range(4)]
        self.assertEqual(split_unit(words), [words])

    def test_cut_at_strongest_disjunctive(self):
        # 7 מילים, אתנחתא על השלישית, טפחא על הראשונה → החיתוך על האתנחתא
        words = [w("אבג", TIPEHA), w("דהו", MUNAH), w("זחט", ETNAHTA),
                 w("יכל", MUNAH), w("מנס", TIPEHA), w("עפצ", MUNAH), w("קרש")]
        segs = split_unit(words)
        self.assertEqual([len(s) for s in segs], [3, 4])

    def test_disjunctive_on_last_word_is_not_an_internal_cut(self):
        # מפסיק רק על המילה האחרונה → אין חלוקה פנימית → פולבק חלוקה שווה
        words = [w("אבג", MUNAH) for _ in range(4)] + [w("דהו", TIPEHA)]
        segs = split_unit(words)
        self.assertEqual([len(s) for s in segs], [2, 3])

    def test_tie_break_prefers_middle(self):
        # שני זקפים באותה דרגה (אינדקסים 1 ו-3 מתוך 6) → נבחר הקרוב לאמצע (3)
        words = [w("אבג"), w("דהו", ZAQEF_QATAN), w("זחט"),
                 w("יכל", ZAQEF_QATAN), w("מנס"), w("עפצ")]
        segs = split_unit(words)
        self.assertEqual([len(s) for s in segs], [4, 2])

    def test_fallback_equal_split_when_no_disjunctives(self):
        words = [w("אבג", MUNAH) for _ in range(6)]
        segs = split_unit(words)
        self.assertEqual([len(s) for s in segs], [3, 3])

    def test_recursive_depth_two(self):
        # 9 מילים: אתנחתא באינדקס 4 מפצלת ל-5+4; החמישייה השמאלית מתפצלת
        # שוב על הזקף באינדקס 1; הרביעייה הימנית כבר בגודל חוקי ולא מתפצלת
        words = [w("אבג"), w("דהו", ZAQEF_QATAN), w("זחט"), w("יכל", MUNAH),
                 w("מנס", ETNAHTA), w("עפצ"), w("קרש", TIPEHA), w("תבג"), w("דוז")]
        segs = split_unit(words)
        self.assertEqual([len(s) for s in segs], [2, 3, 4])


class TestAlignmentText(unittest.TestCase):
    def test_maqaf_expands_to_spoken_words(self):
        word = "עַל" + MAQAF + "פְּנֵ" + TIPEHA + "י"
        self.assertEqual(to_alignment_words(word, keep_niqqud=False),
                         ["על", "פני"])

    def test_vocalized_keeps_niqqud_drops_taamim(self):
        word = "בָּרָ" + MUNAH + "א"
        (out,) = to_alignment_words(word, keep_niqqud=True)
        self.assertNotIn(MUNAH, out)
        self.assertIn("ָ", out)  # קמץ נשאר

    def test_qere_perpetuum_shem_hashem(self):
        word = "יְהוָ" + TIPEHA + "ה"
        self.assertEqual(to_alignment_words(word, keep_niqqud=False), ["אדני"])
        self.assertEqual(to_alignment_words(word, keep_niqqud=True), ["אֲדֹנָי"])

    def test_display_and_alignment_stay_index_aligned(self):
        verse = ("בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם "
                 "וְאֵ֥ת הָאָֽרֶץ׃")
        segs = segments_for_pipeline(verse)
        self.assertEqual(len(segs), 2)
        for seg in segs:
            n = len(seg["display"].split(" "))
            self.assertEqual(len(seg["align_plain"]), n)
            self.assertEqual(len(seg["align_vocalized"]), n)


class TestSampleVerse(unittest.TestCase):
    """בראשית א:א משוחזר מזיכרון — לאימות סופי מול MAM ב-Colab."""

    VERSE = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"

    def test_splits_on_etnahta(self):
        segs = verse_to_segments(self.VERSE)
        self.assertEqual(len(segs), 2)
        self.assertTrue(segs[0].endswith("אֱלֹהִ֑ים"))
        self.assertEqual(len(segs[1].split(" ")), 4)

    def test_sof_pasuq_survives_display(self):
        segs = verse_to_segments(self.VERSE)
        self.assertIn(taamim.SOF_PASUQ, segs[-1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
