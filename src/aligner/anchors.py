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
from itertools import product

# --- נורמליזציה --------------------------------------------------------------

_HEBREW_LETTER_RE = re.compile(r"[א-ת]")
_FINALS = str.maketrans("ךםןףץ", "כמנפצ")

# קרי-קבוע בצד ה-ASR: הקורא הוגה "אדני"; מנועי תמלול נוטים לכתוב "אדוני".
# (בצד הטקסט ההחלפה יהוה→אדני כבר נעשתה ב-chunker — וגם צורות הסידור
# יְיָ / ה׳, עם תחילית או בלעדיה, במצב תפילה; ראה chunker.is_tefila_divine_name.)
# המפתחות אחרי קיפול סופיות (ם→מ). "אדושם" (כינוי שנאמר בתרגול) אינו מופיע
# בשום טקסט תנ״כי — ולכן ההחלפה בטוחה גם בתנ״ך, ומשותפת לשני המצבים.
#
# שם ה׳ עם תחילית (PLAN_TEFILA 8.21): בטקסט לַיהֹוָה / לה' ⇒ "לאדני", והתמלול
# כותב "לאדוני" / "ואדושם". אותה תחילית (1–3 אותיות מ-ו ב כ ל מ ש ה, כמו
# בצד הטקסט) + אדוני/אדושם ⇒ תחילית + אדני. בטוח גם לתנ״ך: normalize_word רץ
# על שני הצדדים (גם על מילות הטקסט), כך ש"לאדוני" ו"לַאדֹנִי" (לְאדוני שלי)
# מנורמלים לאותה מחרוזת בדיוק — זה רק איחוד כתיב מלא/חסר, לא החלפת מילה.
# בכוונה **לא** ממפים "השם"/"בשם"/"לשם": אלה מילים רגילות בתנ״ך ובתפילה
# (אֶת־הַשֵּׁם, בְּשֵׁם, לְשֵׁם). ‏"אלוהים" לא צריך החלפה — ו״ו נוספת זולה ממילא.
# ⚠️ צורות נוספות של התמלול בתפילה ממתינות לתמלולים אמיתיים (שלב 0.2).
_ASR_NAME_PREFIX_LETTERS = "ובכלמשה"


def _prefixed_name_substitutions() -> dict:
    out = {}
    for n in range(4):  # תחילית ריקה ועד שלוש אותיות
        for prefix in product(_ASR_NAME_PREFIX_LETTERS, repeat=n):
            p = "".join(prefix)
            out[p + "אדוני"] = p + "אדני"
            out[p + "אדושמ"] = p + "אדני"
    return out


_ASR_SUBSTITUTIONS = _prefixed_name_substitutions()


def normalize_word(word: str) -> str:
    """מילה כלשהי → אותיות עבריות רגילות בלבד (בלי ניקוד/סופיות/פיסוק)."""
    word = unicodedata.normalize("NFC", word)
    plain = "".join(_HEBREW_LETTER_RE.findall(word)).translate(_FINALS)
    return _ASR_SUBSTITUTIONS.get(plain, plain)


# --- דמיון מילים: Levenshtein משוקלל -----------------------------------------

# הוספה/מחיקה של אימות-קריאה — כמעט חינם (כתיב חסר מול כתיב מלא)
_CHEAP_CHARS = frozenset("וי")
_CHEAP_COST = 0.25


def _weighted_distance_raw(a: str, b: str) -> float:
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


# הגרסה עם ה-cache — ל-word_similarity הציבורית (שאילתות בודדות חוזרות).
# ‏align_sequences לא משתמש בה: הוא מחשב כל זוג (מילת תמלול, מילת טקסט) פעם
# אחת בלבד ושומר רק זוגות דומים, ולכן ה-cache רק היה תופס זיכרון (8.19).
_weighted_distance = lru_cache(maxsize=1 << 18)(_weighted_distance_raw)


def word_similarity(a: str, b: str) -> float:
    """דמיון ב-[0,1] בין שתי מילים מנורמלות. 1.0 = זהות."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if abs(len(a) - len(b)) > 3:
        return 0.0
    return max(0.0, 1.0 - _weighted_distance(a, b) / max(len(a), len(b)))


def _word_similarity_uncached(a: str, b: str) -> float:
    """בדיוק word_similarity (אותן פעולות, אותו ערך עד הביט) — בלי ה-cache."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if abs(len(a) - len(b)) > 3:
        return 0.0
    return max(0.0, 1.0 - _weighted_distance_raw(a, b) / max(len(a), len(b)))


def _weighted_distance_within(a: str, b: str, limit: float):
    """‏_weighted_distance_raw(a, b) — אותן פעולות צפות בכל תא, ולכן אותו
    ערך עד הביט — או None ברגע שכל שורת ה-DP גדולה מ-limit (המינימום של
    שורה אינו יורד משורה לשורה, כי כל המחירים אי-שליליים; ולכן גם המרחק
    הסופי > limit)."""
    cheap, ccost = _CHEAP_CHARS, _CHEAP_COST
    icost = [ccost if cb in cheap else 1.0 for cb in b]
    prev = [0.0]
    for c in icost:
        prev.append(prev[-1] + c)
    for ca in a:
        dcost = ccost if ca in cheap else 1.0
        left = prev[0] + dcost
        cur = [left]
        k = 0
        for cb, ic in zip(b, icost):
            x = prev[k] + (0.0 if ca == cb else 1.0)        # החלפה
            y = prev[k + 1] + dcost                          # מחיקה
            if y < x:
                x = y
            y = left + ic                                    # הוספה
            if y < x:
                x = y
            cur.append(x)
            left = x
            k += 1
        if min(cur) > limit:
            return None
        prev = cur
    return prev[-1]


# --- יישור רצפים גלובלי (Needleman–Wunsch ברצועה) ----------------------------

_GAP = -0.4          # קנס על מילה חסרה באחד הצדדים
_MISMATCH = -0.5     # ציון לזוג שדמיונו מתחת לסף
_MATCH_FLOOR = 0.5   # מתחת לזה — הזוג נחשב אי-התאמה

# מצביעי ה-traceback (בית אחד לתא; 0 = אין מצביע)
_DIAG, _UP, _LEFT = 1, 2, 3


def _multiset_signatures(words) -> dict:
    """מילה → (sig, csig): שני int שהביטים שלהם הם מופעי האותיות במילה —
    המופע ה-k של אות x = ביט משלו; ‏sig לאותיות רגילות, ‏csig ל-ו/י.
    כך ‎popcount(sig_a & ~sig_b)‎ הוא בדיוק עודף-המולטיסט
    Σ max(0, count_a(x) − count_b(x)) על האותיות הרגילות (וכך גם csig)."""
    bit_of = {}
    sigs = {}
    for w in words:
        if w in sigs:
            continue
        sig = csig = 0
        seen = {}
        for ch in w:
            k = seen.get(ch, 0)
            seen[ch] = k + 1
            bit = bit_of.get((ch, k))
            if bit is None:
                bit = bit_of[(ch, k)] = len(bit_of)
            if ch in _CHEAP_CHARS:
                csig |= 1 << bit
            else:
                sig |= 1 << bit
        sigs[w] = (sig, csig)
    return sigs


try:
    _popcount = int.bit_count              # Python 3.10+
except AttributeError:                     # pragma: no cover
    def _popcount(x: int) -> int:
        return bin(x).count("1")


def _similar_refs(aw: str, a_sigs: tuple, ref_ids, ref_vocab: list,
                  ref_sigs: list) -> dict:
    """מילת תמלול אחת מול קבוצת מזהי מילות-טקסט ⇒ {מזהה: sim} רק לזוגות
    שבהם sim ≥ ‏_MATCH_FLOOR. לכל זוג אחר תרומת האלכסון היא ‏_MISMATCH
    בדיוק כמו קודם, ולכן אין צורך לשמור אותו.

    סינון בלי DP, שאינו פוסל אף זוג דומה. ‏sim ≥ 0.5 ⇔ d ≤ L/2 ‏(L = האורך
    הגדול). חסם תחתון על d: ‏E_a/E_b — עודף המופעים של אותיות רגילות בכל צד,
    ‏C_a/C_b — עודף מופעי ו/י. כל מופע עודף אינו מותאם לאות זהה, ולכן נמחק/
    נוסף (1, או 0.25 ל-ו/י) או מוחלף (1, ומכסה לכל היותר מופע אחד מכל צד).
    עם s החלפות המחיר ≥ ‎s + Σ צד (עודף רגיל שלא כוסה)·1 + (עודף ו/י שלא
    כוסה)·0.25‎; המינימום על s מתקבל ב-s = E_hi ‏(הצד שעודפו הרגיל גדול):
    ‎d ≥ E_hi + C_hi/4 + max(0, C_lo − (E_hi − E_lo))/4‎. אם החסם > L/2 —
    ‏d ≥ L/2 + 0.25 (d כפולה של 0.25), ‏d/L > 0.5 בפער ≥ 1/(4L), ולכן גם
    בחישוב הצף sim < 0.5. אורכים שרחוקים ביותר מ-3 ומילה ריקה — 0.0 כבר
    ב-word_similarity.
    """
    good = {}
    la = len(aw)
    if not la:
        return good
    a_sig, a_csig = a_sigs
    for rid in ref_ids:
        rw = ref_vocab[rid]
        if rw == aw:
            good[rid] = 1.0
            continue
        lr = len(rw)
        if not lr or la - lr > 3 or lr - la > 3:
            continue
        r_sig, r_csig = ref_sigs[rid]
        ea = _popcount(a_sig & ~r_sig)
        eb = _popcount(r_sig & ~a_sig)
        L2 = 2 * (la if la > lr else lr)
        if 4 * (ea if ea > eb else eb) > L2:   # כבר החלק הרגיל מכריע
            continue
        ca = _popcount(a_csig & ~r_csig)
        cb = _popcount(r_csig & ~a_csig)
        if ea >= eb:                       # החסם ברבעים
            rest = cb - (ea - eb)
            q = 4 * ea + ca + (rest if rest > 0 else 0)
        else:
            rest = ca - (eb - ea)
            q = 4 * eb + cb + (rest if rest > 0 else 0)
        if q > L2:
            continue
        # כמו word_similarity (המילים לא ריקות, שונות, ופער האורכים ≤ 3)
        L = la if la > lr else lr
        d = _weighted_distance_within(aw, rw, L / 2)
        if d is None:
            continue
        sim = max(0.0, 1.0 - d / L)
        if sim >= _MATCH_FLOOR:
            good[rid] = sim
    return good


def align_sequences(asr_words: list, ref_words: list, band: int = 250) -> list:
    """יישור גלובלי מונוטוני בין שתי רשימות מילים מנורמלות.

    מחזיר רשימת זוגות (asr_i | None, ref_j | None, sim) לפי הסדר.
    הרצועה (band) חוסמת את ה-DP סביב האלכסון המשוער — מספיק לקריאה שלמה
    והופך את הריצה לזניחה גם ב-Python טהור.

    מימוש (PLAN_TEFILA 8.19, פלט זהה עד הביט למימוש הקודם — ראה
    tests/test_anchors_equivalence.py): דמיון מחושב פעם אחת לכל זוג מילים
    *ייחודי* (מילת תמלול × מילת טקסט שבתחום הרצועה שלה), אחרי סינון זול
    שאינו פוסל זוג דומה, ונשמרים רק זוגות שדמיונם ≥ 0.5; ה-DP שומר רק את
    השורה הקודמת של הציונים (רשימה), והמצביעים — bytearray לשורה.
    """
    n, m = len(asr_words), len(ref_words)
    if n == 0 or m == 0:
        return ([(i, None, 0.0) for i in range(n)]
                + [(None, j, 0.0) for j in range(m)])

    ratio = m / n
    NEG = float("-inf")
    GAP = _GAP
    MIS = _MISMATCH

    # רצועת כל שורה: עמודות [los[i], his[i]] (כולל) — בדיוק j_range הקודם
    los, his = [], []
    for i in range(n + 1):
        center = round(i * ratio)
        los.append(max(0, center - band))
        his.append(min(m, center + band))

    # מזהים לאוצר המילים; חתימות מולטיסט לסינון
    ref_index = {}
    rid = []
    for w in ref_words:
        k = ref_index.get(w)
        if k is None:
            k = ref_index[w] = len(ref_index)
        rid.append(k)
    ref_vocab = list(ref_index)
    sigs = _multiset_signatures(list(ref_index) + list(asr_words))
    ref_sigs = [sigs[w] for w in ref_vocab]

    # לכל מילת תמלול ייחודית: איחוד עמודות הטקסט שבכל השורות שלה ⇒ זוגות דומים
    rows_of = {}
    for i, w in enumerate(asr_words, 1):
        rows_of.setdefault(w, []).append(i)
    good_of = {}
    for w, rows in rows_of.items():
        ids = set()
        s0 = e0 = None
        for i in rows:                 # מקטעי rid[s:e] של האלכסון, ממוזגים
            s, e = max(los[i] - 1, 0), his[i]
            if e0 is not None and s <= e0:
                if e > e0:
                    e0 = e
                continue
            if e0 is not None:
                ids.update(rid[s0:e0])
            s0, e0 = s, e
        if e0 is not None:
            ids.update(rid[s0:e0])
        good_of[w] = _similar_refs(w, sigs[w], ids, ref_vocab, ref_sigs)
    del rows_of

    # שורה 0: ‏score = j·GAP; המצביעים שלה אינם נקראים (ב-i=0 תמיד "שמאלה")
    plo, phi = los[0], his[0]
    prow = [j * _GAP for j in range(plo, phi + 1)]
    ptrs = [None]

    for i in range(1, n + 1):
        lo, hi = los[i], his[i]
        gget = good_of[asr_words[i - 1]].get
        row = []
        pt = bytearray()
        append, pappend = row.append, pt.append

        def generic(j):
            """תא בשולי הרצועה — העתק מילולי של הלוגיקה הקודמת."""
            best, move = NEG, 0
            if j > 0 and plo <= j - 1 <= phi:
                diag = prow[j - 1 - plo]
                if diag > NEG:
                    sc = diag + gget(rid[j - 1], MIS)
                    if sc > best:
                        best, move = sc, _DIAG
            if plo <= j <= phi:
                up = prow[j - plo]
                if up > NEG and up + GAP > best:
                    best, move = up + GAP, _UP
            if j > lo:
                left = row[j - 1 - lo]
                if left > NEG and left + GAP > best:
                    best, move = left + GAP, _LEFT
            if move == 0:
                best, move = i * _GAP + j * _GAP, _UP
            append(best)
            pappend(move)

        # פנים הרצועה: גם אלכסון, גם למעלה, גם שמאלה קיימים
        j0 = max(lo + 1, plo + 1)
        j1 = min(hi, phi)
        for j in range(lo, min(j0 - 1, hi) + 1):
            generic(j)
        if j0 <= j1:
            left = row[-1]
            for dg, up, c in zip(prow[j0 - 1 - plo:j1 - plo],
                                 prow[j0 - plo:j1 - plo + 1],
                                 [gget(r, MIS) for r in rid[j0 - 1:j1]]):
                dg = dg + c
                up = up + GAP
                lf = left + GAP
                if up > dg:
                    if lf > up:
                        left = lf
                        pappend(_LEFT)
                    else:
                        left = up
                        pappend(_UP)
                elif lf > dg:
                    left = lf
                    pappend(_LEFT)
                else:
                    left = dg
                    pappend(_DIAG)
                append(left)
        for j in range(max(j1 + 1, j0), hi + 1):
            generic(j)

        ptrs.append(pt)
        prow, plo, phi = row, lo, hi

    # traceback מהפינה (n, m) — אם m מחוץ לרצועת השורה האחרונה, מהקצה הקרוב
    i, j = n, max(range(los[n], his[n] + 1))
    pairs = []
    while i > 0 or j > 0:
        move = 0
        if i > 0:
            k = j - los[i]
            if 0 <= k <= his[i] - los[i]:
                move = ptrs[i][k]
        if move == _DIAG:
            sim = _word_similarity_uncached(asr_words[i - 1], ref_words[j - 1])
            pairs.append((i - 1, j - 1, sim))
            i, j = i - 1, j - 1
        elif move == _UP or (move == 0 and i > 0):
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
                   gap_words=50, gap_seconds=90.0, relaxed_sim=0.7,
                   recruit_context=False):
    """מסנן את זוגות ההתאמה לעוגנים אמינים.

    ‏recruit_context=True (פרופיל שירה) — גם עוגני הגיוס השני דורשים הקשר:
    בלעדיו מילת דיבור שאינו בטקסט ("אני" משם הניגון) נכנסה כעוגן ל"אֵין".

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
            recruits += candidates(relaxed_sim, need_context=recruit_context,
                                   within=(a["ref"], b["ref"]))
    if recruits:
        merged = {a["ref"]: a for a in recruits}
        merged.update({a["ref"]: a for a in anchors})  # לעוגן מקורי עדיפות
        anchors = sorted(merged.values(), key=lambda a: a["ref"])
        anchors = _longest_increasing_by_time(anchors)
        anchors = _enforce_rate(anchors, rate_range)

    return sorted(anchors, key=lambda a: a["ref"]), coverage


# --- הממשק הנוח: מילות ASR גולמיות → עוגנים -----------------------------------

def find_anchors(asr_words: list, ref_plain_words: list, band: int = 250,
                 nontext=None, **kw):
    """asr_words — [{"word","start","end",...}] מהתמלול;
    ref_plain_words — align_plain השטוח מה-chunker.

    מחזיר dict: anchors, coverage, matches (להצלבת אי-הסכמה בהמשך).
    ‏nontext — פרמטרי nontext_runs (פרופיל שירה); כשנמסר, ה-dict כולל גם
    nontext_runs — ריצות דיבור שאינו בטקסט (העוגנים עצמם לא משתנים כאן;
    ראה apply_nontext_runs).
    """
    norm, times, raw = [], [], []
    for w in asr_words:
        nw = normalize_word(w["word"])
        if nw:
            norm.append(nw)
            times.append((float(w["start"]), float(w["end"])))
            raw.append(w["word"])
    ref_norm = [normalize_word(w) for w in ref_plain_words]

    pairs = align_sequences(norm, ref_norm, band=band)
    anchors, coverage = select_anchors(pairs, times, ref_norm, **kw)

    matches = [{"ref": rj, "asr_start": times[ai][0],
                "asr_end": times[ai][1], "sim": sim}
               for ai, rj, sim in pairs
               if ai is not None and rj is not None and sim >= 0.5]
    out = {"anchors": anchors, "coverage": coverage, "matches": matches}
    if nontext is not None:
        out["nontext_runs"] = nontext_runs(pairs, times, raw, **nontext)
    return out


# --- דיבור שאינו בטקסט (PLAN_TEFILA 8.26; פרופיל שירה) -------------------------
#
# חזן מדבר לפני/בין הקטעים: הקדמה, הכרזה, שם הניגון. התמלול שומע את הדיבור
# הזה היטב — רצף מילים קצרות (0.1–0.5 ש׳ למילה) שאין להן אח בטקסט — בעוד
# שמילים מושרות ארוכות (0.7–2 ש׳). זה הסימן: ריצה של מילים קצרות שאינן
# טקסט = דיבור שאינו בטקסט. ממנה נגזרים שני תיקונים (apply_nontext_runs):
# עוגנים בתוכה נזרקים, ותחילת השורה שאחריה חסומה מלמטה בסוף הדיבור.

def nontext_runs(pairs: list, times: list, words: list, *, text_sim=0.6,
                 max_word_sec=0.6, min_words=3, min_total_sec=0.8,
                 split_gap_sec=1.0, merge_gap_sec=3.0) -> list:
    """זוגות align_sequences + זמני/מילות התמלול (המסוננים) → ריצות דיבור.

    מחזיר [{"start","end","text","asr_lo","asr_hi"}] לפי הזמן.
    """
    textlike = [False] * len(times)
    for ai, rj, sim in pairs:
        if ai is not None and rj is not None and sim >= text_sim:
            textlike[ai] = True
    runs, cur = [], []
    for i, (s, e) in enumerate(times):
        speechy = not textlike[i] and e - s <= max_word_sec
        if cur and (not speechy or s - times[cur[-1]][1] > split_gap_sec):
            runs.append(cur)
            cur = []
        if speechy:
            cur.append(i)
    if cur:
        runs.append(cur)
    runs = [(r[0], r[-1]) for r in runs
            if len(r) >= min_words
            and times[r[-1]][1] - times[r[0]][0] >= min_total_sec]
    merged = []
    for lo, hi in runs:
        if (merged and not any(textlike[merged[-1][1] + 1:lo])
                and times[lo][0] - times[merged[-1][1]][1] <= merge_gap_sec):
            merged[-1] = (merged[-1][0], hi)
        else:
            merged.append((lo, hi))
    return [{"start": times[lo][0], "end": times[hi][1],
             "text": " ".join(words[lo:hi + 1]), "asr_lo": lo, "asr_hi": hi}
            for lo, hi in merged]


def apply_nontext_runs(anchors: list, runs: list, unit_starts, n_ref: int,
                       audio_dur: float, *, drop_before_sec=1.0,
                       min_sec_per_word=0.15) -> list:
    """עוגנים + ריצות דיבור → עוגנים מתוקנים (ממוינים לפי ref).

    לכל ריצה: (1) עוגן שמתחיל ב-[start − drop_before_sec, end] נזרק — מילת
    טקסט "שנשמעה" בתוך דיבור שאינו בטקסט היא כמעט תמיד התאמה מקרית;
    (2) תחילת היחידה (שורה) הראשונה שבין העוגנים התוחמים את הריצה מקבלת
    עוגן-דמה עם חסם תחתון: {"lower_bound": True, "start": סוף הריצה,
    "run_start": תחילתה} — המילה לא תתחיל לפני סוף הדיבור, והמילים שלפניה
    יסתיימו לפני תחילתו (ראה windows.build_windows). החסם נוסף רק אם יש
    מקום סביר (min_sec_per_word) למילים שמשני צדיו — כך דיבור בסוף ההקלטה
    ("תודה רבה") לא מושך שורה שלמה אחריו.
    ‏unit_starts — אינדקסי המילים (השטוחים) שפותחות יחידה. כל ריצה שעברה
    מקבלת "pseudo_ref" (או None) לדיווח.
    """
    starts = sorted(set(unit_starts))
    anchors = sorted(anchors, key=lambda a: a["start"])
    for run in sorted(runs, key=lambda r: r["start"]):
        t0, t1 = run["start"], run["end"]
        anchors = [a for a in anchors
                   if not (t0 - drop_before_sec <= a["start"] <= t1)]
        left = [a for a in anchors if a["start"] < t0]
        right = [a for a in anchors if a["start"] > t1]
        lo = left[-1]["ref"] if left else -1
        lo_t = left[-1]["end"] if left else 0.0
        hi = right[0]["ref"] if right else n_ref
        hi_t = right[0]["start"] if right else audio_dur
        run["pseudo_ref"] = None
        cands = [u for u in starts if lo < u < hi]
        if not cands:
            continue
        u = cands[0]
        if t0 - lo_t < (u - lo - 1) * min_sec_per_word:
            continue
        if hi_t - t1 < (hi - u) * min_sec_per_word:
            continue
        anchors.append({"ref": u, "asr": None, "start": t1, "end": t1,
                        "sim": None, "lower_bound": True, "run_start": t0})
        anchors.sort(key=lambda a: a["start"])
        run["pseudo_ref"] = u
    return sorted(anchors, key=lambda a: a["ref"])
