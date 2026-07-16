# -*- coding: utf-8 -*-
"""איתור עוגנים: הצלבת תמלול ASR עם טקסט הפסוקים הידוע מ-Sefaria.

Python טהור, אפס תלויות — ניתן לבדיקה מלאה בלי רשת/GPU (ראה tests/test_anchors.py).

הרעיון: התמלול (Whisper עברי) נותן לכל מילה חותמת-זמן גסה. יישור-רצפים גלובלי
ומונוטוני בין מילות התמלול למילות הטקסט הידוע מאתר "עוגנים" — מילים שזוהו
בביטחון גבוה — שמתחמים חלונות קצרים ליישור הכפוי (MMS) וחוסמים סחיפה.

נקודה קריטית: טקסט התורה בכתיב חסר (כהנים) בעוד שהתמלול המודרני בכתיב מלא
(כוהנים). לכן מרחק-העריכה מוזיל הוספה/מחיקה של ו/י (עלות 0.25 במקום 1).
"""

import re
import unicodedata
from bisect import bisect_left
from functools import lru_cache

# --- נורמליזציה --------------------------------------------------------------

_HEBREW_LETTER_RE = re.compile(r"[א-ת]")
_FINALS = str.maketrans("ךםןףץ", "כמנפצ")

# קרי-קבוע בצד ה-ASR: הקורא הוגה "אדני"; מנועי תמלול נוטים לכתוב "אדוני".
# (בצד הטקסט ההחלפה יהוה→אדני כבר נעשתה ב-chunker.)
_ASR_SUBSTITUTIONS = {"אדוני": "אדני"}


def normalize_word(word: str) -> str:
    """מילה כלשהי → אותיות עבריות רגילות בלבד (בלי ניקוד/סופיות/פיסוק)."""
    word = unicodedata.normalize("NFC", word)
    plain = "".join(_HEBREW_LETTER_RE.findall(word)).translate(_FINALS)
    return _ASR_SUBSTITUTIONS.get(plain, plain)


# --- דמיון מילים: Levenshtein משוקלל -----------------------------------------

# הוספה/מחיקה של אימות-קריאה — כמעט חינם (כתיב חסר מול כתיב מלא)
_CHEAP_CHARS = frozenset("וי")
_CHEAP_COST = 0.25


@lru_cache(maxsize=1 << 18)
def _weighted_distance(a: str, b: str) -> float:
    """מרחק עריכה שבו הוספה/מחיקה של ו/י עולה 0.25 והשאר 1.0."""
    prev = [0.0] * (len(b) + 1)
    for j, cb in enumerate(b, 1):
        prev[j] = prev[j - 1] + (_CHEAP_COST if cb in _CHEAP_CHARS else 1.0)
    for ca in a:
        cur = [prev[0] + (_CHEAP_COST if ca in _CHEAP_CHARS else 1.0)]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j - 1] + (0.0 if ca == cb else 1.0),           # החלפה
                prev[j] + (_CHEAP_COST if ca in _CHEAP_CHARS else 1.0),   # מחיקה
                cur[j - 1] + (_CHEAP_COST if cb in _CHEAP_CHARS else 1.0)))  # הוספה
        prev = cur
    return prev[-1]


def word_similarity(a: str, b: str) -> float:
    """דמיון ב-[0,1] בין שתי מילים מנורמלות. 1.0 = זהות."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if abs(len(a) - len(b)) > 3:
        return 0.0
    return max(0.0, 1.0 - _weighted_distance(a, b) / max(len(a), len(b)))


# --- יישור רצפים גלובלי (Needleman–Wunsch ברצועה) ----------------------------

_GAP = -0.4          # קנס על מילה חסרה באחד הצדדים
_MISMATCH = -0.5     # ציון לזוג שדמיונו מתחת לסף
_MATCH_FLOOR = 0.5   # מתחת לזה — הזוג נחשב אי-התאמה


def align_sequences(asr_words: list, ref_words: list, band: int = 250) -> list:
    """יישור גלובלי מונוטוני בין שתי רשימות מילים מנורמלות.

    מחזיר רשימת זוגות (asr_i | None, ref_j | None, sim) לפי הסדר.
    הרצועה (band) חוסמת את ה-DP סביב האלכסון המשוער — מספיק לקריאה שלמה
    והופך את הריצה לזניחה גם ב-Python טהור.
    """
    n, m = len(asr_words), len(ref_words)
    if n == 0 or m == 0:
        return ([(i, None, 0.0) for i in range(n)]
                + [(None, j, 0.0) for j in range(m)])

    ratio = m / n
    NEG = float("-inf")

    def j_range(i):
        center = round(i * ratio)
        return max(0, center - band), min(m, center + band)

    # score[i] = מילון j→ציון בשורה i; ptr[i][j] = 'd'/'u'/'l'
    scores = [dict() for _ in range(n + 1)]
    ptrs = [dict() for _ in range(n + 1)]
    lo0, hi0 = j_range(0)
    for j in range(lo0, hi0 + 1):
        scores[0][j] = j * _GAP
        ptrs[0][j] = "l"
    ptrs[0].pop(0, None)

    for i in range(1, n + 1):
        lo, hi = j_range(i)
        row, prow = scores[i], scores[i - 1]
        pt = ptrs[i]
        aw = asr_words[i - 1]
        for j in range(lo, hi + 1):
            best, move = NEG, None
            if j > 0:
                diag = prow.get(j - 1, NEG)
                if diag > NEG:
                    sim = word_similarity(aw, ref_words[j - 1])
                    sc = diag + (sim if sim >= _MATCH_FLOOR else _MISMATCH)
                    if sc > best:
                        best, move = sc, "d"
            up = prow.get(j, NEG)
            if up > NEG and up + _GAP > best:
                best, move = up + _GAP, "u"
            if j > 0:
                left = row.get(j - 1, NEG)
                if left > NEG and left + _GAP > best:
                    best, move = left + _GAP, "l"
            if move is None:
                best, move = i * _GAP + j * _GAP, "u" if i else "l"
            row[j] = best
            pt[j] = move

    # traceback מהפינה (n, m) — אם m מחוץ לרצועת השורה האחרונה, מהקצה הקרוב
    i, j = n, max(k for k in scores[n])
    pairs = []
    while i > 0 or j > 0:
        move = ptrs[i].get(j)
        if move == "d":
            sim = word_similarity(asr_words[i - 1], ref_words[j - 1])
            pairs.append((i - 1, j - 1, sim))
            i, j = i - 1, j - 1
        elif move == "u" or (move is None and i > 0):
            pairs.append((i - 1, None, 0.0))
            i -= 1
        else:
            pairs.append((None, j - 1, 0.0))
            j -= 1
    pairs.reverse()
    # השלמת עמודות ref שנשארו מחוץ לרצועה בסוף
    covered = {p[1] for p in pairs if p[1] is not None}
    for j in range(m):
        if j not in covered:
            pairs.append((None, j, 0.0))
    return pairs


# --- בחירת עוגנים -------------------------------------------------------------

def _repeated_nearby(ref_words: list, j: int, radius: int) -> bool:
    """האם המילה ref_words[j] חוזרת בסביבתה (מלכודת מילים חוזרות: ויאמר…)."""
    w = ref_words[j]
    lo, hi = max(0, j - radius), min(len(ref_words), j + radius + 1)
    return any(k != j and ref_words[k] == w for k in range(lo, hi))


def _longest_increasing_by_time(anchors: list) -> list:
    """תת-סדרה עולה ממש בזמן (end) — מסלקת עוגנים עם זמנים לא-סדורים."""
    if not anchors:
        return []
    n = len(anchors)
    best_len = [1] * n
    parent = [-1] * n
    for i in range(1, n):
        for k in range(i):
            if (anchors[k]["end"] < anchors[i]["end"]
                    and best_len[k] + 1 > best_len[i]):
                best_len[i] = best_len[k] + 1
                parent[i] = k
    i = max(range(n), key=lambda k: best_len[k])
    out = []
    while i >= 0:
        out.append(anchors[i])
        i = parent[i]
    return out[::-1]


def _enforce_rate(anchors: list, rate_range: tuple) -> list:
    """קצב קריאה בין עוגנים עוקבים חייב להיות סביר — אחרת מפילים את החלש."""
    lo, hi = rate_range
    anchors = list(anchors)
    changed = True
    while changed and len(anchors) >= 2:
        changed = False
        for i in range(len(anchors) - 1):
            a, b = anchors[i], anchors[i + 1]
            dw = b["ref"] - a["ref"]
            dt = b["start"] - a["end"] + (b["end"] - b["start"])
            rate = max(dt, 1e-6) / max(dw, 1)
            if not (lo <= rate <= hi):
                drop = i if a["sim"] <= b["sim"] else i + 1
                anchors.pop(drop)
                changed = True
                break
    return anchors


def select_anchors(pairs, asr_times, ref_words,
                   min_sim=0.85, min_len=3, context_sim=0.6,
                   repeat_radius=10, rate_range=(0.12, 4.0),
                   gap_words=50, gap_seconds=90.0, relaxed_sim=0.7):
    """מסנן את זוגות ההתאמה לעוגנים אמינים.

    pairs — פלט align_sequences; asr_times — [(start, end)] לפי אינדקס ASR;
    ref_words — רשימת מילות הטקסט המנורמלות.
    מחזיר (רשימת עוגנים ממוינת לפי ref, כיסוי ההתאמה ב-[0,1]).
    """
    matched = [(k, ai, rj, sim) for k, (ai, rj, sim) in enumerate(pairs)
               if ai is not None and rj is not None]
    covered = sum(1 for _, _, _, sim in matched if sim >= relaxed_sim)
    coverage = covered / len(ref_words) if ref_words else 0.0

    def has_context(k, floor):
        idx = next(i for i, mk in enumerate(matched) if mk[0] == k)
        for nb in (idx - 1, idx + 1):
            if 0 <= nb < len(matched):
                nk, _, nrj, nsim = matched[nb]
                if abs(nk - k) == 1 and nsim >= floor:
                    return True
        return False

    def candidates(sim_floor, need_context, within=None):
        out = []
        for k, ai, rj, sim in matched:
            if within and not (within[0] < rj < within[1]):
                continue
            if sim < sim_floor or len(ref_words[rj]) < min_len:
                continue
            if _repeated_nearby(ref_words, rj, repeat_radius):
                continue
            if need_context and not has_context(k, context_sim):
                continue
            start, end = asr_times[ai]
            out.append({"ref": rj, "asr": ai, "start": start,
                        "end": end, "sim": sim})
        return out

    anchors = candidates(min_sim, need_context=True)
    anchors = _longest_increasing_by_time(anchors)
    anchors = _enforce_rate(anchors, rate_range)

    # גיוס שני בפערים גדולים מדי (במילים או בשניות), בסף מקל ובלי שער-הקשר
    bounds = ([{"ref": -1, "end": 0.0}] + anchors
              + [{"ref": len(ref_words), "start": float("inf")}])
    recruits = []
    for a, b in zip(bounds, bounds[1:]):
        wide = (b["ref"] - a["ref"] > gap_words
                or (b.get("start", 0) - a.get("end", 0)) > gap_seconds)
        if wide:
            recruits += candidates(relaxed_sim, need_context=False,
                                   within=(a["ref"], b["ref"]))
    if recruits:
        merged = {a["ref"]: a for a in recruits}
        merged.update({a["ref"]: a for a in anchors})  # לעוגן מקורי עדיפות
        anchors = sorted(merged.values(), key=lambda a: a["ref"])
        anchors = _longest_increasing_by_time(anchors)
        anchors = _enforce_rate(anchors, rate_range)

    return sorted(anchors, key=lambda a: a["ref"]), coverage


# --- הממשק הנוח: מילות ASR גולמיות → עוגנים -----------------------------------

def find_anchors(asr_words: list, ref_plain_words: list, band: int = 250, **kw):
    """asr_words — [{"word","start","end",...}] מהתמלול;
    ref_plain_words — align_plain השטוח מה-chunker.

    מחזיר dict: anchors, coverage, matches (להצלבת אי-הסכמה בהמשך).
    """
    norm, times = [], []
    for w in asr_words:
        nw = normalize_word(w["word"])
        if nw:
            norm.append(nw)
            times.append((float(w["start"]), float(w["end"])))
    ref_norm = [normalize_word(w) for w in ref_plain_words]

    pairs = align_sequences(norm, ref_norm, band=band)
    anchors, coverage = select_anchors(pairs, times, ref_norm, **kw)

    matches = [{"ref": rj, "asr_start": times[ai][0],
                "asr_end": times[ai][1], "sim": sim}
               for ai, rj, sim in pairs
               if ai is not None and rj is not None and sim >= 0.5]
    return {"anchors": anchors, "coverage": coverage, "matches": matches}
