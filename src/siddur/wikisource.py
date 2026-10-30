# -*- coding: utf-8 -*-
"""מקור טקסט שני לקטלוג הסידור: ויקיטקסט העברי (PLAN_TEFILA.md 4.4.1).

ספריה סטנדרטית בלבד (רץ גם בפונקציית Vercel, ‏api/siddur.py, וגם בבונה הקטלוג,
‏tools/build_siddur_catalog.py — מימוש יחיד לשניהם).

עלה מוויקיטקסט = **סעיף אחד בדף, בגרסה (oldid) קבועה**: ‏{page, rev, section,
heading}. בונה הקטלוג מושך את הדף המוצג (HTML מורחב — התבניות כבר מוחלות),
מפצל לסעיפים וממיר כאן לפסקאות במבנה ש-src/siddur/markup.py מכיר מ-Sefaria:
‏<b>, ‏<small>, ‏<br>, וכל השאר טקסט — כך אותו סיווג הוראות (8.4) רץ על שני
המקורות. הפסקאות נשמרות בצילום בגיט (data/siddur/wikisource/<rev>.json.gz),
ו-api/siddur.py מגיש מהצילום, **בלי רשת**. ההמרה של סעיף בודד מתשובת
‏action=parse (section_paragraphs) נשארה לבדיקה מול ה-API האמיתי.

למה oldid קבוע: הדף ממשיך להיערך בוויקיטקסט; מספרי הסעיפים והטקסט של גרסה
מסוימת לא משתנים, כך שהקטלוג (כותרות, מילים ראשונות, מספר פסקאות) נשאר נכון
וה-CDN יכול לשמור את התשובה. עדכון לגרסה חדשה = בנייה מחדש של הקטלוג.

ההמרה (נבדקה על סידור "מהדורת מרדכי שליח ציבור", עדות המזרח, 29.10.2026):
- פסקה = גוש בין שתי שורות ריקות (‏<br><br>), ‏<p>, ‏<div> או ‏<li>.
- ‏<span style="font-size:83%"> (תבנית "קטן") ו-‏<small> ⇐ ‏<small>: הוראה כשאינה
  מנוקדת, טקסט נאמר בלחש כשהיא מנוקדת — הכלל של markup.py.
- כותרת הסעיף (‏<h2>…<h6> הראשונה) היא שם העלה, לא טקסט; כותרת נוספת (תת-סעיף)
  ⇐ סוף העלה: תת-הסעיפים הם עלים משלהם.
- נזרקים: הערות שוליים (‏sup.reference), רשימות הערות, קישורי עריכה, ‏<style>,
  ‏<script>, טבלאות ניווט, ושילובי שמות של קבלה שאינם נאמרים ("יאהדונהי").
"""

import gzip
import html
import json
import re
import unicodedata
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

API_URL = "https://he.wikisource.org/w/api.php"
SITE = "https://he.wikisource.org"
NAME = "ויקיטקסט"
LICENSE = "CC-BY-SA"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/deed.he"
LICENSE_NAME = "CC BY-SA 4.0"

_HEADINGS = frozenset("h1 h2 h3 h4 h5 h6".split())
_SKIP_TAGS = frozenset("style script table sup ol math figure".split())
_SKIP_CLASSES = frozenset(("mw-editsection reference references mw-references-wrap "
                           "noprint navbox mw-cite-backlink metadata "
                           "mw-empty-elt").split())
_BLOCK_TAGS = frozenset("p div li ul dl dd dt blockquote center section".split())
_VOID = frozenset("br hr img wbr meta link input col area base source".split())
_SMALL_RE = re.compile(r"font-size\s*:\s*(?:(\d+(?:\.\d+)?)\s*%|smaller|small|x-small)",
                       re.I)
# שילובי שמות (כוונות) — מופיעים אחרי שם ה׳, לא נאמרים
_KAVANA_RE = re.compile(r"(?<![א-ת])(?:יאהדונהי|אהדונהי|יאהדונה|יהוה אדני)(?![א-ת])")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_SPACE_PUNCT_RE = re.compile(r" +([,.:;׃])")


class WikisourceError(RuntimeError):
    """תשובה לא צפויה מה-API של ויקיטקסט (הודעה בעברית)."""


def page_url(page: str, rev: int = None, anchor: str = None) -> str:
    """קישור קבוע לדף (לגרסה מסוימת, כשיש rev) — לשורת המקור והרישיון."""
    title = page.replace(" ", "_")
    if rev:
        url = (f"{SITE}/w/index.php?title={urllib.parse.quote(title)}"
               f"&oldid={int(rev)}")
    else:
        url = f"{SITE}/wiki/{urllib.parse.quote(title)}"
    if anchor:
        url += "#" + urllib.parse.quote(anchor.replace(" ", "_"))
    return url


def history_url(page: str) -> str:
    """רשימת התורמים (היסטוריית הדף) — חלק מהייחוס של CC-BY-SA."""
    return (f"{SITE}/w/index.php?title="
            f"{urllib.parse.quote(page.replace(' ', '_'))}&action=history")


def parse_params(rev: int, section) -> dict:
    """פרמטרי ‏action=parse לסעיף אחד בגרסה קבועה."""
    return {"action": "parse", "oldid": str(int(rev)), "section": str(section),
            "prop": "text", "format": "json", "formatversion": "2",
            "disableeditsection": "1", "disablelimitreport": "1",
            "disabletoc": "1"}


def _is_small(attrs: dict) -> bool:
    m = _SMALL_RE.search(attrs.get("style") or "")
    if not m:
        return False
    return m.group(1) is None or float(m.group(1)) < 100


class _Converter(HTMLParser):
    """HTML של סעיף ⇐ (כותרת, [פסקאות במבנה Sefaria])."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = None
        self._in_heading = 0
        self._heading_buf = []
        self.done = False
        self.paragraphs = []
        self._cur = []          # חלקי HTML של הפסקה הנוכחית
        self._stack = []        # [(tag, emitted_close or None, skip)]
        self._skip = 0
        self._pending_br = 0    # מעברי שורה שעוד לא נכתבו (שניים ⇐ פסקה)

    # --- פסקאות -----------------------------------------------------------
    def _has_text(self) -> bool:
        return any(not p.startswith("<") and p.strip() for p in self._cur)

    def _break(self):
        self._pending_br = 0
        if self._has_text():
            closing = [c for _, c, _, o in reversed(self._stack) if o]
            self.paragraphs.append(_tidy("".join(self._cur + closing)))
        # תגיות פתוחות (small/b) נמשכות לפסקה הבאה
        self._cur = [o for _, _, _, o in self._stack if o]

    def _flush_br(self):
        if self._pending_br >= 2:
            self._break()
        elif self._pending_br == 1 and self._has_text():
            self._cur.append("<br>")
        self._pending_br = 0

    # --- HTMLParser -----------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        a = {k: (v or "") for k, v in attrs}
        classes = set(a.get("class", "").split())
        if tag in _HEADINGS:
            if self.heading is None and not self._in_heading:
                self._in_heading = 1
                self._heading_buf = []
                return
            if not self._in_heading:
                self._break()
                self.done = True  # תת-סעיף — עלה משלו
                return
        if tag in _VOID:
            if tag == "br" and not self._skip and not self._in_heading:
                self._pending_br += 1
            return
        skip = bool(self._skip) or tag in _SKIP_TAGS or bool(classes & _SKIP_CLASSES)
        open_html = close_html = None
        if not skip and not self._in_heading:
            if tag in _BLOCK_TAGS:
                self._flush_br()
                self._break()
            elif tag == "small" or (tag == "span" and _is_small(a)):
                open_html, close_html = "<small>", "</small>"
            elif tag in ("b", "strong"):
                open_html, close_html = "<b>", "</b>"
        if skip:
            self._skip += 1
        if open_html:
            self._flush_br()
            self._cur.append(open_html)
        self._stack.append((tag, close_html, skip, open_html))

    def handle_endtag(self, tag):
        if self.done:
            return
        if tag in _HEADINGS and self._in_heading:
            self._in_heading = 0
            self.heading = _tidy_text("".join(self._heading_buf))
            return
        if tag in _VOID:
            return
        # סוגרים עד התגית המתאימה (HTML של MediaWiki מאוזן, אבל ליתר ביטחון)
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                for t, close_html, skip, _ in reversed(self._stack[i:]):
                    if skip:
                        self._skip -= 1
                    elif close_html:
                        self._cur.append(close_html)
                    elif t in _BLOCK_TAGS and not self._skip:
                        self._flush_br()
                        self._break()
                del self._stack[i:]
                break

    def handle_data(self, data):
        if self.done:
            return
        if self._in_heading:
            if not self._skip:
                self._heading_buf.append(data)
            return
        if self._skip:
            return
        if not data.strip():
            if data and self._cur and not self._cur[-1].endswith(" "):
                self._cur.append(" ")
            return
        self._flush_br()
        text = _KAVANA_RE.sub(" ", data)
        self._cur.append(html.escape(text, quote=False))

    def close(self):
        super().close()
        if not self.done:
            self._flush_br()
            self._break()


def _tidy_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return _WS_RE.sub(" ", s.replace("\n", " ")).strip()


_EMPTY_TAG_RE = re.compile(r"<(small|b)>\s*</\1>")
_BR_EDGE_RE = re.compile(r"^(?:\s*<br>)+|(?:<br>\s*)+$")


def _tidy(par: str) -> str:
    s = unicodedata.normalize("NFC", par).replace("\n", " ")
    for _ in range(3):
        s = _EMPTY_TAG_RE.sub(" ", s)
    s = _BR_EDGE_RE.sub("", s)
    s = re.sub(r"\s*<br>\s*", "<br>", s)
    s = _WS_RE.sub(" ", s)
    # רווח שנשאר לפני פיסוק אחרי שילוב שמות שנזרק ("יְהֹוָה ," ⇐ "יְהֹוָה,")
    return _SPACE_PUNCT_RE.sub(r"\1", s).strip()


def html_to_paragraphs(text: str):
    """HTML של סעיף (מ-action=parse) ⇐ (כותרת הסעיף, [פסקאות]).

    פסקה היא HTML מצומצם (‏<b>, ‏<small>, ‏<br>) כמו פסקה של Sefaria. פסקה
    בלי אות עברית (מספור, קישור בודד) נזרקת. תת-סעיף (כותרת שנייה) — סוף."""
    conv = _Converter()
    conv.feed(text or "")
    conv.close()
    paras = [p for p in conv.paragraphs if re.search("[א-ת]", _strip_tags(p))]
    return conv.heading or "", paras


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def same_heading(a: str, b: str) -> bool:
    """השוואת כותרות סעיפים בלי ניקוד, רווחים וגרשיים (״ / ")."""
    def norm(s):
        s = unicodedata.normalize("NFC", s or "")
        s = re.sub("[֑-ׇ]", "", s)
        s = s.replace("״", '"').replace("׳", "'")
        return re.sub(r"\s+", " ", s).strip()
    return norm(a) == norm(b)


def section_paragraphs(data: dict, heading: str = None):
    """תשובת ‏action=parse (JSON) ⇐ פסקאות הסעיף. מוודא שהכותרת היא הכותרת
    שבקטלוג — סעיף אחר באותו מספר הוא שגיאה ולא טקסט שקט אחר."""
    if not isinstance(data, dict):
        raise WikisourceError("ויקיטקסט החזיר תשובה שאינה JSON תקין")
    if "error" in data:
        err = data["error"] or {}
        raise WikisourceError(f"ויקיטקסט החזיר שגיאה: {err.get('code', '')}"
                              f" — {err.get('info', '')}".strip(" —"))
    parse = data.get("parse") or {}
    text = parse.get("text")
    if isinstance(text, dict):  # formatversion=1
        text = text.get("*")
    if not isinstance(text, str):
        raise WikisourceError("ויקיטקסט החזיר תשובה בלי טקסט לסעיף")
    got, paras = html_to_paragraphs(text)
    if heading and not same_heading(got, heading):
        raise WikisourceError(f"ויקיטקסט החזיר סעיף אחר מהצפוי («{got}» במקום "
                              f"«{heading}») — צריך לבנות מחדש את הקטלוג")
    return paras


_HEADING_DIV_RE = re.compile(r'<div class="mw-heading mw-heading\d')
_HEADING_TAG_RE = re.compile(r"<h[1-6][\s>]", re.I)


def split_page_sections(page_html: str, sections: list) -> dict:
    """HTML של דף שלם (‏action=parse&oldid=…&prop=text) ⇐ {index: פסקאות} לכל
    סעיף ברשימת prop=sections, בלי בקשה לכל סעיף (בונה הקטלוג — מגבלת הקצב
    של ויקיטקסט). כל חתיכה מתחילה בכותרת שלה ונגמרת לפני הכותרת הבאה — בדיוק
    מה ש-section_paragraphs מחזיר לסעיף שנמשך לבד (נבדק על כל סעיפי דף ראש
    השנה, 29.10.2026). כותרת שלא מתאימה לרשימה ⇐ WikisourceError."""
    marks = [m.start() for m in _HEADING_DIV_RE.finditer(page_html or "")]
    if not marks:
        marks = [m.start() for m in _HEADING_TAG_RE.finditer(page_html or "")]
    if len(marks) != len(sections):
        raise WikisourceError(f"מספר הכותרות בדף ({len(marks)}) שונה ממספר "
                              f"הסעיפים ({len(sections)})")
    out = {}
    for i, s in enumerate(sections):
        end = marks[i + 1] if i + 1 < len(marks) else len(page_html)
        head, paras = html_to_paragraphs(page_html[marks[i]:end])
        if not same_heading(head, s.get("line", "")):
            raise WikisourceError(f"כותרת «{head}» במקום «{s.get('line')}»")
        out[str(s["index"])] = paras
    return out


# --- דף מוצג (/wiki/…) — לבונה הקטלוג --------------------------------------------
# ה-API של ויקיטקסט מגביל קצב לפי כתובת IP (429, ‏Retry-After 30–50 שניות מסביבת
# הסוכנים, 29.10.2026), אבל הדף המוצג (/wiki/<דף>) מוגש מה-CDN. הבונה מושך אותו
# פעם אחת, מוודא שהגרסה שלו (wgRevisionId) היא הגרסה הקבועה שבקטלוג, ומפצל
# לסעיפים. מספרי הסעיפים (index) = סדר הכותרות בדף, כמו ב-action=parse
# (נבדק מול prop=sections בארבעת הדפים).

_REV_RE = re.compile(r'"wgRevisionId"\s*:\s*(\d+)')
_HEADING_FULL_RE = re.compile(
    r'<div class="mw-heading mw-heading(\d)[^"]*"[^>]*>\s*<h\d[^>]*\bid="([^"]+)"[^>]*>'
    r'(.*?)</h\d>', re.S)
_EDITSECTION_RE = re.compile(r'<span class="mw-editsection.*?</span>\s*</span>', re.S)


def page_revision(page_html: str):
    """מספר הגרסה של דף מוצג (‏wgRevisionId), או None."""
    m = _REV_RE.search(page_html or "")
    return int(m.group(1)) if m else None


def content_html(page_html: str) -> str:
    """רק תוכן הדף (‏mw-parser-output), בלי תפריטים, קטגוריות ותחתית."""
    page_html = page_html or ""
    start = page_html.find("mw-parser-output")
    start = page_html.rfind("<", 0, start) if start >= 0 else 0
    end = page_html.find('class="printfooter"', start)
    end = page_html.rfind("<", 0, end) if end >= 0 else len(page_html)
    return page_html[start:end]


def sections_from_html(html_text: str) -> list:
    """רשימת סעיפים כמו ‏action=parse&prop=sections: ‏{index, level, number,
    line, anchor} לפי סדר הכותרות."""
    out, counters = [], []
    for i, m in enumerate(_HEADING_FULL_RE.finditer(html_text or ""), 1):
        level = int(m.group(1))
        depth = max(1, level - 1)
        counters = counters[:depth] + [0] * (depth - len(counters))
        counters[depth - 1] += 1
        line = _EDITSECTION_RE.sub("", m.group(3))
        line = _tidy_text(html.unescape(re.sub(r"<[^>]+>", "", line)))
        out.append({"index": str(i), "level": str(level),
                    "number": ".".join(str(c) for c in counters if c),
                    "line": line, "anchor": html.unescape(m.group(2))})
    return out


def paragraphs_from_page(page_html: str, rev, section, heading: str = None) -> list:
    """הדף המוצג ⇐ פסקאות של סעיף אחד — רק אם הדף בדיוק בגרסה rev (אחרת
    WikisourceError: הדף נערך מאז שנבנה הקטלוג, ומספרי הסעיפים אולי זזו)."""
    got = page_revision(page_html)
    if got != int(rev):
        raise WikisourceError(f"הדף בוויקיטקסט בגרסה {got}, לא {rev}")
    content = content_html(page_html)
    secs = sections_from_html(content)
    s = next((s for s in secs if s["index"] == str(section)), None)
    if s is None or (heading and not same_heading(s["line"], heading)):
        raise WikisourceError(f"אין בדף סעיף {section} «{heading}»")
    return split_page_sections(content, secs)[str(section)]


# --- צילום בגיט (data/siddur/wikisource/<rev>.json.gz) ---------------------------
# ה-API של האפליקציה לא פונה לוויקיטקסט בכלל: הטקסט של עלי ויקיטקסט נשמר בגיט
# (‏CC BY-SA 4.0 מתיר הפצה עם ייחוס — הייחוס בקובץ עצמו ובשורת המקור שבאפליקציה).
# קובץ לכל דף, לפי מספר הגרסה הקבועה (rev) שבקטלוג; רק הסעיפים שהקטלוג משתמש
# בהם, כבר כפסקאות (אותה המרה). בונה הקטלוג כותב אותו מחדש בכל בנייה
# (tools/build_siddur_catalog.py), כך שעדכון = עדכון rev ב-overrides.json + בנייה.

SNAPSHOT_DIR = (Path(__file__).resolve().parent.parent.parent
                / "data" / "siddur" / "wikisource")
SNAPSHOT_FORMAT = 1


def snapshot_path(rev, directory=None) -> Path:
    return Path(directory or SNAPSHOT_DIR) / f"{int(rev)}.json.gz"


def make_snapshot(page: str, rev, fetched: str, sections: dict) -> dict:
    """{index: (כותרת, [פסקאות])} ⇐ רשומת הצילום, עם כל פרטי הייחוס."""
    return {
        "format": SNAPSHOT_FORMAT,
        "source": NAME,
        "page": page,
        "rev": int(rev),
        "fetched": fetched,
        "page_url": page_url(page, rev),
        "history_url": history_url(page),
        "license": LICENSE,
        "license_name": LICENSE_NAME,
        "license_url": LICENSE_URL,
        "about": ("טקסט מוויקיטקסט העברי, בגרסה הקבועה rev, כפסקאות בסגנון Sefaria "
                  "(src/siddur/wikisource.py). מופץ ברישיון CC BY-SA 4.0 — ראו "
                  "page_url ו-history_url לתורמים. נבנה ע״י tools/build_siddur_catalog.py."),
        "sections": {str(k): {"heading": h, "paragraphs": list(p)}
                     for k, (h, p) in sorted(sections.items(), key=lambda kv: int(kv[0]))},
    }


def write_snapshot(snap: dict, directory=None) -> Path:
    """כתיבה דטרמיניסטית (‏gzip בלי חותמת זמן) — אותו קלט ⇐ אותו קובץ."""
    path = snapshot_path(snap["rev"], directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with open(path, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0,
                           compresslevel=9) as gz:
            gz.write(raw)
    return path


_SNAPSHOTS = {}


def load_snapshot(rev, directory=None) -> dict:
    """הצילום של גרסה אחת (נטען פעם אחת לכל תהליך). חסר ⇐ WikisourceError."""
    path = snapshot_path(rev, directory)
    key = str(path)
    if key not in _SNAPSHOTS:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                _SNAPSHOTS[key] = json.load(fh)
        except FileNotFoundError:
            raise WikisourceError(f"חסר צילום הטקסט של ויקיטקסט (גרסה {rev}) — "
                                  "צריך לבנות מחדש את הקטלוג")
    return _SNAPSHOTS[key]


def snapshot_paragraphs(w: dict, directory=None) -> list:
    """עלה ויקיטקסט מהקטלוג (‏{page, rev, section, heading}) ⇐ פסקאות מהצילום,
    בלי רשת. כותרת או דף אחרים מהצפוי ⇐ WikisourceError."""
    snap = load_snapshot(w["rev"], directory)
    if snap.get("page") != w["page"] or int(snap.get("rev", -1)) != int(w["rev"]):
        raise WikisourceError("צילום ויקיטקסט לא תואם לקטלוג — צריך לבנות מחדש")
    sec = (snap.get("sections") or {}).get(str(w["section"]))
    if sec is None or (w.get("heading") and not same_heading(sec["heading"], w["heading"])):
        raise WikisourceError(f"אין בצילום סעיף {w['section']} «{w.get('heading')}» — "
                              "צריך לבנות מחדש את הקטלוג")
    return list(sec["paragraphs"])
