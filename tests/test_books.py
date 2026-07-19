# -*- coding: utf-8 -*-
"""בדיקות למודול הספרים המשותף — src/chunker/books.py. רץ בלי רשת."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chunker import books  # noqa: E402


class TestCanon(unittest.TestCase):
    def test_full_tanakh_present(self):
        """39 ספרים: 5 תורה, 21 נביאים (תרי-עשר בנפרד), 13 כתובים."""
        self.assertEqual(len(books.TORAH), 5)
        self.assertEqual(len(books.NEVIIM), 21)
        self.assertEqual(len(books.KETUVIM), 13)
        self.assertEqual(len(books.ALL_BOOKS), 39)

    def test_no_duplicate_names(self):
        he = [h for h, _ in books.ALL_BOOKS]
        en = [e for _, e in books.ALL_BOOKS]
        self.assertEqual(len(set(he)), len(he))
        self.assertEqual(len(set(en)), len(en))

    def test_to_english_hebrew_names(self):
        self.assertEqual(books.to_english("בראשית"), "Genesis")
        self.assertEqual(books.to_english("שמואל א"), "I Samuel")
        self.assertEqual(books.to_english("שיר השירים"), "Song of Songs")
        self.assertEqual(books.to_english("דברי הימים ב"), "II Chronicles")

    def test_to_english_passthrough_and_trim(self):
        self.assertEqual(books.to_english("Genesis"), "Genesis")
        self.assertEqual(books.to_english(" תהלים "), "Psalms")
        self.assertEqual(books.to_english("ספר לא קיים"), "ספר לא קיים")

    def test_aliases(self):
        self.assertEqual(books.to_english("תהילים"), "Psalms")
        self.assertEqual(books.to_english("ישעיה"), "Isaiah")
        self.assertEqual(books.to_english("קוהלת"), "Ecclesiastes")

    def test_is_known(self):
        self.assertTrue(books.is_known("איוב"))
        self.assertTrue(books.is_known("II Kings"))
        self.assertTrue(books.is_known("תהילים"))
        self.assertFalse(books.is_known("ספר הישר"))
        self.assertFalse(books.is_known(""))
        self.assertFalse(books.is_known(None))


class TestUiListMatchesCanon(unittest.TestCase):
    """תפריט הספרים ב-index.html חייב להכיל בדיוק את שמות הקנון בעברית."""

    def test_index_html_book_options(self):
        import re
        html = (Path(__file__).resolve().parent.parent
                / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<select id="book">(.*?)</select>', html, re.S)
        self.assertIsNotNone(m)
        options = re.findall(r"<option>([^<]+)</option>", m.group(1))
        self.assertEqual(options, [he for he, _ in books.ALL_BOOKS])

    def test_index_html_fallback_chapters(self):
        import re
        html = (Path(__file__).resolve().parent.parent
                / "index.html").read_text(encoding="utf-8")
        m = re.search(r"const FALLBACK_CHAPTERS = \{(.*?)\};", html, re.S)
        self.assertIsNotNone(m)
        names = re.findall(r'"([^"]+)":', m.group(1))
        self.assertEqual(sorted(names), sorted(he for he, _ in books.ALL_BOOKS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
