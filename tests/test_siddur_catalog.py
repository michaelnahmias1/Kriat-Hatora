# -*- coding: utf-8 -*-
"""בדיקות לקטלוג הסידור (PLAN_TEFILA.md 4.2.1) — בלי רשת.

1. הקטלוג האמיתי שנשמר בגיט (data/siddur/catalog.json): מבנה ואינווריאנטים.
2. src/siddur/catalog.py (ניווט, ref לעלה, חיפוש) — על fixture סינתטי קטן.
3. הפונקציות הטהורות של tools/build_siddur_catalog.py — על fixtures סינתטיים.

⚠️ ה-fixtures בסעיפים 2–3 **סינתטיים** ונכתבו ביד; הם לא משקפים את Sefaria.

הרצה:  python3 -m unittest discover -s tests -v
"""

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from siddur import Catalog, load_catalog, normalize, split_path  # noqa: E402
from siddur.catalog import CATALOG_PATH  # noqa: E402

_SPEC = importlib.util.spec_from_file_location(
    "build_siddur_catalog", ROOT / "tools" / "build_siddur_catalog.py")
bc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bc)

KEY_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def walk(nodes, keys=()):
    for n in nodes:
        p = keys + (n["key"],)
        yield p, n
        if "children" in n:
            yield from walk(n["children"], p)


# =============================================================================
# 1. הקטלוג האמיתי
# =============================================================================

class RealCatalogTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.raw = CATALOG_PATH.read_text(encoding="utf-8")
        cls.data = json.loads(cls.raw)
        cls.cat = load_catalog()
        cls.overrides = json.loads(
            (ROOT / "data" / "siddur" / "overrides.json").read_text(encoding="utf-8"))

    def test_three_nusachim(self):
        got = {n["key"]: n["index"] for n in self.data["nusachim"]}
        self.assertEqual(got, {"edot-hamizrach": "Siddur Edot HaMizrach",
                               "sefard": "Siddur Sefard",
                               "ashkenaz": "Siddur Ashkenaz"})

    def test_compact(self):
        # בלי גוף טקסט — הקטלוג קטן (מוגש מה-API כמו שהוא)
        self.assertLess(len(self.raw.encode("utf-8")), 600 * 1024)

    def test_day_types_level(self):
        day_keys = [d["key"] for d in self.data["day_types"]]
        for nus in self.data["nusachim"]:
            keys = [d["key"] for d in nus["children"]]
            self.assertTrue(set(keys) <= set(day_keys), keys)
            self.assertEqual(keys, [k for k in day_keys if k in keys])  # בסדר הקבוע
            for need in ("weekday", "shabbat", "rosh-chodesh", "festivals"):
                self.assertIn(need, keys, nus["key"])

    def test_every_node_has_titles_and_valid_key(self):
        for path, n in walk(self.data["nusachim"]):
            with self.subTest(path="/".join(path)):
                self.assertTrue(KEY_RE.match(n["key"]), n["key"])
                he = n.get("heTitle", "")
                self.assertTrue(he and he == he.strip())
                self.assertTrue(re.search(r"[א-ת]", he))
                self.assertTrue(n.get("title"))
                if "children" in n:
                    self.assertTrue(n["children"], "צומת ביניים בלי ילדים")

    def test_no_duplicate_paths(self):
        paths = ["/".join(p) for p, _ in walk(self.data["nusachim"])]
        self.assertEqual(len(paths), len(set(paths)))

    def test_every_leaf_has_ref_and_version_or_unavailable(self):
        for nus in self.data["nusachim"]:
            versions = nus["versions"]
            for path, n in walk(nus["children"], (nus["key"],)):
                if "children" in n:
                    continue
                with self.subTest(path="/".join(path)):
                    # עלה של אוסף (4.4.1) — ה-ref של האינדקס שלו, או דף בוויקיטקסט
                    index = (versions.get(n["v"]) or {}).get("index") or nus["index"]
                    if n.get("ws"):
                        self.assertTrue(n["ref"].startswith(n["ws"]["page"] + "#"))
                    elif not n.get("unavailable"):
                        self.assertTrue(n["ref"].startswith(index + ", ")
                                        or n["ref"] == index, n["ref"])
                    if n.get("unavailable"):
                        self.assertIsNone(n["v"])
                    else:
                        self.assertIn(n["v"], versions)
                    for a in n.get("alt", []):
                        self.assertIn(a, versions)
                        self.assertNotEqual(a, n["v"])

    def test_chosen_version_follows_policy(self):
        for nus in self.data["nusachim"]:
            pol = nus["policy"]
            coll_versions = {v for v, d in nus["versions"].items() if d.get("source")}
            for day in nus["children"]:
                prefs = pol.get(day["key"]) or pol["*"]
                for path, n in walk(day["children"]):
                    if "children" in n or not n.get("v"):
                        continue
                    if n["v"] in coll_versions:  # אוסף — מהדורה משלו (4.4.1)
                        continue
                    have = [n["v"]] + n.get("alt", [])
                    self.assertEqual(n["v"], [p for p in prefs if p in have][0],
                                     n["ref"])

    def test_versions_and_licenses_recorded(self):
        vers = {n["key"]: n["versions"] for n in self.data["nusachim"]}
        # versionTitle מדויק — כולל הרווח בהתחלה (docs/siddur_survey.md)
        self.assertEqual(vers["edot-hamizrach"]["shaliehsaboo"]["title"],
                         " Shaliehsaboo Edition")
        for nus, vs in vers.items():
            for vid, v in vs.items():
                with self.subTest(nusach=nus, version=vid):
                    self.assertTrue(v["license"] and v["license"] != "unknown")
        self.assertEqual(vers["edot-hamizrach"]["shaliehsaboo"]["license"], "CC0")

    def test_versions_match_overrides(self):
        for cfg in self.overrides["nusachim"]:
            nus = self.cat.node(cfg["key"])
            self.assertEqual({k: v["title"] for k, v in nus["versions"].items()
                              if not v.get("source")}, cfg["versions"])
            self.assertEqual({k for k, v in nus["versions"].items() if v.get("source")},
                             set(cfg.get("collection_versions", {})))
            self.assertEqual(nus["policy"], cfg["policy"])

    def test_most_leaves_available(self):
        for nus in self.data["nusachim"]:
            leaves = self.cat.leaves(nus["key"])
            ok = sum(1 for _, n in leaves if n.get("v"))
            self.assertGreater(ok / len(leaves), 0.9, nus["key"])

    def test_stats_match_tree(self):
        for nus in self.data["nusachim"]:
            st = self.data["stats"][nus["key"]]
            leaves = self.cat.leaves(nus["key"])
            self.assertEqual(st["leaves"], len(leaves))
            self.assertEqual(st["available"], sum(1 for _, n in leaves if n.get("v")))
            self.assertEqual(st["day_types"], len(nus["children"]))

    def test_sefaria_titles_kept_verbatim_in_ref(self):
        # ‏Sefaria דוחה את ה-ref בלי הרווח שבסוף הכותר (נבדק מול ה-API)
        refs = [n["ref"] for _, n in self.cat.leaves("sefard")]
        self.assertTrue(any(r.startswith("Siddur Sefard, Additional Prayers , ")
                            for r in refs))

    def test_source_for_real_leaf(self):
        hits = [r for r in self.cat.search_titles("אשרי", nusach="edot-hamizrach")
                if r["leaf"] and r["available"]]
        self.assertTrue(hits)
        src = self.cat.source(hits[0]["path"])
        self.assertEqual(src["index"], "Siddur Edot HaMizrach")
        self.assertIn(src["version"], (" Shaliehsaboo Edition", "Torat Emet 357"))
        self.assertTrue(src["ref"].startswith("Siddur Edot HaMizrach, "))

    def test_first_words_mostly_present(self):
        leaves = [n for _, n in self.cat.leaves("") if n.get("v")]
        with_first = [n for n in leaves if n.get("first")]
        self.assertGreater(len(with_first) / len(leaves), 0.9)
        for n in with_first:
            self.assertLessEqual(len(n["first"].split()), bc.FIRST_WORDS)


# =============================================================================
# 2. src/siddur/catalog.py — fixture סינתטי
# =============================================================================

SYNTH = {  # סינתטי
    "schema_version": 1,
    "nusachim": [
        {"key": "nus-a", "title": "Nusach A", "heTitle": "נוסח א",
         "index": "Fake Siddur A",
         "versions": {"v1": {"title": " Lead Space", "license": "CC0"},
                      "v2": {"title": "Second", "license": "Public Domain"}},
         "policy": {"*": ["v1", "v2"]},
         "children": [
             {"key": "weekday", "title": "Weekday", "heTitle": "ימי חול",
              "children": [
                  {"key": "shacharit", "title": "Shacharit", "heTitle": "שחרית",
                   "children": [
                       {"key": "ashrei", "title": "Ashrei", "heTitle": "אשרי",
                        "ref": "Fake Siddur A, Shacharit, Ashrei", "v": "v1",
                        "alt": ["v2"], "first": "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ"},
                       {"key": "aleinu", "title": "Aleinu", "heTitle": "עלינו",
                        "ref": "Fake Siddur A, Shacharit, Aleinu", "v": None,
                        "unavailable": True},
                       {"key": "kaddish", "title": "Mourner's Kaddish",
                        "heTitle": "קדיש יתום",
                        "ref": "Fake Siddur A, Shacharit, Mourner's Kaddish",
                        "v": "v2", "first": "יִתְגַּדַּל וְיִתְקַדַּשׁ"},
                   ]},
                  {"key": "kabbalat", "title": "Tehillat Ashrei",
                   "heTitle": "תהלה לדוד",
                   "ref": "Fake Siddur A, Tehillat", "v": "v1",
                   "first": "תְּהִלָּה לְדָוִד אֲרוֹמִמְךָ", "depth": 2},
              ]},
         ]},
        {"key": "nus-b", "title": "Nusach B", "heTitle": "נוסח ב",
         "index": "Fake Siddur B",
         "versions": {"x": {"title": "X", "license": "CC-BY"}},
         "policy": {"*": ["x"]},
         "children": [
             {"key": "shabbat", "title": "Shabbat", "heTitle": "שבת",
              "children": [
                  {"key": "ashrei", "title": "Ashrei", "heTitle": "אַשְׁרֵי",
                   "ref": "Fake Siddur B, Ashrei", "v": "x",
                   "first": "אַשְׁרֵי־יוֹשְׁבֵי"},
              ]},
         ]},
    ],
}


class CatalogApiTest(unittest.TestCase):

    def setUp(self):
        self.cat = Catalog(json.loads(json.dumps(SYNTH)))

    def test_split_path(self):
        self.assertEqual(split_path("/a/b/"), ["a", "b"])
        self.assertEqual(split_path(["a", "", "b"]), ["a", "b"])
        self.assertEqual(split_path(None), [])
        self.assertEqual(split_path(""), [])

    def test_root_children_are_nusachim(self):
        ch = self.cat.children("")
        self.assertEqual([c["path"] for c in ch], ["nus-a", "nus-b"])
        self.assertFalse(ch[0]["leaf"])
        self.assertEqual(ch[0]["heTitle"], "נוסח א")

    def test_children_of_prayer(self):
        ch = self.cat.children("nus-a/weekday/shacharit")
        self.assertEqual([c["key"] for c in ch], ["ashrei", "aleinu", "kaddish"])
        self.assertEqual(ch[0]["path"], "nus-a/weekday/shacharit/ashrei")
        self.assertTrue(ch[0]["leaf"] and ch[0]["available"])
        self.assertFalse(ch[1]["available"])
        self.assertEqual(ch[0]["first"], "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ")

    def test_children_of_day_counts(self):
        ch = self.cat.children(["nus-a", "weekday"])
        self.assertEqual(ch[0]["count"], 3)
        self.assertTrue(ch[1]["leaf"])  # תפילה שהיא עלה בעצמה

    def test_children_of_leaf_or_missing_is_none(self):
        self.assertIsNone(self.cat.children("nus-a/weekday/shacharit/ashrei"))
        self.assertIsNone(self.cat.children("nus-a/nope"))

    def test_node_and_leaf(self):
        self.assertEqual(self.cat.node("nus-a/weekday")["heTitle"], "ימי חול")
        self.assertIsNone(self.cat.node(""))
        self.assertIsNone(self.cat.node("nus-a/weekday/shacharit/ashrei/deeper"))
        self.assertIsNone(self.cat.leaf("nus-a/weekday"))
        self.assertEqual(self.cat.leaf("nus-a/weekday/shacharit/ashrei")["key"],
                         "ashrei")

    def test_source(self):
        src = self.cat.source("nus-a/weekday/shacharit/ashrei")
        self.assertEqual(src, {"ref": "Fake Siddur A, Shacharit, Ashrei",
                               "version": " Lead Space", "version_id": "v1",
                               "license": "CC0", "index": "Fake Siddur A",
                               "depth": 1, "nusach": "nus-a", "source": "sefaria"})
        self.assertEqual(self.cat.source("nus-a/weekday/kabbalat")["depth"], 2)
        self.assertEqual(
            self.cat.source("nus-a/weekday/shacharit/kaddish")["version"], "Second")

    def test_source_unavailable_and_missing(self):
        self.assertIsNone(self.cat.source("nus-a/weekday/shacharit/aleinu"))
        with self.assertRaises(KeyError):
            self.cat.source("nus-a/weekday")
        with self.assertRaises(KeyError):
            self.cat.source("nus-a/missing")

    def test_leaves_and_breadcrumb(self):
        self.assertEqual([p for p, _ in self.cat.leaves("nus-a")],
                         ["nus-a/weekday/shacharit/ashrei",
                          "nus-a/weekday/shacharit/aleinu",
                          "nus-a/weekday/shacharit/kaddish",
                          "nus-a/weekday/kabbalat"])
        self.assertEqual(len(self.cat.leaves("")), 5)
        self.assertEqual([p for p, _ in self.cat.leaves("nus-a/weekday/kabbalat")],
                         ["nus-a/weekday/kabbalat"])
        self.assertEqual(self.cat.leaves("nus"), [])  # תחילית של מפתח אינה נתיב
        self.assertEqual(self.cat.breadcrumb("nus-a/weekday/shacharit/ashrei"),
                         ["נוסח א", "ימי חול", "שחרית", "אשרי"])

    def test_normalize(self):
        self.assertEqual(normalize("בָּרוּךְ־שֶׁאָמַר"), "ברוך שאמר")
        self.assertEqual(normalize("ה׳ אֱלֹהֵינוּ"), "ה' אלהינו")
        self.assertEqual(normalize("אַ֥שְׁרֵי, יוֹשְׁבֵ֖י!"), "אשרי יושבי")
        self.assertEqual(normalize("Mourner's  KADDISH"), "mourner's kaddish")
        self.assertEqual(normalize(""), "")

    def test_search_titles_ranking(self):
        res = self.cat.search_titles("אשרי")
        paths = [r["path"] for r in res]
        # התאמה מלאה (בשני הנוסחים, בסדר הקטלוג) לפני תת-מחרוזת באנגלית
        self.assertEqual(paths[:2], ["nus-a/weekday/shacharit/ashrei",
                                     "nus-b/shabbat/ashrei"])
        self.assertEqual(res[0]["breadcrumb"], ["נוסח א", "ימי חול", "שחרית", "אשרי"])
        self.assertEqual(res[0]["match"], "title")
        self.assertNotIn("nus-a/weekday/kabbalat", paths)
        # באנגלית: התאמה מלאה ("Ashrei") לפני תת-מחרוזת ("Tehillat Ashrei")
        self.assertEqual([r["path"] for r in self.cat.search_titles("ASHREI")],
                         ["nus-a/weekday/shacharit/ashrei", "nus-b/shabbat/ashrei",
                          "nus-a/weekday/kabbalat"])

    def test_search_titles_filters(self):
        self.assertEqual([r["path"] for r in self.cat.search_titles("אשרי", "nus-b")],
                         ["nus-b/shabbat/ashrei"])
        self.assertEqual(self.cat.search_titles("   "), [])
        self.assertEqual(self.cat.search_titles("נוסח"), [])  # נוסח אינו תוצאה
        self.assertEqual([r["path"] for r in self.cat.search_titles("shachar")],
                         ["nus-a/weekday/shacharit"])  # גם צמתי ביניים
        self.assertEqual(len(self.cat.search_titles("a", limit=2)), 2)

    def test_search_first_words(self):
        res = self.cat.search_first_words("אשרי יושבי")
        self.assertEqual([r["path"] for r in res],
                         ["nus-a/weekday/shacharit/ashrei", "nus-b/shabbat/ashrei"])
        self.assertEqual(res[0]["match"], "first")
        # המילה האחרונה כתחילית; ניקוד בשאילתה לא משנה
        self.assertEqual([r["path"] for r in self.cat.search_first_words("יִתְגַּ")],
                         ["nus-a/weekday/shacharit/kaddish"])
        self.assertEqual(self.cat.search_first_words("יושבי"), [])  # רק מההתחלה
        self.assertEqual(self.cat.search_first_words("תהלה לדוד ארוממך אלהי"), [])
        self.assertEqual(len(self.cat.search_first_words("אשרי", nusach="nus-b")), 1)

    def test_search_combined_no_duplicates(self):
        res = self.cat.search("אשרי")
        paths = [r["path"] for r in res]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(self.cat.search("יתגדל")[0]["path"],
                         "nus-a/weekday/shacharit/kaddish")
        self.assertEqual(self.cat.search("יתגדל")[0]["match"], "first")

    def test_load_from_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.json"
            p.write_text(json.dumps(SYNTH, ensure_ascii=False), encoding="utf-8")
            cat = load_catalog(p)
            self.assertEqual(len(cat.children()), 2)


# =============================================================================
# 3. tools/build_siddur_catalog.py — פונקציות טהורות
# =============================================================================

SYNTH_SCHEMA = {  # סינתטי — בפורמט של v2/raw/index (titles + nodes)
    "key": "Fake Siddur",
    "titles": [{"lang": "en", "text": "Fake Siddur", "primary": True}],
    "nodes": [
        {"key": "Weekday", "titles": [
            {"lang": "en", "text": "Weekday", "primary": True},
            {"lang": "he", "text": "ימי חול", "primary": True}],
         "nodes": [
             {"key": "Shacharit", "titles": [
                 {"lang": "en", "text": "Shacharit", "primary": True},
                 {"lang": "he", "text": "שחרית", "primary": True}],
              "nodes": [
                  {"key": "Ashrei", "depth": 1, "titles": [
                      {"lang": "en", "text": "Ashrei", "primary": True},
                      {"lang": "he", "text": "אשרי", "primary": True}]},
                  {"key": "Kaddish", "depth": 1, "titles": [
                      {"lang": "en", "text": "Mourner's Kaddish", "primary": True},
                      {"lang": "he", "text": "קדיש יתום", "primary": True}]},
                  {"key": "Kaddish", "depth": 1, "titles": [
                      {"lang": "en", "text": "Mourner's Kaddish", "primary": True},
                      {"lang": "he", "text": "קדיש יתום", "primary": True}]},
              ]}]},
        {"key": "Extra ", "titles": [
            {"lang": "en", "text": "Extra ", "primary": True},
            {"lang": "he", "text": " תוספות", "primary": True}],
         "nodes": [
             {"key": "Avot", "depth": 2, "titles": [
                 {"lang": "en", "text": "Avot", "primary": True},
                 {"lang": "he", "text": "אבות", "primary": True}]}]},
        {"key": "Havdalah", "depth": 1, "titles": [
            {"lang": "en", "text": "Havdalah", "primary": True},
            {"lang": "he", "text": "הבדלה", "primary": True}]},
    ],
}


class BuilderPureTest(unittest.TestCase):

    def test_schema_leaves(self):
        leaves = bc.schema_leaves(SYNTH_SCHEMA, "Fake Siddur")
        self.assertEqual([lf["ref"] for lf in leaves], [
            "Fake Siddur, Weekday, Shacharit, Ashrei",
            "Fake Siddur, Weekday, Shacharit, Mourner's Kaddish",
            "Fake Siddur, Weekday, Shacharit, Mourner's Kaddish",
            "Fake Siddur, Extra , Avot",  # כותר כמו שהוא, כולל הרווח
            "Fake Siddur, Havdalah"])
        self.assertEqual(leaves[0]["he"], ["ימי חול", "שחרית", "אשרי"])
        self.assertNotEqual(leaves[1]["ids"], leaves[2]["ids"])  # אחים נפרדים
        self.assertEqual(leaves[1]["ids"][:2], leaves[2]["ids"][:2])
        self.assertEqual(leaves[3]["depth"], 2)

    def test_match_rule_longest_prefix(self):
        rules = [{"path": ["A"], "day": "weekday"},
                 {"path": ["A", "B"], "day": "fasts"},
                 {"path": ["C"], "day": "shabbat"}]
        self.assertEqual(bc.match_rule(rules, ["A", "B", "x"])["day"], "fasts")
        self.assertEqual(bc.match_rule(rules, ["A", "Bx"])["day"], "weekday")
        self.assertIsNone(bc.match_rule(rules, ["D", "x"]))
        self.assertIsNone(bc.match_rule([{"path": ["A "], "day": "x"}], ["A"]))

    def test_slugify_and_unique_key(self):
        self.assertEqual(bc.slugify("Mourner's Kaddish"), "mourners-kaddish")
        self.assertEqual(bc.slugify("Various Prayers & Segulot"),
                         "various-prayers-and-segulot")
        self.assertEqual(bc.slugify("Additional Prayers "), "additional-prayers")
        self.assertEqual(bc.slugify("The'Nasi' Readings"), "thenasi-readings")
        self.assertEqual(bc.slugify("!!!"), "node")
        taken = set()
        self.assertEqual([bc.unique_key("a", taken) for _ in range(3)],
                         ["a", "a-2", "a-3"])

    def test_has_text(self):
        self.assertFalse(bc.has_text(""))
        self.assertFalse(bc.has_text([]))
        self.assertFalse(bc.has_text(["", [" "]]))
        self.assertTrue(bc.has_text([[""], ["x"]]))

    def test_first_words_skips_instructions(self):
        text = ["<small>כשיעור משנתו יאמר</small> <b>מוֹדֶה</b> אֲנִי לְפָנֶיךָ,",
                "מֶלֶךְ חַי וְקַיָּם, שֶׁהֶחֱזַרְתָּ"]
        self.assertEqual(bc.first_words(text), "מוֹדֶה אֲנִי לְפָנֶיךָ מֶלֶךְ חַי")
        self.assertEqual(bc.first_words(text, n=2), "מוֹדֶה אֲנִי")

    def test_first_words_brackets_parens_taamim(self):
        text = ["(תהלים קמה) [אמן] אַ֭שְׁרֵי יוֹשְׁבֵ֣י (וְ) בֵיתֶ֑ךָ"]
        self.assertEqual(bc.first_words(text), "אַשְׁרֵי יוֹשְׁבֵי וְ בֵיתֶךָ")

    def test_first_words_spoken_divine_name_and_vocalized_small(self):
        self.assertEqual(bc.first_words(["בָּרוּךְ אַתָּה ה' לַה' ג\"פ"]),
                         "בָּרוּךְ אַתָּה ה' לַה'")
        self.assertEqual(bc.first_words(["<small>בָּרוּךְ שֵׁם</small> כְּבוֹד"]),
                         "בָּרוּךְ שֵׁם כְּבוֹד")
        self.assertEqual(bc.first_words(["<b>שליח ציבור:</b>"]), "")

    def test_choose_version(self):
        pol = {"weekday": ["m", "d"], "*": ["d", "m"]}
        self.assertEqual(bc.choose_version(pol, "weekday", ["d", "m"]), ("m", ["d"]))
        self.assertEqual(bc.choose_version(pol, "shabbat", ["d", "m"]), ("d", ["m"]))
        self.assertEqual(bc.choose_version(pol, "shabbat", ["m"]), ("m", []))
        self.assertEqual(bc.choose_version(pol, "weekday", []), (None, []))

    def _leaves(self, rules):
        leaves = bc.schema_leaves(SYNTH_SCHEMA, "Fake Siddur")
        for lf in leaves:
            r = bc.match_rule(rules, lf["path"])
            lf["day"], lf["strip"] = r["day"], r.get("strip", 0)
            lf["leaf"] = {"ref": lf["ref"], "v": "v1"}
        return leaves

    DAYS = [{"key": "weekday", "title": "Weekday", "heTitle": "ימי חול"},
            {"key": "shabbat", "title": "Shabbat", "heTitle": "שבת"},
            {"key": "general", "title": "General", "heTitle": "שונות"}]

    def test_build_tree(self):
        rules = [{"path": ["Weekday"], "day": "weekday", "strip": 1},
                 {"path": ["Extra "], "day": "general"},
                 {"path": ["Havdalah"], "day": "shabbat"}]
        days = bc.build_tree(self._leaves(rules), self.DAYS)
        self.assertEqual([d["key"] for d in days], ["weekday", "shabbat", "general"])
        paths = ["/".join(p) for p, _ in walk(days)]
        self.assertEqual(paths, [
            "weekday", "weekday/shacharit", "weekday/shacharit/ashrei",
            "weekday/shacharit/mourners-kaddish",
            "weekday/shacharit/mourners-kaddish-2",
            "shabbat", "shabbat/havdalah",
            "general", "general/extra", "general/extra/avot"])
        extra = days[2]["children"][0]
        self.assertEqual((extra["title"], extra["heTitle"]), ("Extra", "תוספות"))
        self.assertEqual(extra["children"][0]["ref"], "Fake Siddur, Extra , Avot")

    def test_build_tree_strip_too_deep(self):
        rules = [{"path": ["Havdalah"], "day": "shabbat", "strip": 1},
                 {"path": ["Weekday"], "day": "weekday"},
                 {"path": ["Extra "], "day": "general"}]
        with self.assertRaises(ValueError):
            bc.build_tree(self._leaves(rules), self.DAYS)

    def test_dump_catalog_roundtrip(self):
        text = bc.dump_catalog(SYNTH)
        self.assertEqual(json.loads(text), SYNTH)
        # כל עלה בשורה אחת
        self.assertTrue(any('"key": "ashrei"' in ln and '"ref"' in ln
                            for ln in text.splitlines()))


if __name__ == "__main__":
    unittest.main()
