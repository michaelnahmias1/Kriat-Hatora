# -*- coding: utf-8 -*-
"""בדיקות ל-api/structure.py — הלוגיקה בלבד, בלי רשת ובלי שרת."""

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

_SPEC = importlib.util.spec_from_file_location(
    "api_structure", Path(__file__).resolve().parent.parent / "api" / "structure.py")
api = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(api)

SHAPE_RESPONSE = [{
    "section": "Torah", "length": 3, "book": "Genesis",
    "title": "Genesis", "heTitle": "בראשית",
    "chapters": [31, 25, 24],
}]


class TestChaptersForBook(unittest.TestCase):
    def setUp(self):
        api._shape_cache.clear()
        patcher = mock.patch.object(api, "_get_json", return_value=SHAPE_RESPONSE)
        self.mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_hebrew_book_maps_and_returns_chapters(self):
        payload = api.build_payload({"book": "בראשית"})
        self.assertEqual(payload["book"], "בראשית")
        self.assertEqual(payload["chapters"], [31, 25, 24])

    def test_result_is_cached(self):
        api.chapters_for_book("Genesis")
        api.chapters_for_book("Genesis")
        self.assertEqual(self.mock.call_count, 1)

    def test_missing_book_rejected(self):
        with self.assertRaises(ValueError):
            api.build_payload({})


class TestBadShape(unittest.TestCase):
    def test_empty_chapters_raises(self):
        api._shape_cache.clear()
        with mock.patch.object(api, "_get_json", return_value=[{"chapters": []}]):
            with self.assertRaises(LookupError):
                api.chapters_for_book("Genesis")


if __name__ == "__main__":
    unittest.main()
