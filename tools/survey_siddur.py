# -*- coding: utf-8 -*-
"""סקר הסידור ב-Sefaria — PLAN_TEFILA.md משימה 0.1 (שאלות 8.2, 8.4, 8.5).

ספריה סטנדרטית בלבד (urllib, json) — רץ מהמחשב או מ-Colab בלי התקנות:

    python3 tools/survey_siddur.py                       # סקר מלא
    python3 tools/survey_siddur.py --limit 3             # ריצה מהירה: 3 אינדקסים
    python3 tools/survey_siddur.py --nusach Ashkenaz     # רק אינדקסים שבשמם "Ashkenaz"
    python3 tools/survey_siddur.py --offline             # רק מה-cache, בלי רשת

פלט: docs/siddur_survey.md (דוח בעברית) + data/siddur/sefaria_index_snapshot.json.

⚠️ כלל PLAN.md: לא מניחים שמות API/אינדקסים מהזיכרון. לכן:
- שמות האינדקסים **מתגלים** מעץ התוכן של Sefaria (‏/api/index) לפי מילות
  חיפוש בשם הקטגוריה/הכותר. רשימת SEED_TITLES היא רק זרעי חיפוש
  לא-מאומתים (נבדקים מול ‏/api/name ו-/api/v2/raw/index), לא עובדה.
- מבנה התשובות של ה-API מטופל בהגנה (‏.get, בדיקות טיפוס) — כל מבנה לא
  צפוי נרשם בתמונת המצב ובדוח במקום להפיל את הריצה.
- נתיבי ה-endpoint עצמם (למטה, ENDPOINTS) הם הנחת עבודה: ‏`/api/texts/versions`
  ו-`/api/v3/texts` כבר בשימוש בצינור (src/aligner/pipeline.py); השאר
  ⚠️ לאמת — אם אחד מהם מחזיר שגיאה, הדוח יראה זאת בטבלת "שגיאות".

הפונקציות שמנתחות נתונים (walk_toc, walk_schema, analyze_texts, render_report
וכו') טהורות ונבדקות בלי רשת ב-tests/test_survey_siddur.py.
"""

import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEFARIA_BASE = "https://www.sefaria.org"
USER_AGENT = ("Kriat-Hatora-survey/1.0 "
              "(+https://github.com/michaelnahmias1/Kriat-Hatora)")

# ⚠️ לאמת — נתיבים שלא נבדקו מהסביבה הזו (sefaria.org חסום בה, שאלה 8.1).
ENDPOINTS = {
    "toc": "/api/index",                        # עץ התוכן המלא
    "index": "/api/v2/raw/index/{title}",       # רשומת אינדקס + schema
    "index_fallback": "/api/index/{title}",     # ‏API ישן לאותה רשומה
    "versions": "/api/texts/versions/{title}",  # בשימוש ב-pipeline.py
    "texts_v3": "/api/v3/texts/{ref}",          # בשימוש ב-pipeline.py
    "name": "/api/name/{query}",                # השלמת שמות (לזרעים)
}

# מילות חיפוש לגילוי אינדקסים בעץ התוכן (התאמה לא תלוית-רישיות, תת-מחרוזת).
DISCOVERY_KEYWORDS = (
    "liturgy", "siddur", "machzor", "mahzor", "selichot", "slichot", "kinot",
    "kinnot", "haggadah", "haggada", "zemirot", "piyut", "piyyut", "prayer",
    "סידור", "מחזור", "סליחות", "קינות", "הגדה", "זמירות", "פיוט", "תפילה",
    "תפלה",
)

# ⚠️ זרעי חיפוש לא-מאומתים: שמות שעלו בתכנון (PLAN_TEFILA.md 0.1). הסקריפט
# בודק אותם, אבל רק מה שהשרת מחזיר נכנס לדוח כקיים.
SEED_TITLES = (
    "Siddur Ashkenaz", "Siddur Sefard", "Siddur Edot HaMizrach",
    "Machzor Rosh Hashanah", "Machzor Yom Kippur", "Selichot", "Kinot",
    "Pesach Haggadah", "Zemirot Shabbat",
)

# סיווג נוסח לפי מילים בכותר — היוריסטיקה בלבד, הדוח מציין זאת. הסדר חשוב:
# "Sephardi"/"ספרדי" (עדות המזרח) נבדק לפני "Sefard" (נוסח ספרד החסידי).
NUSACH_RULES = (
    ("עדות המזרח / ספרדי", ("edot", "mizrach", "sephardi", "sefaradi",
                            "sephardic", "עדות המזרח", "ספרדי")),
    ("ספרד", ("sefard", "sfard", "sephard", "נוסח ספרד", "ספרד")),
    ("אשכנז", ("ashkenaz", "אשכנז")),
    ("חב״ד / האר״י", ("chabad", "arizal", "ari ", "חב״ד", "חב\"ד", "האר״י")),
    ("תימן", ("teiman", "yemen", "baladi", "shami", "תימן", "בלדי")),
    ("איטליה / רומא", ("italian", "italki", "roma", "איטלקי", "איטליה")),
)

KIND_RULES = (
    ("מחזור", ("machzor", "mahzor", "מחזור")),
    ("סליחות", ("selichot", "slichot", "סליחות")),
    ("קינות", ("kinot", "kinnot", "קינות")),
    ("הגדה", ("haggadah", "haggada", "הגדה")),
    ("זמירות", ("zemirot", "זמירות")),
    ("פיוטים", ("piyut", "piyyut", "פיוט")),
    ("סידור", ("siddur", "סידור", "prayer", "תפילה", "תפלה")),
)


# =============================================================================
# ניתוח טהור (בלי רשת) — נבדק ב-tests/test_survey_siddur.py
# =============================================================================

def _match_rules(text: str, rules) -> str:
    low = (text or "").lower()
    for label, words in rules:
        if any(w in low for w in words):
            return label
    return ""


def guess_nusach(title: str, he_title: str = "") -> str:
    """ניחוש נוסח לפי הכותר (היוריסטיקה — לאימות אנושי)."""
    return (_match_rules(title, NUSACH_RULES)
            or _match_rules(he_title, NUSACH_RULES) or "לא מסווג")


def guess_kind(title: str, he_title: str = "", categories=()) -> str:
    """סוג החיבור (סידור/מחזור/סליחות/...) לפי כותר וקטגוריות."""
    for text in (title, he_title, " ".join(categories or ())):
        k = _match_rules(text, KIND_RULES)
        if k:
            return k
    return "אחר"


def _matches_keywords(texts, keywords=DISCOVERY_KEYWORDS) -> bool:
    low = " ".join(t for t in texts if t).lower()
    return any(k in low for k in keywords)


def walk_toc(toc, keywords=DISCOVERY_KEYWORDS) -> list:
    """עובר על עץ התוכן (‏/api/index) ומחזיר את הספרים שמתאימים למילות החיפוש.

    המבנה מטופל בהגנה: dict עם "contents" = קטגוריה (שם ב-"category" /
    "heCategory"); dict עם "title" = ספר. ספר נכלל אם הכותר שלו או אחת
    מקטגוריות-האב מכילים מילת חיפוש. מחזיר [{title, heTitle, categories}].
    """
    found, seen = [], set()

    def visit(node, path, he_path):
        if isinstance(node, list):
            for item in node:
                visit(item, path, he_path)
            return
        if not isinstance(node, dict):
            return
        if isinstance(node.get("contents"), list):
            cat = node.get("category") or node.get("title") or ""
            he_cat = node.get("heCategory") or node.get("heTitle") or ""
            visit(node["contents"], path + [cat], he_path + [he_cat])
            return
        title = node.get("title")
        if not title or title in seen:
            return
        he_title = node.get("heTitle", "")
        cats = node.get("categories") or path
        if _matches_keywords([title, he_title] + list(path) + list(he_path)
                             + list(cats), keywords):
            seen.add(title)
            found.append({"title": title, "heTitle": he_title,
                          "categories": list(cats)})

    visit(toc, [], [])
    return found


def node_titles(node: dict) -> tuple:
    """(כותר אנגלי ראשי, כותר עברי ראשי) של צומת schema — בשני הפורמטים
    האפשריים: שדות title/heTitle ישירים, או רשימת titles [{text, lang, primary}]."""
    en = node.get("title") or node.get("enTitle") or ""
    he = node.get("heTitle") or ""
    titles = node.get("titles")
    if isinstance(titles, list):
        for lang in ("en", "he"):
            cands = [t for t in titles
                     if isinstance(t, dict) and t.get("lang") == lang]
            prim = [t for t in cands if t.get("primary")] or cands
            if prim:
                if lang == "en" and not en:
                    en = prim[0].get("text", "")
                if lang == "he" and not he:
                    he = prim[0].get("text", "")
    return en, he


def is_default_node(node: dict) -> bool:
    return bool(node.get("default")) or node.get("key") == "default"


def build_ref(index_title: str, path: list) -> str:
    """ref לצומת: "Index, Node, Sub" — ⚠️ פורמט Sefaria לצמתים מורכבים, לאמת
    בסקר (הדוגמאות שנמשכות בפועל מראות אם הוא עובד). צומת default לא נכנס."""
    return ", ".join([index_title] + [p for p in path if p])


def walk_schema(schema: dict, index_title: str) -> list:
    """schema (מורכב או פשוט) → רשימה שטוחה של צמתים לפי הסדר.

    לכל צומת: depth (עומק בעץ, השורש=0), title, heTitle, leaf, ref,
    nodeType, text_depth (עומק הטקסט בעלה), sectionNames, addressTypes.
    """
    out = []

    def visit(node, depth, path):
        if not isinstance(node, dict):
            return
        en, he = node_titles(node)
        children = node.get("nodes")
        leaf = not (isinstance(children, list) and children)
        own = "" if (depth == 0 or is_default_node(node)) else en
        new_path = path + ([own] if own else [])
        out.append({
            "depth": depth,
            "title": en,
            "heTitle": he,
            "leaf": leaf,
            "default": is_default_node(node),
            "ref": build_ref(index_title, new_path),
            "nodeType": node.get("nodeType", ""),
            "text_depth": node.get("depth"),
            "sectionNames": node.get("sectionNames"),
            "addressTypes": node.get("addressTypes"),
        })
        if not leaf:
            for ch in children:
                visit(ch, depth + 1, new_path)

    visit(schema or {}, 0, [])
    return out


def schema_summary(nodes: list) -> dict:
    """סיכום מבנה: מספר צמתים/עלים, עומק מרבי, כמה חסרי heTitle, דוגמת ref."""
    leaves = [n for n in nodes if n["leaf"]]
    text_depths = Counter(str(n.get("text_depth")) for n in leaves)
    return {
        "n_nodes": len(nodes),
        "n_leaves": len(leaves),
        "max_depth": max((n["depth"] for n in nodes), default=0),
        "missing_heTitle": sum(1 for n in nodes if n["depth"] and not n["heTitle"]),
        "leaf_text_depths": dict(text_depths),
        "sectionNames": sorted({" / ".join(n["sectionNames"])
                                for n in leaves
                                if isinstance(n.get("sectionNames"), list)}),
        "example_leaf_ref": leaves[0]["ref"] if leaves else "",
        "top_level": [(n["title"], n["heTitle"]) for n in nodes
                      if n["depth"] == 1][:40],
    }


def pick_samples(items: list, k: int) -> list:
    """k פריטים בפיזור אחיד (ראשון, ..., אחרון) — לדגימה מייצגת."""
    if k <= 0 or not items:
        return []
    if len(items) <= k:
        return list(items)
    if k == 1:
        return [items[0]]
    step = (len(items) - 1) / (k - 1)
    return [items[round(i * step)] for i in range(k)]


def text_shape(obj) -> dict:
    """צורת שדה text: עומק קינון, מספר מחרוזות, אורכי רשימות ברמה העליונה."""
    def depth(o):
        if isinstance(o, list):
            return 1 + max((depth(x) for x in o), default=0)
        return 0
    strings = flatten_strings(obj)
    return {
        "type": type(obj).__name__,
        "nesting": depth(obj),
        "n_strings": len(strings),
        "n_empty": sum(1 for s in strings if not s.strip()),
        "top_len": len(obj) if isinstance(obj, list) else None,
    }


def flatten_strings(obj) -> list:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, list):
        out = []
        for x in obj:
            out.extend(flatten_strings(x))
        return out
    return []


# --- ניתוח טקסט ---------------------------------------------------------------

_TAG_RE = re.compile(r"<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9]*)([^>]*)>")
_CLASS_RE = re.compile(r"""class\s*=\s*["']([^"']*)["']""")
_SMALL_RE = re.compile(r"<small[^>]*>(.*?)</small>", re.S | re.I)
_PAREN_RE = re.compile(r"\(([^()]*)\)")
_BRACKET_RE = re.compile(r"\[([^\[\]]*)\]")
_ANY_TAG_RE = re.compile(r"<[^>]+>")

_NIQQUD = {chr(c) for c in range(0x05B0, 0x05BD)} | {"\u05BF", "\u05C1",
                                                    "\u05C2", "\u05C7"}
_TAAMIM = {chr(c) for c in range(0x0591, 0x05B0)}
_METEG = "\u05BD"
_KAMATZ_KATAN = "\u05C7"
_HEB_LETTER_RE = re.compile(r"[\u05D0-\u05EA]")
_MARKS_RE = re.compile(r"[\u0591-\u05C7]")

# סימני פיסוק נספרים בנפרד — מקף, סוף פסוק, פסק, גרש/גרשיים ועוד
PUNCT_CHARS = {
    ".": "נקודה", ",": "פסיק", ":": "נקודתיים", ";": "נקודה-פסיק",
    "?": "סימן שאלה", "!": "סימן קריאה", "\u05BE": "מקף (־)",
    "\u05C3": "סוף פסוק (׃)", "\u05C0": "פסק (׀)", "\u05F3": "גרש (׳)",
    "\u05F4": "גרשיים (״)", "'": "גרש לטיני (')", '"': "מרכאות (\")",
    "-": "מקף לטיני (-)", "\u2013": "קו מפריד (–)", "\u2014": "קו ארוך (—)",
}

# הוראות טיפוסיות בסידור (8.4) — מילות מפתח לזיהוי, לא רשימה סגורה.
INSTRUCTION_HINTS = (
    "אומרים", "אומר", "החזן", "הקהל", "שליח ציבור", "ש\"ץ", "ש״ץ", "בשבת",
    "בחול", "בעשי\"ת", "בעשי״ת", "בעשרת ימי תשובה", "בראש חודש", "בר\"ח",
    "בר״ח", "נוהגים", "יש אומרים", "ואין אומרים", "בחנוכה", "בפורים",
    "בתענית", "ביום טוב", "כאן", "עד כאן",
)

_PREFIXES = "ובכלמשה"


def strip_marks(word: str) -> str:
    """מסיר ניקוד וטעמים (U+0591–U+05C7) — משאיר אותיות וגרשים."""
    return _MARKS_RE.sub("", unicodedata.normalize("NFC", word))


def classify_god_name(token: str) -> str:
    """מסווג מילה לצורת כתיבה של שם ה׳, או "" אם אינה שם ה׳.

    צורות: "יהוה" (כולל כל ניקוד), "יי", "ה׳ (קיצור)", "ידוד", "אדני".
    מתיר עד שתי אותיות-שימוש בתחילה (וּ, לַ, בַּ, מֵ, שֶׁ, כְּ, הַ).
    """
    bare = strip_marks(token).strip(".,:;?!׃()[]{}\"“”")
    bare = bare.replace("\u05F3", "'")  # גרש עברי → אחיד
    for cut in range(0, 3):
        if cut and not all(c in _PREFIXES for c in bare[:cut]):
            break
        core = bare[cut:]
        if core == "יהוה":
            return "יהוה"
        if core == "יי":
            return "יי"
        if core == "ידוד":
            return "ידוד"
        if core == "ה'":
            return "ה׳ (קיצור)"
        if core in ("אדני", "אדוני") and cut == 0:
            return "אדני"
    return ""


def tokenize_plain(s: str) -> list:
    """מחרוזת (אולי עם HTML) → מילים, מפוצלות גם על מקף עליון."""
    s = _ANY_TAG_RE.sub(" ", s)
    s = s.replace("\u05BE", " ").replace("&nbsp;", " ")
    return [t for t in s.split() if t]


def analyze_texts(strings: list, max_examples: int = 5) -> dict:
    """ניתוח מקבץ מחרוזות של טקסט סידור: סימון, ניקוד, שם ה׳, פיסוק, הוראות.

    מחזיר dict סריאלי ל-JSON. דוגמאות נחתכות ל-max_examples.
    """
    tags, classes = Counter(), Counter()
    small_examples, paren_examples, bracket_examples = [], [], []
    n_small = n_paren = n_bracket = 0
    words = hebrew_words = with_niqqud = with_taamim = 0
    kamatz_katan = meteg = 0
    god_forms, god_exact = Counter(), Counter()
    punct = Counter()
    instr_hits = Counter()
    instr_examples = []

    for s in strings:
        for close, name, attrs in _TAG_RE.findall(s):
            if not close:
                tags[name.lower()] += 1
                for c in _CLASS_RE.findall(attrs):
                    classes[c] += 1
        for m in _SMALL_RE.findall(s):
            n_small += 1
            if len(small_examples) < max_examples:
                small_examples.append(_ANY_TAG_RE.sub("", m).strip()[:80])
        plain = _ANY_TAG_RE.sub(" ", s)
        for m in _PAREN_RE.findall(plain):
            n_paren += 1
            if len(paren_examples) < max_examples:
                paren_examples.append(m.strip()[:80])
        for m in _BRACKET_RE.findall(plain):
            n_bracket += 1
            if len(bracket_examples) < max_examples:
                bracket_examples.append(m.strip()[:80])
        for ch in plain:
            if ch in PUNCT_CHARS:
                punct[PUNCT_CHARS[ch]] += 1
        kamatz_katan += plain.count(_KAMATZ_KATAN)
        meteg += plain.count(_METEG)
        bare_plain = strip_marks(plain)
        for hint in INSTRUCTION_HINTS:
            if hint in bare_plain:
                instr_hits[hint] += 1
                if len(instr_examples) < max_examples:
                    instr_examples.append(bare_plain.strip()[:80])
        for tok in tokenize_plain(s):
            words += 1
            if not _HEB_LETTER_RE.search(tok):
                continue
            hebrew_words += 1
            if any(c in _NIQQUD for c in tok):
                with_niqqud += 1
            if any(c in _TAAMIM for c in tok):
                with_taamim += 1
            form = classify_god_name(tok)
            if form:
                god_forms[form] += 1
                god_exact[unicodedata.normalize("NFC", tok)] += 1

    def frac(a, b):
        return round(a / b, 4) if b else None

    return {
        "n_strings": len(strings),
        "n_words": words,
        "n_hebrew_words": hebrew_words,
        "niqqud_frac": frac(with_niqqud, hebrew_words),
        "taamim_frac": frac(with_taamim, hebrew_words),
        "kamatz_katan": kamatz_katan,
        "meteg": meteg,
        "html_tags": dict(tags.most_common()),
        "html_classes": dict(classes.most_common(10)),
        "small": {"count": n_small, "examples": small_examples},
        "parentheses": {"count": n_paren, "examples": paren_examples},
        "brackets": {"count": n_bracket, "examples": bracket_examples},
        "instruction_hints": dict(instr_hits.most_common()),
        "instruction_examples": instr_examples,
        "god_name_forms": dict(god_forms.most_common()),
        "god_name_exact": dict(god_exact.most_common(10)),
        "punctuation": dict(punct.most_common()),
        "avg_words_per_string": round(words / len(strings), 1) if strings else None,
    }


def merge_analyses(analyses: list) -> dict:
    """איחוד ניתוחים של כמה דגימות לסיכום אחד לאינדקס."""
    tot = Counter()
    god, punct, tags, hints = Counter(), Counter(), Counter(), Counter()
    small_ex, paren_ex = [], []
    nq = tm = 0.0
    for a in analyses:
        hw = a.get("n_hebrew_words") or 0
        tot["strings"] += a.get("n_strings", 0)
        tot["words"] += a.get("n_words", 0)
        tot["hebrew"] += hw
        tot["kamatz_katan"] += a.get("kamatz_katan", 0)
        tot["meteg"] += a.get("meteg", 0)
        tot["small"] += a.get("small", {}).get("count", 0)
        tot["paren"] += a.get("parentheses", {}).get("count", 0)
        nq += (a.get("niqqud_frac") or 0) * hw
        tm += (a.get("taamim_frac") or 0) * hw
        god.update(a.get("god_name_forms", {}))
        punct.update(a.get("punctuation", {}))
        tags.update(a.get("html_tags", {}))
        hints.update(a.get("instruction_hints", {}))
        small_ex += a.get("small", {}).get("examples", [])
        paren_ex += a.get("parentheses", {}).get("examples", [])
    h = tot["hebrew"]
    return {
        "n_strings": tot["strings"], "n_words": tot["words"],
        "n_hebrew_words": h,
        "niqqud_frac": round(nq / h, 4) if h else None,
        "taamim_frac": round(tm / h, 4) if h else None,
        "kamatz_katan": tot["kamatz_katan"], "meteg": tot["meteg"],
        "small_count": tot["small"], "paren_count": tot["paren"],
        "small_examples": small_ex[:5], "paren_examples": paren_ex[:5],
        "god_name_forms": dict(god.most_common()),
        "punctuation": dict(punct.most_common()),
        "html_tags": dict(tags.most_common()),
        "instruction_hints": dict(hints.most_common(10)),
    }


def summarize_versions(versions) -> list:
    """רשימת הגרסאות מ-/api/texts/versions → שדות רלוונטיים בלבד."""
    if not isinstance(versions, list):
        return []
    out = []
    for v in versions:
        if not isinstance(v, dict):
            continue
        out.append({
            "versionTitle": v.get("versionTitle", ""),
            "language": v.get("language", v.get("actualLanguage", "")),
            "license": v.get("license", ""),
            "versionSource": v.get("versionSource", ""),
            "status": v.get("status", ""),
        })
    return out


def describe_v3_response(status: int, data) -> dict:
    """תקציר תשובת /api/v3/texts — לבדיקת ההתנהגות על refs מורכבים/טווחים."""
    out = {"http_status": status}
    if not isinstance(data, dict):
        out["body_type"] = type(data).__name__
        return out
    out["keys"] = sorted(data.keys())[:30]
    if "error" in data:
        out["error"] = str(data["error"])[:300]
    if data.get("warnings"):
        out["warnings"] = str(data["warnings"])[:300]
    versions = data.get("versions")
    if isinstance(versions, list) and versions:
        v0 = versions[0] if isinstance(versions[0], dict) else {}
        out["n_versions"] = len(versions)
        out["versionTitle"] = v0.get("versionTitle", "")
        out["license"] = v0.get("license", "")
        out["shape"] = text_shape(v0.get("text"))
    for k in ("ref", "heRef", "sectionRef", "isComplex", "spanningRefs"):
        if k in data:
            out[k] = data[k] if not isinstance(data[k], list) else data[k][:5]
    return out


# --- הדוח ------------------------------------------------------------------------

def _pct(x):
    return "—" if x is None else f"{x * 100:.0f}%"


def _fmt_counter(d: dict, n: int = 4) -> str:
    if not d:
        return "—"
    return ", ".join(f"{k}×{v}" for k, v in list(d.items())[:n])


def _cell(s) -> str:
    return str(s if s not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def render_report(snapshot: dict) -> str:
    """תמונת מצב (dict) → דוח Markdown בעברית, טבלה לכל נוסח."""
    meta = snapshot.get("meta", {})
    idx = snapshot.get("indexes", {})
    L = [
        "# סקר הסידור ב-Sefaria (משימה 0.1)",
        "",
        f"> נוצר אוטומטית ע״י `tools/survey_siddur.py` ב-{meta.get('generated_at', '?')}"
        f" מול `{meta.get('base', SEFARIA_BASE)}`. פרמטרים: `{meta.get('args', {})}`.",
        "> סיווג הנוסח והסוג הוא היוריסטיקה לפי הכותר — לאימות אנושי.",
        "> ההכרעה אילו נוסחים ומחזורים נכנסים לשלבים 2 ו-4 — של בעל הפרויקט"
        " (סעיף \"הכרעות\" בסוף, ריק בכוונה).",
        "",
        "## סיכום",
        "",
        f"- אינדקסים שנמצאו בעץ התוכן לפי מילות חיפוש: {len(snapshot.get('toc_matches', []))}",
        f"- אינדקסים שנסקרו: {len(idx)}",
        f"- שגיאות רשת/API: {len(snapshot.get('errors', []))}",
        "",
    ]
    seeds = snapshot.get("seed_checks", {})
    if seeds:
        L += ["## זרעי חיפוש (שמות מהתכנון — ⚠️ לא מאומתים מראש)", "",
              "| זרע | נמצא כאינדקס? | השלמות מ-/api/name |", "|---|---|---|"]
        for seed, info in seeds.items():
            L.append(f"| {_cell(seed)} | {'כן' if info.get('is_index') else 'לא'} "
                     f"| {_cell(', '.join(info.get('completions', [])[:5]))} |")
        L.append("")

    groups = {}
    for title, rec in idx.items():
        groups.setdefault(rec.get("nusach_guess", "לא מסווג"), []).append((title, rec))
    for nusach in sorted(groups):
        L += [f"## נוסח: {nusach}", "",
              "| אינדקס | כותר עברי | סוג | קטגוריות | צמתים/עלים | עומק | "
              "גרסאות עבריות | רישיונות | ניקוד | טעמים | שם ה׳ | `<small>` | סוגריים |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for title, rec in sorted(groups[nusach]):
            sm = rec.get("schema_summary", {})
            agg = rec.get("aggregate", {})
            he_versions = [v for v in rec.get("versions", [])
                           if v.get("language") == "he"]
            lic = sorted({v.get("license") or "?" for v in he_versions})
            L.append(
                f"| {_cell(title)} | {_cell(rec.get('heTitle'))} | {_cell(rec.get('kind_guess'))} "
                f"| {_cell(' / '.join(rec.get('categories', [])))} "
                f"| {sm.get('n_nodes', '—')}/{sm.get('n_leaves', '—')} | {sm.get('max_depth', '—')} "
                f"| {len(he_versions)} | {_cell(', '.join(lic))} "
                f"| {_pct(agg.get('niqqud_frac'))} | {_pct(agg.get('taamim_frac'))} "
                f"| {_cell(_fmt_counter(agg.get('god_name_forms', {})))} "
                f"| {agg.get('small_count', '—')} | {agg.get('paren_count', '—')} |")
        L.append("")
        for title, rec in sorted(groups[nusach]):
            L += _render_index_detail(title, rec)

    probes = snapshot.get("v3_probes", [])
    if probes:
        L += ["## התנהגות `api/v3/texts` על refs מורכבים וטווחים", "",
              "| בדיקה | ref | HTTP | שגיאה/אזהרה | צורת text | ref שהוחזר |",
              "|---|---|---|---|---|---|"]
        for p in probes:
            r = p.get("result", {})
            sh = r.get("shape") or {}
            shape = (f"קינון {sh.get('nesting')}, {sh.get('n_strings')} מחרוזות"
                     if sh else "—")
            L.append(f"| {_cell(p.get('kind'))} | `{_cell(p.get('ref'))}` "
                     f"| {r.get('http_status', '—')} "
                     f"| {_cell(r.get('error') or r.get('warnings'))} "
                     f"| {_cell(shape)} | {_cell(r.get('ref'))} |")
        L.append("")

    errors = snapshot.get("errors", [])
    if errors:
        L += ["## שגיאות", "", "| URL | שגיאה |", "|---|---|"]
        for e in errors[:100]:
            L.append(f"| `{_cell(e.get('url'))}` | {_cell(e.get('error'))} |")
        L.append("")

    L += ["## הכרעות (למילוי ע״י בעל הפרויקט)", "",
          "- נוסחים לשלב 2: ___", "- מחזורים/סליחות/קינות לשלב 4: ___",
          "- רישיון: ___", ""]
    return "\n".join(L)


def _render_index_detail(title: str, rec: dict) -> list:
    sm = rec.get("schema_summary", {})
    agg = rec.get("aggregate", {})
    L = [f"### {title} — {rec.get('heTitle', '')}", ""]
    L.append(f"- דוגמת ref לעלה: `{sm.get('example_leaf_ref') or '—'}`")
    L.append(f"- עומק טקסט בעלים: {sm.get('leaf_text_depths', {})}; "
             f"sectionNames: {', '.join(sm.get('sectionNames', [])) or '—'}; "
             f"צמתים בלי heTitle: {sm.get('missing_heTitle', '—')}")
    top = sm.get("top_level", [])
    if top:
        L.append("- צמתים ברמה הראשונה: " + "; ".join(
            f"{en} ({he})" for en, he in top[:25])
            + (" …" if len(top) > 25 else ""))
    if agg:
        L.append(f"- דגימה: {agg.get('n_strings')} מחרוזות, {agg.get('n_words')} מילים; "
                 f"ניקוד {_pct(agg.get('niqqud_frac'))}, טעמים {_pct(agg.get('taamim_frac'))}, "
                 f"קמץ קטן (U+05C7) ×{agg.get('kamatz_katan')}, מתג ×{agg.get('meteg')}")
        L.append(f"- שם ה׳: {_fmt_counter(agg.get('god_name_forms', {}), 6)}")
        L.append(f"- תגיות HTML: {_fmt_counter(agg.get('html_tags', {}), 8)}")
        if agg.get("small_examples"):
            L.append("- דוגמאות `<small>`: " + " · ".join(
                f"«{_cell(x)}»" for x in agg["small_examples"]))
        if agg.get("paren_examples"):
            L.append("- דוגמאות בסוגריים: " + " · ".join(
                f"«{_cell(x)}»" for x in agg["paren_examples"]))
        L.append(f"- מילות הוראה: {_fmt_counter(agg.get('instruction_hints', {}), 8)}")
        L.append(f"- פיסוק: {_fmt_counter(agg.get('punctuation', {}), 8)}")
    for s in rec.get("samples", [])[:6]:
        sh = s.get("shape") or {}
        L.append(f"  - דגימה `{_cell(s.get('ref'))}` [{_cell(s.get('version'))}]: "
                 f"HTTP {s.get('http_status', '—')}, קינון {sh.get('nesting', '—')}, "
                 f"{sh.get('n_strings', '—')} מחרוזות"
                 + (f" — שגיאה: {_cell(s.get('error'))}" if s.get("error") else ""))
    L.append("")
    return L


# =============================================================================
# רשת: cache, קצב מנומס, ניסיונות חוזרים
# =============================================================================

class Client:
    """לקוח HTTP מינימלי עם cache בדיסק, השהיה בין בקשות וניסיונות חוזרים.

    ‏cache לפי URL מלא — ריצה חוזרת לא מושכת שוב. גם תשובות שגיאה 4xx נשמרות
    (הן חלק מהסקר — למשל ref מורכב שלא נתמך). 5xx/429/שגיאות רשת — ניסיון חוזר.
    """

    def __init__(self, base=SEFARIA_BASE, cache_dir=None, delay=1.0,
                 retries=4, timeout=60, offline=False):
        self.base = base.rstrip("/")
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.delay, self.retries, self.timeout = delay, retries, timeout
        self.offline = offline
        self.errors = []
        self._last = 0.0
        self.n_network = self.n_cached = 0

    def _cache_path(self, url):
        return self.cache_dir / (hashlib.sha1(url.encode()).hexdigest() + ".json")

    def get(self, path: str, params: dict = None):
        """מחזיר (status, data). status=0 = לא הושג (שגיאת רשת / offline)."""
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        cp = self._cache_path(url) if self.cache_dir else None
        if cp and cp.exists():
            self.n_cached += 1
            rec = json.loads(cp.read_text(encoding="utf-8"))
            return rec["status"], rec["data"]
        if self.offline:
            return 0, None
        last_err = None
        for attempt in range(self.retries + 1):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT, "Accept": "application/json"})
            try:
                self.n_network += 1
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    status, body = resp.status, resp.read()
            except urllib.error.HTTPError as e:
                status, body = e.code, e.read()
                if status == 429 or status >= 500:
                    last_err = f"HTTP {status}"
                    time.sleep(min(60, 2 ** attempt * 2))
                    continue
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = f"{type(e).__name__}: {e}"
                time.sleep(min(60, 2 ** attempt * 2))
                continue
            try:
                data = json.loads(body.decode("utf-8"))
            except ValueError:
                data = {"_non_json": body[:300].decode("utf-8", "replace")}
            if cp:
                cp.write_text(json.dumps({"url": url, "status": status,
                                          "data": data}, ensure_ascii=False),
                              encoding="utf-8")
            if status >= 400:
                self.errors.append({"url": url, "error": f"HTTP {status}"})
            return status, data
        self.errors.append({"url": url, "error": last_err})
        return 0, None


def _q(s: str) -> str:
    return urllib.parse.quote(s, safe="")


# =============================================================================
# הסקר עצמו
# =============================================================================

def check_seeds(client: Client, seeds) -> dict:
    out = {}
    for seed in seeds:
        st, data = client.get(ENDPOINTS["name"].format(query=_q(seed)),
                              {"limit": 10})
        info = {"name_status": st, "completions": [], "is_index": False}
        if isinstance(data, dict):
            comps = data.get("completions")
            if isinstance(comps, list):
                info["completions"] = [str(c) for c in comps][:10]
            info["is_index"] = bool(data.get("is_book") or data.get("index"))
            info["raw_keys"] = sorted(data.keys())[:20]
        out[seed] = info
    return out


def fetch_index_record(client: Client, title: str):
    st, data = client.get(ENDPOINTS["index"].format(title=_q(title)))
    if st == 200 and isinstance(data, dict) and "error" not in data:
        return data, "v2/raw/index"
    st2, data2 = client.get(ENDPOINTS["index_fallback"].format(title=_q(title)))
    if st2 == 200 and isinstance(data2, dict) and "error" not in data2:
        return data2, "index"
    return None, f"{st}/{st2}"


def fetch_text(client: Client, ref: str, version_title: str = None):
    params = {"version": f"hebrew|{version_title}"} if version_title else None
    return client.get(ENDPOINTS["texts_v3"].format(ref=_q(ref)), params)


def survey_index(client: Client, entry: dict, samples: int,
                 max_versions: int) -> dict:
    title = entry["title"]
    rec = {"heTitle": entry.get("heTitle", ""),
           "categories": entry.get("categories", []),
           "nusach_guess": guess_nusach(title, entry.get("heTitle", "")),
           "kind_guess": guess_kind(title, entry.get("heTitle", ""),
                                    entry.get("categories", []))}
    record, how = fetch_index_record(client, title)
    rec["index_source"] = how
    nodes = []
    if record:
        schema = record.get("schema")
        if not isinstance(schema, dict):  # אינדקס פשוט בלי schema מורכב
            schema = {"depth": record.get("depth"),
                      "sectionNames": record.get("sectionNames"),
                      "heTitle": record.get("heTitle", "")}
        nodes = walk_schema(schema, title)
        rec["schema_summary"] = schema_summary(nodes)
        rec["nodes"] = nodes
        rec["index_keys"] = sorted(record.keys())[:40]

    st, versions = client.get(ENDPOINTS["versions"].format(title=_q(title)))
    rec["versions"] = summarize_versions(versions)
    he_versions = [v["versionTitle"] for v in rec["versions"]
                   if v.get("language") == "he" and v.get("versionTitle")]

    leaves = [n for n in nodes if n["leaf"]] or [{"ref": title}]
    rec["samples"], analyses = [], []
    for vt in (he_versions[:max_versions] or [None]):
        for leaf in pick_samples(leaves, samples):
            st, data = fetch_text(client, leaf["ref"], vt)
            desc = describe_v3_response(st, data)
            sample = {"ref": leaf["ref"], "version": vt or "(ברירת מחדל)",
                      "http_status": st, "shape": desc.get("shape"),
                      "error": desc.get("error")}
            if isinstance(data, dict) and isinstance(data.get("versions"), list) \
                    and data["versions"]:
                v0 = data["versions"][0]
                strings = flatten_strings(v0.get("text") if isinstance(v0, dict) else None)
                a = analyze_texts(strings)
                sample["analysis"] = a
                sample["first_strings"] = [s[:200] for s in strings[:3]]
                analyses.append(a)
            rec["samples"].append(sample)
    rec["aggregate"] = merge_analyses(analyses) if analyses else {}
    return rec


def v3_probes(client: Client, title: str, nodes: list) -> list:
    """בדיקות התנהגות של api/v3/texts על אינדקס אחד: עלה, צומת ביניים,
    טווח בתוך עלה, טווח בין שני עלים סמוכים, והאינדקס כולו."""
    leaves = [n for n in nodes if n["leaf"]]
    inner = [n for n in nodes if not n["leaf"] and n["depth"] > 0]
    probes = []
    if leaves:
        probes.append(("עלה", leaves[0]["ref"]))
        probes.append(("טווח בתוך עלה (1-3)", leaves[0]["ref"] + " 1-3"))
        probes.append(("סגמנט בודד (:1 / 1)", leaves[0]["ref"] + " 1"))
    if len(leaves) >= 2:
        a, b = leaves[0], leaves[1]
        probes.append(("טווח בין עלים (ref מלא-ref מלא)", f"{a['ref']}-{b['ref']}"))
        probes.append(("טווח בין עלים (ref-כותר)", f"{a['ref']}-{b['title']}"))
    if inner:
        probes.append(("צומת ביניים", inner[0]["ref"]))
    probes.append(("האינדקס כולו", title))
    out = []
    for kind, ref in probes:
        st, data = fetch_text(client, ref)
        out.append({"index": title, "kind": kind, "ref": ref,
                    "result": describe_v3_response(st, data)})
    return out


def run_survey(client: Client, limit: int = None, nusach: str = None,
               samples: int = 5, max_versions: int = 3,
               seeds=SEED_TITLES, args_meta=None, log=print) -> dict:
    snap = {"meta": {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "base": client.base, "endpoints": ENDPOINTS,
                     "args": args_meta or {}},
            "toc_matches": [], "seed_checks": {}, "indexes": {},
            "v3_probes": [], "errors": []}
    log("1/4 עץ התוכן (/api/index)…")
    st, toc = client.get(ENDPOINTS["toc"])
    if toc is None:
        log("    ✗ עץ התוכן לא הושג — האם sefaria.org נגיש מכאן? (שאלה 8.1)")
        snap["errors"] = client.errors
        return snap  # אין טעם לנסות עוד עשרות בקשות שייכשלו
    snap["toc_matches"] = walk_toc(toc)
    log(f"    {len(snap['toc_matches'])} אינדקסים תואמים")

    log("2/4 זרעי חיפוש (לא מאומתים)…")
    snap["seed_checks"] = check_seeds(client, seeds)
    known = {e["title"] for e in snap["toc_matches"]}
    for seed, info in snap["seed_checks"].items():
        if info.get("is_index") and seed not in known:
            snap["toc_matches"].append({"title": seed, "heTitle": "",
                                        "categories": ["(זרע)"]})

    entries = snap["toc_matches"]
    if nusach:
        n = nusach.lower()
        entries = [e for e in entries
                   if n in e["title"].lower() or n in (e.get("heTitle") or "")
                   or n in guess_nusach(e["title"], e.get("heTitle", "")).lower()]
    if limit:
        entries = entries[:limit]

    log(f"3/4 סוקר {len(entries)} אינדקסים…")
    for k, e in enumerate(entries, 1):
        log(f"    [{k}/{len(entries)}] {e['title']}")
        snap["indexes"][e["title"]] = survey_index(client, e, samples, max_versions)

    log("4/4 בדיקות התנהגות api/v3/texts…")
    probed = 0
    for title, rec in snap["indexes"].items():
        if rec.get("nodes") and rec["schema_summary"].get("max_depth", 0) >= 1:
            snap["v3_probes"] += v3_probes(client, title, rec["nodes"])
            probed += 1
            if probed >= 2:
                break
    snap["errors"] = client.errors
    return snap


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="סקר הסידור ב-Sefaria (PLAN_TEFILA.md 0.1)")
    ap.add_argument("--limit", type=int, help="מספר אינדקסים מרבי לסקירה")
    ap.add_argument("--nusach", help="סינון לפי תת-מחרוזת בכותר/בנוסח המשוער")
    ap.add_argument("--samples", type=int, default=5, help="עלים לדגימה בכל גרסה")
    ap.add_argument("--max-versions", type=int, default=3,
                    help="גרסאות עבריות מרביות לדגימה בכל אינדקס")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="שניות בין בקשות רשת (נימוס כלפי Sefaria)")
    ap.add_argument("--cache-dir", default=str(Path.home() / ".cache"
                                               / "kriat-hatora-sefaria"))
    ap.add_argument("--offline", action="store_true", help="רק מה-cache")
    ap.add_argument("--base", default=SEFARIA_BASE)
    ap.add_argument("--out-md", default=str(ROOT / "docs" / "siddur_survey.md"))
    ap.add_argument("--out-json", default=str(ROOT / "data" / "siddur"
                                              / "sefaria_index_snapshot.json"))
    args = ap.parse_args(argv)

    client = Client(args.base, args.cache_dir, delay=args.delay,
                    offline=args.offline)
    meta = {k: v for k, v in vars(args).items()
            if k in ("limit", "nusach", "samples", "max_versions")}
    snap = run_survey(client, args.limit, args.nusach, args.samples,
                      args.max_versions, args_meta=meta)
    if not snap["indexes"] and not snap["toc_matches"]:
        print("✗ לא נאסף שום נתון — לא כותב פלט (כדי לא לדרוס סקר קודם).")
        return 1
    for path, content in (
            (args.out_json, json.dumps(snap, ensure_ascii=False, indent=1)),
            (args.out_md, render_report(snap))):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        print(f"✅ נכתב: {path}")
    print(f"בקשות רשת: {client.n_network}, מה-cache: {client.n_cached}, "
          f"שגיאות: {len(client.errors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
