# -*- coding: utf-8 -*-
"""בדיקות ל-api/siddur.py ול-src/siddur/markup.py — בלי רשת (PLAN_TEFILA 4.2.2).

הקטלוג: האמיתי שבגיט (data/siddur/catalog.json). Sefaria: ‏_get_json מוחלף
בתשובות **אמיתיות שהוקלטו** מ-sefaria.org ב-29.10.2026 ונשמרו מקוצרות
ב-tests/fixtures/siddur/*.json (כל קובץ אומר בשדה ‏_recorded מה קוצר). מקרים
סינתטיים מסומנים ככאלה במקום.

הרצה:  python3 -m unittest discover -s tests -v
"""

import copy
import importlib.util
import json
import socket
import sys
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "siddur"

_SPEC = importlib.util.spec_from_file_location("api_siddur",
                                               ROOT / "api" / "siddur.py")
api = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(api)
ts = sys.modules[api.check_units_limits.__module__]  # api/text_segments.py

from siddur import markup  # noqa: E402  (api הוסיף את src ל-sys.path)
from aligner.pipeline import units_to_segments  # noqa: E402


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


# (ref, versionTitle) ⇐ תשובה מוקלטת — בדיוק ה-ref והגרסה שבקטלוג
RECORDED = {
    ("Siddur Ashkenaz, Weekday, Shacharit, Pesukei Dezimra, Ashrei",
     "The Metsudah siddur, 1981"): "ashkenaz_ashrei_metsudah",
    ("Siddur Edot HaMizrach, Weekday Shacharit, Ashrei",
     " Shaliehsaboo Edition"): "edot_ashrei_shaliehsaboo",
    ("Siddur Sefard, Kabbalat Shabbat", "Torat Emet 357"):
        "sefard_kabbalat_shabbat_torat_emet",
    ("Siddur Ashkenaz, Shabbat, Shacharit, Ashrei", "Daat Siddur Ashkenaz"):
        "ashkenaz_shabbat_ashrei_daat",
    ("Siddur Ashkenaz, Berachot, Asher Yatzar Etchem Badin",
     "Daat Siddur Ashkenaz"): "ashkenaz_asher_yatzar_daat",
    # תוספות תלויות-יום (4.4.2) — עמידה בכל נוסח/מהדורה, שיר של יום
    ("Siddur Edot HaMizrach, Weekday Shacharit, Amida",
     " Shaliehsaboo Edition"): "edot_weekday_amida_shaliehsaboo",
    ("Siddur Sefard, Weekday Shacharit, Amidah", "The Metsudah siddur, 1981"):
        "sefard_weekday_amidah_metsudah",
    ("Siddur Ashkenaz, Weekday, Shacharit, Amidah, Temple Service",
     "The Metsudah siddur, 1981"): "ashkenaz_temple_service_metsudah",
    ("Siddur Ashkenaz, Weekday, Shacharit, Amidah, Divine Might",
     "The Metsudah siddur, 1981"): "ashkenaz_divine_might_metsudah",
    ("Siddur Ashkenaz, Weekday, Shacharit, Amidah, Thanksgiving",
     "The Metsudah siddur, 1981"): "ashkenaz_thanksgiving_metsudah",
    ("Siddur Ashkenaz, Weekday, Shacharit, Amidah, Prosperity",
     "The Metsudah siddur, 1981"): "ashkenaz_prosperity_metsudah",
    ("Siddur Sefard, Holidays, Maariv, Shacharit & Mincha Amidah",
     "Torat Emet 357"): "sefard_festival_amidah_torat_emet",
    ("Siddur Ashkenaz, Shabbat, Shacharit, Amidah, Temple Service",
     "Daat Siddur Ashkenaz"): "ashkenaz_shabbat_temple_service_daat",
    ("Siddur Sefard, Weekday Shacharit, Song of the Day",
     "The Metsudah siddur, 1981"): "sefard_song_of_the_day_metsudah",
}
EMPTY = "sefard_ashrei_torat_emet_empty"  # ‏versions ריק — תשובה אמיתית

ASHK_ASHREI = "ashkenaz/weekday/shacharit/pesukei-dezimra/ashrei"
EDOT_ASHREI = "edot-hamizrach/weekday/weekday-shacharit/ashrei"
SEFARD_KS = "sefard/shabbat/kabbalat-shabbat"
DAAT_ASHREI = "ashkenaz/shabbat/shacharit/ashrei"
DAAT_ASHER = "ashkenaz/general/berachot/asher-yatzar-etchem-badin"
SEFARD_ASHREI = "sefard/weekday/weekday-shacharit/ashrei"
UNAVAILABLE = ("ashkenaz/weekday/shacharit/torah-reading/reading-from-sefer/"
               "prayers-for-welfare-of-the-people")


class FakeSefaria:
    """מחליף את _get_json: מפענח את ה-URL ומחזיר את התשובה המוקלטת."""

    def __init__(self, table=None):
        self.table = dict(RECORDED) if table is None else table
        self.calls = []

    def __call__(self, url, params=None):
        self.calls.append((url, params))
        prefix = api.SEFARIA_BASE + "/api/v3/texts/"
        assert url.startswith(prefix), url
        ref = urllib.parse.unquote(url[len(prefix):])
        vt = params["version"].split("|", 1)[1]
        hit = self.table.get((ref, vt), EMPTY)
        return copy.deepcopy(fixture(hit) if isinstance(hit, str) else hit)


class SiddurTestCase(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSefaria()
        p = mock.patch.object(api, "_get_json", side_effect=self.fake)
        p.start()
        self.addCleanup(p.stop)

    def get(self, **params):
        return api.respond(urllib.parse.urlencode(params))

    def ok(self, **params):
        payload, status, headers = self.get(**params)
        self.assertEqual(status, 200, payload.get("error"))
        return payload, headers


# =============================================================================
# ניווט וחיפוש (בלי Sefaria)
# =============================================================================

class TestChildren(SiddurTestCase):
    def test_root_lists_nusachim(self):
        payload, headers = self.ok()
        self.assertEqual([c["key"] for c in payload["children"]],
                         ["edot-hamizrach", "sefard", "ashkenaz"])
        self.assertEqual(payload["children"][2]["title"], "אשכנז")
        self.assertEqual(payload["breadcrumb"], [])
        self.assertIsNone(payload["nusach"])
        self.assertTrue(all(not c["is_leaf"] and c["available"]
                            for c in payload["children"]))
        self.assertIn("s-maxage", headers["Cache-Control"])
        self.assertEqual(self.fake.calls, [])  # ניווט — בלי רשת

    def test_nusach_roots(self):
        payload, _ = self.ok(nusach="ashkenaz")
        self.assertEqual(payload["path"], "ashkenaz")
        self.assertEqual(payload["children"][0],
                         {"key": "weekday", "path": "ashkenaz/weekday",
                          "title": "ימי חול", "title_en": "Weekday",
                          "is_leaf": False, "available": True, "count": 3})
        self.assertEqual(len(payload["children"]), 8)  # + ימים נוראים (4.4.1)
        self.assertEqual(payload["breadcrumb"],
                         [{"key": "ashkenaz", "path": "ashkenaz",
                           "title": "אשכנז"}])

    def test_relative_and_full_path_same(self):
        rel, _ = self.ok(nusach="ashkenaz", path="weekday/shacharit")
        full, _ = self.ok(path="ashkenaz/weekday/shacharit")
        both, _ = self.ok(nusach="ashkenaz", path="ashkenaz/weekday/shacharit")
        self.assertEqual(rel, full)
        self.assertEqual(rel, both)
        self.assertEqual([b["title"] for b in rel["breadcrumb"]],
                         ["אשכנז", "ימי חול", "תפילת שחרית"])

    def test_leaf_children_and_unavailable(self):
        payload, _ = self.ok(path="ashkenaz/weekday/shacharit/pesukei-dezimra")
        ashrei = next(c for c in payload["children"] if c["key"] == "ashrei")
        self.assertTrue(ashrei["is_leaf"] and ashrei["available"])
        self.assertEqual(ashrei["path"], ASHK_ASHREI)
        self.assertTrue(ashrei["first_words"].startswith("אַשְׁרֵי"))
        parent, key = UNAVAILABLE.rsplit("/", 1)
        payload, _ = self.ok(path=parent)
        item = next(c for c in payload["children"] if c["key"] == key)
        self.assertFalse(item["available"])

    def test_bad_paths(self):
        for params, status in [({"path": "ashkenaz/nope"}, 404),
                               ({"nusach": "yemenite"}, 404),
                               ({"nusach": "sefard",
                                 "path": "ashkenaz/weekday"}, 400),
                               ({"path": "ashkenaz/weekday", "from": "2"}, 400)]:
            payload, st, headers = self.get(**params)
            self.assertEqual(st, status, params)
            self.assertRegex(payload["error"], "[א-ת]")
            self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.fake.calls, [])


class TestSearch(SiddurTestCase):
    def test_title_search_in_nusach(self):
        payload, headers = self.ok(q="אשרי", nusach="sefard")
        paths = [r["path"] for r in payload["results"]]
        self.assertIn(SEFARD_ASHREI, paths)
        self.assertTrue(all(p.startswith("sefard/") for p in paths))
        first = payload["results"][0]
        self.assertEqual(first["match"], "title")
        self.assertEqual(first["breadcrumb"][0], "ספרד")
        self.assertIn("is_leaf", first)
        self.assertIn("s-maxage", headers["Cache-Control"])

    def test_first_words_search(self):
        payload, _ = self.ok(q="אשרי יושבי ביתך", nusach="ashkenaz")
        self.assertIn("first", {r["match"] for r in payload["results"]})

    def test_cap_and_errors(self):
        payload, _ = self.ok(q="ה")  # כמעט כל צומת — נחתך
        self.assertEqual(len(payload["results"]), api.MAX_SEARCH_RESULTS)
        self.assertTrue(payload["truncated"])
        for q in ["", "   ", "א" * (api.MAX_QUERY_CHARS + 1)]:
            payload, status, _ = self.get(q=q)
            self.assertEqual(status, 400)
            self.assertRegex(payload["error"], "[א-ת]")


# =============================================================================
# עלה: טקסט מ-Sefaria ⇐ יחידות ⇐ מקטעים
# =============================================================================

SEGMENT_KEYS = {"display", "label", "unit", "verse", "words", "letters",
                "verse_end"}


class TestLeafAshkenazMetsudah(SiddurTestCase):
    def test_exact_ref_and_version_requested(self):
        self.ok(path=ASHK_ASHREI)
        (url, params), = self.fake.calls
        self.assertEqual(urllib.parse.unquote(url.rsplit("/", 1)[1]),
                         "Siddur Ashkenaz, Weekday, Shacharit, "
                         "Pesukei Dezimra, Ashrei")
        self.assertEqual(params, {"version": "hebrew|The Metsudah siddur, 1981"})

    def test_payload_shape_like_text_segments(self):
        payload, headers = self.ok(path=ASHK_ASHREI)
        self.assertEqual(payload["mode"], "tefila")
        self.assertEqual(payload["max_words"], 4)
        self.assertEqual(payload["n_units"], len(payload["units"]))
        for seg in payload["segments"]:
            self.assertEqual(set(seg), SEGMENT_KEYS)
        self.assertEqual(payload["ref"], "Siddur Ashkenaz, Weekday, Shacharit, "
                                         "Pesukei Dezimra, Ashrei")
        self.assertEqual(payload["version"], "The Metsudah siddur, 1981")
        self.assertEqual(payload["license"], "CC-BY")
        self.assertIsNone(payload["version_fallback"])
        self.assertEqual(payload["title"], "אשרי")
        self.assertEqual(payload["breadcrumb"][-1]["path"], ASHK_ASHREI)
        self.assertEqual(payload["range"], {"from": 1, "to": 2, "total": 2})
        self.assertEqual(headers["Cache-Control"], api.CACHE_TEXT)

    def test_small_unvocalized_is_instruction(self):
        payload, _ = self.ok(path=ASHK_ASHREI)
        u0, u1 = payload["units"]
        self.assertEqual(u0["kind"], "instruction")
        self.assertTrue(u0["text"].startswith("צריך לכוין בתהלה לדוד"))
        self.assertNotIn("chunk", u0)
        self.assertEqual(u1["kind"], "paragraph")
        self.assertEqual(u1["label"], "אשרי · 2")
        # מצודה: סגולתא כסימן שווא נע — לא טעמים (8.24) ⇐ חותך הפרוזה
        self.assertIn("֒", u1["text"])
        self.assertEqual(u1["chunk"], "punct")
        self.assertEqual({s["unit"] for s in payload["segments"]}, {1})
        self.assertEqual([(p["n"], p["kind"]) for p in payload["paragraphs"]],
                         [(1, "instruction"), (2, "paragraph")])
        self.assertTrue(payload["paragraphs"][1]["first_words"]
                        .startswith("אַשְׁרֵי יוֹשְׁבֵי"))

    def test_single_segmentation_implementation(self):
        payload, _ = self.ok(path=ASHK_ASHREI, max_words="6")
        self.assertEqual(payload["max_words"], 6)
        self.assertEqual(payload["segments"],
                         ts.segments_payload(payload["units"], 6, "tefila"))
        direct = units_to_segments(payload["units"], 6, mode="tefila")
        self.assertEqual([s["display"] for s in payload["segments"]],
                         [s["display"] for s in direct])

    def test_bad_max_words(self):
        payload, status, _ = self.get(path=ASHK_ASHREI, max_words="ארבע")
        self.assertEqual(status, 400)
        self.assertIn("max_words", payload["error"])


class TestLeafEdotShaliehsaboo(SiddurTestCase):
    def test_version_title_with_leading_space(self):
        payload, _ = self.ok(path=EDOT_ASHREI)
        self.assertEqual(self.fake.calls[0][1],
                         {"version": "hebrew| Shaliehsaboo Edition"})
        self.assertEqual(payload["version"], " Shaliehsaboo Edition")
        self.assertEqual(payload["license"], "CC0")

    def test_title_citation_and_taamim(self):
        payload, _ = self.ok(path=EDOT_ASHREI)
        kinds = [p["kind"] for p in payload["paragraphs"]]
        # 1 כותרת לא מנוקדת, 4 — מראה מקום באמצע, 5 — הוראת דילוג ("ביום שאין
        # אומרים בו תחנון מדלגים למנצח"), ולכן 6 (למנצח) — תוספת תלויית-יום
        # (4.4.2): נאמרת בכל יום חוץ מימים שאין בהם תחנון
        self.assertEqual(kinds, ["instruction", "paragraph", "paragraph",
                                 "mixed", "instruction", "conditional"])
        self.assertEqual(payload["paragraphs"][5]["conditions"], ["no-tachanun"])
        para4 = [u for u in payload["units"] if u["label"] == "אשרי · 4"]
        self.assertEqual([u["kind"] for u in para4],
                         ["paragraph", "instruction", "paragraph"])
        self.assertEqual(para4[1]["text"], "(תהילים קמ״ה:א׳-ב׳)")
        self.assertTrue(para4[0]["text"].startswith("תְּהִלָּ֗ה"))
        # Shaliehsaboo: פסוקים מוטעמים באמת ⇐ חותך הטעמים
        self.assertEqual(para4[2]["chunk"], "taamim")
        self.assertEqual(payload["paragraphs"][0]["first_words"],
                         "אשרי יושבי ביתך")


class TestLeafSefardKabbalatShabbat(SiddurTestCase):
    def units_of(self, payload, n, cond=False):
        """היחידות של פסקה n (תווית "קבלת שבת · n", גם עם תנאי אחריה)."""
        return [(u["kind"], u["text"]) + ((u.get("condition"),) if cond else ())
                for u in payload["units"]
                if u["label"].split(" · ")[:2] == ["קבלת שבת", str(n)]]

    def test_vocalized_small_is_spoken(self):
        payload, _ = self.ok(path=SEFARD_KS)
        self.assertEqual(self.units_of(payload, 18), [
            ("paragraph", "לְכָה דוֹדִי לִקְרַאת כַּלָּה, פְּנֵי שַׁבָּת נְקַבְּלָה:")])

    def test_instruction_kinds(self):
        payload, _ = self.ok(path=SEFARD_KS)
        self.assertEqual(self.units_of(payload, 8)[1], ("instruction", 'אב"ג ית"ץ'))
        self.assertEqual(self.units_of(payload, 16)[0][0], "instruction")
        # הוראה שמצטטת מילים מנוקדות — כולה הוראה
        self.assertEqual(self.units_of(payload, 23), [
            ("instruction", "ביום טוב ובשבת חול המועד מדלגים "
                            "ל:יָמִין וּשְׂמֹאל תִּפְרוֹצִי")])
        # תוספת ליו״ט / לעשי״ת (4.4.2): ההוראה + התוספת. הקטע של שבת ⇐ ברירת
        # המחדל שבת, והתוספות כבויות; בקשה בלי day (ממשק ישן) ⇐ "instruction"
        self.assertEqual(self.units_of(payload, 37, cond=True)[1:3], [
            ("instruction", '(ביו"ט מוסיפים:', None),
            ("instruction", "בְּשִׂמְחָה)", "yom-tov")])
        self.assertEqual(self.units_of(payload, 43, cond=True)[1:3], [
            ("instruction", '(בעשי"ת', None),
            ("instruction", "הַשָּׁלוֹם)", "aseret-yemei-teshuva")])

    def test_range_inside_leaf(self):
        payload, _ = self.ok(path=SEFARD_KS, **{"from": "17", "to": "38"})
        self.assertEqual(payload["range"], {"from": 17, "to": 38, "total": 43})
        self.assertEqual(len(payload["paragraphs"]), 43)  # לבחירת טווח בממשק
        labels = {" · ".join(u["label"].split(" · ")[:2]) for u in payload["units"]}
        self.assertEqual(labels, {f"קבלת שבת · {n}" for n in range(17, 39)})
        self.assertTrue(payload["units"][0]["text"].startswith("לְכָה דוֹדִי"))
        self.assertEqual(len(self.fake.calls), 1)  # עלה אחד, משיכה אחת
        self.assertEqual(payload["ref"], "Siddur Sefard, Kabbalat Shabbat")

    def test_open_ended_ranges(self):
        payload, _ = self.ok(path=SEFARD_KS, **{"from": "40"})
        self.assertEqual(payload["range"], {"from": 40, "to": 43, "total": 43})
        payload, _ = self.ok(path=SEFARD_KS, to="2")
        self.assertEqual(payload["range"], {"from": 1, "to": 2, "total": 43})

    def test_bad_ranges(self):
        for rng in [{"from": "40", "to": "50"}, {"from": "5", "to": "3"},
                    {"from": "0"}, {"from": "abc"}, {"to": "-1"}]:
            payload, status, _ = self.get(path=SEFARD_KS, **rng)
            self.assertEqual(status, 400, rng)
            self.assertRegex(payload["error"], "[א-ת]")

    def test_instruction_only_range(self):
        payload, status, _ = self.get(path=SEFARD_KS, **{"from": "16", "to": "16"})
        self.assertEqual(status, 400)
        self.assertIn("רק הוראות", payload["error"])
        self.assertEqual(payload["units"][0]["kind"], "instruction")


class TestLeafDaat(SiddurTestCase):
    def test_unvocalized_divine_name_is_spoken(self):
        payload, _ = self.ok(path=DAAT_ASHREI)
        (unit,) = payload["units"]
        self.assertEqual(unit["kind"], "paragraph")
        self.assertIn("שה'", unit["text"])
        self.assertIn("גָּדול ה'", unit["text"])
        # ‏"עוד" (חולם מלא בלי ניקוד) נאמר ונכנס ליישור
        self.assertIn("עוד", unit["text"])
        segs = units_to_segments(payload["units"], 4, mode="tefila")
        words = [w for s in segs for w in s["align_plain"]]
        self.assertIn("שאדני", words)
        self.assertIn("עוד", words)

    def test_fully_unvocalized_leaf(self):
        payload, status, headers = self.get(path=DAAT_ASHER)
        self.assertEqual(status, 422)
        self.assertTrue(payload["unvocalized"])
        self.assertIn("אינו מנוקד", payload["error"])
        self.assertEqual({u["kind"] for u in payload["units"]}, {"instruction"})
        self.assertEqual(headers["Cache-Control"], "no-store")


class TestLeafErrors(SiddurTestCase):
    def test_empty_versions_is_clear_error(self):
        payload, status, headers = self.get(path=SEFARD_ASHREI)
        self.assertEqual(status, 502)
        self.assertIn("versions ריק", payload["error"])
        self.assertIn("The Metsudah siddur, 1981", payload["error"])
        self.assertEqual(len(self.fake.calls), 1)  # אין alt בקטלוג ⇐ אין נפילה
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_fallback_only_to_catalog_alt_and_reported(self):
        # סינתטי: Sefaria "מחזירה" versions ריק במהדורה שנבחרה, ואת הטקסט
        # המוקלט של Shaliehsaboo כאילו הוא תורת אמת (המהדורה ב-alt של העלה)
        alt = fixture("edot_ashrei_shaliehsaboo")
        alt["versions"][0]["versionTitle"] = "Torat Emet 357"
        self.fake.table = {("Siddur Edot HaMizrach, Weekday Shacharit, Ashrei",
                            "Torat Emet 357"): alt}
        payload, _ = self.ok(path=EDOT_ASHREI)
        self.assertEqual(payload["version"], "Torat Emet 357")
        self.assertEqual(payload["license"], "Public Domain")
        self.assertEqual(payload["version_fallback"]["requested"],
                         " Shaliehsaboo Edition")
        self.assertEqual(payload["version_fallback"]["used"], "Torat Emet 357")
        self.assertEqual([c[1]["version"] for c in self.fake.calls],
                         ["hebrew| Shaliehsaboo Edition", "hebrew|Torat Emet 357"])

    def test_other_version_in_response_is_rejected(self):
        wrong = fixture("ashkenaz_ashrei_metsudah")
        wrong["versions"][0]["versionTitle"] = "Some Other Edition"
        self.fake.table = {("Siddur Ashkenaz, Weekday, Shacharit, Pesukei "
                            "Dezimra, Ashrei", "The Metsudah siddur, 1981"): wrong}
        payload, status, _ = self.get(path=ASHK_ASHREI)
        self.assertEqual(status, 502)

    def test_unavailable_leaf_no_fetch(self):
        payload, status, _ = self.get(path=UNAVAILABLE)
        self.assertEqual(status, 404)
        self.assertIn("לא זמין", payload["error"])
        self.assertEqual(self.fake.calls, [])

    def test_ref_with_trailing_space_sent_verbatim(self):
        self.get(path="sefard/weekday/additional-prayers/thirteen-principles")
        url = self.fake.calls[0][0]
        self.assertTrue(url.endswith(
            "/Siddur%20Sefard%2C%20Additional%20Prayers%20%2C%20Thirteen%20Principles"))

    def test_network_errors(self):
        cases = [
            (urllib.error.URLError(socket.timeout("timed out")), 504),
            (socket.timeout("timed out"), 504),
            (urllib.error.HTTPError("u", 404, "nf", {}, None), 502),
            (urllib.error.HTTPError("u", 500, "err", {}, None), 502),
            (urllib.error.URLError("refused"), 502),
        ]
        for exc, status in cases:
            with mock.patch.object(api, "_get_json", side_effect=exc):
                payload, st, headers = self.get(path=ASHK_ASHREI)
            self.assertEqual(st, status, exc)
            self.assertRegex(payload["error"], "Sefaria")
            self.assertEqual(headers["Cache-Control"], "no-store")


class TestCaps(SiddurTestCase):
    def test_max_paragraphs(self):
        with mock.patch.object(api, "MAX_PARAGRAPHS", 10):
            payload, status, _ = self.get(path=SEFARD_KS)
            self.assertEqual(status, 413)
            self.assertIn("from/to", payload["error"])
            self.assertEqual(len(payload["paragraphs"]), 43)
            payload, _ = self.ok(path=SEFARD_KS, **{"from": "17", "to": "26"})
            self.assertEqual(payload["range"]["to"], 26)

    def test_worker_units_limits(self):
        with mock.patch.object(ts, "MAX_UNITS_BYTES", 2000):
            payload, status, _ = self.get(path=SEFARD_KS)
        self.assertEqual(status, 413)
        self.assertIn("ארוך מדי לסנכרון", payload["error"])
        with mock.patch.object(ts, "MAX_UNITS", 5):
            payload, status, _ = self.get(path=SEFARD_KS)
        self.assertEqual(status, 413)
        self.assertEqual(len(payload["paragraphs"]), 43)


# =============================================================================
# src/siddur/markup.py — הכלל לבדו (מחרוזות סינתטיות, בסגנון הטקסט האמיתי)
# =============================================================================

class TestMarkup(unittest.TestCase):
    C = staticmethod(markup.classify_paragraph)

    def test_small_rule(self):
        self.assertEqual(self.C("<small>אומרים בלחש</small> בָּרוּךְ שֵׁם"),
                         [("instruction", "אומרים בלחש"),
                          ("spoken", "בָּרוּךְ שֵׁם")])
        self.assertEqual(self.C("<small>בָּרוּךְ שֵׁם כְּבוֹד</small>"),
                         [("spoken", "בָּרוּךְ שֵׁם כְּבוֹד")])

    def test_divine_name_exception(self):
        self.assertEqual(self.C("בָּרוּךְ אַתָּה ה' לַה' וּבה'"),
                         [("spoken", "בָּרוּךְ אַתָּה ה' לַה' וּבה'")])
        # בתוך הוראה של מצודה ה' נשאר הוראה
        self.assertEqual(
            self.C("<small>ואומר ברוך ה' לעולם</small> בָּרוּךְ ה' לְעוֹלָם "
                   "אָמֵן וְאָמֵן"),
            [("instruction", "ואומר ברוך ה' לעולם"),
             ("spoken", "בָּרוּךְ ה' לְעוֹלָם אָמֵן וְאָמֵן")])
        self.assertEqual(self.C("<small>(ה')</small> אָמֵן"),
                         [("spoken", "(ה') אָמֵן")])

    def test_brackets_parens_and_abbreviations(self):
        self.assertEqual(self.C("[אמן] אַשְׁרֵי (וְ) בֵיתֶךָ ג\"פ"),
                         [("instruction", "[אמן]"),
                          ("spoken", "אַשְׁרֵי (וְ) בֵיתֶךָ"),
                          ("instruction", 'ג"פ')])
        # סוגר בלי פותח — סתם תו
        self.assertEqual(self.C("אָמֵן) וְאָמֵן"), [("spoken", "אָמֵן) וְאָמֵן")])

    def test_unmarked_runs_and_holam_male(self):
        self.assertEqual(self.C("ואומר החזן בקול: יִתְגַּדַּל וְיִתְקַדַּשׁ"),
                         [("instruction", "ואומר החזן בקול:"),
                          ("spoken", "יִתְגַּדַּל וְיִתְקַדַּשׁ")])
        self.assertEqual(self.C("עוד יְהַלְלוּךָ סֶּלָה: בְּכָל יום"),
                         [("spoken", "עוד יְהַלְלוּךָ סֶּלָה: בְּכָל יום")])
        self.assertEqual(self.C("<small>מֶלֶךְ עוזֵר וּמושִׁיעַ</small>"),
                         [("spoken", "מֶלֶךְ עוזֵר וּמושִׁיעַ")])

    def test_unvocalized_lines_and_br(self):
        self.assertEqual(self.C("<b>שליח ציבור:</b>"),
                         [("instruction", "שליח ציבור:")])
        self.assertEqual(self.C("י\"ט ניסן<br>הַיּוֹם אַרְבָּעָה יָמִים לָעֹמֶר:"),
                         [("instruction", 'י"ט ניסן'),
                          ("spoken", "הַיּוֹם אַרְבָּעָה יָמִים לָעֹמֶר:")])
        self.assertEqual(self.C("שׁוּרָה רִאשׁוֹנָה<br/>שׁוּרָה שְׁנִיָּה"),
                         [("spoken", "שׁוּרָה רִאשׁוֹנָה\nשׁוּרָה שְׁנִיָּה")])
        self.assertEqual(self.C(""), [])
        self.assertEqual(self.C("<b> </b>&nbsp;"), [])

    def test_footnotes_and_entities_removed(self):
        self.assertEqual(
            self.C('אָמֵן<sup>1</sup><i class="footnote">הערה</i> &amp; סֶלָה'),
            [("spoken", "אָמֵן & סֶלָה")])

    def test_first_words_and_vocalized(self):
        self.assertEqual(markup.first_words(
            ["<small>כשיעור משנתו יאמר</small> <b>מוֹדֶה</b> אֲנִי,",
             "מֶלֶךְ חַי וְקַיָּם"], 4), "מוֹדֶה אֲנִי מֶלֶךְ חַי")
        self.assertFalse(markup.has_vocalized(["ברוך אתה יי", ["אלהינו"]]))
        self.assertTrue(markup.has_vocalized(["ברוך", ["אַתָּה"]]))
        self.assertEqual(markup.flatten(["א", ["ב", ["ג"]], 5]), ["א", "ב", "ג"])


# =============================================================================
# פריסה: הפונקציה רשומה, והקבצים שהיא צריכה לא מסוננים
# =============================================================================

class TestDeployConfig(unittest.TestCase):
    def test_registered_in_vercel_json(self):
        cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        fn = cfg["functions"]["api/siddur.py"]
        self.assertEqual(fn["maxDuration"], 30)
        self.assertGreater(fn["maxDuration"], api.SEFARIA_TIMEOUT)
        for needed in ("data/", "src/", "api/"):
            self.assertNotIn(needed, fn.get("excludeFiles", ""))
        self.assertNotIn("includeFiles", fn)  # הכל נכלל כברירת מחדל

    def test_import_when_api_dir_on_path(self):
        """הקובץ api/siddur.py והחבילה src/siddur באותו שם. סביבת הריצה טוענת
        את הפונקציה כמודול "api.siddur" (נתיב מנוקד מהשורש); גם אם תיקיית
        api/ ראשונה ב-sys.path, "siddur" חייב להיות החבילה. (טעינת הקובץ
        עצמו בשם החשוף "siddur" אינה נתמכת — לשניים אין שם משותף.)"""
        import subprocess
        code = ("import sys, importlib; sys.path.insert(0, 'api'); "
                "h = importlib.import_module('api.siddur'); "
                "p, s, _ = h.respond('nusach=sefard'); "
                "print(s, p['breadcrumb'][0]['title'], hasattr(h, 'handler'), "
                "sys.modules['siddur'].__file__.endswith('src/siddur/__init__.py'))")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.stdout.strip(), "200 ספרד True True", out.stderr)

    def test_vercelignore_keeps_runtime_files(self):
        lines = [ln.strip().rstrip("/") for ln in
                 (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith("#")]
        for path in ("data/siddur/catalog.json", "src/siddur/markup.py",
                     "src/siddur/catalog.py", "api/text_segments.py"):
            parts = path.split("/")
            prefixes = {"/".join(parts[:i]) for i in range(1, len(parts) + 1)}
            self.assertFalse(prefixes & set(lines), path)
            self.assertTrue((ROOT / path).exists(), path)


if __name__ == "__main__":
    unittest.main()
