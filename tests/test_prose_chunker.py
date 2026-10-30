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

from aligner.pipeline import (  # noqa: E402
    _taamim_evidence,
    _unit_chunk,
    units_to_segments,
)
from chunker import (  # noqa: E402
    clean_sefaria_text,
    letters_only,
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


class TestMetsudahPronunciationMarks(unittest.TestCase):
    """‏PLAN_TEFILA 8.24: סידור מצודה משתמש ב-U+0592 (סגולתא) אחרי שווא כסימן
    לשווא נע, וב-U+05AF (עיגול מסורה) כמפריד מילים בקריאת שמע. אלה אינם
    טעמי מקרא — היחידה נחתכת לפי פיסוק. המחרוזות כאן מהטקסט האמיתי
    (Siddur Ashkenaz / Sefard, ‏The Metsudah siddur, 1981)."""

    SEGOLTA, MASORA_CIRCLE = "\u0592", "\u05AF"
    # ברכו — שווא נע מסומן בסגולתא (בָּרְ֒כוּ, הַמְ֒בֹרָךְ)
    BARCHU = "בָּרְ֒כוּ אֶת יְהֹוָה הַמְ֒בֹרָךְ:"
    # קריאת שמע — גם עיגול מסורה (בְּכָל֯־לְ֯בָבְ֒ךָ)
    SHEMA = ("וְאָהַבְתָּ אֵת יְהֹוָה אֱלֹהֶֽיךָ בְּכָל֯־לְ֯בָבְ֒ךָ "
             "וּבְכָל־נַפְשְׁ֒ךָ וּבְכָל־מְאֹדֶֽךָ: וְהָיוּ הַדְּ֒בָרִים הָאֵֽלֶּה "
             "אֲשֶׁר֯ אָ֯נֹכִי מְצַוְּ֒ךָ הַיּוֹם עַל֯־לְ֯בָבֶֽךָ:")
    # פסוק מוטעם באמת שמצוטט במצודה ספרד (דברים י:יב)
    DEUT = ("וְעַתָּה֙ יִשְׂרָאֵ֔ל מָ֚ה יְהוָ֣ה אֱלֹהֶ֔יךָ שֹׁאֵ֖ל מֵעִמָּ֑ךְ "
            "כִּ֣י אִם־לְ֠יִרְאָה אֶת־יְהוָ֨ה אֱלֹהֶ֜יךָ לָלֶ֤כֶת בְּכָל־דְּרָכָיו֙")

    def chunk(self, text):
        return _unit_chunk({"text": text, "kind": "paragraph"})

    def test_shva_na_marker_is_not_taamim(self):
        self.assertEqual(self.chunk(self.BARCHU), "punct")
        self.assertEqual(_taamim_evidence(clean_sefaria_text("בָּרְ֒כוּ")),
                         set())

    def test_shema_separator_is_not_taamim(self):
        self.assertEqual(self.chunk(self.SHEMA), "punct")
        self.assertEqual(_taamim_evidence("אָ֯נֹכִי"), set())

    def test_genuine_cantillated_verse_still_detected(self):
        self.assertEqual(self.chunk(self.DEUT), "taamim")
        self.assertEqual(
            self.chunk(TestRoutingInPipeline.VERSE), "taamim")

    def test_genuine_verse_with_shva_na_marks_still_detected(self):
        """פסקת מצודה עם פסוק מוטעם וגם סימני שווא נע — עדיין טעמים."""
        self.assertEqual(self.chunk(self.BARCHU + " " + self.DEUT), "taamim")

    def test_real_segolta_counts(self):
        """סגולתא שאינה על אות עם שווא היא טעם (וַיִּקְרָא֒ — Shaliehsaboo)."""
        self.assertEqual(_taamim_evidence(clean_sefaria_text("וַיִּקְרָא֒")),
                         {self.SEGOLTA})

    def test_single_stray_accent_is_not_enough(self):
        """סגולתא בודדת שלא אחרי שווא (5 כאלה במצודה ספרד) — לא מספיק:
        פסוק מוטעם אמיתי נושא לפחות שני טעמים שונים."""
        self.assertEqual(self.chunk("יְהִי כְבוֹדֶֽ֒ךָ לְעוֹלָם וָעֶד:"),
                         "punct")
        self.assertEqual(self.chunk("יְהוָ֣ה מֶ֑לֶךְ"), "taamim")

    def test_marks_kept_in_display_and_dropped_from_alignment(self):
        segs = units_to_segments([{"text": self.SHEMA, "kind": "paragraph"}],
                                 mode="tefila")
        self.assertEqual(displays(segs),
                         displays(prose_segments(self.SHEMA, mode="tefila")))
        display = " ".join(displays(segs))
        self.assertIn(self.SEGOLTA, display)
        self.assertIn(self.MASORA_CIRCLE, display)
        for seg in segs:
            for w in seg["align_vocalized"] + seg["align_plain"]:
                self.assertNotIn(self.SEGOLTA, w)
                self.assertNotIn(self.MASORA_CIRCLE, w)
        # מילת יישור אחת לכל חלק-מקף — אותה ספירה כמו isAudible בדפדפן
        pieces = [p for seg in segs for tok in seg["display"].split(" ")
                  for p in tok.split(MAQAF) if letters_only(p)]
        self.assertEqual(sum(len(s["align_plain"]) for s in segs),
                         len(pieces))
        self.assertIn("בכל", segs[0]["align_plain"] + segs[1]["align_plain"])


class TestMixedParagraphs(unittest.TestCase):
    """פסקה מעורבת — פסוק מוטעם מצוטט בתוך תפילה בלי טעמים (‏chunk_pieces,
    ‏split_mixed_unit). הטקסטים — מהטקסט האמיתי של עדות המזרח (כל נדרי
    מוויקיטקסט, עננו מ-Shaliehsaboo), מקוצרים."""

    # סוף כל נדרי: ארמית בלי טעמים, ואחריה במדבר טו:כו מוטעם
    KOL_NIDRE = ("וְדִי חֲרַמְנָא וְדִי נַחֲרִים. וְדִי אֲסָרְנָא עַל נַפְשָׁתָנָא "
                 "וְדִי נֶאְסַר. כֻּלְּהוֹן אִתְחָרַטְנָא בְהוֹן. יְהֵא רַעֲוָא דִי "
                 "יְהוֹן שְׁבִיתִין וּשְׁבִיקִין לָא שְׁרִירִין וְלָא קַיָּמִין. "
                 "וְנִסְלַ֗ח לְכׇל־עֲדַת֙ בְּנֵ֣י יִשְׂרָאֵ֔ל וְלַגֵּ֖ר הַגָּ֣ר "
                 "בְּתוֹכָ֑ם כִּ֥י לְכׇל־הָעָ֖ם בִּשְׁגָגָֽה׃")
    # עננו: "כַּדָּבָר שֶׁנֶּאֱמַר:" + ישעיה סה:כד, ואחריו המשך התפילה. מילת
    # הסילוק (אֶשְׁמָֽע:) — בלי טעם אחר — נשארת עם הפסוק
    ANENU = ("טֶֽרֶם נִקְרָא אֵלֶֽיךָ אַתָּה תַֽעֲנֶה, נְדַבֵּר וְאַתָּה תִשְׁמַע, "
             "כַּדָּבָר שֶׁנֶּאֱמַר: וְהָיָ֥ה טֶֽרֶם־יִקְרָ֖אוּ וַאֲנִ֣י אֶעֱנֶ֑ה "
             "ע֛וֹד הֵ֥ם מְדַבְּרִ֖ים וַאֲנִ֥י אֶשְׁמָֽע: כִּי אַתָּה יְהֹוָה "
             "פּוֹדֶה וּמַצִּיל וְעוֹנֶה וּמְרַחֵם בְּכָל־עֵת צָרָה וְצוּקָה.")

    def pieces(self, text):
        from aligner.pipeline import chunk_pieces
        return chunk_pieces(text)

    def assert_partition(self, text, pieces):
        """החלקים — חתיכות רצופות של הטקסט: אותן מילים, בשני החותכים."""
        from chunker import tokenize
        self.assertEqual(" ".join(t for _, t in pieces).split(), text.split())
        self.assertEqual([w for _, t in pieces
                          for w in tokenize(clean_sefaria_text(t))],
                         tokenize(clean_sefaria_text(text)))
        self.assertEqual(sum(len(prose_tokens(t)) for _, t in pieces),
                         len(prose_tokens(text)))

    def test_kol_nidre_split_at_the_verse(self):
        p = self.pieces(self.KOL_NIDRE)
        self.assertEqual([c for c, _ in p], ["punct", "taamim"])
        self.assertTrue(p[0][1].endswith("וְלָא קַיָּמִין."))
        self.assertTrue(p[1][1].startswith("וְנִסְלַ֗ח"))
        self.assert_partition(self.KOL_NIDRE, p)
        self.assertEqual(_unit_chunk({"text": self.KOL_NIDRE}), "taamim",
                         "יחידה שלא פוצלה — כמו קודם")

    def test_kol_nidre_subtitles_follow_punctuation(self):
        from aligner.pipeline import split_mixed_unit
        units = split_mixed_unit({"text": self.KOL_NIDRE, "label": "כל נדרי · 6",
                                  "kind": "paragraph"})
        self.assertEqual([(u["label"], u["chunk"], u.get("cont")) for u in units],
                         [("כל נדרי · 6", "punct", None),
                          ("כל נדרי · 6", "taamim", True)])
        segs = displays(units_to_segments(units, 4, None, "tefila"))
        self.assertIn("וְדִי חֲרַמְנָא וְדִי נַחֲרִים.", segs)
        self.assertNotIn("נַחֲרִים. וְדִי", segs)       # כך חתך חותך הטעמים
        self.assertEqual(segs[-3:], ["וְנִסְלַ֗ח לְכׇל־עֲדַת֙ בְּנֵ֣י יִשְׂרָאֵ֔ל",
                                     "וְלַגֵּ֖ר הַגָּ֣ר בְּתוֹכָ֑ם",
                                     "כִּ֥י לְכׇל־הָעָ֖ם בִּשְׁגָגָֽה׃"])
        whole = units_to_segments([{"text": self.KOL_NIDRE, "chunk": "taamim"}],
                                  4, None, "tefila")
        self.assertEqual(sum(len(s["align_plain"]) for s in whole),
                         sum(len(s["align_plain"]) for s in
                             units_to_segments(units, 4, None, "tefila")))

    def test_verse_in_the_middle_with_silluq_word(self):
        p = self.pieces(self.ANENU)
        self.assertEqual([c for c, _ in p], ["punct", "taamim", "punct"])
        self.assertTrue(p[0][1].endswith("שֶׁנֶּאֱמַר:"))
        self.assertTrue(p[1][1].endswith("אֶשְׁמָֽע:"))
        self.assert_partition(self.ANENU, p)

    def test_pure_verse_and_short_intro_unchanged(self):
        verse = TestRoutingInPipeline.VERSE
        self.assertEqual(self.pieces(verse), [("taamim", verse)])
        # מבוא קצר ("וְנֶאֱמַר:") — נשאר עם הפסוק, יחידה אחת כמו קודם
        intro = "וְנֶאֱמַר: " + verse
        self.assertEqual(self.pieces(intro), [("taamim", intro)])
        # מצודה: שווא נע + פסוק אמיתי (8.24) — ללא שינוי
        m = TestMetsudahPronunciationMarks
        self.assertEqual(_unit_chunk({"text": m.BARCHU + " " + m.DEUT}), "taamim")
        self.assertEqual(self.pieces(m.SHEMA), [("punct", m.SHEMA)])

    def test_stray_accents_in_prose_are_not_a_verse(self):
        """שני טעמים על שתי מילים בסוף פיוט (שבת זכור, עדות המזרח) — לא פסוק:
        היחידה כולה לפי פיסוק."""
        text = ("וַיְהִי בִּימֵי אֲחַשְׁוֵרוֹשׁ, מֶלֶךְ הוּקָם עָל כִּבְרוֹשׁ, נִשָּׂא "
                "וָרָם עַל כָּל־קָצִין וָרֹאשׁ, וַיהֹוָ֛ה הֵנִיחַֽ־ל֥וֹ:")
        self.assertEqual(self.pieces(text), [("punct", text)])
        self.assertEqual(_unit_chunk({"text": text}), "punct")

    def test_forced_chunk_is_never_split(self):
        from aligner.pipeline import split_mixed_unit
        unit = {"text": self.KOL_NIDRE, "kind": "verse", "chunk": "taamim"}
        self.assertEqual(split_mixed_unit(unit), [unit])
        with self.assertRaises(ValueError):
            split_mixed_unit({"text": "אָמֵן", "chunk": "nope"})

    def test_line_breaks_inside_a_unit(self):
        text = self.ANENU.replace(" כַּדָּבָר", "\nכַּדָּבָר")
        p = self.pieces(text)
        self.assertEqual([c for c, _ in p], ["punct", "taamim", "punct"])
        self.assert_partition(text, p)


if __name__ == "__main__":
    unittest.main(verbosity=2)
