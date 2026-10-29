# -*- coding: utf-8 -*-
"""בדיקות לרשימת הקטעים הנפוצים — data/siddur/popular.json ו-?popular=1 של
‏api/siddur.py (PLAN_TEFILA.md 4.2.3). בלי רשת.

כל רשומה חייבת להצביע על עלה קיים וזמין בקטלוג, עם טווח פסקאות תקין מול
מספר הפסקאות שנרשם בבדיקה החיה (tools/verify_siddur_popular.py). לרשומות
שיש להן תשובת Sefaria מוקלטת (tests/fixtures/siddur) — גם המילים הראשונות
של פסקאות from/to נבדקות מול הטקסט האמיתי.

הרצה:  python3 -m unittest discover -s tests -v
"""

import importlib.util
import json
import re
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
POPULAR = ROOT / "data" / "siddur" / "popular.json"

_SPEC = importlib.util.spec_from_file_location(
    "test_api_siddur_shared", Path(__file__).resolve().parent / "test_api_siddur.py")
shared = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(shared)
api = shared.api

HEBREW = re.compile(r"[א-ת]")
# הרשימה בתוכנית (4.2.3); "קדיש" — על סוגיו. אושרה ב-29.10.2026 (8.16) בתוספת
# נשמת וישתבח; "שוכן עד" (ובעדות המזרח "שועת עניים") — המקום שהחזן מתחיל בו
PLAN_ITEMS = ["קבלת שבת", "לכה דודי", "אשרי", "קדיש", "קדושה", "הלל", "עלינו",
              "אדון עולם", "יגדל", "אין כאלהינו", "אנעים זמירות", "אבינו מלכנו",
              "נשמת", "ישתבח", "שוכן עד", "שועת עניים"]


def load():
    return json.loads(POPULAR.read_text(encoding="utf-8"))


class TestPopularFile(unittest.TestCase):
    def setUp(self):
        self.pop = load()
        self.cat = api.load_catalog()

    def entries(self):
        for nusach, items in self.pop["nusachim"].items():
            for e in items:
                yield nusach, e

    def test_approved_and_note(self):
        self.assertIs(self.pop["draft"], False)  # אושר ע"י בעל הפרויקט (8.16)
        self.assertIn("אושרה", self.pop["note"])
        self.assertIn("29.10.2026", self.pop["note"])
        self.assertNotIn("טיוטה", self.pop["note"])

    def test_owner_additions_in_every_nusach(self):
        """נשמת וישתבח בכל נוסח, ומקום הפתיחה של החזן (שוכן עד / שועת עניים)."""
        for nusach, items in self.pop["nusachim"].items():
            labels = [e["label"] for e in items]
            with self.subTest(nusach=nusach):
                self.assertIn("נשמת", labels)
                self.assertIn("ישתבח", labels)
                self.assertTrue({"שוכן עד", "שועת עניים"} & set(labels))
                by = {e["label"]: e for e in items}
                self.assertTrue(by["נשמת"]["first"].startswith("נִשְׁמַת כָּל"))
                self.assertTrue(by["ישתבח"]["first"].startswith("יִשְׁתַּבַּח שִׁמְךָ"))

    def test_nishmat_ranges(self):
        """הטווחים שנבחרו מול הטקסט האמיתי (‏tools/verify_siddur_popular.py,
        ‏29.10.2026): נשמת — עד סוף הגוש שלפני ישתבח; שוכן עד/שועת עניים — מאותו
        גוש, מהמקום שהחזן מתחיל בו. באשכנז נשמת ושוכן עד הם עלים נפרדים (אין
        טווח בין עלים)."""
        nus = self.pop["nusachim"]
        get = lambda n, label: next(e for e in nus[n] if e["label"] == label)
        edot, sef, ash = (get("edot-hamizrach", "נשמת"), get("sefard", "נשמת"),
                          get("ashkenaz", "נשמת"))
        self.assertEqual((edot["from"], edot["to"]), (20, 28))
        self.assertEqual((sef["from"], sef["to"]), (90, 97))
        self.assertNotIn("from", ash)  # העלה "נשמת כל חי" כולו
        sh = get("edot-hamizrach", "שועת עניים")
        self.assertEqual((sh["path"], sh["from"], sh["to"]), (edot["path"], 23, 28))
        self.assertTrue(sh["first"].startswith("שַׁוְעַת עֲנִיִּים"))
        sa = get("sefard", "שוכן עד")
        self.assertEqual((sa["path"], sa["from"], sa["to"]), (sef["path"], 96, 97))
        self.assertTrue(sa["first"].startswith("שׁוֹכֵן עַד"))
        aa = get("ashkenaz", "שוכן עד")
        self.assertTrue(aa["path"].endswith("/shochen-ad"))
        self.assertEqual((aa["from"], aa["to"]), (2, aa["paragraph_count"]))
        # הגוש נגמר במקהלות — הפסקה שלפני ישתבח
        for e in (edot, sef, sh, sa, aa):
            self.assertRegex(re.sub("[\u0591-\u05c7]", "", e["last"]),
                             "^ו?במקהלו")

    def test_all_nusachim(self):
        self.assertEqual(set(self.pop["nusachim"]),
                         {n["key"] for n in self.cat.nusachim})

    def test_every_entry_is_available_leaf_with_valid_range(self):
        for nusach, e in self.entries():
            with self.subTest(nusach=nusach, label=e["label"]):
                self.assertTrue(e["path"].startswith(nusach + "/"))
                self.assertIsNotNone(self.cat.leaf(e["path"]), "לא עלה בקטלוג")
                self.assertIsNotNone(self.cat.source(e["path"]), "עלה לא זמין")
                total = e["paragraph_count"]
                self.assertIsInstance(total, int)
                self.assertGreaterEqual(total, 1)
                self.assertLessEqual(total, api.MAX_PARAGRAPHS)
                self.assertEqual("from" in e, "to" in e)
                start, end = e.get("from", 1), e.get("to", total)
                self.assertIsInstance(start, int)
                self.assertIsInstance(end, int)
                self.assertTrue(1 <= start <= end <= total, (start, end, total))
                for k in ("first", "last"):
                    self.assertRegex(e[k], HEBREW)

    def test_labels(self):
        for nusach, items in self.pop["nusachim"].items():
            labels = [e["label"] for e in items]
            self.assertEqual(len(labels), len(set(labels)), nusach)
            for label in labels:
                self.assertRegex(label, HEBREW)
                self.assertTrue(any(label.startswith(p) or p in label
                                    for p in PLAN_ITEMS), label)
        # כל פריט בתוכנית מופיע לפחות בנוסח אחד
        every = [e["label"] for _, e in self.entries()]
        for item in PLAN_ITEMS:
            self.assertTrue(any(item in label for label in every), item)


class TestPopularAgainstRecordedText(shared.SiddurTestCase):
    """רשומות שיש להן תשובה אמיתית מוקלטת: הטווח נטען, ומתחיל ונגמר בפסקאות
    שנרשמו בבדיקה החיה."""

    def test_recorded_entries(self):
        cat = api.load_catalog()
        checked = 0
        for nusach, items in load()["nusachim"].items():
            for e in items:
                src = cat.source(e["path"])
                if (src["ref"], src["version"]) not in shared.RECORDED:
                    continue
                q = {"path": e["path"]}
                if "from" in e:
                    q.update({"from": e["from"], "to": e["to"]})
                with self.subTest(label=e["label"], nusach=nusach):
                    payload, _ = self.ok(**q)
                    r, paras = payload["range"], payload["paragraphs"]
                    self.assertEqual(r["total"], e["paragraph_count"])
                    self.assertEqual(paras[r["from"] - 1]["first_words"], e["first"])
                    self.assertEqual(paras[r["to"] - 1]["first_words"], e["last"])
                    self.assertTrue(payload["segments"])
                checked += 1
        # לפחות: לכה דודי וקבלת שבת בספרד, אשרי בעדות ובאשכנז
        self.assertGreaterEqual(checked, 4)


class TestPopularApi(shared.SiddurTestCase):
    def test_items_for_nusach(self):
        payload, headers = self.ok(popular="1", nusach="sefard")
        entries = load()["nusachim"]["sefard"]
        self.assertEqual(payload["nusach"], "sefard")
        self.assertIs(payload["draft"], False)
        self.assertEqual([i["label"] for i in payload["items"]],
                         [e["label"] for e in entries])
        ld = next(i for i in payload["items"] if i["label"] == "לכה דודי")
        self.assertEqual(ld, {"label": "לכה דודי", "path": shared.SEFARD_KS,
                              "title": "קבלת שבת",
                              "breadcrumb": ["ספרד", "שבת", "קבלת שבת"],
                              "available": True, "from": 17, "to": 38})
        whole = next(i for i in payload["items"] if i["label"] == "קבלת שבת")
        self.assertNotIn("from", whole)
        self.assertTrue(all(i["available"] for i in payload["items"]))
        self.assertIn("s-maxage", headers["Cache-Control"])
        self.assertEqual(self.fake.calls, [])  # בלי Sefaria

    def test_every_nusach(self):
        for n in ("edot-hamizrach", "sefard", "ashkenaz"):
            payload, _ = self.ok(popular="1", nusach=n)
            self.assertTrue(payload["items"])

    def test_errors(self):
        for params, status in [({"popular": "1"}, 400),
                               ({"popular": "1", "nusach": "yemenite"}, 404)]:
            payload, st, headers = self.get(**params)
            self.assertEqual(st, status, params)
            self.assertRegex(payload["error"], HEBREW)
            self.assertEqual(headers["Cache-Control"], "no-store")

    def test_entry_not_in_catalog_is_skipped(self):
        fake = {"draft": True, "nusachim": {"sefard": [
            {"label": "לא קיים", "path": "sefard/nope"},
            {"label": "אשרי", "path": shared.SEFARD_ASHREI}]}}
        with mock.patch.object(api, "load_popular", return_value=fake):
            payload, _ = self.ok(popular="1", nusach="sefard")
        self.assertEqual([i["label"] for i in payload["items"]], ["אשרי"])

    def test_popular_json_deployed(self):
        lines = [ln.strip().rstrip("/") for ln in
                 (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith("#")]
        for prefix in ("data", "data/siddur", "data/siddur/popular.json"):
            self.assertNotIn(prefix, lines)
        self.assertEqual(api.POPULAR_PATH, POPULAR)


if __name__ == "__main__":
    unittest.main()
