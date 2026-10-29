# -*- coding: utf-8 -*-
"""בדיקות ל-modal_worker/params.py — ולידציית הפרמטרים של ה-worker בענן.

נטען ישירות מהנתיב (בלי לייבא את modal_worker/app.py, שדורש את חבילת modal).
רץ בלי רשת, כמו שאר הבדיקות.
"""

import importlib.util
import inspect
import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SPEC = importlib.util.spec_from_file_location(
    "modal_params", _ROOT / "modal_worker" / "params.py")
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
                               "chapter_end": None, "max_words": 4,
                               "splits": None})

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


class TestParseSplits(unittest.TestCase):
    """חלוקת הכתוביות שהמשתמש ערך ידנית בממשק."""

    def test_json_list_parsed(self):
        self.assertEqual(params.parse_splits("[3, 4, 2]"), [3, 4, 2])
        self.assertEqual(params.parse_splits([1, 1]), [1, 1])

    def test_empty_is_none(self):
        self.assertIsNone(params.parse_splits(""))
        self.assertIsNone(params.parse_splits("   "))
        self.assertIsNone(params.parse_splits(None))

    def test_broken_input_raises(self):
        """קלט פגום נכשל בקול — ריצה בחלוקה אחרת הייתה מבלבלת את המשתמש."""
        for bad in ("לא JSON", "[]", "{}", "[0]", "[-1]", '["3"]', "[1.5]",
                    "[true]"):
            with self.assertRaises(ValueError):
                params.parse_splits(bad)

    def test_absurd_length_rejected(self):
        with self.assertRaises(ValueError):
            params.parse_splits([1] * (params.MAX_SPLIT_WORDS + 1))

    def test_reaches_params_dict(self):
        got = params.parse_params({"book": "בראשית", "chapter": "1",
                                   "splits": "[2, 5]"})
        self.assertEqual(got["splits"], [2, 5])


ASHREI = [
    {"text": "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ, עוֹד יְהַלְלוּךָ סֶּלָה.",
     "label": "אשרי · 1", "kind": "line", "chunk": "punct"},
    {"text": "בעשרת ימי תשובה:", "kind": "instruction"},
    {"text": "אַשְׁרֵי הָעָם שֶׁכָּכָה לּוֹ"},
]


def _units_form(**extra):
    form = {"source": "text", "units": json.dumps(ASHREI, ensure_ascii=False)}
    form.update(extra)
    return form


class TestParseParamsUnits(unittest.TestCase):
    """מקור text/siddur‏ (PLAN_TEFILA.md 3.3) — יחידות טקסט במקום ספר/פרק."""

    def test_text_source_defaults(self):
        got = params.parse_params(_units_form())
        self.assertEqual(got, {"source": "text", "units": ASHREI, "title": "",
                               "max_words": 4, "splits": None,
                               "performance": None, "profile": "reading",
                               "mode": "tefila"})

    def test_siddur_source_and_all_fields(self):
        got = params.parse_params(_units_form(
            source="siddur", title="  אשרי   לשבת ", max_words="3",
            splits="[2, 3, 1]", performance="[0, 1, 0, 2]",
            profile="singing", book="בראשית"))  # book מתעלמים — לא תנ״ך
        self.assertEqual(got["source"], "siddur")
        self.assertEqual(got["title"], "אשרי לשבת")
        self.assertEqual(got["max_words"], 3)
        self.assertEqual(got["splits"], [2, 3, 1])
        self.assertEqual(got["performance"], [0, 1, 0, 2])
        self.assertEqual(got["profile"], "singing")
        self.assertNotIn("book", got)

    def test_unknown_unit_fields_dropped(self):
        units = [{"text": "שָׁלוֹם", "extra": 1, "label": "א"}]
        got = params.parse_params({"source": "text",
                                   "units": json.dumps(units)})
        self.assertEqual(got["units"], [{"text": "שָׁלוֹם", "label": "א"}])

    def test_missing_units(self):
        for units in (None, "", "   "):
            with self.assertRaisesRegex(ValueError, "חסר הטקסט"):
                params.parse_params({"source": "text", "units": units})

    def test_broken_json(self):
        with self.assertRaisesRegex(ValueError, "JSON"):
            params.parse_params({"source": "text", "units": '[{"text": '})

    def test_not_a_list(self):
        for bad in ("{}", "[]", '"שלום"', "5"):
            with self.assertRaisesRegex(ValueError, "רשימה לא ריקה"):
                params.parse_params({"source": "text", "units": bad})

    def test_oversized_json(self):
        big = json.dumps([{"text": "א" * 1000}] * 300, ensure_ascii=False)
        self.assertGreater(len(big.encode("utf-8")), params.MAX_UNITS_BYTES)
        with self.assertRaisesRegex(ValueError, "ארוך מדי"):
            params.parse_params({"source": "text", "units": big})

    def test_too_many_units(self):
        units = json.dumps([{"text": "א"}] * (params.MAX_UNITS + 1))
        with self.assertRaisesRegex(ValueError, "יותר מדי"):
            params.parse_params({"source": "text", "units": units})

    def test_unit_text_too_long(self):
        units = [{"text": "א" * (params.MAX_UNIT_TEXT + 1)}]
        with self.assertRaisesRegex(ValueError, "יחידה 1: ארוכה מדי"):
            params.parse_units(units)

    def test_bad_unit_fields(self):
        cases = [
            (["שלום"], "אובייקט"),
            ([{"label": "א"}], "חסר טקסט"),
            ([{"text": "   "}], "חסר טקסט"),
            ([{"text": 5}], "חסר טקסט"),
            ([{"text": "שלום", "kind": "poem"}], "kind"),
            ([{"text": "שלום", "chunk": "words"}], "chunk"),
            ([{"text": "שלום", "label": 7}], "label"),
            ([{"text": "שלום", "label": "א" * (params.MAX_LABEL + 1)}],
             "label"),
        ]
        for units, msg in cases:
            with self.assertRaisesRegex(ValueError, msg):
                params.parse_params({"source": "text",
                                     "units": json.dumps(units,
                                                         ensure_ascii=False)})

    def test_error_names_unit_number(self):
        units = [{"text": "שלום"}, {"text": "עולם", "kind": "x"}]
        with self.assertRaisesRegex(ValueError, "יחידה 2"):
            params.parse_units(units)

    def test_requires_hebrew(self):
        with self.assertRaisesRegex(ValueError, "אות עברית"):
            params.parse_units([{"text": "hello world 123"}])
        # עברית רק בהוראה (שלא נכנסת ליישור) — אין מה לסנכרן
        with self.assertRaisesRegex(ValueError, "אות עברית"):
            params.parse_units([{"text": "ביום שבת:", "kind": "instruction"},
                                {"text": "Amen"}])

    def test_unknown_source(self):
        with self.assertRaisesRegex(ValueError, "מקור טקסט לא מוכר"):
            params.parse_params({"source": "mishna", "units": "[]"})

    def test_unknown_profile(self):
        with self.assertRaisesRegex(ValueError, "פרופיל לא מוכר"):
            params.parse_params(_units_form(profile="shouting"))

    def test_title_too_long(self):
        with self.assertRaisesRegex(ValueError, "הכותרת ארוכה מדי"):
            params.parse_params(_units_form(title="א" * (params.MAX_TITLE + 1)))

    def test_performance_shape(self):
        for bad in ("לא JSON", "[]", "{}", '["1"]', "[1.5]", "[true]"):
            with self.assertRaisesRegex(ValueError, "performance"):
                params.parse_params(_units_form(performance=bad))
        with self.assertRaisesRegex(ValueError, "0 ומעלה"):
            params.parse_params(_units_form(performance="[0, -1]"))
        with self.assertRaisesRegex(ValueError, "ארוך מדי"):
            params.parse_performance([0] * (params.MAX_PERFORMANCE + 1))

    def test_performance_out_of_range_with_splits(self):
        """כשה-splits ידוע — טווח האינדקסים נבדק כבר כאן."""
        with self.assertRaisesRegex(ValueError, "שאינה קיימת"):
            params.parse_params(_units_form(splits="[2, 3]",
                                            performance="[0, 1, 2]"))
        got = params.parse_params(_units_form(splits="[2, 3]",
                                              performance="[1, 0, 1]"))
        self.assertEqual(got["performance"], [1, 0, 1])

    def test_performance_without_splits_checks_shape_only(self):
        """בלי splits מספר הכתוביות ידוע רק אחרי החיתוך — בצינור עצמו."""
        got = params.parse_params(_units_form(performance="[0, 99]"))
        self.assertEqual(got["performance"], [0, 99])

    def test_bad_max_words_and_splits_in_units_mode(self):
        with self.assertRaisesRegex(ValueError, "מקסימום מילים"):
            params.parse_params(_units_form(max_words="11"))
        with self.assertRaises(ValueError):
            params.parse_params(_units_form(splits="[0]"))


class TestTanakhBackwardCompat(unittest.TestCase):
    """טופס של היום (בלי השדות החדשים) ⇒ בדיוק אותו מילון כמו לפני ההרחבה."""

    OLD = {"book": "בראשית", "chapter": "1", "verse_start": "",
           "verse_end": "0", "chapter_end": None, "max_words": "",
           "splits": "[2, 5]"}
    EXPECTED = {"book": "בראשית", "chapter": 1, "verse_start": None,
                "verse_end": None, "chapter_end": None, "max_words": 4,
                "splits": [2, 5]}

    def test_old_form_unchanged(self):
        self.assertEqual(params.parse_params(dict(self.OLD)), self.EXPECTED)

    def test_empty_new_fields_unchanged(self):
        """השרת ממלא "" לכל שדה שדפדפן ישן לא שלח (Form(""))."""
        form = dict(self.OLD, source="", units="", title="", performance="",
                    profile="")
        self.assertEqual(params.parse_params(form), self.EXPECTED)
        form["source"] = "tanakh"
        self.assertEqual(params.parse_params(form), self.EXPECTED)

    def test_tanakh_ignores_units(self):
        form = dict(self.OLD, units="לא JSON בכלל")
        self.assertEqual(params.parse_params(form), self.EXPECTED)

    def test_tanakh_title_only_adds_label(self):
        got = params.parse_params(dict(self.OLD, title="פרשת בראשית"))
        self.assertEqual(got, dict(self.EXPECTED, title="פרשת בראשית"))

    def test_tanakh_rejects_performance_and_singing(self):
        with self.assertRaisesRegex(ValueError, "performance"):
            params.parse_params(dict(self.OLD, performance="[0, 1]"))
        with self.assertRaisesRegex(ValueError, "שירה"):
            params.parse_params(dict(self.OLD, profile="singing"))
        params.parse_params(dict(self.OLD, profile="reading"))  # לא זורק


class TestRouting(unittest.TestCase):
    """הניתוב ב-process‏ (pipeline_call / notify_label) — בלי modal/torch."""

    def test_tanakh_routes_to_run_hybrid_exactly_as_before(self):
        p = params.parse_params({"book": "שמות", "chapter": "12",
                                 "verse_start": "1", "verse_end": "20",
                                 "splits": "[3]"})
        name, kw = params.pipeline_call(p, "/t/rec.m4a", "/t/out.srt", "/t")
        self.assertEqual(name, "run_hybrid")
        # בדיוק הארגומנטים ש-app.py העביר ל-run_hybrid לפני ההרחבה
        self.assertEqual(kw, {"book": "שמות", "chapter": 12,
                              "audio_path": "/t/rec.m4a",
                              "out_srt_path": "/t/out.srt",
                              "verse_start": 1, "chapter_end": None,
                              "verse_end": 20, "max_words": 4,
                              "work_dir": "/t", "splits": [3]})
        self.assertEqual(params.notify_label(p), "שמות 12")

    def test_units_route_to_run_hybrid_units(self):
        p = params.parse_params(_units_form(title="אשרי", splits="[2, 2]",
                                            performance="[0, 1, 0]"))
        name, kw = params.pipeline_call(p, "/t/a.wav", "/t/o.srt", "/t")
        self.assertEqual(name, "run_hybrid_units")
        self.assertEqual(kw, {"units": ASHREI, "audio_path": "/t/a.wav",
                              "out_srt_path": "/t/o.srt", "max_words": 4,
                              "splits": [2, 2], "performance": [0, 1, 0],
                              "profile": "reading", "mode": "tefila",
                              "work_dir": "/t"})
        self.assertEqual(params.notify_label(p), "אשרי")

    def test_singing_routes_to_run_hybrid_units(self):
        """פרופיל שירה (4.3.5) עובר כמו שהוא לצינור היחידות, תמיד ב-tefila."""
        p = params.parse_params(_units_form(profile="singing"))
        name, kw = params.pipeline_call(p, "/t/a.wav", "/t/o.srt", "/t")
        self.assertEqual(name, "run_hybrid_units")
        self.assertEqual((kw["profile"], kw["mode"]), ("singing", "tefila"))

    def test_profiles_in_sync_with_pipeline(self):
        """‏params.PROFILES (העתק — ה-web לא טוען את הצינור) = profiles.py."""
        sys.path.insert(0, str(_ROOT / "src"))
        from aligner import profiles
        self.assertEqual(set(params.PROFILES), set(profiles.PROFILES))

    def test_routing_kwargs_match_pipeline_signatures(self):
        """שמות הארגומנטים תואמים לחתימות בפועל ב-src/aligner/hybrid.py."""
        sys.path.insert(0, str(_ROOT / "src"))
        from aligner import hybrid
        for p in (params.parse_params({"book": "בראשית", "chapter": "1"}),
                  params.parse_params(_units_form())):
            name, kw = params.pipeline_call(p, "a", "o", "w")
            inspect.signature(getattr(hybrid, name)).bind(**kw)

    def test_notify_label_fallbacks(self):
        self.assertEqual(params.notify_label(
            params.parse_params(_units_form())), "טקסט חופשי")
        self.assertEqual(params.notify_label(
            params.parse_params(_units_form(source="siddur"))), "תפילה")

    def test_constants_in_sync_with_pipeline(self):
        """ההעתק של UNIT_KINDS / CHUNK_MODES ב-params.py חייב להישאר מסונכרן."""
        sys.path.insert(0, str(_ROOT / "src"))
        from aligner import pipeline
        self.assertEqual(params.UNIT_KINDS, pipeline.UNIT_KINDS)
        self.assertEqual(params.CHUNK_MODES, pipeline.CHUNK_MODES)


if __name__ == "__main__":
    unittest.main()
