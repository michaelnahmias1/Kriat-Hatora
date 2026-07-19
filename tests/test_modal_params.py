# -*- coding: utf-8 -*-
"""בדיקות ל-modal_worker/params.py — ולידציית הפרמטרים של ה-worker בענן.

נטען ישירות מהנתיב (בלי לייבא את modal_worker/app.py, שדורש את חבילת modal).
רץ בלי רשת, כמו שאר הבדיקות.
"""

import importlib.util
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "modal_params",
    Path(__file__).resolve().parent.parent / "modal_worker" / "params.py")
params = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(params)


class TestParseParams(unittest.TestCase):

    def test_full_chapter_defaults(self):
        """פרק שלם: ריק/0 בטווחים → None, ‏max_words → ברירת המחדל 4."""
        got = params.parse_params({"book": "בראשית", "chapter": "1",
                                   "verse_start": "", "verse_end": "0",
                                   "chapter_end": None})
        self.assertEqual(got, {"book": "בראשית", "chapter": 1,
                               "verse_start": None, "verse_end": None,
                               "chapter_end": None, "max_words": 4})

    def test_verse_range_and_cross_chapter(self):
        got = params.parse_params({"book": "דברים", "chapter": "3",
                                   "verse_start": "23", "verse_end": "11",
                                   "chapter_end": "7", "max_words": "3"})
        self.assertEqual(got["verse_start"], 23)
        self.assertEqual(got["chapter_end"], 7)
        self.assertEqual(got["verse_end"], 11)  # מותר קטן מההתחלה כשחוצים פרק
        self.assertEqual(got["max_words"], 3)

    def test_english_book_name_accepted(self):
        """גם שם אנגלי עובר (run_hybrid ממפה עברית→אנגלית ומקבל את שניהם)."""
        got = params.parse_params({"book": "Genesis", "chapter": 2})
        self.assertEqual(got["book"], "Genesis")

    def test_whitespace_trimmed(self):
        got = params.parse_params({"book": " שמות ", "chapter": " 12 "})
        self.assertEqual(got["book"], "שמות")
        self.assertEqual(got["chapter"], 12)

    def test_nakh_books_accepted(self):
        """כל התנ״ך נתמך — כולל כתיב חלופי (תהילים) ושמות Sefaria באנגלית."""
        for book in ("תהלים", "תהילים", "שמואל א", "דברי הימים ב", "I Samuel"):
            got = params.parse_params({"book": book, "chapter": "1"})
            self.assertEqual(got["book"], book)

    def test_unknown_book_rejected(self):
        with self.assertRaisesRegex(ValueError, "ספר לא מוכר"):
            params.parse_params({"book": "ספר הישר", "chapter": "1"})
        with self.assertRaisesRegex(ValueError, "חסר שם ספר"):
            params.parse_params({"book": "  ", "chapter": "1"})

    def test_missing_chapter_rejected(self):
        with self.assertRaisesRegex(ValueError, "חסר מספר פרק"):
            params.parse_params({"book": "ויקרא", "chapter": ""})

    def test_non_numeric_rejected(self):
        with self.assertRaisesRegex(ValueError, "מספר שלם"):
            params.parse_params({"book": "במדבר", "chapter": "אבג"})

    def test_backwards_ranges_rejected(self):
        with self.assertRaisesRegex(ValueError, "פרק הסיום"):
            params.parse_params({"book": "בראשית", "chapter": "5",
                                 "chapter_end": "2"})
        with self.assertRaisesRegex(ValueError, "פסוק הסיום"):
            params.parse_params({"book": "בראשית", "chapter": "5",
                                 "verse_start": "9", "verse_end": "3"})

    def test_max_words_bounds(self):
        with self.assertRaisesRegex(ValueError, "מקסימום מילים"):
            params.parse_params({"book": "בראשית", "chapter": "1",
                                 "max_words": "11"})
        with self.assertRaisesRegex(ValueError, "לפחות 1"):
            params.parse_params({"book": "בראשית", "chapter": "1",
                                 "max_words": "-2"})


class TestParsePushSub(unittest.TestCase):
    """שדה ה-push_sub הוא best-effort: תקין → dict מצומצם, כל השאר → None."""

    VALID = ('{"endpoint": "https://push.example.com/x", '
             '"expirationTime": null, '
             '"keys": {"p256dh": "PKEY", "auth": "AKEY"}}')

    def test_valid_subscription_normalized(self):
        got = params.parse_push_sub(self.VALID)
        self.assertEqual(got, {"endpoint": "https://push.example.com/x",
                               "keys": {"p256dh": "PKEY", "auth": "AKEY"}})

    def test_empty_and_whitespace(self):
        self.assertIsNone(params.parse_push_sub(""))
        self.assertIsNone(params.parse_push_sub("   "))
        self.assertIsNone(params.parse_push_sub(None))

    def test_garbage_rejected_silently(self):
        self.assertIsNone(params.parse_push_sub("לא JSON"))
        self.assertIsNone(params.parse_push_sub("[1,2]"))
        self.assertIsNone(params.parse_push_sub('{"endpoint": 5}'))

    def test_non_https_endpoint_rejected(self):
        self.assertIsNone(params.parse_push_sub(
            '{"endpoint": "http://x", "keys": {"p256dh": "a", "auth": "b"}}'))

    def test_missing_keys_rejected(self):
        self.assertIsNone(params.parse_push_sub(
            '{"endpoint": "https://x", "keys": {"p256dh": "a"}}'))
        self.assertIsNone(params.parse_push_sub('{"endpoint": "https://x"}'))


if __name__ == "__main__":
    unittest.main()
