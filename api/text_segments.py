# -*- coding: utf-8 -*-
"""ה-API של "טקסט חופשי" — פונקציית Vercel (Python, ספריה סטנדרטית בלבד).

POST /api/text_segments   (JSON)
    {"text": "<טקסט מודבק>", "max_words": 4, "mode": "tefila"}

כל שורה בטקסט היא יחידה (kind="line", ‏chunk מזוהה אוטומטית — טעמים אם יש
בה טעמי מקרא, אחרת פיסוק). החיתוך נעשה ב-units_to_segments — אותו מימוש
בדיוק שה-worker מריץ על היחידות (PLAN_TEFILA.md 3.3, ‏4.1.4) — ולכן מה
שהמשתמש רואה בטלפון הוא מה שיסונכרן בענן.

מבנה התשובה כמו /api/segments (‏segments[] עם display, ‏verse, ‏words,
‏letters, ‏verse_end), ובנוסף לכל מקטע label ו-unit, וברמה העליונה units —
היחידות עצמן, לשליחה ל-worker כמו שהן.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner.pipeline import (ALIGN_MODES, _unit_chunk,  # noqa: E402
                              units_to_segments)
from chunker.chunker import _HEBREW_LETTER_RE  # noqa: E402

MAX_CHARS = 100_000
# גוף הבקשה: עד 6 בתים לתו (‏\uXXXX ב-JSON) + מעטפת
MAX_BODY_BYTES = MAX_CHARS * 6 + 4096
_TOO_LONG = {"error": f"הטקסט ארוך מדי — עד {MAX_CHARS:,} תווים"}
DEFAULT_MODE = "tefila"  # טקסט חופשי: מילה לא מנוקדת נקראת (4.1.2)
# מגבלות ה-worker על היחידות (modal_worker/params.py, ‏parse_units) — העתק,
# כי modal_worker/ לא נכלל ב-Vercel (‏.vercelignore); בדיקה שומרת על הסנכרון.
# בודקים כאן, כדי שהמשתמש לא יגלה את הדחייה רק אחרי העלאת הקלטה שלמה.
MAX_UNITS_BYTES = 200 * 1024
MAX_UNITS = 3000
MAX_UNIT_TEXT = 20000


class TooLarge(ValueError):
    """קלט שחורג ממגבלות הגודל — תשובת 413."""


def units_json(units: list) -> str:
    """היחידות כפי שהדפדפן שולח אותן ל-worker (‏JSON.stringify — בלי רווחים)."""
    return json.dumps(units, ensure_ascii=False, separators=(",", ":"))


def check_units_limits(units: list) -> None:
    """אותן מגבלות כמו parse_units ב-worker. זורק TooLarge."""
    if len(units) > MAX_UNITS:
        raise TooLarge(f"יותר מדי שורות ({len(units):,}) — עד {MAX_UNITS:,} "
                       "שורות בסנכרון אחד. פצלו את הטקסט לכמה חלקים")
    for i, unit in enumerate(units, 1):
        if len(unit["text"]) > MAX_UNIT_TEXT:
            raise TooLarge(f"שורה {i} ארוכה מדי ({len(unit['text']):,} תווים)"
                           f" — עד {MAX_UNIT_TEXT:,} תווים בשורה")
    size = len(units_json(units).encode("utf-8"))
    if size > MAX_UNITS_BYTES:
        raise TooLarge(f"הטקסט ארוך מדי לסנכרון ({size // 1024}KB) — עד "
                       f"{MAX_UNITS_BYTES // 1024}KB. פצלו את הטקסט לכמה חלקים")


def text_units(text: str) -> list:
    """טקסט מודבק → יחידות: כל שורה שיש בה אות עברית היא יחידה.

    התווית "שורה N" ממוספרת לפי השורות שנשארו (שורות ריקות לא נספרות).
    ‏chunk נקבע כאן במפורש, כדי שה-worker לא יצטרך לזהות שוב.
    """
    units = []
    for line in text.splitlines():
        line = line.strip()
        if not _HEBREW_LETTER_RE.search(line):
            continue
        unit = {"text": line, "label": f"שורה {len(units) + 1}",
                "kind": "line"}
        unit["chunk"] = _unit_chunk(unit)
        units.append(unit)
    return units


def _read_max_words(raw) -> int:
    if raw is None or raw == "":
        return 4
    try:
        value = int(raw)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"ערך לא תקין בשדה max_words: {raw}")
    return min(max(value, 2), 8)


def segments_payload(units: list, max_words: int, mode: str) -> list:
    """יחידות ⇐ רשימת המקטעים בתשובה (‏display/label/unit/verse/words/
    letters/verse_end). משותף ל-/api/text_segments ול-/api/siddur — אותו
    מבנה בדיוק, ואותו חיתוך (units_to_segments) שה-worker מריץ."""
    segs = units_to_segments(units, max_words, mode=mode)
    segments = []
    for i, seg in enumerate(segs):
        unit_end = i + 1 == len(segs) or segs[i + 1]["unit"] != seg["unit"]
        segments.append({
            "display": seg["display"],
            "label": seg["label"],
            "unit": seg["unit"],
            # ‏verse = מספר היחידה מ-1 — תאימות לממשק שמקבץ לפי verse
            "verse": seg["unit"] + 1,
            "words": len(seg["align_plain"]),
            "letters": sum(len(w) for w in seg["align_plain"]),
            "verse_end": unit_end,
        })
    return segments


def build_payload(body: dict) -> dict:
    """גוף הבקשה (dict) → מבנה ה-JSON המלא של התשובה."""
    if not isinstance(body, dict):
        raise ValueError("גוף הבקשה חייב להיות אובייקט JSON")
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("חסר טקסט")
    if len(text) > MAX_CHARS:
        raise ValueError(_TOO_LONG["error"])
    if not _HEBREW_LETTER_RE.search(text):
        raise ValueError("לא נמצאו אותיות עבריות בטקסט")
    max_words = _read_max_words(body.get("max_words"))
    mode = body.get("mode") or DEFAULT_MODE
    if mode not in ALIGN_MODES:
        raise ValueError(f"מצב לא מוכר: {mode}")

    units = text_units(text)
    check_units_limits(units)
    segments = segments_payload(units, max_words, mode)
    if not segments:
        raise ValueError("לא נמצאו בטקסט מילים לסנכרון"
                         + (" — טקסט לא מנוקד דורש מצב תפילה"
                            if mode == "tanakh" else ""))
    return {
        "mode": mode,
        "max_words": max_words,
        "n_units": len(units),
        "units": units,
        "segments": segments,
    }


def respond(raw: bytes):
    """גוף בקשה גולמי → (payload, status). נפרד מה-handler לבדיקות."""
    if len(raw) > MAX_BODY_BYTES:
        return dict(_TOO_LONG), 413
    try:
        body = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"error": "גוף הבקשה אינו JSON תקין"}, 400
    try:
        return build_payload(body), 200
    except TooLarge as e:
        return {"error": str(e)}, 413
    except ValueError as e:
        return {"error": str(e)}, 400
    except Exception as e:  # noqa: BLE001 — תשובת JSON גם על הפתעות
        # הפרטים ללוג בלבד — לא חושפים חריגות פנימיות למשתמש
        print(f"text_segments: {type(e).__name__}: {e}", file=sys.stderr)
        return {"error": "שגיאה פנימית — נסו שוב מאוחר יותר"}, 500


class handler(BaseHTTPRequestHandler):
    def _send(self, payload: dict, status: int):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802 — השם נדרש ע"י Vercel
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0:
            payload, status = {"error": "כותרת Content-Length לא תקינה"}, 400
        elif length > MAX_BODY_BYTES:
            # לא קוראים גוף ענק לזיכרון — דוחים לפי הכותרת
            payload, status = dict(_TOO_LONG), 413
        else:
            payload, status = respond(self.rfile.read(length))
        self._send(payload, status)

    def do_GET(self):  # noqa: N802
        self._send({"error": "יש לשלוח POST עם JSON: {text, max_words, mode}"},
                   405)
