# -*- coding: utf-8 -*-
"""הפרדת הוראות מטקסט נאמר בפסקה של הסידור (PLAN_TEFILA.md 8.4, ‏4.2.2).

מימוש יחיד: משרת גם את ‏api/siddur.py (יחידות טקסט) וגם את
tools/build_siddur_catalog.py ("מילים ראשונות" בקטלוג). ספריה סטנדרטית בלבד.

הכלל (מהסקר, ‏docs/siddur_survey.md סעיף ד), מדויק על הטקסט המלא של כל
העלים בקטלוג (29.10.2026):
- תוכן של ‏<small>, סוגריים עגולים ומרובעים ("אזור מסומן"): מילה **לא מנוקדת**
  ⇐ הוראה; מילה **מנוקדת** ⇐ טקסט נאמר (אולי אופציונלי/חלופי).
- חריג: שם ה׳ לא מנוקד (‏ה', ‏יי, גם עם תחילית — ‏לה', ‏וה') **נאמר** (דעת
  אשכנז). הוא "ניטרלי": מקבל את הסוג של שכנו באותו אזור, כך שבתוך הוראה
  של מצודה ("<small>…ברוך ה'…</small>") הוא נשאר הוראה.
- אזור מסומן מעורב שעד מחציתו מנוקד ⇐ כולו הוראה: הלכה שמצטטת מילים
  מנוקדות ("מדלגים ל:יָמִין וּשְׂמֹאל"), ותוספת לפי זמן ("(ביו"ט מוסיפים:
  בְּשִׂמְחָה)", "(בעשי"ת הַשָּׁלוֹם)") — ברירת המחדל היא יום רגיל. אזור שרובו
  מנוקד מתפצל לפי מילים ("קהל: קַבֵּל בְּרַחֲמִים" ⇐ הוראה "קהל:" + נאמר).
- שורה (עד ‏<br>) שפחות מ-40% ממילותיה מנוקדות ⇐ כולה הוראה (כותרת "אשרי
  יושבי ביתך", "שליח ציבור:", הלכה).
- מחוץ לאזור מסומן מילה לא מנוקדת נאמרת (בדעת חולם מלא נכתב בלי ניקוד:
  ‏"עוד", ‏"יום"), חוץ מקיצור עם גרשיים/גרש (‏בעשי"ת, ‏ג"פ, ‏וכו') ומרצף של
  3 מילים לא מנוקדות ומעלה ("ואומר החזן:") ⇐ הוראה.
- מילה לא מנוקדת בודדת בתוך אזור מסומן, בין שתי מילים מנוקדות של אותו
  אזור, נאמרת (חולם מלא של דעת בתוך ‏<small> מנוקד).

הפלט של classify_paragraph הוא רשימת חלקים [(kind, text)] לפי הסדר, ‏kind
‏"spoken" או "instruction"; ‏text הוא הטקסט הנקי (בלי HTML), עם מעברי שורה
(‏<br>) כ-"\\n" — גבול קשיח לחותך הפרוזה.
"""

import html
import re
import unicodedata

from chunker.chunker import (_FOOTNOTE_RE, _HEBREW_LETTER_RE,
                             _INVISIBLE_RE, _NIQQUD_RE, is_tefila_divine_name)

SPOKEN = "spoken"
INSTRUCTION = "instruction"

# HTML: תגית | ישות | רצף טקסט | תו "<"/"&" בודד
_PIECE_RE = re.compile(r"<[^>]*>|&#?[A-Za-z0-9]+;|[^<&]+|[<&]", re.S)
_SMALL_OPEN_RE = re.compile(r"^<\s*small\b", re.I)
_SMALL_CLOSE_RE = re.compile(r"^<\s*/\s*small\b", re.I)
_BR_TAG_RE = re.compile(r"^<\s*br\b", re.I)
_PAIRS = {"(": ")", "[": "]"}
_OPENERS = frozenset("([{")
# קיצור: גרשיים בין אותיות (בעשי"ת) או גרש אחרי אות (וכו', פי׳)
_ABBR_RE = re.compile("[א-ת][\"״”][א-ת]"
                      "|[א-ת]['׳’]")
_TAAMIM_RE = re.compile("[֑-֯]")
_EDGE_PUNCT = ".,:;?!()[]{}\"“”״-–—׃׀"
_BREAK = "\n"
# שורה שפחות מ-40% ממילותיה מנוקדות — כולה הוראה (שם ה׳ לא נספר). פסוק עם
# תגובת קהל לא מנוקדת ("…וְיִשְׁמְרֶךָ, עונים: כן יהי רצון") נשאר נאמר,
# והתגובה נתפסת ככלל הרצף שלמטה.
MIN_SPOKEN_SHARE = 0.4
# אזור מסומן מעורב שעד מחצית מילותיו מנוקדות — כולו הוראה
MIXED_REGION_MAX_SHARE = 0.5
# רצף כזה של מילים לא מנוקדות מחוץ לסימון ⇐ הוראה ("שליח ציבור אומר:");
# קצר ממנו נאמר (חולם מלא בלי ניקוד בדעת: "עוד", "יום")
MIN_UNMARKED_RUN = 3


# --- סריקה --------------------------------------------------------------------

def _scan(text: str):
    """HTML ⇐ (תווים, מזהה אזור לכל תו). אזור 0 = לא מסומן; כל ‏<small>
    חיצוני וכל זוג סוגריים מאוזן (מחוץ ל-small) מקבל מזהה משלו."""
    text = unicodedata.normalize("NFC", text or "")
    text = _FOOTNOTE_RE.sub(" ", text)
    chars, regions = [], []
    depth, next_id, cur = 0, 1, 0
    for piece in _PIECE_RE.findall(text):
        if piece.startswith("<") and piece.endswith(">") and len(piece) > 1:
            if _SMALL_OPEN_RE.match(piece):
                if depth == 0:
                    cur, next_id = next_id, next_id + 1
                depth += 1
            elif _SMALL_CLOSE_RE.match(piece):
                depth = max(0, depth - 1)
            elif _BR_TAG_RE.match(piece):
                chars.append(_BREAK)
                regions.append(cur if depth else 0)
            # שאר התגיות (b, big, em…) מוסרות בלי רווח, כמו clean_sefaria_text
            continue
        if piece.startswith("&") and piece.endswith(";"):
            piece = html.unescape(piece)
        piece = _INVISIBLE_RE.sub("", piece)  # NBSP הוא רווח (isspace)
        for ch in piece:
            chars.append(ch)
            regions.append(cur if depth else 0)
    # סוגריים מאוזנים בלבד (סוגר בלי פותח — סתם תו)
    stack, spans = [], []
    for i, ch in enumerate(chars):
        if ch in _PAIRS:
            stack.append(i)
        elif ch in _PAIRS.values():
            for k in range(len(stack) - 1, -1, -1):
                if _PAIRS[chars[stack[k]]] == ch:
                    spans.append((stack[k], i))
                    del stack[k:]
                    break
    spans.sort()
    end = -1
    for a, b in spans:
        if a <= end:  # זוג פנימי — כבר בתוך אזור
            continue
        rid, next_id, end = next_id, next_id + 1, b
        for k in range(a, b + 1):
            if regions[k] == 0:
                regions[k] = rid
    return chars, regions


def _tokens(text: str) -> list:
    """HTML ⇐ טוקנים: {"t": טקסט, "r": אזור} או {"br": True}."""
    chars, regions = _scan(text)
    out, buf, reg = [], [], []

    def flush():
        if buf:
            tok = "".join(buf)
            heb = [r for c, r in zip(buf, reg) if "\u05D0" <= c <= "\u05EA"]
            out.append({"t": tok, "r": (heb or reg)[0]})
            buf.clear()
            reg.clear()

    for ch, r in zip(chars, regions):
        if ch == _BREAK:
            flush()
            out.append({"br": True})
        elif ch.isspace():
            flush()
        else:
            buf.append(ch)
            reg.append(r)
    flush()
    return out


def _word_class(tok: str) -> str:
    """‏P פיסוק (בלי אות) · ‏S מנוקד · ‏N שם ה׳ לא מנוקד · ‏U לא מנוקד."""
    if not _HEBREW_LETTER_RE.search(tok):
        return "P"
    if _NIQQUD_RE.search(tok):
        return "S"
    if is_tefila_divine_name(tok):
        return "N"
    return "U"


def _is_abbr(tok: str) -> bool:
    return bool(_ABBR_RE.search(tok))


# --- סיווג ----------------------------------------------------------------------

def _vocalized_share(tokens: list) -> float:
    """חלק המילים המנוקדות מתוך המילים "החזקות" (מנוקדות + לא מנוקדות)."""
    s = sum(1 for t in tokens if t["c"] == "S")
    u = sum(1 for t in tokens if t["c"] == "U")
    return s / (s + u) if s + u else 0.0


def _classify_tokens(toks: list) -> list:
    """מוסיף לכל טוקן (לא מעבר שורה) "k": ‏SPOKEN / ‏INSTRUCTION."""
    words = [t for t in toks if "t" in t]
    for t in words:
        t["c"] = _word_class(t["t"])
    # שורה (עד ‏<br>) שאין בה ניקוד, או שרובה לא מנוקד — כולה הוראה
    # (כותרת, "שליח ציבור:", הלכה שמצטטת מילים מנוקדות)
    line = []
    for t in toks + [{"br": True}]:
        if "br" not in t:
            line.append(t)
            continue
        if _vocalized_share([w for w in line if w["c"] != "P"]) < MIN_SPOKEN_SHARE:
            for w in line:
                w["k"] = INSTRUCTION
        line = []
    content = [t for t in words if t["c"] != "P" and "k" not in t]
    by_region = {}
    for t in content:
        by_region.setdefault(t["r"], []).append(t)
    # אזור מסומן שרובו לא מנוקד — כולו הוראה, כולל מילים מנוקדות שהוא
    # מצטט ("מדלגים ל: יָמִין וּשְׂמֹאל") או תוספת לפי זמן ("(ביו"ט
    # מוסיפים: בְּשִׂמְחָה)", "(בעשי"ת הַשָּׁלוֹם)") — ברירת המחדל היא יום רגיל.
    whole = {r for r, ts in by_region.items()
             if r and any(t["c"] == "U" for t in ts)
             and _vocalized_share(ts) <= MIXED_REGION_MAX_SHARE}
    # שלב 1: מילים "חזקות" (S, ‏U)
    for i, t in enumerate(content):
        if t["r"] in whole:
            t["k"] = INSTRUCTION
        elif t["c"] == "S":
            t["k"] = SPOKEN
        elif t["c"] == "U" and t["r"] == 0:
            t["k"] = (INSTRUCTION if _is_abbr(t["t"])
                      or _unvocalized_run(content, i) >= MIN_UNMARKED_RUN
                      else SPOKEN)
        elif t["c"] == "U":
            prev = content[i - 1] if i > 0 else None
            nxt = content[i + 1] if i + 1 < len(content) else None
            sandwiched = (prev and nxt and not _is_abbr(t["t"])
                          and prev["c"] == nxt["c"] == "S"
                          and prev["r"] == nxt["r"] == t["r"])
            t["k"] = SPOKEN if sandwiched else INSTRUCTION
    # שלב 2: שם ה׳ לא מנוקד — הסוג של השכן הקרוב באותו אזור
    for i, t in enumerate(content):
        if t["c"] != "N" or "k" in t:
            continue
        if t["r"] == 0:
            t["k"] = SPOKEN
            continue
        # כל אזור הוא רצף אחד, ולכן "אותו מזהה" = "אותו אזור, ברצף"
        near = content[:i][::-1] + content[i + 1:]  # קודם אחורה, אחר-כך קדימה
        o = next((o for o in near if o["r"] == t["r"] and o["c"] in "SU"),
                 None)
        t["k"] = o["k"] if o else SPOKEN
    # שלב 3: פיסוק — פותח הולך עם הבא, כל השאר עם הקודם
    for i, t in enumerate(words):
        if t["c"] != "P" or "k" in t:
            continue
        prev = next((w for w in reversed(words[:i]) if "k" in w), None)
        nxt = next((w for w in words[i + 1:] if w["c"] != "P"), None)
        opener = all(ch in _OPENERS for ch in t["t"])
        pick = (nxt or prev) if opener else (prev or nxt)
        t["k"] = pick["k"] if pick else SPOKEN
    return toks


def _unvocalized_run(content: list, i: int) -> int:
    """אורך רצף המילים הלא מנוקדות (לא שם ה׳) מחוץ לסימון סביב מילה i."""
    def ok(t):
        return t["c"] == "U" and t["r"] == 0
    a = i
    while a > 0 and ok(content[a - 1]):
        a -= 1
    b = i
    while b + 1 < len(content) and ok(content[b + 1]):
        b += 1
    return b - a + 1


def classify_paragraph(text: str) -> list:
    """פסקה (HTML כמו שהגיעה מ-Sefaria) ⇐ [(kind, טקסט נקי)] לפי הסדר.

    חלקים סמוכים מאותו סוג מאוחדים; חלק בלי אות עברית נזרק (הפיסוק שלו
    כבר הודבק לשכן). פסקה ריקה ⇐ [].
    """
    toks = _classify_tokens(_tokens(text))
    parts = []  # [kind, [שורות של מילים]]
    for t in toks:
        if "br" in t:
            if parts:
                parts[-1][1].append([])
            continue
        if not parts or parts[-1][0] != t["k"]:
            parts.append([t["k"], [[]]])
        parts[-1][1][-1].append(t["t"])
    out = []
    for kind, lines in parts:
        body = "\n".join(" ".join(ln) for ln in lines if ln).strip()
        if _HEBREW_LETTER_RE.search(body):
            if out and out[-1][0] == kind:
                out[-1] = (kind, out[-1][1] + " " + body)
            else:
                out.append((kind, body))
    return out


def display_word(tok: str) -> str:
    """מילה לתצוגה קצרה (מילים ראשונות): בלי טעמים ובלי פיסוק בקצוות."""
    return _TAAMIM_RE.sub("", tok).strip(_EDGE_PUNCT).lstrip("'׳")


def first_words(paragraphs, n: int = 5) -> str:
    """המילים הנאמרות הראשונות (לחיפוש "לפי מילים ראשונות" ולתצוגה).

    ‏paragraphs — מחרוזת או רשימה (מקוננת) של פסקאות. נספרות רק מילים
    מנוקדות או שם ה׳ מתוך החלקים הנאמרים — מילה לא מנוקדת (חולם מלא של
    דעת) מדולגת, כך שהמפתח לחיפוש יציב בין המהדורות.
    """
    words = []
    for para in _flatten(paragraphs):
        for kind, body in classify_paragraph(para):
            if kind != SPOKEN:
                continue
            for tok in body.split():
                w = display_word(tok)
                if _word_class(w) in ("S", "N"):
                    words.append(w)
                    if len(words) >= n:
                        return " ".join(words)
    return " ".join(words)


def has_vocalized(paragraphs) -> bool:
    """האם יש בטקסט מילה מנוקדת אחת לפחות. עלה בלי אף מילה מנוקדת (למשל
    "קידושא רבה" בדעת אשכנז) הוא מהדורה לא מנוקדת — לא הוראות."""
    return any(_word_class(t["t"]) == "S"
               for p in _flatten(paragraphs) for t in _tokens(p) if "t" in t)


def flatten(obj) -> list:
    """טקסט של עלה (מחרוזת / רשימה / רשימה מקוננת, עומק > 1) ⇐ פסקאות לפי
    הסדר."""
    return _flatten(obj)


def _flatten(obj) -> list:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, list):
        return [s for x in obj for s in _flatten(x)]
    return []
