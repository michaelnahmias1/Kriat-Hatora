# -*- coding: utf-8 -*-
"""בדיקות ל-api/text_segments.py — הלוגיקה בלבד, בלי רשת ובלי שרת.

בודקים פירוק לשורות-יחידות, ולידציה של קלט, ומבנה ה-JSON — אותו מבנה
כמו /api/segments, שהממשק בדפדפן מסתמך עליו.
"""

import contextlib
import importlib.util
import io
import json
import re
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "api_text_segments",
    Path(__file__).resolve().parent.parent / "api" / "text_segments.py")
api = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(api)

ASHREI = ("אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ, עוֹד יְהַלְלוּךָ סֶּלָה׃\n"
          "\n"
          "אַשְׁרֵי הָעָם שֶׁכָּכָה לּוֹ, אַשְׁרֵי הָעָם שֶׁיְהֹוָה אֱלֹהָיו׃\n")
VERSE = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"


class TestUnits(unittest.TestCase):
    def test_lines_become_units(self):
        units = api.text_units(ASHREI + "---\n" + VERSE)
        self.assertEqual([u["label"] for u in units],
                         ["שורה 1", "שורה 2", "שורה 3"])
        self.assertEqual({u["kind"] for u in units}, {"line"})
        self.assertEqual([u["chunk"] for u in units],
                         ["punct", "punct", "taamim"])


class TestBuildPayload(unittest.TestCase):
    def test_shape_matches_segments_api(self):
        payload = api.build_payload({"text": ASHREI})
        self.assertEqual(payload["mode"], "tefila")
        self.assertEqual(payload["max_words"], 4)
        self.assertEqual(payload["n_units"], 2)
        self.assertEqual(len(payload["units"]), 2)
        for seg in payload["segments"]:
            for key in ("display", "label", "unit", "verse", "words",
                        "letters", "verse_end"):
                self.assertIn(key, seg)

    def test_segments_and_unit_end(self):
        segs = api.build_payload({"text": ASHREI})["segments"]
        self.assertEqual([s["display"] for s in segs], [
            "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ,", "עוֹד יְהַלְלוּךָ סֶּלָה׃",
            "אַשְׁרֵי הָעָם שֶׁכָּכָה לּוֹ,", "אַשְׁרֵי הָעָם שֶׁיְהֹוָה אֱלֹהָיו׃"])
        self.assertEqual([s["verse_end"] for s in segs],
                         [False, True, False, True])
        self.assertEqual([s["unit"] for s in segs], [0, 0, 1, 1])
        self.assertEqual([s["verse"] for s in segs], [1, 1, 2, 2])
        self.assertEqual(segs[2]["label"], "שורה 2")
        self.assertEqual(segs[0]["words"], 3)
        self.assertEqual(segs[0]["letters"], len("אשרייושביביתך"))

    def test_accented_line_uses_taamim_chunker(self):
        segs = api.build_payload({"text": VERSE})["segments"]
        self.assertEqual(segs[0]["display"], "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים")

    def test_unvocalized_text_in_tefila_mode(self):
        payload = api.build_payload({"text": "ברוך אתה ה' אלהינו מלך העולם"})
        self.assertEqual(sum(s["words"] for s in payload["segments"]), 6)

    def test_unvocalized_text_in_tanakh_mode_rejected(self):
        with self.assertRaises(ValueError):
            api.build_payload({"text": "ברוך אתה", "mode": "tanakh"})

    def test_max_words_clamped_and_parsed(self):
        self.assertEqual(api.build_payload(
            {"text": ASHREI, "max_words": 99})["max_words"], 8)
        self.assertEqual(api.build_payload(
            {"text": ASHREI, "max_words": "1"})["max_words"], 2)
        with self.assertRaises(ValueError):
            api.build_payload({"text": ASHREI, "max_words": "ארבע"})

    def test_invalid_input_rejected(self):
        for body in [{}, {"text": ""}, {"text": "   \n"}, {"text": 5},
                     {"text": "hello world"}, [ASHREI],
                     {"text": ASHREI, "mode": "siddur"},
                     {"text": "א" * (api.MAX_CHARS + 1)}]:
            with self.assertRaises(ValueError, msg=repr(body)[:40]):
                api.build_payload(body)


class TestUnitsLimits(unittest.TestCase):
    """המגבלות של ה-worker (‏parse_units) נאכפות כבר כאן — לפני העלאת הקלטה."""

    def test_unit_count(self):
        # ישירות על היחידות: ב-3,000 שורות מה-API (עם label/kind/chunk)
        # מגבלת הבתים נתפסת עוד קודם — ראה test_respond_413
        api.check_units_limits([{"text": "אב"}] * api.MAX_UNITS)
        with self.assertRaises(api.TooLarge) as cm:
            api.check_units_limits([{"text": "אב"}] * (api.MAX_UNITS + 1))
        self.assertIn("יותר מדי שורות", str(cm.exception))

    def test_unit_text_length(self):
        line = ("אבגד " * (api.MAX_UNIT_TEXT // 5)).strip()
        line += "א" * (api.MAX_UNIT_TEXT - len(line))
        self.assertEqual(len(line), api.MAX_UNIT_TEXT)
        payload = api.build_payload({"text": line})
        self.assertEqual(len(payload["units"][0]["text"]), api.MAX_UNIT_TEXT)
        with self.assertRaises(api.TooLarge) as cm:
            api.build_payload({"text": line + "א"})
        self.assertIn("שורה 1 ארוכה מדי", str(cm.exception))

    def _text_of_bytes(self, target):
        """טקסט שה-JSON של היחידות שלו שוקל target בתים בדיוק.

        מקפים ארוכים (3 בתים לתו) — כדי לעבור את מגבלת הבתים מתחת ל-MAX_CHARS.
        """
        def size(lines):
            return len(api.units_json(api.text_units("\n".join(lines)))
                       .encode("utf-8"))
        lines = ["א" + "—" * 4999] * 14
        lines[-1] = "." * (-(size(lines) - target) % 3) + lines[-1]
        excess = size(lines) - target
        self.assertGreater(excess, 0)
        self.assertEqual(excess % 3, 0)
        lines[-1] = lines[-1][:-(excess // 3)]
        text = "\n".join(lines)
        self.assertLess(len(text), api.MAX_CHARS)
        self.assertEqual(
            len(api.units_json(api.text_units(text)).encode("utf-8")), target)
        return text

    def test_units_bytes(self):
        ok = self._text_of_bytes(api.MAX_UNITS_BYTES)
        self.assertEqual(api.build_payload({"text": ok})["n_units"], 14)
        with self.assertRaises(api.TooLarge) as cm:
            api.build_payload({"text": ok + "א"})
        self.assertIn("ארוך מדי לסנכרון", str(cm.exception))

    def test_units_json_matches_browser(self):
        """כמו JSON.stringify: בלי רווחים ובלי escape לעברית."""
        self.assertEqual(api.units_json([{"text": "א ב", "kind": "line"}]),
                         '[{"text":"א ב","kind":"line"}]')

    def test_respond_413(self):
        payload, status = api.respond(json.dumps(
            {"text": "\n".join(["אב"] * 3500)}).encode("utf-8"))
        self.assertEqual(status, 413)
        self.assertIn("יותר מדי שורות", payload["error"])
        # ‏3,000 שורות קצרות — מעבר לגודל ה-JSON (מעטפת label/kind/chunk)
        payload, status = api.respond(json.dumps(
            {"text": "\n".join(["אב"] * api.MAX_UNITS)}).encode("utf-8"))
        self.assertEqual(status, 413)
        self.assertIn("ארוך מדי לסנכרון", payload["error"])

    def test_constants_in_sync_with_worker(self):
        """ההעתק ב-api/ וב-js/cloud.js חייב להישאר מסונכרן עם ה-worker."""
        root = Path(__file__).resolve().parent.parent
        spec = importlib.util.spec_from_file_location(
            "modal_params_sync", root / "modal_worker" / "params.py")
        params = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(params)
        for name in ("MAX_UNITS_BYTES", "MAX_UNITS", "MAX_UNIT_TEXT"):
            self.assertEqual(getattr(api, name), getattr(params, name), name)
        js = (root / "js" / "cloud.js").read_text(encoding="utf-8")
        m = re.search(r"const MAX_UNITS_BYTES = (\d+) \* (\d+);", js)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)) * int(m.group(2)),
                         params.MAX_UNITS_BYTES)


class TestRespond(unittest.TestCase):
    def test_ok(self):
        payload, status = api.respond(
            json.dumps({"text": ASHREI}).encode("utf-8"))
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["segments"]), 4)

    def test_bad_json(self):
        payload, status = api.respond(b"{not json")
        self.assertEqual(status, 400)
        self.assertIn("JSON", payload["error"])

    def test_hebrew_error_message(self):
        payload, status = api.respond(b'{"text": "hello"}')
        self.assertEqual(status, 400)
        self.assertRegex(payload["error"], "[א-ת]")

    def test_max_words_infinity(self):
        payload, status = api.respond(
            '{"text": "אבג", "max_words": 1e999}'.encode("utf-8"))
        self.assertEqual(status, 400)
        self.assertIn("max_words", payload["error"])

    def test_internal_error_hides_details(self):
        def boom(body):
            raise RuntimeError("סוד פנימי /etc/passwd")
        orig, api.build_payload = api.build_payload, boom
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err:
                payload, status = api.respond(b'{"text": "x"}')
        finally:
            api.build_payload = orig
        self.assertEqual(status, 500)
        self.assertNotIn("סוד", payload["error"])
        self.assertRegex(payload["error"], "[א-ת]")
        self.assertIn("סוד פנימי", err.getvalue())

    def test_too_large(self):
        _, status = api.respond(b" " * (api.MAX_BODY_BYTES + 1))
        self.assertEqual(status, 413)


class TestHandler(unittest.TestCase):
    """ה-handler עצמו, עם בקשה מדומה — בלי שרת ובלי רשת."""

    def post(self, raw: bytes, length=None):
        h = api.handler.__new__(api.handler)
        h.headers = {"Content-Length": str(len(raw) if length is None
                                           else length)}
        h.rfile, h.wfile = io.BytesIO(raw), io.BytesIO()
        sent = {}
        h.send_response = lambda code: sent.setdefault("status", code)
        h.send_header = lambda k, v: None
        h.end_headers = lambda: None
        h.do_POST()
        return sent["status"], json.loads(h.wfile.getvalue().decode("utf-8"))

    def test_post_ok(self):
        status, payload = self.post(
            json.dumps({"text": ASHREI, "max_words": 8}).encode("utf-8"))
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["segments"]), 2)

    def test_post_huge_rejected_by_header(self):
        status, payload = self.post(b"{}", length=api.MAX_BODY_BYTES + 1)
        self.assertEqual(status, 413)
        self.assertIn("ארוך", payload["error"])


if __name__ == "__main__":
    unittest.main()
