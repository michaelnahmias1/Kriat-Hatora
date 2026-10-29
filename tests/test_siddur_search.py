# -*- coding: utf-8 -*-
"""בדיקות לחיפוש בסידור (PLAN_TEFILA.md 4.2.4) — בלי רשת.

1. ‏fold / skeleton / Aliases / Catalog.find (src/siddur/catalog.py) על קטלוג,
   קיצורים ושמות נרדפים **סינתטיים** קטנים — דירוג ומקרי קצה.
2. ‏/api/siddur?q= על הקטלוג האמיתי, popular.json ו-aliases.json שבגיט:
   שמות נרדפים מוצאים את הקיצור הנכון, הנוסח הנוכחי קודם, "בתוך", סבילות לכתיב.

הרצה:  python3 -m unittest discover -s tests -v
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from siddur import Aliases, Catalog, fold, load_aliases  # noqa: E402
from siddur.catalog import (ALIASES_PATH, _first_words_match,  # noqa: E402
                            _fuzzy_match, _title_tier, _within_one, skeleton)

_SPEC = importlib.util.spec_from_file_location(
    "test_api_siddur_shared_s", Path(__file__).resolve().parent / "test_api_siddur.py")
shared = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(shared)
api = shared.api


def leaf(key, he, first="", title=""):
    return {"key": key, "title": title or key, "heTitle": he, "ref": "R " + key,
            "v": "v", "first": first}


def folder(key, he, children):
    return {"key": key, "title": key, "heTitle": he, "children": children}


SYNTH = {  # סינתטי
    "nusachim": [
        {"key": "a", "title": "A", "heTitle": "נוסח א", "versions": {"v": {"title": "V"}},
         "children": [folder("wd", "ימי חול", [
             leaf("amida", "עמידה", "אֲדֹנָי שְׂפָתַי תִּפְתָּח"),
             leaf("amida2", "תפילת עמידה למנחה", "אֲדֹנָי שְׂפָתַי"),
             leaf("pz", "פסוקי דזמרה", "בָּרוּךְ שֶׁאָמַר וְהָיָה"),
             leaf("bedtime", "קריאת שמע שעל המיטה", "רִבּוֹנוֹ שֶׁל עוֹלָם"),
             leaf("shema", 'ק"ש וברכותיה', "בָּרוּךְ אַתָּה יְהֹוָה"),
             leaf("shimon", "לכבוד רבי שמעון", "בַּר יוֹחַאי"),
             leaf("kiddush", "קידוש", "סַבְרִי מָרָנָן"),
             leaf("yigdal", "יגדל", "יִגְדַּל אֱלֹהִים חַי"),
             leaf("ein", "אין כאלהינו", "אֵין כֵּאלֹהֵינוּ"),
             leaf("ps93", "תהילים צג", "ה' מָלָךְ גֵּאוּת לָבֵשׁ"),
             leaf("hamazon", "ברכת המזון", "שִׁיר הַמַּעֲלוֹת"),
         ])]},
        {"key": "b", "title": "B", "heTitle": "נוסח ב", "versions": {"v": {"title": "V"}},
         "children": [folder("sh", "שבת", [
             leaf("amida", "עמידה", "אֲדֹנָי שְׂפָתַי"),
             leaf("nishmat", "נשמת כל חי", "נִשְׁמַת כָּל חַי"),
         ])]},
    ]}

POPULAR = {"nusachim": {
    "a": [{"label": "נשמת", "path": "a/wd/pz", "from": 5, "to": 9,
           "first": "נִשְׁמַת כָּל חַי תְּבָרֵךְ"},
          {"label": "קדיש יתום", "path": "a/wd/pz", "from": 10, "to": 11,
           "first": "יִתְגַּדַּל וְיִתְקַדַּשׁ"},
          {"label": "יגדל", "path": "a/wd/yigdal", "first": "יִגְדַּל אֱלֹהִים"},
          {"label": "חסר", "path": "a/nope"}],
    "b": [{"label": "נשמת", "path": "b/sh/nishmat", "first": "נִשְׁמַת כָּל חַי"}],
}}

ALIASES = {"groups": [
    {"names": ["שמונה עשרה", "עמידה", "תפילת עמידה"]},
    {"names": ["קריאת שמע", "שמע", 'ק"ש וברכותיה']},
    {"names": ["קדיש יתום", "קדיש אבלים"]},
    {"names": ["ברכת המזון", 'בהמ"ז']},
    {"names": ["קידוש", "קדוש"]},
    {"names": ["יעלה ויבוא", "יעלה ויבא"], "inside": ["עמידה", "ברכת המזון"]},
]}


class FoldTest(unittest.TestCase):
    def test_fold(self):
        self.assertEqual(fold("בָּרוּךְ־שֶׁאָמַר"), "ברוכ שאמר")      # סופיות ⇐ רגילות
        self.assertEqual(fold('ק"ש'), fold("ק״ש"))
        self.assertEqual(fold('ק"ש'), "קש")
        self.assertEqual(fold('בהמ"ז'), "בהמז")
        for name in ["ה'", "ה׳", "יי", "יְהֹוָה", "יהוה"]:
            self.assertEqual(fold(name + " מלך"), "ה מלכ", name)
        self.assertEqual(fold("לה'"), "לה")
        self.assertEqual(fold("לַיהֹוָה"), "לה")
        self.assertEqual(fold("אלקינו"), fold("אלהינו"))
        self.assertEqual(fold("אֱלוֹקִים"), "אלהימ")
        self.assertEqual(fold("Mourner's KADDISH"), "mourners kaddish")
        self.assertEqual(fold("  "), "")

    def test_skeleton_and_edit_distance(self):
        self.assertEqual(skeleton(fold("אין כאלוהינו")), skeleton(fold("אין כאלהינו")))
        self.assertEqual(skeleton("יגדל"), "יגדל")   # אות ראשונה נשמרת
        self.assertTrue(_within_one("ישתבכ", "ישתבח"))
        self.assertTrue(_within_one("ישתבח", "ישתבחה"))
        self.assertFalse(_within_one("ישתבח", "ישבחה"))
        self.assertTrue(_fuzzy_match(fold("שוכן עד"), fold("שכן עד")))
        self.assertFalse(_fuzzy_match("הלל", "הלא"))     # קצר מדי לשגיאת אות

    def test_title_tier(self):
        self.assertEqual(_title_tier("עמידה", "עמידה"), 0)
        self.assertEqual(_title_tier("עמידה למנחה", "עמידה"), 1)
        self.assertEqual(_title_tier("תפילת עמידה", "עמידה"), 2)
        self.assertIsNone(_title_tier("תפילת עמידה", "מידה"))
        self.assertEqual(_title_tier("תפילת עמידה", "מידה", mid=True), 3)
        self.assertIsNone(_title_tier("לכבוד רבי שמעונ", "שמע", whole=True))
        self.assertEqual(_title_tier("לכבוד רבי שמעונ", "שמע"), 2)
        self.assertIsNone(_title_tier("מלוה מלכה", "ה מלכ", mid=True))  # רב-מילים — לא באמצע
        self.assertTrue(_first_words_match("אשרי יושבי ביתכ", "אשרי יוש"))
        self.assertFalse(_first_words_match("אשרי יושבי ביתכ", "אשרי יוש", whole=True))

    def test_alias_expand(self):
        al = Aliases(ALIASES)
        forms = {v: via for v, via, _ in al.expand(fold("שמונה עשרה"))}
        self.assertEqual(forms[fold("שמונה עשרה")], 0)
        self.assertEqual(forms["עמידה"], 1)
        self.assertEqual(forms["תפילת עמידה"], 1)
        # תחילית של שם (מ-3 תווים) בוחרת את הקבוצה
        self.assertIn("עמידה", {v for v, _, _ in al.expand(fold("שמונה ע"))})
        self.assertEqual(len(al.expand(fold("שמ"))), 1)          # קצר מדי
        # "בתוך": דרך 2, עם השם לתצוגה
        inside = [(v, d) for v, via, d in al.expand(fold("יעלה ויבא")) if via == 2]
        self.assertEqual(inside, [("עמידה", "יעלה ויבוא"), ("ברכת המזונ", "יעלה ויבוא")])
        # לא לפי skeleton: "קדיש" ו"קידוש" זהים בו, אבל אינם שמות נרדפים
        self.assertNotIn("קידוש", {v for v, _, _ in al.expand(fold("קדיש"))})


class FindTest(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog(json.loads(json.dumps(SYNTH)))
        self.al = Aliases(ALIASES)

    def find(self, q, nusach="a", every=False, **kw):
        return self.cat.find(q, nusach=nusach, all_nusachim=every, popular=POPULAR,
                             aliases=self.al, **kw)

    def paths(self, res):
        return [r["path"] for r in res["results"]]

    def test_ranking_exact_prefix_contains_first(self):
        res = self.find("עמידה")
        self.assertEqual(self.paths(res)[:2], ["a/wd/amida", "a/wd/amida2"])
        self.assertEqual([r["match"] for r in res["results"][:2]], ["title", "title"])
        # מילים ראשונות — אחרי כל התאמות הכותרת
        res = self.find("אדני שפתי")
        self.assertEqual(self.paths(res), ["a/wd/amida", "a/wd/amida2"])
        self.assertEqual({r["match"] for r in res["results"]}, {"first"})

    def test_alias_finds_title(self):
        res = self.find("שמונה עשרה")
        self.assertEqual(self.paths(res), ["a/wd/amida", "a/wd/amida2"])
        self.assertEqual(res["results"][0]["via"], "alias")
        # "קריאת שמע": השם הנרדף הזהה לכותרת קודם לתחילית ישירה; לא "שמעון"
        res = self.find("קריאת שמע")
        self.assertEqual(self.paths(res), ["a/wd/shema", "a/wd/bedtime"])
        res = self.find('בהמ"ז')
        self.assertEqual(self.paths(res), ["a/wd/hamazon"])

    def test_shortcuts_first_and_by_alias(self):
        res = self.find("קדיש אבלים")
        self.assertEqual([s["label"] for s in res["shortcuts"]], ["קדיש יתום"])
        sc = res["shortcuts"][0]
        self.assertEqual((sc["from"], sc["to"], sc["nusach"], sc["via"]), (10, 11, "a", "alias"))
        self.assertEqual(sc["title"], "פסוקי דזמרה")
        # הקיצור הוא מילה ראשונה של שאילתה ארוכה יותר
        res = self.find("נשמת כל חי")
        self.assertEqual([s["label"] for s in res["shortcuts"]], ["נשמת"])
        # קיצור לעלה שלם — העלה לא מוצג שוב ברשימה
        res = self.find("יגדל")
        self.assertEqual([s["label"] for s in res["shortcuts"]], ["יגדל"])
        self.assertNotIn("a/wd/yigdal", self.paths(res))
        # רשומה שאינה עלה בקטלוג — מושמטת
        self.assertEqual(self.find("חסר")["shortcuts"], [])

    def test_inside_hint(self):
        res = self.find("יעלה ויבוא")
        self.assertEqual(self.paths(res), ["a/wd/amida", "a/wd/hamazon", "a/wd/amida2"])
        self.assertEqual(res["results"][0]["via"], "inside")
        self.assertIn("«יעלה ויבוא»", res["results"][0]["hint"])

    def test_nusach_scope(self):
        self.assertEqual([s["nusach"] for s in self.find("נשמת")["shortcuts"]], ["a"])
        res = self.find("נשמת", nusach="b", every=True)
        self.assertEqual([s["nusach"] for s in res["shortcuts"]], ["b", "a"])  # הנוכחי קודם
        res = self.find("עמידה", nusach="b", every=True)
        self.assertEqual(self.paths(res)[0], "b/sh/amida")
        self.assertEqual({r["nusach"] for r in res["results"]}, {"a", "b"})
        res = self.find("עמידה", nusach=None)   # בלי נוסח — הכול, בסדר הקטלוג
        self.assertEqual(self.paths(res)[0], "a/wd/amida")

    def test_fuzzy_only_when_nothing_else(self):
        res = self.find("אין כאלוהינו")
        self.assertEqual(self.paths(res), ["a/wd/ein"])
        self.assertEqual(res["results"][0]["match"], "fuzzy")
        res = self.find("יגדלל")                     # אות עודפת
        self.assertEqual([s["label"] for s in res["shortcuts"]], ["יגדל"])
        self.assertEqual(res["shortcuts"][0]["match"], "fuzzy")
        # יש התאמה ישירה ⇐ בלי תוצאות מטושטשות
        self.assertEqual(self.paths(self.find("קידוש")), ["a/wd/kiddush"])

    def test_divine_name_and_finals(self):
        for q in ["ה' מלך", "יי מלך", "יהוה מלך", "ה׳ מָלָךְ"]:
            self.assertEqual(self.paths(self.find(q)), ["a/wd/ps93"], q)

    def test_empty_and_limit(self):
        self.assertEqual(self.find("  "), {"shortcuts": [], "results": [], "truncated": False})
        res = self.find("ע", limit=1)
        self.assertEqual(len(res["results"]), 1)
        self.assertTrue(res["truncated"])


class RealDataSearchTest(shared.SiddurTestCase):
    """‏/api/siddur?q= על הקטלוג, הקיצורים והשמות הנרדפים האמיתיים."""

    def search(self, **params):
        payload, headers = self.ok(**params)
        self.assertEqual(self.fake.calls, [])  # חיפוש — בלי Sefaria
        return payload

    def labels(self, payload):
        return [(s["nusach"], s["label"]) for s in payload["shortcuts"]]

    def test_aliases_file(self):
        data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
        seen = {}
        for g in data["groups"]:
            self.assertTrue(g["names"])
            self.assertLessEqual(set(g), {"names", "inside"})
            for n in g["names"]:
                f = fold(n)
                self.assertTrue(f, n)
                self.assertNotIn(f, seen, f"{n} בשתי קבוצות")
                seen[f] = g
        lines = [ln.strip().rstrip("/") for ln in
                 (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()]
        self.assertNotIn("data/siddur/aliases.json", lines)   # נפרס עם הפונקציה
        self.assertEqual(len(load_aliases().groups), len(data["groups"]))

    def test_every_alias_group_finds_something(self):
        """כל קבוצה מוצאת משהו לפחות בנוסח אחד — שם נרדף שלא מוביל לשום דבר
        הוא טעות בקובץ."""
        data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
        for g in data["groups"]:
            with self.subTest(name=g["names"][0]):
                p = self.search(q=g["names"][0])
                self.assertTrue(p["shortcuts"] or p["results"])

    def test_alias_query_finds_shortcut(self):
        p = self.search(q="קדיש אבלים", nusach="ashkenaz")
        self.assertEqual(self.labels(p)[0], ("ashkenaz", "קדיש יתום"))
        p = self.search(q="שיר הכבוד", nusach="sefard")
        self.assertEqual(self.labels(p)[0], ("sefard", "אנעים זמירות"))
        sc = p["shortcuts"][0]
        self.assertEqual((sc["from"], sc["to"]), (117, 148))
        self.assertEqual(sc["path"], "sefard/shabbat/musaf")
        p = self.search(q="נשמת כל חי", nusach="edot-hamizrach")
        self.assertEqual(self.labels(p)[0], ("edot-hamizrach", "נשמת"))
        p = self.search(q="שוכן עד", nusach="edot-hamizrach")
        self.assertEqual(self.labels(p)[0], ("edot-hamizrach", "שועת עניים"))

    def test_alias_query_finds_titles(self):
        p = self.search(q="שמונה עשרה", nusach="sefard")
        self.assertTrue(p["results"])
        self.assertTrue(all("עמידה" in r["title"] for r in p["results"][:5]))
        p = self.search(q="מעריב", nusach="sefard")
        self.assertIn("ערבית", p["results"][0]["title"])
        p = self.search(q='בהמ"ז', nusach="edot-hamizrach")
        self.assertIn("ברכת המזון", p["results"][0]["title"])
        p = self.search(q="יעלה ויבוא", nusach="ashkenaz")
        self.assertEqual(p["results"][0]["via"], "inside")
        self.assertIn("«יעלה ויבוא»", p["results"][0]["hint"])

    def test_nusach_scope_and_all(self):
        p = self.search(q="נשמת", nusach="sefard")
        self.assertEqual(self.labels(p), [("sefard", "נשמת")])
        self.assertFalse(p["all"])
        self.assertTrue(all(r["path"].startswith("sefard/") for r in p["results"]))
        p = self.search(q="נשמת", nusach="sefard", all="1")
        self.assertTrue(p["all"])
        self.assertEqual([n for n, _ in self.labels(p)],
                         ["sefard", "edot-hamizrach", "ashkenaz"])
        self.assertEqual(self.search(q="נשמת")["all"], True)   # בלי נוסח — הכול

    def test_shortcuts_then_results_shape(self):
        p = self.search(q="ישתבח", nusach="ashkenaz")
        self.assertEqual(self.labels(p), [("ashkenaz", "ישתבח")])
        sc = p["shortcuts"][0]
        self.assertEqual(set(sc) - {"via"}, {"label", "path", "title", "breadcrumb",
                                            "available", "nusach", "match"})
        # הקיצור הוא העלה של חול כולו — לא מוצג שוב; של שבת כן
        paths = [r["path"] for r in p["results"]]
        self.assertNotIn(sc["path"], paths)
        self.assertIn("ashkenaz/shabbat/shacharit/pesukei-dezimra/yishtabach", paths)
        r = p["results"][0]
        self.assertTrue({"key", "path", "title", "is_leaf", "available", "breadcrumb",
                         "nusach", "match"} <= set(r))

    def test_typo_tolerance(self):
        p = self.search(q="ישתבך", nusach="sefard")      # ח ⇐ כ
        self.assertEqual(self.labels(p), [("sefard", "ישתבח")])
        self.assertEqual(p["shortcuts"][0]["match"], "fuzzy")
        p = self.search(q="אין כאלוהינו", nusach="ashkenaz")   # כתיב מלא
        self.assertEqual(self.labels(p)[0], ("ashkenaz", "אין כאלהינו"))


if __name__ == "__main__":
    unittest.main()
