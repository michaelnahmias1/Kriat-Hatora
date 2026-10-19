# -*- coding: utf-8 -*-
"""בדיקות ל-tools/survey_siddur.py — פונקציות הניתוח בלבד, בלי רשת.

⚠️ כל ה-fixtures כאן **סינתטיים** ונכתבו ביד לצורך הבדיקה: עץ תוכן מזויף,
schema מזויף וטקסטים מזויפים. הם לא משקפים את המבנה האמיתי של Sefaria
ואין להסיק מהם דבר על הסידור ב-Sefaria — הממצאים האמיתיים ב-docs/siddur_survey.md.
"""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "survey_siddur",
    Path(__file__).resolve().parent.parent / "tools" / "survey_siddur.py")
sv = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sv)

# --- fixtures סינתטיים -------------------------------------------------------

SYNTH_TOC = [  # סינתטי
    {"category": "Tanakh", "heCategory": "תנ״ך", "contents": [
        {"title": "Fake Genesis", "heTitle": "בראשית מזויף",
         "categories": ["Tanakh"]}]},
    {"category": "Liturgy", "heCategory": "תפילה", "contents": [
        {"category": "Siddur", "heCategory": "סידור", "contents": [
            {"title": "Fake Siddur Ashkenaz", "heTitle": "סידור אשכנז מזויף",
             "categories": ["Liturgy", "Siddur"]},
            {"title": "Fake Siddur Edot HaMizrach", "heTitle": "סידור עדות המזרח מזויף",
             "categories": ["Liturgy", "Siddur"]}]},
        {"title": "Fake Machzor", "heTitle": "מחזור מזויף",
         "categories": ["Liturgy"]}]},
    {"category": "Other", "contents": [
        {"title": "Fake Pesach Haggadah", "heTitle": "הגדה מזויפת"}]},
]

SYNTH_SCHEMA = {  # סינתטי: שורש ← שחרית (← default + ברכות) ← מנחה
    "nodeType": "SchemaNode",
    "titles": [{"text": "Fake Siddur", "lang": "en", "primary": True},
               {"text": "סידור מזויף", "lang": "he", "primary": True}],
    "nodes": [
        {"nodeType": "SchemaNode",
         "titles": [{"text": "Shacharit", "lang": "en", "primary": True},
                    {"text": "Shaharit", "lang": "en"},
                    {"text": "שחרית", "lang": "he", "primary": True}],
         "nodes": [
             {"nodeType": "JaggedArrayNode", "key": "default", "default": True,
              "depth": 1, "sectionNames": ["Paragraph"],
              "titles": []},
             {"nodeType": "JaggedArrayNode", "depth": 1,
              "sectionNames": ["Paragraph"],
              "title": "Blessings", "heTitle": "ברכות"}]},
        {"nodeType": "JaggedArrayNode", "depth": 2,
         "sectionNames": ["Section", "Line"],
         "titles": [{"text": "Mincha", "lang": "en", "primary": True}]},
    ],
}

# טקסטים סינתטיים — מנוקדים בכוונה עם צורות שם ה׳ שונות והוראות
SYNTH_TEXTS = [
    "<small>בשבת אומרים:</small> בָּרוּךְ אַתָּה יְיָ אֱלֹהֵינוּ",
    "וַיהֹוָה אָמַר (בעשי״ת: הַמֶּלֶךְ) בָּרוּךְ ה' לְעוֹלָם.",
    "לַייָ הָאָרֶץ וּמְלוֹאָהּ, ה׳ הוּא הָאֱלֹהִים׃",
    "<b>קׇדְשֵׁנוּ</b> plain latin words",
]


class TestDiscovery(unittest.TestCase):
    def test_walk_toc_finds_liturgy_by_keyword(self):
        titles = [e["title"] for e in sv.walk_toc(SYNTH_TOC)]
        self.assertIn("Fake Siddur Ashkenaz", titles)
        self.assertIn("Fake Siddur Edot HaMizrach", titles)
        self.assertIn("Fake Machzor", titles)
        self.assertIn("Fake Pesach Haggadah", titles)  # לפי הכותר בלבד
        self.assertNotIn("Fake Genesis", titles)

    def test_walk_toc_category_path_used_when_missing(self):
        e = {x["title"]: x for x in sv.walk_toc(SYNTH_TOC)}
        self.assertEqual(e["Fake Pesach Haggadah"]["categories"], ["Other"])
        self.assertEqual(e["Fake Machzor"]["categories"], ["Liturgy"])

    def test_walk_toc_tolerates_garbage(self):
        self.assertEqual(sv.walk_toc(None), [])
        self.assertEqual(sv.walk_toc({"weird": 1}), [])
        self.assertEqual(sv.walk_toc([1, "x", {"contents": "no"}]), [])

    def test_guess_nusach(self):
        self.assertEqual(sv.guess_nusach("Siddur Ashkenaz"), "אשכנז")
        self.assertEqual(sv.guess_nusach("Siddur Sefard"), "ספרד")
        self.assertEqual(sv.guess_nusach("Siddur Edot HaMizrach"),
                         "עדות המזרח / ספרדי")
        self.assertEqual(sv.guess_nusach("Sephardic Siddur"),
                         "עדות המזרח / ספרדי")
        self.assertEqual(sv.guess_nusach("X", "סידור תימן"), "תימן")
        self.assertEqual(sv.guess_nusach("Foo"), "לא מסווג")

    def test_guess_kind(self):
        self.assertEqual(sv.guess_kind("Machzor Rosh Hashana"), "מחזור")
        self.assertEqual(sv.guess_kind("Kinot for Tisha B'Av"), "קינות")
        self.assertEqual(sv.guess_kind("Foo", categories=["Liturgy", "Siddur"]),
                         "סידור")
        self.assertEqual(sv.guess_kind("Foo"), "אחר")


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.nodes = sv.walk_schema(SYNTH_SCHEMA, "Fake Siddur")

    def test_node_titles_both_formats(self):
        self.assertEqual(sv.node_titles(SYNTH_SCHEMA["nodes"][0]),
                         ("Shacharit", "שחרית"))
        self.assertEqual(sv.node_titles(SYNTH_SCHEMA["nodes"][0]["nodes"][1]),
                         ("Blessings", "ברכות"))

    def test_walk_order_depth_and_refs(self):
        refs = [(n["depth"], n["ref"], n["leaf"]) for n in self.nodes]
        self.assertEqual(refs, [
            (0, "Fake Siddur", False),
            (1, "Fake Siddur, Shacharit", False),
            (2, "Fake Siddur, Shacharit", True),           # default — בלי כותר
            (2, "Fake Siddur, Shacharit, Blessings", True),
            (1, "Fake Siddur, Mincha", True),
        ])

    def test_summary(self):
        s = sv.schema_summary(self.nodes)
        self.assertEqual(s["n_nodes"], 5)
        self.assertEqual(s["n_leaves"], 3)
        self.assertEqual(s["max_depth"], 2)
        self.assertEqual(s["leaf_text_depths"], {"1": 2, "2": 1})
        # default (בלי heTitle) ו-Mincha (בלי כותר עברי) חסרים
        self.assertEqual(s["missing_heTitle"], 2)
        self.assertEqual(s["example_leaf_ref"], "Fake Siddur, Shacharit")
        self.assertIn("Section / Line", s["sectionNames"])

    def test_simple_schema_is_single_leaf(self):
        nodes = sv.walk_schema({"depth": 2}, "Simple")
        self.assertEqual(len(nodes), 1)
        self.assertTrue(nodes[0]["leaf"])
        self.assertEqual(nodes[0]["ref"], "Simple")

    def test_pick_samples(self):
        self.assertEqual(sv.pick_samples(list(range(10)), 3), [0, 4, 9])
        self.assertEqual(sv.pick_samples([1, 2], 5), [1, 2])
        self.assertEqual(sv.pick_samples([], 3), [])
        self.assertEqual(sv.pick_samples([7, 8], 1), [7])


class TestTextAnalysis(unittest.TestCase):
    def test_god_name_forms(self):
        c = sv.classify_god_name
        self.assertEqual(c("יְיָ"), "יי")
        self.assertEqual(c("לַייָ"), "יי")
        self.assertEqual(c("וַיהֹוָה"), "יהוה")
        self.assertEqual(c("יְהֹוָה,"), "יהוה")
        self.assertEqual(c("ה'"), "ה׳ (קיצור)")
        self.assertEqual(c("ה׳"), "ה׳ (קיצור)")
        self.assertEqual(c("וְה׳"), "ה׳ (קיצור)")
        self.assertEqual(c("ידוד"), "ידוד")
        self.assertEqual(c("אֲדֹנָי"), "אדני")
        # לא שם ה׳
        self.assertEqual(c("הָאָרֶץ"), "")
        self.assertEqual(c("ה"), "")
        self.assertEqual(c("וַיְהִי"), "")

    def test_analyze_texts(self):
        a = sv.analyze_texts(SYNTH_TEXTS)
        self.assertEqual(a["n_strings"], 4)
        self.assertEqual(a["god_name_forms"], {"יי": 2, "ה׳ (קיצור)": 2, "יהוה": 1})
        self.assertEqual(a["small"]["count"], 1)
        self.assertEqual(a["small"]["examples"], ["בשבת אומרים:"])
        self.assertEqual(a["parentheses"]["examples"], ["בעשי״ת: הַמֶּלֶךְ"])
        self.assertEqual(a["html_tags"], {"small": 1, "b": 1})
        self.assertEqual(a["kamatz_katan"], 1)
        self.assertIn("בשבת", a["instruction_hints"])
        self.assertIn("בעשי״ת", a["instruction_hints"])
        self.assertIn("סוף פסוק (׃)", a["punctuation"])
        self.assertIn("גרש (׳)", a["punctuation"])
        # ניקוד: כל המילים העבריות מנוקדות חוץ מ"ה'" "ה׳" ו"בשבת אומרים:" ו-"בעשי״ת:"
        self.assertGreater(a["niqqud_frac"], 0.6)
        self.assertLess(a["niqqud_frac"], 1.0)
        self.assertEqual(a["taamim_frac"], 0.0)

    def test_taamim_detected(self):
        a = sv.analyze_texts(["בְּרֵאשִׁ֖ית בָּרָ֣א"])  # סינתטי עם טעמים
        self.assertEqual(a["taamim_frac"], 1.0)

    def test_text_shape(self):
        sh = sv.text_shape([["א", "ב"], ["", "ג"]])
        self.assertEqual(sh["nesting"], 2)
        self.assertEqual(sh["n_strings"], 4)
        self.assertEqual(sh["n_empty"], 1)
        self.assertEqual(sh["top_len"], 2)
        self.assertEqual(sv.text_shape("x")["nesting"], 0)

    def test_merge_analyses_weights_by_words(self):
        a1 = sv.analyze_texts(["בָּרוּךְ אַתָּה"])     # 100% ניקוד
        a2 = sv.analyze_texts(["ברוך אתה יי אלהינו"])  # 0% ניקוד
        m = sv.merge_analyses([a1, a2])
        self.assertEqual(m["n_hebrew_words"], 6)
        self.assertAlmostEqual(m["niqqud_frac"], 2 / 6, places=3)
        self.assertEqual(m["god_name_forms"], {"יי": 1})

    def test_versions_and_v3_description(self):
        vs = sv.summarize_versions([
            {"versionTitle": "Synthetic Ed.", "language": "he",
             "license": "CC0", "extra": 1}, "junk"])
        self.assertEqual(vs, [{"versionTitle": "Synthetic Ed.", "language": "he",
                               "license": "CC0", "versionSource": "",
                               "status": ""}])
        self.assertEqual(sv.summarize_versions({"error": "x"}), [])
        d = sv.describe_v3_response(200, {
            "ref": "Fake, A", "versions": [{"versionTitle": "V", "text": ["a", "b"]}]})
        self.assertEqual(d["shape"]["n_strings"], 2)
        self.assertEqual(d["versionTitle"], "V")
        e = sv.describe_v3_response(400, {"error": "synthetic error"})
        self.assertEqual(e["error"], "synthetic error")
        self.assertEqual(sv.describe_v3_response(0, None)["body_type"], "NoneType")


class FakeClient:
    """לקוח מזויף: מחזיר תשובות סינתטיות לפי הנתיב, בלי רשת."""

    base = "https://synthetic.invalid"

    def __init__(self):
        self.errors = []
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(path)
        if path == sv.ENDPOINTS["toc"]:
            return 200, SYNTH_TOC
        if path.startswith("/api/name/"):
            return 200, {"completions": [], "is_book": False}
        if path.startswith("/api/v2/raw/index/"):
            return 200, {"title": "x", "schema": SYNTH_SCHEMA}
        if path.startswith("/api/texts/versions/"):
            return 200, [{"versionTitle": "Synthetic Ed.", "language": "he",
                          "license": "CC0"}]
        if path.startswith("/api/v3/texts/"):
            if "-" in path:  # טווח — "לא נתמך" בעולם הסינתטי
                return 400, {"error": "synthetic: ranges unsupported"}
            return 200, {"ref": "x", "versions": [
                {"versionTitle": "Synthetic Ed.", "text": SYNTH_TEXTS}]}
        return 404, {"error": "unknown"}


class TestEndToEndOffline(unittest.TestCase):
    def test_run_survey_and_report(self):
        client = FakeClient()
        snap = sv.run_survey(client, limit=2, samples=2, log=lambda *_: None)
        self.assertEqual(len(snap["indexes"]), 2)
        rec = snap["indexes"]["Fake Siddur Ashkenaz"]
        self.assertEqual(rec["nusach_guess"], "אשכנז")
        self.assertEqual(rec["schema_summary"]["n_leaves"], 3)
        self.assertEqual(rec["aggregate"]["god_name_forms"]["יי"], 4)
        kinds = {p["kind"]: p["result"]["http_status"] for p in snap["v3_probes"]}
        self.assertEqual(kinds["עלה"], 200)
        self.assertEqual(kinds["טווח בין עלים (ref מלא-ref מלא)"], 400)
        json.dumps(snap, ensure_ascii=False)  # סריאלי ל-JSON

        md = sv.render_report(snap)
        self.assertIn("## נוסח: אשכנז", md)
        self.assertIn("## נוסח: עדות המזרח / ספרדי", md)
        self.assertIn("Fake Siddur Ashkenaz", md)
        self.assertIn("synthetic: ranges unsupported", md)
        self.assertIn("## הכרעות", md)

    def test_probes_prefer_siddur_category(self):
        # סינתטי: ספר לא-סידור מתגלה ראשון (כמו בריצה האמיתית, שבה פירושים
        # על משנה תורה הופיעו לפני הסידורים) — הבדיקות צריכות לרוץ על הסידור.
        client = FakeClient()
        toc = [{"category": "Liturgy", "contents": [
            {"title": "Fake Prayer Commentary", "categories": ["Halakhah"]},
            {"category": "Siddur", "contents": [
                {"title": "Fake Siddur Ashkenaz",
                 "categories": ["Liturgy", "Siddur"]}]}]}]
        orig = client.get
        client.get = lambda path, params=None: (
            (200, toc) if path == sv.ENDPOINTS["toc"] else orig(path, params))
        snap = sv.run_survey(client, samples=1, log=lambda *_: None)
        self.assertEqual(list(snap["indexes"])[0], "Fake Prayer Commentary")
        self.assertEqual(snap["v3_probes"][0]["index"], "Fake Siddur Ashkenaz")

    def test_sample_without_text_in_version_is_reported(self):
        # סינתטי: 200 עם versions ריק ואזהרה — כך עונה v3 לגרסה בלי טקסט בצומת
        client = FakeClient()
        orig = client.get
        client.get = lambda path, params=None: (
            (200, {"ref": "x", "versions": [], "warnings": [{"w": "synthetic"}]})
            if path.startswith("/api/v3/texts/") else orig(path, params))
        snap = sv.run_survey(client, limit=1, samples=1, log=lambda *_: None)
        rec = snap["indexes"]["Fake Siddur Ashkenaz"]
        self.assertIn("synthetic", rec["samples"][0]["warnings"])
        md = sv.render_report(snap)
        self.assertIn("אין טקסט בגרסה הזו", md)
        self.assertIn("דגימות בלי טקסט בגרסה המבוקשת", md)

    def test_nusach_filter(self):
        snap = sv.run_survey(FakeClient(), nusach="Ashkenaz", samples=1,
                             log=lambda *_: None)
        self.assertEqual(list(snap["indexes"]), ["Fake Siddur Ashkenaz"])

    def test_offline_client_uses_cache_only(self):
        with tempfile.TemporaryDirectory() as d:
            client = sv.Client("https://synthetic.invalid", d, offline=True)
            self.assertEqual(client.get("/api/index"), (0, None))
            url = "https://synthetic.invalid/api/index"
            client._cache_path(url).write_text(
                json.dumps({"url": url, "status": 200, "data": [1]}),
                encoding="utf-8")
            self.assertEqual(client.get("/api/index"), (200, [1]))
            self.assertEqual(client.n_network, 0)
            self.assertEqual(client.errors, [])
            url = "https://synthetic.invalid/api/name/x"
            client._cache_path(url).write_text(
                json.dumps({"url": url, "status": 404, "data": {}}),
                encoding="utf-8")
            self.assertEqual(client.get("/api/name/x"), (404, {}))
            self.assertEqual(client.errors, [{"url": url, "error": "HTTP 404"}])

    def test_main_writes_nothing_without_data(self):
        with tempfile.TemporaryDirectory() as d:
            md, js = Path(d) / "r.md", Path(d) / "s.json"
            with contextlib.redirect_stdout(io.StringIO()):
                rc = sv.main(["--offline", "--cache-dir", str(Path(d) / "c"),
                              "--base", "https://synthetic.invalid",
                              "--out-md", str(md), "--out-json", str(js)])
            self.assertEqual(rc, 1)
            self.assertFalse(md.exists() or js.exists())


if __name__ == "__main__":
    unittest.main()
