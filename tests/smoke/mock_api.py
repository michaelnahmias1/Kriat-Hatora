# -*- coding: utf-8 -*-
"""מוק ל-/api/* עבור בדיקת העשן (tests/smoke/smoke.mjs) — בלי רשת.

מריץ את build_payload האמיתי של api/segments.py ו-api/structure.py, רק
שהקריאות ל-Sefaria מוחלפות בנתונים קבועים; ו-api/text_segments.py (טקסט
חופשי) כמו שהוא — הוא ממילא לא יוצא לרשת. כך התשובה שהדפדפן מקבל בבדיקה
היא בדיוק במבנה של הפרודקשן, כולל החיתוך האמיתי של src/chunker.

שימוש: python3 mock_api.py segments|structure|text_segments '<json של הפרמטרים / גוף ה-POST>'
מדפיס: {"status": <קוד>, "body": <תשובה>}
"""

import importlib.util
import json
import sys
from pathlib import Path
from unittest import mock
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent.parent

# פסוקים בסגנון MAM (בראשית א:א–ג) — מוחזרים במחזוריות לכל טווח שמתבקש
VERSES = [
    "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃",
    "וְהָאָ֗רֶץ הָיְתָ֥ה תֹ֙הוּ֙ וָבֹ֔הוּ וְחֹ֖שֶׁךְ עַל־פְּנֵ֣י תְה֑וֹם "
    "וְר֣וּחַ אֱלֹהִ֔ים מְרַחֶ֖פֶת עַל־פְּנֵ֥י הַמָּֽיִם׃",
    "וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃",
]

# מספר הפסוקים בכל פרק — בראשית ושמות כמו ב-Sefaria; שאר הספרים: 10 פרקים × 30
SHAPES = {
    "Genesis": [31, 25, 24, 26, 32, 22, 24, 22, 29, 32, 32, 20, 18, 24, 21, 16,
                27, 33, 38, 18, 34, 24, 20, 67, 34, 35, 46, 22, 35, 43, 55, 32,
                20, 31, 29, 43, 36, 30, 23, 23, 57, 38, 34, 34, 28, 34, 31, 22,
                33, 26],
    "Exodus": [22, 25, 22, 31, 23, 30, 25, 32, 35, 29, 10, 51, 22, 31, 27, 36,
               16, 27, 25, 26, 36, 31, 33, 18, 40, 37, 21, 43, 46, 38, 18, 35,
               23, 35, 35, 38, 29, 31, 43, 38],
}


def _load(name):
    spec = importlib.util.spec_from_file_location(
        "api_" + name, ROOT / "api" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _count_verses(ref):
    # "Genesis 1:1-5" / "Exodus 13:17-14:8" / "Genesis 1"
    tail = ref.rsplit(" ", 1)[-1]
    if ":" not in tail:
        return 3
    a, _, b = tail.partition("-")
    if not b:
        return 1
    if ":" in b:
        return 4  # חוצה-פרקים: מספיק לבדיקה
    return max(1, int(b) - int(a.split(":")[1]) + 1)


def segments(q):
    api = _load("segments")

    def fake_get_json(url, params=None):
        if "/api/texts/versions/" in url:
            return [{"versionTitle": "Miqra according to the Masorah", "language": "he"}]
        if "/api/v3/texts/" in url:
            ref = unquote(url.split("/api/v3/texts/", 1)[1])
            n = _count_verses(ref)
            return {"versions": [{"text": [VERSES[i % len(VERSES)] for i in range(n)]}]}
        raise AssertionError(url)

    with mock.patch.object(api, "_get_json", side_effect=fake_get_json):
        try:
            return 200, api.build_payload(q)
        except ValueError as e:
            return 400, {"error": str(e)}


def structure(q):
    api = _load("structure")

    def fake_get_json(url):
        en = unquote(url.rsplit("/", 1)[1])
        return [{"chapters": SHAPES.get(en, [30] * 10)}]

    with mock.patch.object(api, "_get_json", side_effect=fake_get_json):
        try:
            return 200, api.build_payload(q)
        except ValueError as e:
            return 400, {"error": str(e)}


def text_segments(q):
    # בלי רשת בכלל — ה-respond האמיתי על גוף ה-POST כמו שהוא
    api = _load("text_segments")
    payload, status = api.respond(json.dumps(q, ensure_ascii=False).encode("utf-8"))
    return status, payload


if __name__ == "__main__":
    kind, q = sys.argv[1], json.loads(sys.argv[2])
    status, body = {"segments": segments, "structure": structure,
                    "text_segments": text_segments}[kind](q)
    sys.stdout.write(json.dumps({"status": status, "body": body}, ensure_ascii=False))
