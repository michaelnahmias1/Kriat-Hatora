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
from collections import Counter

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
    """HTML ⇐ (תווים, מזהה אזור לכל תו, (מזהה פנימי, עומק) לכל תו).

    אזור 0 = לא מסומן; כל ‏<small> חיצוני וכל זוג סוגריים מאוזן (מחוץ
    ל-small) מקבל מזהה משלו — זה מה שהסיווג משתמש בו. בנוסף, לתוספות
    תלויות-יום (classify_leaf): המזהה הפנימי — של ה-<small> או זוג הסוגריים
    הפנימי ביותר סביב התו (גם בתוך small אחר), והעומק — כמה כאלה עוטפים
    אותו."""
    text = unicodedata.normalize("NFC", text or "")
    text = _FOOTNOTE_RE.sub(" ", text)
    chars, regions, inner = [], [], []
    depth, next_id, cur = 0, 1, 0
    stack = []   # מזהים פנימיים של ה-<small> הפתוחים
    for piece in _PIECE_RE.findall(text):
        if piece.startswith("<") and piece.endswith(">") and len(piece) > 1:
            if _SMALL_OPEN_RE.match(piece):
                if depth == 0:
                    cur, next_id = next_id, next_id + 1
                depth += 1
                stack.append(next_id)
                next_id += 1
            elif _SMALL_CLOSE_RE.match(piece):
                depth = max(0, depth - 1)
                if stack:
                    stack.pop()
            elif _BR_TAG_RE.match(piece):
                chars.append(_BREAK)
                regions.append(cur if depth else 0)
                inner.append([stack[-1] if stack else 0, len(stack)])
            # שאר התגיות (b, big, em…) מוסרות בלי רווח, כמו clean_sefaria_text
            continue
        if piece.startswith("&") and piece.endswith(";"):
            piece = html.unescape(piece)
        piece = _INVISIBLE_RE.sub("", piece)  # NBSP הוא רווח (isspace)
        for ch in piece:
            chars.append(ch)
            regions.append(cur if depth else 0)
            inner.append([stack[-1] if stack else 0, len(stack)])
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
    # מזהה פנימי: החיצוני קודם, הפנימי דורס אותו
    for a, b in sorted(spans, key=lambda ab: ab[0] - ab[1]):
        iid, next_id = next_id, next_id + 1
        for k in range(a, b + 1):
            inner[k][0] = iid
            inner[k][1] += 1
    return chars, regions, inner


def _tokens(text: str) -> list:
    """HTML ⇐ טוקנים: {"t": טקסט, "r": אזור, "ir": אזור פנימי, "d": עומק
    הסימון} או {"br": True}."""
    chars, regions, inner = _scan(text)
    out, buf, reg = [], [], []

    def flush():
        if buf:
            tok = "".join(buf)
            # \u05D4\u05D0\u05D6\u05D5\u05E8 \u05E9\u05DC \u05D4\u05D0\u05D5\u05EA \u05D4\u05E2\u05D1\u05E8\u05D9\u05EA \u05D4\u05E8\u05D0\u05E9\u05D5\u05E0\u05D4 (\u05E1\u05D5\u05D2\u05E8/\u05E4\u05D5\u05EA\u05D7 \u05E6\u05DE\u05D5\u05D3 \u05DC\u05D0 \u05E7\u05D5\u05D1\u05E2)
            heb = [x for x in reg if "\u05D0" <= x[0] <= "\u05EA"]
            _, r, (ir, d) = (heb or reg)[0]
            out.append({"t": tok, "r": r, "ir": ir, "d": d})
            buf.clear()
            reg.clear()

    for ch, r, (ir, d) in zip(chars, regions, inner):
        if ch == _BREAK:
            flush()
            out.append({"br": True})
        elif ch.isspace():
            flush()
        else:
            buf.append(ch)
            reg.append((ch, r, (ir, d)))
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


# =============================================================================
# תוספות תלויות-יום (PLAN_TEFILA.md 4.4.2)
# =============================================================================
# הוראה שמציינת יום/עונה ("בעשי"ת:", "בקיץ:", "לר"ח:", "(ביו"ט מוסיפים:",
# "בראש חדש ובחול המועד אומרים זה:") ואחריה טקסט מנוקד = תוספת תלויית-יום.
# הטקסט הזה נאמר רק כשהיום מתאים — לכן הוא מסומן CONDITIONAL עם התנאי שלו,
# וה-API מחליט אם הוא נכנס ליישור (src/siddur/days.py). אוצר המילים נבנה
# מסריקת כל 791 העלים הזמינים (29.10.2026) — הספירות בסטטוס של 4.4.2.
#
# התנאי ("cond"): ‏{"any": [[slug, ...], ...], "negate": bool, "names": [...]}
# — "או" בין הרשימות, "וגם" בתוך רשימה ("בשבת חוה"מ פסח" = שבת וגם חוה"מ
# פסח; "בחנוכה ופורים" = חנוכה או פורים). ‏negate — "אין אומרים ב…",
# "בימים שיש בהם תחנון": נאמר בכל יום חוץ מהימים האלה.
#
# היקף התוספת (מה נחשב לטקסט של ההוראה):
# 1. בתוך אותה פסקה, אחרי ההוראה: אם הטקסט שאחריה בתוך אזור מסומן (‏<small>
#    / סוגריים — גם האזור של ההוראה עצמה: "<small><small>בעשי"ת:</small>
#    זָכְרֵנוּ…</small> מֶלֶךְ עוֹזֵר") — עד סוף האזור. אחרת — עד ההוראה
#    הבאה, מעבר שורה או סוף הפסקה ("<small>בקיץ:</small> מוֹרִיד הַטָּל.").
# 2. הוראה בסוף פסקה (בלי טקסט אחריה) — הפסקה הבאה: אם היא כולה מסומנת
#    (עדות המזרח: התוספות כולן ב-<small>) — כל הפסקאות המסומנות שאחריה, עד
#    פסקה לא מסומנת או פסקת הוראה בלבד; אחרת — הפסקה הבאה בלבד, עד ההוראה
#    הראשונה בה. חריג אחד: "יעלה ויבוא" שמתפצל לכמה פסקאות (מצודה ספרד) —
#    עד הפסקה שבה "…חַנּוּן וְרַחוּם אָתָּה".
# 3. הוראה שאומרת את שם התוספת ("בתענית ציבור אומר כאן הש"ץ עננו") — חלה רק
#    אם הטקסט שאחריה באמת מתחיל בשם הזה (אחרת זו הפניה למקום אחר).
# 4. הלכה ארוכה שהמשפט הראשון שלה הוא הוראה כזו ("בחנוכה ופורים אומרים על
#    הנסים. שכח לומר…") — רק לפי כלל 3.
# 5. תוספת בתוך אזור מסומן שרובו לא מנוקד ("(ביו"ט מוסיפים: בְּשִׂמְחָה)",
#    "(בעשי"ת הַשָּׁלוֹם)") — שהכלל הכללי מסווג כולו כהוראה — מתפצלת להוראה +
#    תוספת.
# כותרת = ביטוי יום בתחילתה, ושאר המילים רק ביטויי יום, פעלים/מקום
# (_FILLERS), שלילה או שם תוספת (_NAMES). הוראה עם מילים אחרות ("בעשי"ת
# השלום", "בעשרת ימי תשובה אומרים: המלך הקדוש" — התחליף כתוב בלי ניקוד בתוך
# ההוראה; "קריאה לחוה"מ פסח" — כותרת של קטע) נשארת הוראה כמו קודם.
#
# קיץ/חורף: אותה הוראה ("בקיץ:") משמשת לשני מקומות שמתחלפים בזמנים שונים
# (משיב הרוח — משמיני עצרת; ותן טל ומטר — מז' בחשוון), ולכן העונה מתורגמת
# לפי הטקסט עצמו: ‏morid-hatal/mashiv-haruach או veten-bracha/tal-umatar.

CONDITIONAL = "conditional"

# סדר התצוגה של התנאים (מתגים בממשק) ותוויותיהם
CONDITION_LABELS = {
    "shabbat": "שבת",
    "motzei-shabbat": "מוצאי שבת",
    "rosh-chodesh": "ראש חודש",
    "aseret-yemei-teshuva": "עשרת ימי תשובה",
    "rosh-hashana": "ראש השנה",
    "yom-kippur": "יום כיפור",
    "yom-tov": "יום טוב",
    "pesach": "פסח",
    "shavuot": "שבועות",
    "sukkot": "סוכות",
    "shemini-atzeret": "שמיני עצרת",
    "chol-hamoed": "חול המועד",
    "chol-hamoed-pesach": "חול המועד פסח",
    "chol-hamoed-sukkot": "חול המועד סוכות",
    "chanukah": "חנוכה",
    "purim": "פורים",
    "taanit": "תענית ציבור",
    "tisha-bav": "תשעה באב",
    "no-tachanun": "יום שאין בו תחנון",
    "half-hallel": "יום של חצי הלל",
    "beit-avel": "בבית האבל",
    "morid-hatal": "מוריד הטל (קיץ)",
    "mashiv-haruach": "משיב הרוח (חורף)",
    "veten-bracha": "ותן ברכה (קיץ)",
    "tal-umatar": "ותן טל ומטר (חורף)",
    "sunday": "יום ראשון",
    "monday": "יום שני",
    "tuesday": "יום שלישי",
    "wednesday": "יום רביעי",
    "thursday": "יום חמישי",
    "friday": "יום שישי",
}
# קבוצות שמוציאות זו את זו — הממשק מציג אותן כבחירה אחת
CONDITION_GROUPS = {
    "gevurot": ("morid-hatal", "mashiv-haruach"),
    "barech": ("veten-bracha", "tal-umatar"),
    "dow": ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday"),
    "chag": ("pesach", "shavuot", "sukkot", "shemini-atzeret"),
}
GROUP_OF = {s: g for g, ss in CONDITION_GROUPS.items() for s in ss}

_SUMMER, _WINTER = "~summer", "~winter"   # עד שהטקסט קובע איזו עונה
_DOW = {"ראשון": "sunday", "שני": "monday", "שלישי": "tuesday",
        "רביעי": "wednesday", "חמישי": "thursday", "שישי": "friday",
        "ששי": "friday"}
# עד כמה מילים הוראה יכולה להיות כותרת של תוספת
MAX_HEADER_WORDS = 10

_HP = r"(?P<vav>ו)?(?:ב|ל)?"   # תחילית: ו, ב, ל ("ובחול המועד", "לר"ח")


def _lex(pattern: str, alts, negate: bool = False):
    return (re.compile("^" + _HP + "(?:" + pattern + r")(?=\s|$)"), alts, negate)


def _chol_hamoed(m):
    fest = m.group("fest") or ""
    if fest == "פסח":
        return [["chol-hamoed-pesach"]]
    if fest in ("סוכות", "סכות"):
        return [["chol-hamoed-sukkot"]]
    return [["chol-hamoed"]]


# אוצר הביטויים — לפי הסדר (הארוך קודם). הטקסט מנורמל (_norm): בלי ניקוד
# וטעמים, גרשיים/גרש אחידים, בלי סוגריים ופיסוק.
_TACHANUN = r"(?:תחנון|נפילת אפים|נפילת אפיים)"
_LEXICON = [
    _lex(r"(?:ימים|יום|ימי) ש(?:אין|לא) (?:גומרים|גומרין)(?: בהם| בו)?(?: את)? ה?הלל",
         [["half-hallel"]]),
    _lex(r"(?:ימים|יום|ימי) ש(?:גומרים|גומרין)(?: בהם| בו)?(?: את)? ה?הלל",
         [["half-hallel"]], negate=True),
    _lex(r"(?:ימים|יום|ימי) ש(?:אין|לא) (?:אומרים|אומרין|נופלים|נופלין|אומר)"
         r"(?: על פניהם)?(?: בהם| בו)? " + _TACHANUN, [["no-tachanun"]]),
    _lex(r"(?:ימים|יום|ימי) ש(?:אין|לא) (?:בהם|בו) " + _TACHANUN,
         [["no-tachanun"]]),
    _lex(r"(?:ימים|יום|ימי) ש(?:יש|אומרים|אומרין)(?: בהם| בו)? " + _TACHANUN,
         [["no-tachanun"]], negate=True),
    _lex(r"שבת (?:ש?תשובה|שובה)", [["aseret-yemei-teshuva", "shabbat"]]),
    _lex(r'עשי"ת|עשרת ימי ה?תשובה|ימים ה?נוראים', [["aseret-yemei-teshuva"]]),
    _lex(r'מוצאי שבת(?: קודש| קדש)?|מוצ"ש|מוצש"ק|מוצאי', [["motzei-shabbat"]]),
    _lex(r"(?:יום )?(?P<dow>ראשון|שני|שלישי|רביעי|חמישי|שישי|ששי) (?:ב|ל)שבת",
         lambda m: [[_DOW[m.group("dow")]]]),
    _lex(r"יום (?P<dow>ראשון|שני|שלישי|רביעי|חמישי|שישי|ששי)",
         lambda m: [[_DOW[m.group("dow")]]]),
    _lex(r"שני וחמישי|ב' וה'", [["monday"], ["thursday"]]),
    _lex(r'ראש ה?חו?דש|ר"ח', [["rosh-chodesh"]]),
    _lex(r'ראש השנה|ר"ה', [["rosh-hashana"]]),
    _lex(r'יום ה?כיפורים|יום ה?כפורים|יום כיפור|יום כפור|יוה"כ|יוהכ"פ|יו"כ',
         [["yom-kippur"]]),
    _lex(r'(?:חול המועד|חולו של מועד|חוה"מ|חה"מ)'
         r'(?: (?:של |ד|ב|ל)?(?P<fest>פסח|סוכות|סכות))?', _chol_hamoed),
    _lex(r'הושענא רבה|הושע"ר', [["chol-hamoed-sukkot"]]),
    _lex(r'שמיני עצרת|שמחת תורה|שמע"צ|שמ"ע ו?ב?ש"ת|שמ"ע', [["shemini-atzeret"]]),
    _lex(r"יום טוב|יו\"ט|ימים טובים|(?:ג'|שלש|שלוש|שלשה|שלושה) רגלים|רגלים|רגל",
         [["yom-tov"]]),
    _lex(r"פסח", [["pesach"]]),
    _lex(r"שבועות", [["shavuot"]]),
    _lex(r"סוכות|סכות", [["sukkot"]]),
    _lex(r"(?:ליל )?שבת(?: קודש| קדש)?|יום השבת|שבתות", [["shabbat"]]),
    _lex(r"חנוכה", [["chanukah"]]),
    _lex(r"(?:שושן )?פורים", [["purim"]]),
    _lex(r"תשעה באב|ט' באב|ט\"ב", [["tisha-bav"]]),
    _lex(r"(?:שבעה עשר|י\"ז) ב?תמוז|(?:עשרה|י') ב?טבת|צום גדליה|תענית אסתר",
         [["taanit"]]),
    _lex(r"(?:יום )?תענית (?:ציבור|צבור|אסתר)|(?:יום )?תענית|תעניות|ת\"צ|(?:יום )?צום"
         r"|(?:ארבע|ד'|ג') צומות", [["taanit"]]),
    _lex(r"בית ה?אבל|בית אבלים", [["beit-avel"]]),
    _lex(r"ה?קיץ|ימות החמה|ימי הקיץ", [[_SUMMER]]),
    _lex(r"ה?חורף|ימות הגשמים|ימי הגשמים|ימי החורף", [[_WINTER]]),
]
# מילים שמותרות בכותרת (פעלים, מי אומר, איפה) — גם עם ו' בתחילתן
_FILLERS = frozenset("""
אומרים אומרין אומר יאמר יאמרו אומרת מוסיפים מוסיפין מוסיף מסיים מסיימים
מסיימין יסיים חותם חותמים חותמין מתחילים מתחילין מתחיל ממשיכים כאן זה זו את
אלו הש"ץ ש"ץ החזן חזן שליח השליח ציבור צבור הקהל קהל היחיד יחיד בחזרה בחזרת
בלחש בתפלת בתפילת הלחש בשחרית במנחה בערבית במוסף במנחת בתפלה בתפילה תפלת
תפילת תפלה תפילה ברכה מזמור פסוק נוסח בנוסח כשחל שחל חל המשולש משולש דמוקפין
מוקפין המוקפין גם כן רק של שיר
""".split())
_NEGATIONS = frozenset("אין לא מדלגים מדלגין מדלג".split())
# שמות של תוספות שהוראה יכולה להזכיר ("אומרים כאן עננו") — כלל 3 למעלה
_NAMES = ("על הנסים", "על הניסים", "יעלה ויבא", "יעלה ויבוא", "עננו",
          "חצי הלל", "הלל שלם", "ההלל", "הלל", "ברכת כהנים", "אבינו מלכנו",
          "אבינו מלכינו",
          "ותודיענו", "ברכי נפשי", "למנצח")
_NORM_SUB_RE = re.compile("[֑-ֽֿ-ׇ]")
_NORM_PUNCT_RE = re.compile("[()\\[\\]{}<>:;,.!?…|׃׀\\-–—]")


def _norm(text: str) -> str:
    """טקסט ⇐ צורה להשוואה: בלי ניקוד וטעמים, מקף ⇐ רווח, גרשיים אחידים,
    בלי סוגריים ופיסוק."""
    t = unicodedata.normalize("NFC", text or "").replace("־", " ")
    t = _NORM_SUB_RE.sub("", t)
    t = re.sub("[״”“]", '"', t)
    t = re.sub("[׳’‘`]", "'", t)
    t = _NORM_PUNCT_RE.sub(" ", t)
    return " ".join(t.split())


def _strip_vav(w: str) -> str:
    return w[1:] if w.startswith("ו") and len(w) > 2 else w


def _match_name(rest: str):
    """שם תוספת בתחילת rest (מנורמל), גם עם ו' — או None."""
    for name in _NAMES:
        for cand in (name, "ו" + name):
            if rest == cand or rest.startswith(cand + " "):
                return name
    return None


def parse_header(text: str):
    """טקסט של הוראה ⇐ התנאי שלה (cond) אם היא כותרת של תוספת, אחרת None.

    כותרת: עד MAX_HEADER_WORDS מילים, ביטוי יום/עונה בשלוש המילים
    הראשונות, וכל השאר — ביטויי יום, מילות שלילה ("אין", "מדלגים"),
    פעלים ומילות מקום (_FILLERS) או שם של תוספת (_NAMES)."""
    # מירכאות סביב שם ("אומרים כאן "יעלה ויבא"") — בקצה המילה; גרשיים של
    # קיצור (ר"ח) תמיד באמצע
    words = [w.strip('"') for w in _norm(text).split()]
    words = [w for w in words if w]
    if not words or len(words) > MAX_HEADER_WORDS:
        return None
    alts, negate, names, chal = None, False, [], False
    i = 0
    while i < len(words):
        rest = " ".join(words[i:])
        hit = None
        for rx, lex_alts, neg in _LEXICON:
            m = rx.match(rest)
            if m:
                hit = (m, lex_alts(m) if callable(lex_alts) else lex_alts, neg)
                break
        if hit:
            m, new, neg = hit
            new = [list(a) for a in new]
            shabbat = {"shabbat", "motzei-shabbat"}
            if alts is None:
                alts = new
            elif not m.group("vav") and (chal or any(
                    shabbat & set(a) for a in alts + new)):
                # "בשבת חוה"מ פסח", "כשחל ר"ח בשבת" — וגם
                alts = [a + b for a in alts for b in new]
            else:
                # "ובחול המועד", "בראש חודש ביום טוב ובחול המועד" — או
                alts = alts + new
            negate ^= neg
            chal = False
            i += len(m.group(0).split())
            continue
        name = _match_name(rest)
        if name:
            names.append(name)
            i += len(name.split())
            continue
        w = words[i]
        if w in _NEGATIONS or _strip_vav(w) in _NEGATIONS:
            negate = not negate
        elif w not in _FILLERS and _strip_vav(w) not in _FILLERS:
            return None
        chal = chal or _strip_vav(w) in ("כשחל", "שחל", "חל")
        i += 1
        if alts is None and i >= 3:
            return None
    if alts is None:
        return None
    uniq = []   # "בצום גדליה ובעשרה בטבת" — שתי פעמים תענית
    for a in alts:
        a = list(dict.fromkeys(a))
        if a not in uniq:
            uniq.append(a)
    return {"any": uniq, "negate": negate, "names": names}


def _resolve_season(cond: dict, text: str) -> dict:
    """קיץ/חורף ⇐ המקום בתפילה לפי הטקסט שהתוספת אומרת."""
    if not any(s in (_SUMMER, _WINTER) for a in cond["any"] for s in a):
        return cond
    t = _norm(text)
    barech = ("טל ומטר" in t or "ברכה" in t.split() or t.startswith("ברכנו")
              or "ברך עלינו" in t)
    gevurot = "משיב הרוח" in t or "מוריד הטל" in t or "מוריד הגשם" in t
    if barech and not gevurot:
        summer, winter = "veten-bracha", "tal-umatar"
    else:
        summer, winter = "morid-hatal", "mashiv-haruach"
    sub = {_SUMMER: summer, _WINTER: winter}
    return dict(cond, any=[[sub.get(s, s) for s in a] for a in cond["any"]])


def condition_slugs(cond: dict) -> list:
    """כל ה-slugs שבתנאי, לפי הסדר, בלי כפילויות."""
    out = []
    for a in cond["any"]:
        for s in a:
            if s not in out:
                out.append(s)
    return out


def condition_label(cond: dict) -> str:
    """תווית בעברית: "ראש חודש / חול המועד", "שבת + חול המועד פסח",
    "לא בשבת / יום טוב"."""
    if cond.get("label"):
        return cond["label"]
    body = " / ".join(" + ".join(CONDITION_LABELS.get(s, s) for s in a)
                      for a in cond["any"])
    return ("לא ב" + body) if cond.get("negate") else body


def is_enabled(cond: dict, enabled) -> bool:
    """האם התוספת נאמרת כשהתנאים שב-enabled מתקיימים."""
    hit = any(all(s in enabled for s in a) for a in cond["any"])
    return hit != bool(cond.get("negate"))


def _rescue_regions(toks: list) -> None:
    """כלל 5: אזור מסומן שכולו סווג כהוראה, שמתחיל בכותרת של תוספת ואחריה
    טקסט שרובו מנוקד — הטקסט הוא תוספת (נאמר), לא הוראה."""
    regions = []
    for t in toks:
        if "t" in t and t["r"] and t["r"] not in regions:
            regions.append(t["r"])
    for r in regions:
        rt = [t for t in toks if "t" in t and t["r"] == r]
        if any(t["k"] != INSTRUCTION for t in rt if t["c"] != "P"):
            continue
        first_s = next((i for i, t in enumerate(rt) if t["c"] == "S"), None)
        if not first_s:
            continue
        head, tail = rt[:first_s], rt[first_s:]
        cond = parse_header(" ".join(t["t"] for t in head))
        # "מדלגים ל:יָמִין…" — שלילה שמצטטת היכן ממשיכים, לא תוספת
        if cond is None or cond["names"] or cond["negate"]:
            continue
        if _vocalized_share([t for t in tail if t["c"] != "P"]) <= 0.5 or \
                _match_name(_norm(" ".join(t["t"] for t in tail))):
            continue
        for t in tail:
            t["k"] = SPOKEN


def _starts_with_names(tokens: list, names: list) -> bool:
    """כלל 3: הטקסט מתחיל באחד השמות שההוראה הזכירה."""
    if not names:
        return True
    return _match_name(_norm(" ".join(t["t"] for t in tokens[:8]))) in names


_YAALE_RE = re.compile("יעלה ויבו?א")
_YAALE_END_RE = re.compile("ורחום את")
_HEADER_END = (":", ":)", ")", "׃", "-", "–", "—")
_DASHES = ("-", "–", "—")


def _is_dow_section(cond: dict) -> bool:
    """"בשני בשבת:" / "מזמור ליום שני" — כותרת של מקטע (שיר של יום)."""
    return (len(cond["any"]) == 1 and len(cond["any"][0]) == 1
            and GROUP_OF.get(cond["any"][0][0]) == "dow" and not cond["negate"])


def classify_leaf(paragraphs) -> list:
    """כל הפסקאות של עלה ⇐ לכל פסקה [(kind, טקסט נקי, cond)] לפי הסדר.

    ‏kind: ‏SPOKEN / ‏INSTRUCTION / ‏CONDITIONAL; ‏cond — התנאי (dict, ראה
    למעלה) לחלקים CONDITIONAL, אחרת None. עלה בלי תוספות — אותם חלקים כמו
    classify_paragraph לכל פסקה (עם cond=None)."""
    paras = []
    for p in _flatten(paragraphs):
        toks = _classify_tokens(_tokens(p))
        _rescue_regions(toks)
        prev = None
        for ti, t in enumerate(toks):
            # "בחורף:" / "(לשבת" — מילה לא מנוקדת בודדת בתוך טקסט מנוקד, שהכלל
            # הכללי משאיר נאמרת (חולם מלא של דעת); כשהיא כותרת של תוספת
            # ועומדת בפני עצמה (נקודתיים או פותחת סוגריים/אזור) — הוראה
            nxt = next((x for x in toks[ti + 1:] if "t" in x), None) \
                if "t" in t and t["c"] == "U" else None
            if "t" in t and t["c"] == "U" and t["k"] == SPOKEN and (
                    t["t"].endswith(":") or t["t"].startswith("(")
                    or prev is None or "br" in prev or prev["ir"] != t["ir"]
                    or (nxt is not None and nxt["t"] in _DASHES)) \
                    and parse_header(t["t"]):
                t["k"] = INSTRUCTION   # "בפסח - חַג הַמַּצּות" (דעת)
            prev = t
        paras.append(toks)
    words = [[t for t in toks if "t" in t] for toks in paras]

    headers = []   # (pi, run, cond, after)
    for pi, toks in enumerate(paras):
        ws = words[pi]
        i = 0
        while i < len(ws):
            if ws[i]["k"] != INSTRUCTION:
                i += 1
                continue
            j = i
            while j < len(ws) and ws[j]["k"] == INSTRUCTION:
                j += 1
            run = ws[i:j]
            after = any(t["c"] != "P" for t in ws[j:])
            text = " ".join(t["t"] for t in run)
            cond = None
            if _header_position(toks, run):
                cond = parse_header(text)
            if cond is None and not after and i == 0 and "." in text:
                # כלל 4: המשפט הראשון של הלכה ארוכה — רק עם שם תוספת
                cond = parse_header(text.split(".", 1)[0])
                if cond is not None and not cond["names"]:
                    cond = None
            if cond is not None:
                headers.append((pi, run, cond, after))
            i = j
    blocks, inlines = [], []   # (cond, [טוקנים])
    per_para = Counter(pi for pi, _, _, _ in headers)
    for n, (pi, run, cond, after) in enumerate(headers):
        if _is_dow_section(cond):
            # שיר של יום: עד הכותרת הבאה (של יום אחר או של תוספת אחרת), או
            # עד פסקת הוראה ("(הושיענו וכו'. קדיש יתום.)")
            stop = headers[n + 1][0] if n + 1 < len(headers) else len(paras)
            ext = _inline_extent(paras[pi], run[-1], section=True)
            for q in range(pi + 1, stop):
                if _pure_instruction(words[q]):
                    break
                ext += [t for t in words[q] if t["k"] == SPOKEN]
            blocks.append((cond, ext))
        elif after:
            ext = _inline_extent(paras[pi], run[-1], series=per_para[pi] > 1)
            if _YAALE_RE.search(_norm(" ".join(t["t"] for t in ext))):
                # "יעלה ויבוא" שהתחיל באמצע פסקה (דעת): כל ההמשך עד "…וְרַחוּם
                # אָתָּה", כמו בלוק — התוספות הפנימיות ("בראש חדש -") בתוכו
                blocks.append((cond, _yaale_extent(paras[pi], run[-1], words, pi)))
            else:
                inlines.append((cond, ext))
        else:
            blocks.append((cond, _block_extent(pi, words)))
    # קודם בלוקים, אחר-כך תוספות בתוך פסקה. תוספת פנימית (‏"לר"ח:" בתוך
    # "יעלה ויבוא" של "בראש חודש ובחול המועד") מקבלת את שני התנאים — "וגם".
    composed = {}
    for key, items in (("bcond", blocks), ("icond", inlines)):
        for cond, ext in items:
            if not ext or not _starts_with_names(
                    [t for t in ext if t["c"] != "P"], cond["names"]):
                continue
            resolved = _resolve_season(cond, " ".join(t["t"] for t in ext))
            for t in ext:
                outer = t.get("bcond")
                if outer is not None and outer is not resolved:
                    ck = (id(resolved), id(outer))
                    if ck not in composed:
                        composed[ck] = _compose(resolved, outer)
                    t[key] = composed[ck]
                else:
                    t[key] = resolved

    out = []
    for toks in paras:
        parts = []  # [kind, cond, [שורות של מילים]]
        for t in toks:
            if "br" in t:
                if parts:
                    parts[-1][2].append([])
                continue
            cond = t.get("icond") or t.get("bcond")
            kind = t["k"]
            if kind == SPOKEN and cond is not None:
                kind = CONDITIONAL
            else:
                cond = None
            if not parts or parts[-1][0] != kind or parts[-1][1] is not cond:
                parts.append([kind, cond, [[]]])
            parts[-1][2][-1].append(t["t"])
        res = []
        for kind, cond, lines in parts:
            body = "\n".join(" ".join(ln) for ln in lines if ln).strip()
            if not _HEBREW_LETTER_RE.search(body):
                continue
            if res and res[-1][0] == kind and res[-1][2] is cond:
                res[-1] = (kind, res[-1][1] + " " + body, cond)
            else:
                res.append((kind, body, cond))
        out.append(res)
    return out


def _compose(inner: dict, outer: dict) -> dict:
    """תוספת בתוך תוספת: נאמרת רק כששני התנאים מתקיימים. התווית — של
    הפנימית (הספציפית). עם שלילה — הפנימית לבדה (מקרה נדיר)."""
    if inner.get("negate") or outer.get("negate"):
        return inner
    alts = []
    for a in inner["any"]:
        for b in outer["any"]:
            ab = list(dict.fromkeys(a + b))
            if ab not in alts:
                alts.append(ab)
    # "לר"ח" בתוך "ר"ח / חוה"מ": [ר"ח] מכסה את [ר"ח + חוה"מ] — נשאר [ר"ח]
    alts = [a for a in alts if not any(set(b) < set(a) for b in alts)]
    return dict(inner, any=alts, label=condition_label(inner))


def _header_position(toks: list, run: list) -> bool:
    """הוראה יכולה להיות כותרת רק כשהיא עומדת בפני עצמה: מסתיימת בנקודתיים
    (‏"בעשי"ת:"), או פותחת שורה / אזור מסומן (‏"<small>בקיץ</small>",
    ‏"(בעשי"ת וּלְעֵלָּא)"). קיצור בודד באמצע משפט מנוקד (‏"כְּשֶׁחָל יו"ט
    בְּיוֹם חֹל") אינו כותרת."""
    if run[-1]["t"].endswith(_HEADER_END):
        return True
    end = next(i for i, t in enumerate(toks) if t is run[-1])
    nxt = next((t for t in toks[end + 1:] if "t" in t), None)
    if nxt is not None and nxt["t"] in _DASHES:   # "בפסח - חַג הַמַּצּות" (דעת)
        return True
    idx = next(i for i, t in enumerate(toks) if t is run[0])
    prev = toks[idx - 1] if idx else None
    return prev is None or "br" in prev or prev["ir"] != run[0]["ir"]


def _pure_instruction(ws: list) -> bool:
    c = [t for t in ws if t["c"] != "P"]
    return bool(c) and all(t["k"] == INSTRUCTION for t in c)


def _yaale_extent(toks: list, last_header_tok: dict, words: list, pi: int) -> list:
    """יעלה ויבוא מתוך הוראה באמצע פסקה: הטקסט הנאמר עד "ורחום אתה" — בפסקה
    הזו, ואם אינו בה — עד 6 פסקאות אחריה."""
    idx = next(i for i, t in enumerate(toks) if t is last_header_tok)
    ext = [t for t in toks[idx + 1:] if "t" in t and t["k"] == SPOKEN]
    if _YAALE_END_RE.search(_norm(" ".join(t["t"] for t in ext))):
        cut = next(i for i in range(len(ext))
                   if _YAALE_END_RE.search(_norm(" ".join(t["t"] for t in ext[:i + 1]))))
        return ext[:cut + 2]   # "וְרַחוּם" + "אָתָּה:"
    for q in range(pi + 1, min(pi + 7, len(words))):
        if _pure_instruction(words[q]):
            break
        seg = [t for t in words[q] if t["k"] == SPOKEN]
        ext += seg
        if _YAALE_END_RE.search(_norm(" ".join(t["t"] for t in seg))):
            break
    return ext


def _inline_extent(toks: list, last_header_tok: dict, section=False,
                   series=False) -> list:
    """כלל 1: הטקסט אחרי ההוראה באותה פסקה."""
    idx = next(i for i, t in enumerate(toks) if t is last_header_tok)
    rest = toks[idx + 1:]
    first = next((t for t in rest if "t" in t and t["c"] != "P"), None)
    if first is None or first["k"] != SPOKEN:
        return []
    ext = []
    if section:
        return [t for t in rest if "t" in t and t["k"] == SPOKEN]
    if first["ir"]:   # עד סוף האזור המסומן (הפנימי) שהטקסט מתחיל בו
        started = False
        for t in rest:
            if "br" in t:
                continue
            if t is first:
                started = True
            if not started:
                continue
            if t["ir"] != first["ir"] and t["d"] <= first["d"] or \
                    t["k"] != SPOKEN:
                break
            ext.append(t)
            if series and t["t"].endswith(":"):
                break   # כמה חלופות ברצף — ראה למטה
        return ext
    for t in rest:   # עד ההוראה הבאה / נקודתיים / מעבר שורה / סוף הפסקה
        if "br" in t:
            if ext:
                break
            continue
        if t["k"] != SPOKEN:
            if ext:
                break
            continue
        ext.append(t)
        if series and t["t"].endswith(":") and any(x["c"] != "P" for x in ext):
            # כמה חלופות ברצף באותה פסקה ("לר"ח: …: לפסח: …: לסכות: חַג
            # הַסֻּכּוֹת הַזֶּה: זָכְרֵנוּ…") — כל אחת רק עד הנקודתיים שלה
            break
    return ext


def _block_extent(pi: int, words: list) -> list:
    """כלל 2: הוראה בסוף פסקה ⇐ הפסקה/הפסקאות שאחריה."""
    def spoken(q):
        return [t for t in words[q] if t["k"] == SPOKEN and t["c"] != "P"]

    def pure_instruction(q):
        c = [t for t in words[q] if t["c"] != "P"]
        return bool(c) and all(t["k"] == INSTRUCTION for t in c)

    q = pi + 1
    if q >= len(words):
        return []
    c = [t for t in words[q] if t["c"] != "P"]
    if not c or c[0]["k"] != SPOKEN:
        return []
    # עומק הסימון של הטקסט הרגיל בעלה — הקטן ביותר בין הפסקאות הנאמרות (בתורת
    # אמת יש עלים שכולם ב-<small>; בעדות המזרח הטקסט הרגיל לא מסומן, והתוספות
    # — שבעלה ארוך יכולות להיות רוב המילים — ב-<small>)
    base = min((min(t["d"] for t in spoken(p)) for p in range(len(words))
                if len(spoken(p)) >= 3), default=0)
    depth = min(t["d"] for t in spoken(q))
    ext = []
    if depth > base:   # מסומנת יותר מהטקסט הרגיל — כל הפסקאות המסומנות כך
        while q < len(words):
            s = spoken(q)
            if not s or min(t["d"] for t in s) < depth or pure_instruction(q):
                break
            ext += [t for t in words[q] if t["k"] == SPOKEN]
            q += 1
        return ext
    # הפסקה הבאה כולה (תוספת פנימית בה — "לר"ח:" — מקבלת את התנאי של שתיהן)
    ext = [t for t in words[q] if t["k"] == SPOKEN]
    norm = _norm(" ".join(t["t"] for t in ext))
    if _YAALE_RE.search(norm) and not _YAALE_END_RE.search(norm):
        for q2 in range(q + 1, min(q + 7, len(words))):
            if pure_instruction(q2):
                break
            seg = [t for t in words[q2] if t["k"] == SPOKEN]
            ext += seg
            if _YAALE_END_RE.search(_norm(" ".join(t["t"] for t in seg))):
                break
    return ext
