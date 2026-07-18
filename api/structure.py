# -*- coding: utf-8 -*-
"""מבנה הספר — כמה פרקים, וכמה פסוקים בכל פרק.

GET /api/structure?book=בראשית
  → {"book": "בראשית", "chapters": [31, 25, 24, ...]}

הממשק משתמש בזה כדי לבנות את תפריטי הבחירה (פרק/פסוק) באותיות, כך שאפשר
לבחור רק פרק ופסוק שקיימים באמת. הנתונים נמשכים מ-Sefaria (api/shape) — אותה
חלוקת פרקים/פסוקים שממנה נמשך הטקסט עצמו, כדי שהמספור תמיד יתאים.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

SEFARIA_BASE = "https://www.sefaria.org"
TORAH_BOOKS = {
    "בראשית": "Genesis", "שמות": "Exodus", "ויקרא": "Leviticus",
    "במדבר": "Numbers", "דברים": "Deuteronomy",
}

# cache ברמת המודול — שורד בין קריאות על אותה פונקציה חמה
_shape_cache = {}


def _get_json(url: str):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Kriat-Hatora/1.0 (+https://github.com/michaelnahmias1/Kriat-Hatora)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chapters_for_book(book_en: str) -> list:
    """רשימת מספר הפסוקים בכל פרק בספר (לפי חלוקת Sefaria)."""
    if book_en in _shape_cache:
        return _shape_cache[book_en]
    data = _get_json(f"{SEFARIA_BASE}/api/shape/{urllib.parse.quote(book_en)}")
    entry = data[0] if isinstance(data, list) else data
    chapters = entry.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise LookupError(f"לא התקבל מבנה פרקים עבור {book_en}")
    chapters = [int(c) for c in chapters]
    _shape_cache[book_en] = chapters
    return chapters


def build_payload(q: dict) -> dict:
    book = (q.get("book") or "").strip()
    if not book:
        raise ValueError("חסר שם ספר")
    book_en = TORAH_BOOKS.get(book, book)
    chapters = chapters_for_book(book_en)
    return {"book": book, "chapters": chapters}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 — השם נדרש ע"י Vercel
        query = urllib.parse.urlparse(self.path).query
        q = {k: v[0] for k, v in urllib.parse.parse_qs(query).items()}
        headers = {}
        try:
            payload, status = build_payload(q), 200
            # מבנה הספר קבוע — נותנים ל-CDN של Vercel לשמור תשובות
            headers["Cache-Control"] = "public, max-age=86400, s-maxage=604800"
        except ValueError as e:
            payload, status = {"error": str(e)}, 400
        except LookupError as e:
            payload, status = {"error": str(e)}, 404
        except urllib.error.HTTPError as e:
            payload, status = {"error": f"תקלה בגישה ל-Sefaria: {e}"}, 502
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
