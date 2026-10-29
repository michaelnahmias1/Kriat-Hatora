# -*- coding: utf-8 -*-
"""ה-API של ספריית התפילות — פונקציית Vercel (Python, ספריה סטנדרטית בלבד).
PLAN_TEFILA.md משימה 4.2.2.

GET /api/siddur                                ⇐ רשימת הנוסחים
GET /api/siddur?nusach=ashkenaz                ⇐ סוגי היום בנוסח
GET /api/siddur?nusach=ashkenaz&path=weekday/shacharit   ⇐ הילדים של הצומת
GET /api/siddur?q=אשרי&nusach=sefard           ⇐ חיפוש (כותרות + מילים ראשונות)
GET /api/siddur?path=<עלה>[&from=N&to=M][&max_words=4]   ⇐ טקסט העלה כיחידות
                                                  + מקטעים (כמו /api/text_segments)

‏path הוא נתיב בקטלוג (data/siddur/catalog.json), מפתחות מופרדים ב-"/". עם
‏nusach אפשר לתת נתיב יחסי לנוסח ("weekday/shacharit") או מלא.

עלה: הטקסט נמשך מ-Sefaria עם ה-ref המדויק מהקטלוג (כמו שהוא — רווח בסוף
כותר הוא חלק מה-ref) ובמהדורה שנבחרה לעלה (‏version=hebrew|<versionTitle>).
‏versions ריק ⇐ שגיאה ברורה; עוברים למהדורה אחרת רק אם הקטלוג רשם אותה לעלה
(‏alt), ואז התשובה אומרת זאת במפורש (‏version_fallback). כל פסקה של Sefaria
מסווגת לחלקים נאמרים (‏kind="paragraph") ולהוראות (‏kind="instruction", מוצגות
ולא מיושרות) — src/siddur/markup.py. החיתוך: units_to_segments, אותו מימוש
שה-worker מריץ. טווח ‏from/to (‏1-based, פסקאות של העלה) — כך מגיעים לקטע
נפוץ שהוא פסקה בתוך עלה גדול (8.25). לעולם לא טווח בין עלים.
"""

import http.client
import importlib.util
import json
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent
_SRC = _API_DIR.parent / "src"
sys.path.insert(0, str(_SRC))


def _load_by_path(name: str, path: Path, package: bool = False):
    """טעינת מודול לפי נתיב מפורש, ורישומו ב-sys.modules בשם name.

    הקובץ הזה נקרא siddur.py — אותו שם כמו החבילה src/siddur. אם תיקיית
    api/ נמצאת ב-sys.path (בבדיקות, ואולי בסביבת הריצה), "import siddur"
    היה מוצא את הקובץ הזה עצמו. לכן החבילה נטענת לפי נתיבה, וכך גם
    api/text_segments.py (בלי להוסיף את api/ ל-sys.path).
    """
    mod = sys.modules.get(name)
    target = path / "__init__.py" if package else path
    if mod is not None and Path(getattr(mod, "__file__", "") or ".").resolve() \
            == target.resolve():
        return mod
    spec = importlib.util.spec_from_file_location(
        name, target, submodule_search_locations=[str(path)] if package else None)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_load_by_path("siddur", _SRC / "siddur", package=True)
_ts = _load_by_path("text_segments", _API_DIR / "text_segments.py")

from aligner.pipeline import _unit_chunk  # noqa: E402
from siddur import load_catalog, split_path  # noqa: E402
from siddur.catalog import is_leaf  # noqa: E402
from siddur.markup import (INSTRUCTION, SPOKEN, classify_paragraph,  # noqa: E402
                           display_word, first_words, flatten, has_vocalized)

TooLarge = _ts.TooLarge
_read_max_words = _ts._read_max_words
check_units_limits = _ts.check_units_limits
segments_payload = _ts.segments_payload

SEFARIA_BASE = "https://www.sefaria.org"
SEFARIA_TIMEOUT = 20          # שניות; ‏maxDuration של הפונקציה — 30
MAX_SEFARIA_BYTES = 8 * 1024 * 1024
# פסקאות בבקשה אחת. העלים הגדולים בקטלוג (29.10.2026): ‏299 (סליחות לצום
# גדליה, אשכנז), ‏297 (מוסף שלוש רגלים, עדות). מגבלת הגודל של ה-worker
# (‏check_units_limits) נבדקת בנפרד.
MAX_PARAGRAPHS = 300
MAX_SEARCH_RESULTS = 30
MAX_QUERY_CHARS = 100
FIRST_WORDS = 5
MODE = "tefila"               # מילה לא מנוקדת נקראת, שם ה׳ של הסידור (4.1.2)
CACHE_TEXT = "public, max-age=3600, s-maxage=604800"   # כמו /api/segments
CACHE_CATALOG = "public, max-age=3600, s-maxage=86400"  # משתנה רק בפריסה
USER_AGENT = ("Kriat-Hatora/1.0 "
              "(+https://github.com/michaelnahmias1/Kriat-Hatora)")


class ApiError(Exception):
    """שגיאה עם סטטוס HTTP והודעה בעברית; extra נכנס לגוף התשובה."""

    def __init__(self, status: int, message: str, **extra):
        super().__init__(message)
        self.status, self.extra = status, extra


class EmptyVersion(LookupError):
    """‏Sefaria ענתה 200 עם versions ריק — אין טקסט בעלה במהדורה הזו."""


# --- רשת -----------------------------------------------------------------------

def _get_json(url: str, params: dict = None):
    """GET ל-Sefaria ⇐ JSON. נקודת ההחלפה של הבדיקות (בלי רשת)."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=SEFARIA_TIMEOUT) as resp:
        body = resp.read(MAX_SEFARIA_BYTES + 1)
    if len(body) > MAX_SEFARIA_BYTES:
        raise ApiError(502, "התשובה של Sefaria גדולה מדי")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ApiError(502, "Sefaria החזירה תשובה שאינה JSON תקין")


def fetch_leaf(ref: str, version_title: str):
    """הטקסט של עלה במהדורה אחת ⇐ (פסקאות, אובייקט הגרסה מ-Sefaria).

    ה-ref נשלח כמו שהוא (‏quote שומר רווחים כ-%20 — גם רווח בסוף כותר).
    """
    # כמו tools/survey_siddur.py (‏safe="") — אותן כתובות שנבדקו בבניית הקטלוג
    url = f"{SEFARIA_BASE}/api/v3/texts/{urllib.parse.quote(ref, safe='')}"
    data = _get_json(url, {"version": f"hebrew|{version_title}"})
    versions = data.get("versions") if isinstance(data, dict) else None
    if not versions:
        raise EmptyVersion(version_title)
    ver = versions[0]
    if not isinstance(ver, dict) or ver.get("versionTitle") != version_title:
        # לא מקבלים בשקט מהדורה אחרת ממה שביקשנו
        raise EmptyVersion(version_title)
    return flatten(ver.get("text")), ver


def _sefaria_error(e: Exception) -> ApiError:
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 404:
            return ApiError(502, "Sefaria לא מצאה טקסט לקטע הזה (404) — "
                                 "ייתכן שהמבנה שלה השתנה מאז שנבנה הקטלוג")
        return ApiError(502, f"תקלה בגישה ל-Sefaria (HTTP {e.code})")
    reason = getattr(e, "reason", e)
    if isinstance(e, (socket.timeout, TimeoutError)) or isinstance(
            reason, (socket.timeout, TimeoutError)):
        return ApiError(504, f"Sefaria לא ענתה בזמן ({SEFARIA_TIMEOUT} "
                             "שניות) — נסו שוב בעוד רגע")
    return ApiError(502, "תקלה בגישה ל-Sefaria — נסו שוב בעוד רגע")


# --- קטלוג: ניווט וחיפוש ---------------------------------------------------------

def _keys(cat, q: dict) -> list:
    """nusach + path ⇐ נתיב מלא בקטלוג (רשימת מפתחות)."""
    nusach = (q.get("nusach") or "").strip()
    keys = split_path(q.get("path"))
    if nusach:
        if cat.node([nusach]) is None:
            raise ApiError(404, f"נוסח לא מוכר: {nusach}")
        if not keys or keys[0] != nusach:
            if keys and cat.node([keys[0]]) is not None:
                raise ApiError(400, f"הנתיב שייך לנוסח {keys[0]} ולא ל-{nusach}")
            keys = [nusach] + keys
    return keys


def _crumbs(cat, keys: list) -> list:
    out, level = [], cat.nusachim
    for i, k in enumerate(keys):
        node = next(c for c in level if c.get("key") == k)
        out.append({"key": k, "path": "/".join(keys[:i + 1]),
                    "title": node.get("heTitle", "")})
        level = node.get("children") or []
    return out


def _available(cat, path: str, node: dict) -> bool:
    if is_leaf(node):
        return not node.get("unavailable") and bool(node.get("v"))
    return any(not n.get("unavailable") and n.get("v")
               for _, n in cat.leaves(path))


def _item(cat, path: str, node: dict) -> dict:
    item = {"key": node["key"], "path": path,
            "title": node.get("heTitle", ""), "title_en": node.get("title", ""),
            "is_leaf": is_leaf(node), "available": _available(cat, path, node)}
    if is_leaf(node):
        if node.get("first"):
            item["first_words"] = node["first"]
    else:
        item["count"] = len(node["children"])
    return item


def children_payload(cat, keys: list) -> dict:
    if keys:
        node = cat.node(keys)
        if node is None:
            raise ApiError(404, "הנתיב לא נמצא בקטלוג הסידור: " + "/".join(keys))
        level = node["children"]
    else:
        node, level = None, cat.nusachim
    base = "/".join(keys)
    return {
        "nusach": keys[0] if keys else None,
        "path": base,
        "title": node.get("heTitle", "") if node else "",
        "breadcrumb": _crumbs(cat, keys),
        "children": [_item(cat, (base + "/" if base else "") + c["key"], c)
                     for c in level],
    }


def search_payload(cat, q: dict) -> dict:
    query = (q.get("q") or "").strip()
    if not query:
        raise ApiError(400, "חסר טקסט לחיפוש")
    if len(query) > MAX_QUERY_CHARS:
        raise ApiError(400, f"טקסט החיפוש ארוך מדי — עד {MAX_QUERY_CHARS} תווים")
    keys = _keys(cat, {"nusach": q.get("nusach")})
    nusach = keys[0] if keys else None
    found = cat.search(query, nusach=nusach, limit=MAX_SEARCH_RESULTS + 1)
    results = []
    for r in found[:MAX_SEARCH_RESULTS]:
        item = _item(cat, r["path"], cat.node(r["path"]))
        item["breadcrumb"] = r["breadcrumb"]
        item["match"] = r["match"]  # "title" | "first"
        results.append(item)
    return {"q": query, "nusach": nusach, "results": results,
            "truncated": len(found) > MAX_SEARCH_RESULTS,
            "limit": MAX_SEARCH_RESULTS}


# --- עלה: טקסט ⇐ יחידות ⇐ מקטעים ---------------------------------------------

def _read_pos(q: dict, name: str):
    raw = (q.get(name) or "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(400, f"ערך לא תקין בשדה {name}: {raw}")
    if value < 1:
        raise ApiError(400, f"ערך חייב להיות חיובי בשדה {name}")
    return value


def _paragraph_info(n: int, parts: list) -> dict:
    kinds = {k for k, _ in parts}
    if not parts:
        kind = "empty"
    elif kinds == {SPOKEN}:
        kind = "paragraph"
    elif kinds == {INSTRUCTION}:
        kind = "instruction"
    else:
        kind = "mixed"
    spoken = [b for k, b in parts if k == SPOKEN]
    if spoken:
        fw = first_words(spoken, FIRST_WORDS)
    else:  # הוראה — תחילתה, לתצוגה בבחירת הטווח
        fw = " ".join(display_word(w) for w in
                      " ".join(b for _, b in parts).split()[:FIRST_WORDS])
    return {"n": n, "kind": kind, "first_words": fw}


def _fetch_with_policy(cat, keys: list, leaf: dict, src: dict):
    """המהדורה שנבחרה לעלה; אם versions ריק — רק מהדורות ש-alt של הקטלוג
    רושם לעלה, ובמפורש. ⇐ (פסקאות, גרסה, version_id, fallback)."""
    versions = cat.nusach_of(keys)["versions"]
    tried = []
    for vid in [src["version_id"]] + list(leaf.get("alt", [])):
        title = versions[vid]["title"]
        try:
            paragraphs, ver = fetch_leaf(src["ref"], title)
        except EmptyVersion:
            tried.append(title)
            continue
        except (OSError, http.client.HTTPException) as e:  # רשת, timeout
            raise _sefaria_error(e)
        fallback = None
        if tried:
            fallback = {"requested": tried[0], "used": title,
                        "reason": "Sefaria החזירה versions ריק במהדורה "
                                  "שנבחרה; המהדורה החלופית רשומה בקטלוג לעלה"}
        return paragraphs, ver, vid, fallback
    names = ", ".join(f"«{t.strip()}»" for t in tried)
    raise ApiError(502, f"Sefaria לא החזירה טקסט לקטע «{leaf.get('heTitle', '')}» "
                        f"במהדורה {names} (versions ריק). לא עוברים בשקט "
                        "למהדורה אחרת — כנראה הנתונים ב-Sefaria השתנו, וצריך "
                        "לבנות מחדש את הקטלוג")


def leaf_payload(cat, keys: list, q: dict) -> dict:
    leaf = cat.leaf(keys)
    path = "/".join(keys)
    src = cat.source(keys)
    if src is None:
        raise ApiError(404, "הקטע הזה לא זמין ב-Sefaria במהדורות שנבחרו לנוסח"
                       + (f" ({leaf['note']})" if leaf.get("note") else ""))
    max_words = _read_max_words(q.get("max_words"))
    start, end = _read_pos(q, "from"), _read_pos(q, "to")

    paragraphs, ver, vid, fallback = _fetch_with_policy(cat, keys, leaf, src)
    parts = [classify_paragraph(p) for p in paragraphs]
    info = [_paragraph_info(n, ps) for n, ps in enumerate(parts, 1)]

    total = len(paragraphs)
    if total == 0:
        raise ApiError(502, "Sefaria החזירה עלה בלי פסקאות")
    start = start or 1
    end = end or total
    if start > end or end > total:
        raise ApiError(400, f"טווח פסקאות לא תקין ({start}–{end}) — בקטע "
                            f"«{leaf.get('heTitle', '')}» יש {total} פסקאות",
                       paragraphs=info)
    if end - start + 1 > MAX_PARAGRAPHS:
        raise ApiError(413, f"הקטע ארוך מדי לסנכרון אחד ({end - start + 1} "
                            f"פסקאות) — עד {MAX_PARAGRAPHS}. בחרו טווח "
                            "פסקאות (from/to)", paragraphs=info)

    he_title = leaf.get("heTitle", "")
    units = []
    for n in range(start, end + 1):
        for kind, body in parts[n - 1]:
            unit = {"text": body, "label": f"{he_title} · {n}",
                    "kind": "paragraph" if kind == SPOKEN else "instruction"}
            if kind == SPOKEN:
                unit["chunk"] = _unit_chunk(unit)  # טעמים/פיסוק — 8.24
            units.append(unit)
    try:
        check_units_limits(units)
    except TooLarge as e:
        raise ApiError(413, f"{e} (בחרו טווח פסקאות קצר יותר — from/to)",
                       paragraphs=info)
    segments = segments_payload(units, max_words, MODE)
    if not segments:
        if not has_vocalized(paragraphs):
            # הכלל "לא מנוקד ⇐ הוראה" לא מבחין כאן בין הלכה לתפילה (למשל
            # "קידושא רבה" בדעת). לא מנחשים — אומרים, ונותנים את הטקסט.
            raise ApiError(
                422, f"הקטע «{he_title}» במהדורה «{ver.get('versionTitle', '').strip()}» "
                     "אינו מנוקד כלל, ולכן אי אפשר להבחין בין הוראות לטקסט "
                     "הנאמר — הכל מוצג כהוראות. אפשר להעתיק אותו לטקסט חופשי "
                     "ולסנכרן משם", unvocalized=True, units=units,
                paragraphs=info)
        raise ApiError(400, "בטווח שנבחר אין טקסט נאמר לסנכרון — רק הוראות",
                       units=units, paragraphs=info)
    lic = cat.nusach_of(keys)["versions"][vid].get("license") or \
        ver.get("license") or "unknown"
    return {
        "mode": MODE,
        "max_words": max_words,
        "n_units": len(units),
        "units": units,
        "segments": segments,
        "path": path,
        "nusach": keys[0],
        "title": he_title,
        "title_en": leaf.get("title", ""),
        "breadcrumb": _crumbs(cat, keys),
        "ref": src["ref"],
        "version": ver.get("versionTitle"),
        "license": lic,
        "version_fallback": fallback,
        "source_url": f"{SEFARIA_BASE}/{urllib.parse.quote(src['ref'])}",
        "range": {"from": start, "to": end, "total": total},
        "paragraphs": info,
    }


# --- ניתוב ------------------------------------------------------------------------

def build_payload(q: dict, cat=None):
    """פרמטרי השאילתה ⇐ (payload, Cache-Control)."""
    cat = cat or load_catalog()
    if "q" in q:
        return search_payload(cat, q), CACHE_CATALOG
    keys = _keys(cat, q)
    node = cat.node(keys) if keys else None
    if keys and node is None:
        raise ApiError(404, "הנתיב לא נמצא בקטלוג הסידור: " + "/".join(keys))
    if node is not None and is_leaf(node):
        return leaf_payload(cat, keys, q), CACHE_TEXT
    if q.get("from") or q.get("to"):
        raise ApiError(400, "טווח פסקאות (from/to) אפשרי רק בקטע — לא בתיקייה")
    return children_payload(cat, keys), CACHE_CATALOG


def respond(query: str, cat=None):
    """מחרוזת שאילתה ⇐ (payload, status, headers). נפרד מה-handler לבדיקות."""
    q = {k: v[0] for k, v in urllib.parse.parse_qs(
        query or "", keep_blank_values=True).items()}
    try:
        payload, cache = build_payload(q, cat)
        return payload, 200, {"Cache-Control": cache}
    except ApiError as e:
        payload, status = {"error": str(e)}, e.status
        payload.update(e.extra)
    except ValueError as e:  # ‏max_words לא תקין וכד׳ (הודעה בעברית)
        payload, status = {"error": str(e)}, 400
    except (OSError, http.client.HTTPException) as e:  # רשת (בטחון נוסף)
        err = _sefaria_error(e)
        payload, status = {"error": str(err)}, err.status
    except Exception as e:  # noqa: BLE001 — תשובת JSON גם על הפתעות
        print(f"siddur: {type(e).__name__}: {e}", file=sys.stderr)
        payload, status = {"error": "שגיאה פנימית — נסו שוב מאוחר יותר"}, 500
    # שגיאה (גם תקלה זמנית ב-Sefaria) לא נשמרת ב-CDN
    return payload, status, {"Cache-Control": "no-store"}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 — השם נדרש ע"י Vercel
        payload, status, headers = respond(urllib.parse.urlparse(self.path).query)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
