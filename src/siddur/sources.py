# -*- coding: utf-8 -*-
"""מקורות הטקסט של הקטלוג: שורת מקור ורישיון, ומהדורות "לינאריות"
(PLAN_TEFILA.md 4.4.1). ספריה סטנדרטית בלבד.

שורת המקור (‏attribution) מוצגת באפליקציה ליד כל קטע — גם בסידור וגם במחזורים —
ולא נכנסת לקובץ הכתוביות (החלטת בעל הפרויקט, 29.10.2026). ב-CC-BY וב-CC-BY-SA
היא חובה: שם המקור, שם המהדורה, הרישיון וקישור.
"""

import re
import urllib.parse

from . import wikisource as ws

SEFARIA_BASE = "https://www.sefaria.org"
# הרישיונות הפתוחים שמותרים בקטלוג (8.15; ‏unknown ו-NC — בחוץ)
ALLOWED_LICENSES = ("CC0", "Public Domain", "CC-BY", "CC-BY-SA")
# קישור לרישיון — רק כשהגרסה ידועה בוודאות: ויקיטקסט מצהיר CC BY-SA 4.0
# (‏siteinfo/rightsinfo, נבדק 29.10.2026); ‏CC0 ונחלת הכלל — אין גרסאות.
# ב-Sefaria התווית ("CC-BY") בלי מספר גרסה, ולכן הקישור הוא לעמוד הטקסט
# ב-Sefaria, שמציג את הרישיון.
LICENSE_URLS = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/deed.he",
    "Public Domain": "https://creativecommons.org/publicdomain/mark/1.0/deed.he",
}
LICENSE_NAMES = {"Public Domain": "נחלת הכלל (Public Domain)"}


def sefaria_url(ref: str, version_title: str = None) -> str:
    """עמוד הטקסט ב-Sefaria, במהדורה שנבחרה (‏?ven=…&lang=he)."""
    url = f"{SEFARIA_BASE}/{urllib.parse.quote(ref.replace(' ', '_'), safe=',_')}"
    if version_title:
        url += "?" + urllib.parse.urlencode(
            {"ven": version_title.strip(), "lang": "he"})
    return url


def source_url(src: dict) -> str:
    """הקישור לטקסט של עלה במקור שלו (src — Catalog.source)."""
    if src.get("source") == "wikisource":
        w = src["ws"]
        return ws.page_url(w["page"], w["rev"], w.get("anchor") or w["heading"])
    return sefaria_url(src["ref"], src.get("version"))


def attribution(src: dict, ver: dict) -> dict:
    """עלה (‏Catalog.source) + רשומת המהדורה בקטלוג ⇐ שורת המקור והרישיון."""
    lic = ver.get("license") or src.get("license") or ""
    out = {"edition": (ver.get("heTitle") or ver.get("title") or "").strip(),
           "license": lic,
           "license_name": LICENSE_NAMES.get(lic, lic)}
    if src.get("source") == "wikisource":
        out.update(source=ws.NAME, source_url=source_url(src),
                   license_name=ws.LICENSE_NAME, license_url=ws.LICENSE_URL,
                   history_url=ws.history_url(src["ws"]["page"]))
    else:
        out.update(source="Sefaria", source_url=source_url(src))
        if lic in LICENSE_URLS:
            out["license_url"] = LICENSE_URLS[lic]
    if ver.get("credit"):
        out["credit"] = ver["credit"]
    if ver.get("origin"):
        out["origin"] = dict(ver["origin"])
    return out


_TAG_RE = re.compile(r"<[^>]+>")
_HEADING_RE = re.compile(r"^\s*<b>[^<]*</b>\s*$")


def merge_lines(segments: list) -> list:
    """מהדורה "לינארית" של Sefaria (מחזור מצודה ליום כיפור: קטע = שורה, עד
    1,397 שורות בעלה) ⇐ פסקאות: שורה ריקה, כותרת מודגשת בשורה משלה (‏<b>אבות</b>)
    או שורה שנגמרת ב-":" (סוף פסוק / סוף קטע) — סוף פסקה. כך העלה הגדול ביותר
    יורד ל-~300 פסקאות, קרוב למהדורת הפסקאות של אותו טקסט."""
    out, cur = [], []
    for seg in segments:
        s = seg if isinstance(seg, str) else ""
        if not s.strip():
            if cur:
                out.append(" ".join(cur))
                cur = []
            continue
        if _HEADING_RE.match(s):
            if cur:
                out.append(" ".join(cur))
                cur = []
            out.append(s.strip())
            continue
        cur.append(s.strip())
        if _TAG_RE.sub("", s).rstrip().endswith(":"):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out
