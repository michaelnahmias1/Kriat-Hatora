# -*- coding: utf-8 -*-
"""בדיקות ל-api/segments.py — הלוגיקה בלבד, בלי רשת ובלי שרת.

הקריאות ל-Sefaria מוחלפות ב-stub; בודקים בניית ref, ולידציה של קלט,
ומבנה ה-JSON שהממשק בדפדפן מסתמך עליו.
"""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

_SPEC = importlib.util.spec_from_file_location(
    "api_segments", Path(__file__).resolve().parent.parent / "api" / "segments.py")
api = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(api)

# פסוק אמיתי בסגנון MAM: בראשית א:א (טעמים: טפחא, מונח, אתנחתא...)
VERSE_1 = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
VERSE_2 = "וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃"

VERSIONS_RESPONSE = [
    {"versionTitle": "Tanach with Nikkud", "language": "he"},
    {"versionTitle": "Miqra according to the Masorah", "language": "he"},
]


def fake_get_json(url, params=None):
    if "/api/texts/versions/" in url:
        return VERSIONS_RESPONSE
    if "/api/v3/texts/" in url:
        return {"versions": [{"text": [VERSE_1, VERSE_2]}]}
    raise AssertionError(f"קריאת רשת לא צפויה: {url}")


class TestBuildRef(unittest.TestCase):
    def test_whole_chapter(self):
        self.assertEqual(api.build_ref("Genesis", 1), "Genesis 1")

    def test_verse_range(self):
        self.assertEqual(api.build_ref("Genesis", 1, 1, None, 5), "Genesis 1:1-5")

    def test_cross_chapter(self):
        self.assertEqual(api.build_ref("Exodus", 13, 17, 14, 8),
                         "Exodus 13:17-14:8")


class TestBuildPayload(unittest.TestCase):
    def setUp(self):
        api._version_cache.clear()
        patcher = mock.patch.object(api, "_get_json", side_effect=fake_get_json)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_hebrew_book_name_and_shape(self):
        payload = api.build_payload({"book": "בראשית", "chapter": "1"})
        self.assertEqual(payload["ref"], "Genesis 1")
        self.assertEqual(payload["version"], "Miqra according to the Masorah")
        self.assertEqual(payload["n_verses"], 2)
        self.assertGreater(len(payload["segments"]), 2)
        seg = payload["segments"][0]
        for key in ("display", "verse", "words", "letters", "verse_end"):
            self.assertIn(key, seg)

    def test_segments_respect_max_words_and_verse_end(self):
        payload = api.build_payload({"book": "בראשית", "chapter": "1"})
        segs = payload["segments"]
        self.assertTrue(all(s["words"] >= 1 for s in segs))
        # המקטע האחרון של כל פסוק מסומן — נחוץ למשקל ההפסקה בתזמון האוטומטי
        last_of_verse1 = [s for s in segs if s["verse"] == 1][-1]
        self.assertTrue(last_of_verse1["verse_end"])
        first_of_verse1 = [s for s in segs if s["verse"] == 1][0]
        self.assertFalse(first_of_verse1["verse_end"]
                         if len([s for s in segs if s["verse"] == 1]) > 1 else False)

    def test_verse_numbering_starts_at_verse_start(self):
        payload = api.build_payload(
            {"book": "בראשית", "chapter": "1", "verse_start": "3", "verse_end": "4"})
        self.assertEqual(payload["ref"], "Genesis 1:3-4")
        self.assertEqual(payload["segments"][0]["verse"], 3)

    def test_missing_book_rejected(self):
        with self.assertRaises(ValueError):
            api.build_payload({"chapter": "1"})

    def test_missing_chapter_rejected(self):
        with self.assertRaises(ValueError):
            api.build_payload({"book": "בראשית"})

    def test_bad_number_rejected(self):
        with self.assertRaises(ValueError):
            api.build_payload({"book": "בראשית", "chapter": "אבג"})

    def test_cross_chapter_requires_verse_start(self):
        with self.assertRaises(ValueError):
            api.build_payload({"book": "בראשית", "chapter": "1", "chapter_end": "2"})

    def test_max_words_clamped(self):
        payload = api.build_payload(
            {"book": "בראשית", "chapter": "1", "max_words": "99"})
        self.assertEqual(payload["max_words"], 8)


class TestNoMamVersion(unittest.TestCase):
    def test_lookup_error_when_no_mam(self):
        api._version_cache.clear()
        with mock.patch.object(api, "_get_json",
                               return_value=[{"versionTitle": "Other", "language": "he"}]):
            with self.assertRaises(LookupError):
                api.find_mam_version("Genesis")


if __name__ == "__main__":
    unittest.main()
