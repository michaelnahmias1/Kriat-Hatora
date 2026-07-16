# -*- coding: utf-8 -*-
"""ה-API של הממשק הקבוע — פונקציית Vercel (Python, ספריה סטנדרטית בלבד).

GET /api/segments?book=בראשית&chapter=1&verse_start=1&verse_end=5&max_words=4

משיכת גרסת MAM מ-Sefaria נעשית כאן, בצד השרת: הדפדפן בטלפון מדבר רק עם
הדומיין שלנו (אין תלות ב-CORS של Sefaria), ומימוש החיתוך נשאר יחיד —
src/chunker משרת גם את הממשק וגם את מסלול ה-Colab.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from chunker import segments_for_pipeline  # noqa: E402

SEFARIA_BASE = "https://www.sefaria.org"
TORAH_BOOKS = {
    "בראשית": "Genesis", "שמות": "Exodus", "ויקרא": "Leviticus",
    "במדבר": "Numbers", "דברים": "Deuteronomy",
}

# cache ברמת המודול — שורד בין קריאות על אותה פונקציה חמה
_version_cache = {}


def _get_json(url: str, params: dict = None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Kriat-Hatora/1.0 (+https://github.com/michaelnahmias1/Kriat-Hatora)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_mam_version(book: str) -> str:
    """שם גרסת MAM המדויק בספר — לא מניחים שם מהזיכרון (PLAN, סעיף 2)."""
    if book in _version_cache:
        return _version_cache[book]
    versions = _get_json(
        f"{SEFARIA_BASE}/api/texts/versions/{urllib.parse.quote(book)}")
    for v in versions:
        title = v.get("versionTitle", "")
        if v.get("language") == "he" and (
                "masorah" in title.lower() or "מסורה" in title):
            _version_cache[book] = title
            return title
    raise LookupError(f"לא נמצאה גרסת MAM לספר {book}")


def _flatten(nested):
    """טקסט מ-Sefaria יכול להגיע מקונן (טווח חוצה-פרקים) — משטחים לפי הסדר."""
    if isinstance(nested, str):
        return [nested]
    out = []
    for item in nested:
        out.extend(_flatten(item))
    return out


def build_ref(book, chapter, verse_start=None, chapter_end=None, verse_end=None):
    """בונה ref של Sefaria: פרק שלם, טווח בתוך פרק, או טווח חוצה-פרקים (עלייה)."""
    ref = f"{book} {chapter}"
    if verse_start:
        ref += f":{verse_start}"
        if chapter_end and chapter_end != chapter:
            ref += f"-{chapter_end}:{verse_end or 1}"
        elif verse_end:
            ref += f"-{verse_end}"
    return ref


def fetch_verses(ref: str, version_title: str) -> list:
    data = _get_json(
        f"{SEFARIA_BASE}/api/v3/texts/{urllib.parse.quote(ref)}",
        {"version": f"hebrew|{version_title}"})
    versions = data.get("versions") or []
    if not versions:
        raise LookupError(f"לא הגיעו פסוקים עבור {ref}")
    verses = [v for v in _flatten(versions[0]["text"]) if v and v.strip()]
    if not verses:
        raise LookupError(f"לא הגיעו פסוקים עבור {ref}")
    return verses


def _read_int(q: dict, name: str, required: bool = False):
    raw = (q.get(name) or "").strip()
    if not raw:
        if required:
            raise ValueError(f"חסר ערך בשדה {name}")
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"ערך לא תקין בשדה {name}: {raw}")
    if value < 1:
        raise ValueError(f"ערך חייב להיות חיובי בשדה {name}")
    return value


def build_payload(q: dict) -> dict:
    """פרמטרי השאילתה → מבנה ה-JSON המלא של התשובה."""
    book = (q.get("book") or "").strip()
    if not book:
        raise ValueError("חסר שם ספר")
    book_en = TORAH_BOOKS.get(book, book)

    chapter = _read_int(q, "chapter", required=True)
    verse_start = _read_int(q, "verse_start")
    verse_end = _read_int(q, "verse_end")
    chapter_end = _read_int(q, "chapter_end")
    max_words = min(max(_read_int(q, "max_words") or 4, 2), 8)
    if chapter_end and chapter_end != chapter and not verse_start:
        raise ValueError("טווח חוצה-פרקים דורש פסוק התחלה")

    version = find_mam_version(book_en)
    ref = build_ref(book_en, chapter, verse_start, chapter_end, verse_end)
    verses = fetch_verses(ref, version)

    # מספור הפסוקים סדרתי מפסוק ההתחלה; בטווח חוצה-פרקים זהו מספר סידורי
    # בתוך הטווח (תווית תצוגה בלבד — לא משפיע על החיתוך או על ה-SRT).
    first = verse_start or 1
    segments = []
    for vi, verse in enumerate(verses):
        segs = segments_for_pipeline(verse, max_words)
        for si, seg in enumerate(segs):
            segments.append({
                "display": seg["display"],
                "verse": first + vi,
                "words": len(seg["align_plain"]),
                "letters": sum(len(w) for w in seg["align_plain"]),
                "verse_end": si == len(segs) - 1,
            })
    if not segments:
        raise LookupError(f"לא נמצאו מילים בטווח {ref}")
    return {
        "ref": ref,
        "version": version,
        "book": book,
        "n_verses": len(verses),
        "max_words": max_words,
        "segments": segments,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 — השם נדרש ע"י Vercel
        query = urllib.parse.urlparse(self.path).query
        q = {k: v[0] for k, v in urllib.parse.parse_qs(query).items()}
        headers = {}
        try:
            payload, status = build_payload(q), 200
            # טקסט מקראי לא משתנה — נותנים ל-CDN של Vercel לשמור תשובות
            headers["Cache-Control"] = "public, max-age=3600, s-maxage=604800"
        except ValueError as e:
            payload, status = {"error": str(e)}, 400
        except LookupError as e:
            payload, status = {"error": str(e)}, 404
        except urllib.error.URLError as e:
            payload, status = {"error": f"תקלה בגישה ל-Sefaria: {e}"}, 502
        except Exception as e:  # noqa: BLE001 — תשובת JSON גם על הפתעות
            payload, status = {"error": f"שגיאה פנימית: {e}"}, 500

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
