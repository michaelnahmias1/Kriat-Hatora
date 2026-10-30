# -*- coding: utf-8 -*-
"""בדיקות לאוספים — מחזורים, סליחות, קינות והגדה (PLAN_TEFILA.md 4.4.1). בלי רשת.

1. הקטלוג האמיתי: כלל הכיסוי (כל אוסף קיים בעדות המזרח וגם באשכנז או בספרד),
   רישיון פתוח לכל עלה, ושורת מקור ורישיון לכל עלה זמין — גם בסידור.
2. src/siddur/wikisource.py — המרת HTML של ויקיטקסט לפסקאות, על תשובה אמיתית
   שהוקלטה (tests/fixtures/siddur/ws_yk_kol_nidrei.json, ‏29.10.2026) ועל HTML
   סינתטי קטן (מסומן).
3. src/siddur/sources.py — שורת המקור, איחוד שורות של מהדורה "לינארית".
4. api/siddur.py — עלה מוויקיטקסט, עלה של פרק (סליחות) ועלה לינארי (מחזור מצודה
   ליום כיפור) — על תשובות אמיתיות שהוקלטו.
5. הפונקציות הטהורות החדשות של tools/build_siddur_catalog.py (סינתטי).

הרצה:  python3 -m unittest discover -s tests -v
"""

import copy
import importlib.util
import json
import re
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "siddur"

_SPEC = importlib.util.spec_from_file_location("api_siddur_coll",
                                               ROOT / "api" / "siddur.py")
api = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(api)

from siddur import load_catalog, markup, sources, wikisource as ws  # noqa: E402
from siddur.catalog import is_leaf  # noqa: E402

_BSPEC = importlib.util.spec_from_file_location(
    "build_siddur_catalog_coll", ROOT / "tools" / "build_siddur_catalog.py")
bc = importlib.util.module_from_spec(_BSPEC)
_BSPEC.loader.exec_module(bc)

OVERRIDES = json.loads((ROOT / "data" / "siddur" / "overrides.json")
                       .read_text(encoding="utf-8"))
ALLOWED = {"CC0", "Public Domain", "CC-BY", "CC-BY-SA"}
EXPECTED_COLLECTIONS = {"selichot", "rosh-hashanah", "yom-kippur", "tisha-bav",
                        "haggadah"}


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def walk(nodes, keys=()):
    for n in nodes:
        p = keys + (n["key"],)
        yield p, n
        if "children" in n:
            yield from walk(n["children"], p)


def collection_nodes(cat):
    """[(נוסח, אוסף, נתיב)] — כל הצמתים עם "collection" בקטלוג."""
    out = []
    for nus in cat.nusachim:
        for p, n in walk(nus["children"], (nus["key"],)):
            if n.get("collection"):
                out.append((nus["key"], n["collection"], "/".join(p)))
    return out


# =============================================================================
# 1. הקטלוג האמיתי
# =============================================================================

class RealCatalogCollectionsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cat = load_catalog()
        cls.coll = collection_nodes(cls.cat)

    def test_expected_collections_present(self):
        self.assertEqual({c for _, c, _ in self.coll}, EXPECTED_COLLECTIONS)
        self.assertEqual({c["key"] for c in self.cat.data["collections"]},
                         EXPECTED_COLLECTIONS)

    def test_coverage_rule(self):
        """כלל הכיסוי של בעל הפרויקט (29.10.2026): כל אוסף בקטלוג קיים (עם עלה
        זמין) בעדות המזרח, וגם באשכנז או בספרד."""
        rule = self.cat.data["coverage_rule"]
        self.assertEqual(rule, {"all_of": ["edot-hamizrach"],
                                "any_of": ["ashkenaz", "sefard"]})
        have = bc.collections_by_nusach(self.cat.nusachim)
        self.assertEqual(set(have), EXPECTED_COLLECTIONS)
        for coll, nus in have.items():
            with self.subTest(collection=coll):
                self.assertIn("edot-hamizrach", nus)
                self.assertTrue({"ashkenaz", "sefard"} & set(nus), nus)
        self.assertEqual(bc.check_coverage(self.cat.nusachim, rule), [])

    def test_collection_under_its_day_type(self):
        days = {c["key"]: c["day"] for c in self.cat.data["collections"]}
        for _, coll, path in self.coll:
            self.assertEqual(path.split("/")[1], days[coll], path)

    def test_every_version_open_license(self):
        for nus in self.cat.nusachim:
            for vid, v in nus["versions"].items():
                with self.subTest(nusach=nus["key"], version=vid):
                    self.assertIn(v["license"], ALLOWED)

    def test_every_available_leaf_has_attribution(self):
        """כל עלה זמין — בסידור ובאוספים — יש לו שורת מקור: מקור, קישור,
        מהדורה ורישיון פתוח."""
        n = 0
        for path, leaf in self.cat.leaves(""):
            if not leaf.get("v"):
                continue
            a = self.cat.attribution(path)
            n += 1
            with self.subTest(path=path):
                self.assertIn(a["source"], ("Sefaria", "ויקיטקסט"))
                self.assertTrue(a["source_url"].startswith("https://"))
                self.assertTrue(a["edition"])
                self.assertIn(a["license"], ALLOWED)
                if a["license"] == "CC-BY-SA" or a["source"] == "ויקיטקסט":
                    # שיתוף זהה — מקור + רישיון + קישור, ובוויקיטקסט גם התורמים
                    self.assertTrue(a.get("origin") or a.get("license_url"))
        self.assertGreater(n, 1000)

    def test_wikisource_leaves(self):
        ws_leaves = [(p, lf) for p, lf in self.cat.leaves("") if lf.get("ws")]
        self.assertGreater(len(ws_leaves), 50)
        for p, lf in ws_leaves:
            with self.subTest(path=p):
                self.assertTrue(p.startswith("edot-hamizrach/"))
                w = lf["ws"]
                self.assertTrue(w["page"].startswith("סידור (מהדורת מרדכי שליח ציבור)/"))
                self.assertIsInstance(w["rev"], int)
                self.assertTrue(w["section"].isdigit())
                self.assertTrue(w["heading"] and w["anchor"])
                src = self.cat.source(p)
                self.assertEqual(src["source"], "wikisource")
                self.assertEqual(src["license"], "CC-BY-SA")
                a = self.cat.attribution(p)
                self.assertEqual(a["license_url"], ws.LICENSE_URL)
                self.assertIn(f"oldid={w['rev']}", a["source_url"])
                self.assertIn("action=history", a["history_url"])

    def test_collection_leaves_carry_own_index(self):
        for nus, coll, path in self.coll:
            for p, lf in self.cat.leaves(path):
                if not lf.get("v"):
                    continue
                src = self.cat.source(p)
                if src["source"] == "sefaria":
                    with self.subTest(path=p):
                        self.assertTrue(lf["ref"].startswith(src["index"] + ",")
                                        or lf["ref"] == src["index"],  # ספר פשוט
                                        (lf["ref"], src["index"]))

    def test_chapter_leaves_for_selichot_and_kinot(self):
        """סליחות וקינות (עומק 2 ב-Sefaria) — עלה לכל פרק, ‏ref "<יום> N"."""
        for base in ("ashkenaz/high-holidays/selichot/polin",
                     "ashkenaz/high-holidays/selichot/lita",
                     "ashkenaz/fasts/tisha-bav"):
            leaves = [lf for _, lf in self.cat.leaves(base)]
            self.assertGreater(len(leaves), 40, base)
            for lf in leaves:
                self.assertRegex(lf["ref"], r" \d+$")
                self.assertTrue(lf["heTitle"] and not re.search("[֑-ׇ]", lf["heTitle"]))

    def test_default_day_for_every_collection_leaf(self):
        """ברירת המחדל של "מה אומרים היום?" לכל עלה של כל אוסף בכל נוסח
        (באתר החי עד 30.10.2026: "יום חול רגיל" לכל עלי הימים הנוראים)."""
        from siddur import days
        want = {"rosh-hashanah": "rosh-hashana", "yom-kippur": "yom-kippur",
                "selichot": "weekday", "tisha-bav": "tisha-bav",
                "haggadah": "pesach"}
        # ערב החג / מוצאי החג — היום שבו אומרים אותם בפועל
        erev = {"rosh-hashanah": "weekday", "yom-kippur": "aseret-yemei-teshuva"}
        motzei = {"rosh-hashanah": "aseret-yemei-teshuva", "yom-kippur": "weekday"}
        seen = set()
        for nus, coll, path in self.coll:
            for p, _ in self.cat.leaves(path):
                with self.subTest(path=p):
                    got = days.leaf_day(self.cat, p.split("/"))
                    crumbs = " ".join(str(c) for c in self.cat.breadcrumb(p)) + " " + p
                    if re.search(r"motzei|מוצאי", crumbs) and coll in motzei:
                        self.assertEqual(got, motzei[coll])
                    elif re.search(r"erev|ערב(?![א-ת])", crumbs) and coll in erev:
                        self.assertEqual(got, erev[coll])
                    else:
                        self.assertEqual(got, want[coll])
                    seen.add((nus, coll))
        self.assertTrue({c for _, c in seen} >= set(want), seen)

    def test_kol_nidre_default_day_through_api(self):
        path = _find(self.cat, lambda lf: (lf.get("ws") or {}).get("heading") == "כל נדרי")
        payload, status, _ = api.respond(urllib.parse.urlencode({"path": path}))
        self.assertEqual(status, 200, payload.get("error"))
        self.assertEqual(payload["day"], {"key": "yom-kippur", "label": "יום כיפור",
                                          "auto": True})

    def test_sefard_haggadah_tagged(self):
        node = self.cat.node("sefard/festivals/pesach-haggadah")
        self.assertEqual(node["collection"], "haggadah")

    def test_yom_kippur_ashkenaz_uses_open_linear_edition(self):
        """מחזור מצודה ליום כיפור: מהדורת הפסקאות מסומנת "unknown" ב-Sefaria —
        משתמשים במהדורה הלינארית (CC-BY) ומאחדים שורות לפסקאות."""
        src = self.cat.source("ashkenaz/high-holidays/yom-kippur/kol-nidrei")
        self.assertEqual(src["index"], "Machzor Yom Kippur Ashkenaz Linear")
        self.assertEqual(src["license"], "CC-BY")
        self.assertTrue(src["lines"])


# =============================================================================
# 2. ויקיטקסט ⇐ פסקאות
# =============================================================================

class WikisourceHtmlTest(unittest.TestCase):

    def test_recorded_kol_nidrei_section(self):
        paras = ws.section_paragraphs(fixture("ws_yk_kol_nidrei"), "כל נדרי")
        self.assertGreater(len(paras), 10)
        text = " ".join(paras)
        self.assertNotIn("יאהדונהי", text)          # כוונה — לא נאמרת
        self.assertNotIn("כל נדרי</h2>", text)      # הכותרת אינה טקסט
        parts = markup.classify_paragraph(paras[0])
        self.assertEqual(parts[0], ("instruction", "פותחים ההיכל ואומרים"))
        self.assertEqual(parts[1][0], "spoken")
        self.assertTrue(parts[1][1].startswith("כֹּהֲנֶ֥יךָ"))
        kol = next(p for p in paras if "נִדְרֵי." in p)
        kinds = markup.classify_paragraph(kol)
        self.assertEqual(kinds[0][0], "spoken")
        self.assertTrue(kinds[0][1].startswith("כָּל נִדְרֵי."))
        self.assertEqual(kinds[-1], ("instruction", "שלש פעמים"))
        # רווח לפני פיסוק שנשאר אחרי הסרת הכוונה
        self.assertNotIn("יְהֹוָה ,", text)

    def test_heading_mismatch_and_api_error(self):
        with self.assertRaises(ws.WikisourceError):
            ws.section_paragraphs(fixture("ws_yk_kol_nidrei"), "קבלת שבת")
        with self.assertRaises(ws.WikisourceError):
            ws.section_paragraphs({"error": {"code": "nosuchrevid", "info": "x"}})
        with self.assertRaises(ws.WikisourceError):
            ws.section_paragraphs({"parse": {}})

    def test_stops_at_subsection_and_small_spans(self):  # סינתטי
        html = ('<div class="mw-parser-output"><div class="mw-heading mw-heading2">'
                '<h2 id="x">תפילת ערבית<span class="mw-editsection">עריכה</span></h2></div>'
                '<p><span style="font-size:83%;"><span style="font-size:83%;">החזן אומר'
                '</span></span><br/><b>בָּרְכוּ</b> אֶת יְהֹוָה<sup class="reference">[1]</sup>'
                '<br/>\n<br/>שורה שניה מְנֻקֶּדֶת</p>'
                '<div class="mw-heading mw-heading3"><h3>קריאת שמע</h3></div>'
                '<p>שְׁמַע יִשְׂרָאֵל</p></div>')
        head, paras = ws.html_to_paragraphs(html)
        self.assertEqual(head, "תפילת ערבית")
        self.assertEqual(paras, ["<small><small>החזן אומר</small></small><br>"
                                 "<b>בָּרְכוּ</b> אֶת יְהֹוָה",
                                 "שורה שניה מְנֻקֶּדֶת"])

    def test_same_heading(self):
        self.assertTrue(ws.same_heading("הַגָּדָה שֶׁל פֶּסַח", "הגדה של פסח"))
        self.assertTrue(ws.same_heading('תפילת החיד״א', 'תפילת החיד"א'))
        self.assertFalse(ws.same_heading("כל נדרי", "כל נדרים"))

    def test_urls(self):
        u = ws.page_url("סידור (מהדורת מרדכי שליח ציבור)/סדר יום הכיפורים",
                        2971772, "כל_נדרי")
        self.assertTrue(u.startswith("https://he.wikisource.org/w/index.php?title="))
        self.assertIn("oldid=2971772", u)
        self.assertIn("#", u)
        self.assertEqual(ws.parse_params(2971772, 14)["section"], "14")
        self.assertEqual(ws.parse_params(2971772, 14)["oldid"], "2971772")


class WikisourceSnapshotTest(unittest.TestCase):
    """הצילום בגיט (data/siddur/wikisource) — מה שה-API מגיש."""

    @classmethod
    def setUpClass(cls):
        cls.cat = load_catalog()
        cls.ws_leaves = [lf["ws"] for _, lf in cls.cat.leaves("") if lf.get("ws")]

    def test_snapshot_per_revision_with_attribution(self):
        revs = {w["rev"] for w in self.ws_leaves}
        files = {p.name for p in ws.SNAPSHOT_DIR.glob("*.json.gz")}
        self.assertEqual(files, {f"{r}.json.gz" for r in revs})  # בלי צילומים יתומים
        for r in revs:
            snap = ws.load_snapshot(r)
            with self.subTest(rev=r):
                self.assertEqual(snap["rev"], r)
                self.assertEqual(snap["license"], "CC-BY-SA")
                self.assertEqual(snap["license_url"], ws.LICENSE_URL)
                self.assertIn(f"oldid={r}", snap["page_url"])
                self.assertIn("action=history", snap["history_url"])
                self.assertRegex(snap["fetched"], r"^\d{4}-\d{2}-\d{2}$")

    def test_every_leaf_section_in_snapshot(self):
        for w in self.ws_leaves:
            sec = ws.load_snapshot(w["rev"])["sections"][w["section"]]
            self.assertTrue(ws.same_heading(sec["heading"], w["heading"]))
            self.assertTrue(markup.has_vocalized(sec["paragraphs"]))

    def test_deployed_with_function(self):
        """הצילום חייב להגיע לפונקציה ב-Vercel: לא ב-.vercelignore ולא ב-excludeFiles."""
        ignore = (ROOT / ".vercelignore").read_text(encoding="utf-8").split()
        self.assertFalse(any(x.rstrip("/") in ("data", "data/siddur", "data/siddur/wikisource")
                             or x.startswith("data/siddur/wikisource") for x in ignore), ignore)
        cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        excl = cfg["functions"]["api/siddur.py"].get("excludeFiles", "")
        self.assertNotIn("data", excl)
        total = sum(p.stat().st_size for p in ws.SNAPSHOT_DIR.glob("*.json.gz"))
        self.assertLess(total, 2 * 1024 * 1024)

    def test_write_load_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            snap = ws.make_snapshot("דף/בדיקה", 5, "2026-10-29", {"2": ("כותרת", ["א", "ב"])})
            p1 = ws.write_snapshot(snap, tmp)
            b1 = p1.read_bytes()
            ws.write_snapshot(snap, tmp)
            self.assertEqual(p1.read_bytes(), b1)  # דטרמיניסטי — diff נקי בגיט
            got = ws.snapshot_paragraphs({"page": "דף/בדיקה", "rev": 5, "section": "2",
                                          "heading": "כותרת"}, tmp)
            self.assertEqual(got, ["א", "ב"])
            with self.assertRaises(ws.WikisourceError):
                ws.snapshot_paragraphs({"page": "דף אחר", "rev": 5, "section": "2"}, tmp)


# =============================================================================
# 3. מקורות: שורת מקור, מהדורה לינארית
# =============================================================================

class SourcesTest(unittest.TestCase):

    def test_merge_lines_recorded_kol_nidrei(self):
        lines = fixture("yk_linear_kol_nidrei_metsudah")["versions"][0]["text"]
        self.assertEqual(len(lines), 55)
        paras = sources.merge_lines(lines)
        self.assertLess(len(paras), 15)
        self.assertEqual(paras[0], lines[1] + " " + lines[2])  # "אוֹר זָרוּעַ… שִׂמְחָה:"
        self.assertTrue(paras[0].endswith(":"))
        self.assertTrue(lines[12].startswith("<b>"))   # "<b>כָּל </b>נִדְרֵי"
        kol = next(p for p in paras if p.startswith(lines[12]))
        self.assertIn(" " + lines[13] + " " + lines[14], kol)  # השורות אוחדו

    def test_merge_lines_rules(self):  # סינתטי
        self.assertEqual(sources.merge_lines(["א", "ב:", "ג", "", "<b>כותרת</b>", "ד", ""]),
                         ["א ב:", "ג", "<b>כותרת</b>", "ד"])

    def test_attribution_sefaria_origin(self):
        src = {"source": "sefaria", "ref": "Selichot Nusach Polin, First Day 3",
               "version": "Selichot Nusach Polin -- Wikisource", "license": "CC-BY-SA"}
        ver = {"title": "Selichot Nusach Polin -- Wikisource", "license": "CC-BY-SA",
               "heTitle": "סליחות כמנהג פולין",
               "origin": {"name": "ויקיטקסט", "url": "https://he.wikisource.org/wiki/x"}}
        a = sources.attribution(src, ver)
        self.assertEqual(a["source"], "Sefaria")
        self.assertEqual(a["edition"], "סליחות כמנהג פולין")
        self.assertEqual(a["origin"]["name"], "ויקיטקסט")
        self.assertTrue(a["source_url"].startswith(
            "https://www.sefaria.org/Selichot_Nusach_Polin,_First_Day_3?"))
        self.assertIn("ven=Selichot", a["source_url"])

    def test_attribution_public_domain_link(self):
        a = sources.attribution({"source": "sefaria", "ref": "X, Y", "version": "V"},
                                {"title": "V", "license": "Public Domain"})
        self.assertIn("publicdomain", a["license_url"])


# =============================================================================
# 4. ה-API על עלים של אוספים (תשובות אמיתיות שהוקלטו)
# =============================================================================

def _find(cat, pred):
    return next(p for p, lf in cat.leaves("") if pred(lf))


class FakeSources:
    """מחליף את _get_json: ויקיטקסט ⇐ הסעיף שהוקלט; Sefaria ⇐ לפי ref."""

    def __init__(self, sefaria=None, ws_data=None, ws_exc=None):
        self.sefaria = sefaria or {}
        self.ws_data, self.ws_exc = ws_data, ws_exc
        self.calls = []

    def __call__(self, url, params=None):
        self.calls.append((url, params))
        if url == ws.API_URL:
            if self.ws_exc:
                raise self.ws_exc
            return copy.deepcopy(self.ws_data)
        prefix = api.SEFARIA_BASE + "/api/v3/texts/"
        assert url.startswith(prefix), url
        ref = urllib.parse.unquote(url[len(prefix):])
        return copy.deepcopy(fixture(self.sefaria[ref]))


class ApiCollectionsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cat = load_catalog()

    def run_api(self, fake, **params):
        with mock.patch.object(api, "_get_json", side_effect=fake):
            return api.respond(urllib.parse.urlencode(params))

    def test_wikisource_leaf_from_snapshot_without_network(self):
        """עלה מוויקיטקסט מוגש מהצילום שבגיט — אף בקשת רשת — והפסקאות זהות
        לתשובה האמיתית של ה-API של ויקיטקסט לאותו סעיף (הוקלטה 29.10.2026)."""
        path = _find(self.cat, lambda lf: (lf.get("ws") or {}).get("heading") == "כל נדרי")
        fake = FakeSources(ws_exc=AssertionError("אסור לפנות לרשת"))
        payload, status, headers = self.run_api(fake, path=path)
        self.assertEqual(status, 200, payload.get("error"))
        self.assertEqual(fake.calls, [])
        self.assertIn("s-maxage", headers["Cache-Control"])
        live = ws.section_paragraphs(fixture("ws_yk_kol_nidrei"), "כל נדרי")
        self.assertEqual(ws.snapshot_paragraphs(self.cat.leaf(path)["ws"]), live)
        self.assertEqual(payload["range"]["total"], len(live))
        self.assertEqual(payload["license"], "CC-BY-SA")
        a = payload["attribution"]
        self.assertEqual(a["source"], "ויקיטקסט")
        self.assertEqual(a["license_name"], "CC BY-SA 4.0")
        self.assertIn("action=history", a["history_url"])
        self.assertEqual(payload["source_url"], a["source_url"])
        kinds = {u["kind"] for u in payload["units"]}
        self.assertTrue({"paragraph", "instruction"} <= kinds, kinds)
        self.assertTrue(payload["segments"])
        self.assertFalse(any("יאהדונהי" in u["text"] for u in payload["units"]))

    def test_kol_nidre_mixed_paragraph_split(self):
        """כל נדרי (עדות המזרח): הארמית בלי טעמים והפסוק "וְנִסְלַ֗ח…" המוטעם
        באותה פסקה ⇐ שתי יחידות באותה תווית — הארמית לפי פיסוק, הפסוק לפי
        טעמים (עד 30.10.2026 הפסקה כולה נחתכה לפי טעמים: "נַחֲרִים. וְדִי")."""
        path = _find(self.cat, lambda lf: (lf.get("ws") or {}).get("heading") == "כל נדרי")
        payload, status, _ = self.run_api(FakeSources(), path=path)
        n = next(p["n"] for p in payload["paragraphs"]
                 if p["first_words"].startswith("כָּל נִדְרֵי"))
        payload, status, _ = self.run_api(FakeSources(), path=path, **{"from": n, "to": n})
        self.assertEqual(status, 200, payload.get("error"))
        said = [u for u in payload["units"] if u["kind"] == "paragraph"]
        self.assertEqual([(u["chunk"], u.get("cont", False)) for u in said],
                         [("punct", False), ("taamim", True)])
        self.assertEqual({u["label"] for u in said}, {f"כל נדרי · {n}"})
        self.assertTrue(said[0]["text"].startswith("כָּל נִדְרֵי."))
        self.assertTrue(said[1]["text"].startswith("וְנִסְלַ֗ח"))
        displays = [s["display"] for s in payload["segments"]]
        self.assertNotIn("נַחֲרִים. וְדִי", displays)
        self.assertNotIn("וְדִי נִנְדַּר. וְדִי", displays)
        self.assertEqual(displays[-1], "כִּ֥י לְכׇל־הָעָ֖ם בִּשְׁגָגָֽה׃")
        self.assertEqual(payload["n_units"], len(payload["units"]))

    def test_every_wikisource_leaf_served_from_snapshot(self):
        fake = FakeSources(ws_exc=AssertionError("אסור לפנות לרשת"))
        paths = [p for p, lf in self.cat.leaves("") if lf.get("ws")]
        for p in paths:
            with self.subTest(path=p):
                w = self.cat.leaf(p)["ws"]
                self.assertTrue(ws.snapshot_paragraphs(w))
        # מדגם דרך ה-API (כולם — איטי מדי בלי צורך)
        for p in paths[::10]:
            payload, status, _ = self.run_api(fake, path=p)
            self.assertIn(status, (200, 413), (p, payload.get("error")))
        self.assertEqual(fake.calls, [])

    def test_missing_or_mismatched_snapshot_is_hebrew_error(self):
        import tempfile
        path = _find(self.cat, lambda lf: (lf.get("ws") or {}).get("heading") == "כל נדרי")
        w = self.cat.leaf(path)["ws"]
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(ws, "SNAPSHOT_DIR", Path(tmp)):
                payload, status, headers = self.run_api(FakeSources(), path=path)
                self.assertEqual(status, 502)
                self.assertIn("צילום", payload["error"])
                self.assertEqual(headers["Cache-Control"], "no-store")
                # צילום עם כותרת אחרת באותו סעיף ⇐ שגיאה, לא טקסט אחר
                ws.write_snapshot(ws.make_snapshot(
                    w["page"], w["rev"], "2026-10-29",
                    {w["section"]: ("קבלת שבת", ["שָׁלוֹם"])}), tmp)
                payload, status, _ = self.run_api(FakeSources(), path=path)
                self.assertEqual(status, 502)
                self.assertIn("צילום", payload["error"])

    def test_selichot_chapter_leaf(self):
        ref = "Selichot Nusach Polin, First Day 3"
        path = _find(self.cat, lambda lf: lf.get("ref") == ref)
        fake = FakeSources(sefaria={ref: "selichot_polin_first_day_3"})
        payload, status, _ = self.run_api(fake, path=path)
        self.assertEqual(status, 200, payload.get("error"))
        self.assertEqual(payload["range"]["total"], 22)
        self.assertEqual(payload["license"], "CC-BY-SA")
        self.assertEqual(payload["attribution"]["origin"]["name"], "ויקיטקסט")
        self.assertEqual(payload["paragraphs"][0]["kind"], "instruction")  # "א. פתיחה…"

    def test_yom_kippur_linear_leaf_merged(self):
        path = "ashkenaz/high-holidays/yom-kippur/kol-nidrei"
        ref = self.cat.leaf(path)["ref"]
        fake = FakeSources(sefaria={ref: "yk_linear_kol_nidrei_metsudah"})
        payload, status, _ = self.run_api(fake, path=path)
        self.assertEqual(status, 200, payload.get("error"))
        self.assertLess(payload["range"]["total"], 15)   # 55 שורות ⇐ פסקאות
        self.assertEqual(payload["license"], "CC-BY")
        self.assertEqual(payload["attribution"]["source"], "Sefaria")

    def test_haggadah_daat_leaf(self):
        ref = "Pesach Haggadah, Kadesh"
        path = _find(self.cat, lambda lf: lf.get("ref") == ref)
        self.assertTrue(path.startswith("ashkenaz/festivals/haggadah/"))
        payload, status, _ = self.run_api(
            FakeSources(sefaria={ref: "haggadah_kadesh_daat"}), path=path)
        self.assertEqual(status, 200, payload.get("error"))
        self.assertEqual(payload["license"], "Public Domain")


# =============================================================================
# 5. הבונה — פונקציות טהורות (סינתטי)
# =============================================================================

class BuilderCollectionsTest(unittest.TestCase):

    def test_he_slug(self):
        self.assertEqual(bc.he_slug("כל נדרי"), "kl-ndry")
        self.assertEqual(bc.he_slug("הַגָּדָה שֶׁל פֶּסַח"), "hgdh-shl-psch")
        self.assertEqual(bc.he_slug("תפילת החיד״א"), "tpylt-hchyd-a")

    def test_chapter_title(self):
        paras = ['א. פתיחה. מיוסד על פי א"ב. חתום בנימין.',
                 "אֱלֹהֵינוּ וֵאלֹהֵי אֲבוֹתֵינוּ",
                 "אָדוֹן בִּינָה הֲגִיגֵנוּ. בְּךָ נִשְׁעָנִים"]
        self.assertEqual(bc.chapter_title(paras), "פתיחה: אדון בינה הגיגנו בך")
        self.assertEqual(bc.chapter_title(["שְׁמַע קוֹלֵנוּ"]), "שמע קולנו")
        self.assertEqual(bc.chapter_title(["הוראה בלבד"]), "")

    def test_chapter_leaves_skip_empty(self):
        out = bc.chapter_leaves("Kinnot X, Day", "v", [[], ["", ""], ["שְׁמַע קוֹלֵנוּ אָבִינוּ"]])
        self.assertEqual([(lf["key"], lf["ref"]) for lf in out], [("3", "Kinnot X, Day 3")])

    def test_ws_section_tree(self):
        secs = [{"number": n, "line": t} for n, t in
                [("1", "א"), ("1.1", "ב"), ("2", "ג"), ("2.1", "ד"), ("2.1.1", "ה"),
                 ("3", "ו"), ("13", "ז"), ("13.1", "ח")]]
        tree = bc.ws_section_tree(secs)
        self.assertEqual([n["s"]["line"] for n in tree], ["א", "ג", "ו", "ז"])
        self.assertEqual(tree[1]["children"][0]["children"][0]["s"]["line"], "ה")
        self.assertEqual([n["s"]["line"] for n in bc.ws_section_tree(secs, under="1")],
                         ["ב"])
        # "1" לא תופס את "13"
        self.assertEqual([n["s"]["line"] for n in bc.ws_section_tree(secs, include=["1"])],
                         ["א"])
        self.assertEqual([n["s"]["line"] for n in bc.ws_section_tree(secs, skip={"ג"})],
                         ["א", "ו", "ז"])

    def test_check_coverage(self):
        def nus(key, colls):
            return {"key": key, "children": [
                {"key": "d", "children": [
                    {"key": c, "collection": c,
                     "children": [{"key": "x", "v": "v"}]} for c in colls]}]}
        rule = {"all_of": ["edot-hamizrach"], "any_of": ["ashkenaz", "sefard"]}
        ok = [nus("edot-hamizrach", ["a", "b"]), nus("sefard", ["a"]),
              nus("ashkenaz", ["b"])]
        self.assertEqual(bc.check_coverage(ok, rule), [])
        only_ash = [nus("edot-hamizrach", []), nus("ashkenaz", ["a"])]
        self.assertEqual(len(bc.check_coverage(only_ash, rule)), 1)
        only_edot = [nus("edot-hamizrach", ["a"]), nus("ashkenaz", [])]
        self.assertEqual(len(bc.check_coverage(only_edot, rule)), 1)
        # אוסף בלי אף עלה זמין לא נחשב
        empty = [nus("edot-hamizrach", ["a"]), nus("ashkenaz", ["a"])]
        empty[1]["children"][0]["children"][0]["children"][0]["v"] = None
        self.assertEqual(len(bc.check_coverage(empty, rule)), 1)

    def test_attach_collections_keeps_day_order(self):
        dts = OVERRIDES["day_types"]
        nusach = {"key": "n", "children": [{"key": "weekday", "children": []},
                                           {"key": "festivals", "children": []}]}
        bc.attach_collections(nusach, [("high-holidays", {"key": "rh"}),
                                       ("festivals", {"key": "hg"})], dts)
        self.assertEqual([d["key"] for d in nusach["children"]],
                         ["weekday", "high-holidays", "festivals"])
        self.assertEqual(nusach["children"][1]["heTitle"], "ימים נוראים")
        with self.assertRaises(bc.BuildError):
            bc.attach_collections(nusach, [("festivals", {"key": "hg"})], dts)

    def test_overrides_collections_open_licenses_only(self):
        """הגדרות האוספים: רק מקורות שנבדקו ברישיון פתוח, וכל אוסף מוגדר גם
        בעדות המזרח וגם באשכנז/ספרד (כלל הכיסוי, כבר בקלט)."""
        defined = {c["key"] for c in OVERRIDES["collections"]["list"]}
        by_nus = {n["key"]: {c["collection"] for c in n.get("collections", [])}
                  for n in OVERRIDES["nusachim"]}
        # ההגדה בספרד — צומת של הסידור עצמו (כלל עם "collection")
        for n in OVERRIDES["nusachim"]:
            by_nus[n["key"]] |= {r["collection"] for r in n["rules"]
                                 if r.get("collection")}
        for coll in defined:
            self.assertIn(coll, by_nus["edot-hamizrach"])
            self.assertTrue(coll in by_nus["ashkenaz"] or coll in by_nus["sefard"])
        for n in OVERRIDES["nusachim"]:
            for vid, v in n.get("collection_versions", {}).items():
                self.assertIn(v["source"], ("sefaria", "wikisource"))
                # אף מהדורה "unknown" של Sefaria (שליח ציבור/Shaliehsaboo, קורן)
                self.assertNotIn("Shaliehsaboo", v["title"])
                self.assertNotIn("Koren", v["title"])


if __name__ == "__main__":
    unittest.main()
