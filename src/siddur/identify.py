# -*- coding: utf-8 -*-
"""זיהוי הקטע בסידור מתוך תמלול של הקלטה — PLAN_TEFILA.md משימה 4.5.1.

Python טהור (חוץ מ-run_identify, שמייבא את התמלול בעצלות): מקבל את מילות
התמלול ומחזיר מועמדים מדורגים — נוסח, קטע (עלה בקטלוג) וטווח פסקאות.

האינדקס (‏data/siddur/identify_index.json.gz, ‏tools/build_identify_index.py):
הטקסט הנאמר של כל עלה, כמילים מנורמלות בדיוק כמו מילות היישור בצינור
(‏anchors.normalize_word על align_plain במצב tefila). כאן נבנים ממנו בזיכרון
n-gramים של 3 מילים.

השלבים:
1. **הצבעה:** כל 3 מילים רצופות בתמלול ⇐ המקומות בטקסטים שבהם מופיעות אותן
   3 מילים. המפתח הוא "שלד" המילה — בלי ו/י (כתיב מלא/חסר, ו' החיבור שהתמלול
   מוסיף או משמיט). n-gram שמופיע ביותר מ-MAX_POSTINGS מקומות (‏"ברוך אתה ה'")
   לא מצביע.
2. **שרשור:** בכל עלה — השרשרת הארוכה ביותר של פגיעות שעולה גם בתמלול וגם
   בטקסט, בפערים סבירים (‏CHAIN_GAP) ובלי סטייה גדולה מהאלכסון.
3. **אימות מטושטש:** לעלים המובילים — יישור גלובלי (‏anchors.align_sequences,
   ‏word_similarity — אותו דמיון שהמיישר משתמש בו) בין קטע התמלול לקטע הטקסט,
   והאשכול הצפוף ביותר של התאמות (דמיון ≥ MATCH_SIM). הציון = סכום הדמיון.
4. **רצף עלים:** הקלטה שעוברת מעלה לעלה הבא (בסידור אשכנז, למשל, "נשמת" ו"שוכן
   עד" הם עלים נפרדים) ⇐ מועמד אחד עם כמה חלקים, כשהעלים סמוכים בקטלוג, ההתאמה
   בראשון מגיעה לסופו, וההתאמה בשני מתחילה בתחילתו.
5. **כפילויות:** אותו טקסט בדיוק בכמה עלים (קדיש, אשרי בחול ובשבת) ⇐ מועמד
   אחד, והשאר ב-also.
"""

import gzip
import json
from bisect import bisect_right
from pathlib import Path

FORMAT = 1
INDEX_PATH = (Path(__file__).resolve().parent.parent.parent
              / "data" / "siddur" / "identify_index.json.gz")

GRAM = 3
GRAMS = (3, 2)         # גם זוגות מילים: שגיאת תמלול אחת שוברת 3 שלשות אבל רק 2 זוגות
# n-gram שכיח מזה לא מצביע (נוסחאות ברכה); קדיש ≈ 120 מופעים. לזוגות — תקרה
# נמוכה יותר: זוג שכיח ("אין לנו") לא אומר כלום
MAX_POSTINGS = {3: 400, 2: 60}
_OFF_BITS = 20         # קוד פגיעה = עלה << 20 | היסט (עלה ארוך ביותר ≈ 9000 מילים)
_OFF_MASK = (1 << _OFF_BITS) - 1
MIN_CHAIN = 2          # פגיעות בשרשרת — פחות מזה לא מועמד (האימות המטושטש מסנן)
CHAIN_GAP = 40         # מילים בין פגיעות עוקבות בשרשרת (תמלול וטקסט)
CHAIN_DRIFT = 12       # סטייה מותרת מהאלכסון בין פגיעות עוקבות (+ חצי מהפער)
REFINE_TOP = 16        # כמה עלים עוברים לאימות המטושטש
REFINE_MAX = 48        # ועוד שרשראות באזורים לא מכוסים — עד כאן
NEIGHBOR_MAX = 16      # ועוד שרשראות בעלים סמוכים לעלים שנבחרו (לרצפים)
REGION_MIN = 4         # אזור תמלול "מכוסה" כשיש בו כך שרשראות שנבחרו
MARGIN = 12            # מילים שמוסיפים משני צידי השרשרת לפני האימות
MATCH_SIM = 0.6        # דמיון מילים שנחשב התאמה באימות
EDGE_SIM = 0.8         # התאמה בקצה הרצף צריכה דמיון כזה (אחרת נחתכת)
GAP_FREE = 3           # פער (מילים) בין התאמות עוקבות שלא עולה כלום
REF_GAP_COST = 0.04    # למילת טקסט שלא נשמעה בתמלול (מליסמה: 30 מילים ≈ 1.1)
ASR_GAP_COST = 0.08    # למילת תמלול שאינה בטקסט (דיבור, הכרזה)
GAP_CUT = 150          # פער גדול מזה — לא אותו ביצוע
MIN_MATCHED = 6        # מועמד צריך לפחות כך מילים מתאימות
SEQ_SKIP = 2           # עלים שמותר "לדלג" עליהם ברצף (קצרים בלבד)
SEQ_SKIP_WORDS = 30    # עלה קצר מזה מותר לדילוג ברצף (הוראה, קדיש קצר)
SEQ_EDGE = 40          # כמה מילים מסוף/תחילת עלה עוד נחשבים "הגיע לסופו"
SEQ_ASR_GAP = 80       # פער מרבי בתמלול בין חלקים עוקבים ברצף
PREFERRED_BONUS = 1.03  # הנוסח שהמשתמש בחר — עדיפות בתיקו כמעט
TOP = 5


def skeleton(word: str) -> str:
    """מילה מנורמלת ⇐ מפתח להצבעה: בלי ו/י (מילה שכולה ו/י נשארת)."""
    s = word.replace("ו", "").replace("י", "")
    return s or word


# --- האינדקס -------------------------------------------------------------------

class Index:
    """האינדקס בזיכרון. ‏data — ה-dict של identify_index.json.gz."""

    def __init__(self, data: dict):
        if data.get("format") != FORMAT:
            raise ValueError(f"גרסת אינדקס הזיהוי לא נתמכת: {data.get('format')!r}")
        self.vocab = data["vocab"]
        self.nusach_titles = data.get("nusachim", {})
        self.leaves = []
        for i, lf in enumerate(data["leaves"]):
            words = [self.vocab[w] for w in lf["w"]]
            starts = lf["s"]
            self.leaves.append({
                "i": i, "nusach": lf["n"], "path": lf["p"], "title": lf["t"],
                "crumbs": lf.get("c", []), "total": lf.get("P", 0),
                "par_n": [s[0] for s in starts], "par_off": [s[1] for s in starts],
                "first": lf.get("f", {}), "words": words,
            })
        self._grams = None
        self._sk_id = None

    @classmethod
    def load(cls, path=None) -> "Index":
        p = Path(path) if path else INDEX_PATH
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def _build(self):
        sk_id, sk_of_vocab = {}, []
        for w in self.vocab:
            sk_of_vocab.append(sk_id.setdefault(skeleton(w), len(sk_id)))
        vid = {w: i for i, w in enumerate(self.vocab)}
        self._sk_id, self._k, self._grams = sk_id, len(sk_id) + 1, {}
        grams = self._grams
        for lf in self.leaves:
            ids = [sk_of_vocab[vid[w]] for w in lf["words"]]
            base = lf["i"] << _OFF_BITS
            for size in GRAMS:
                cap = MAX_POSTINGS[size]
                for off in range(len(ids) - size + 1):
                    key = self._key(ids[off:off + size])
                    cur = grams.get(key)
                    code = base | off
                    if cur is None:
                        grams[key] = code
                    elif isinstance(cur, int):
                        grams[key] = [cur, code]
                    elif len(cur) <= cap:
                        cur.append(code)

    def _key(self, ids) -> int:
        """מפתח n-gram: 3 מילים ⇐ מספר חיובי, 2 מילים ⇐ שלילי (מרחב נפרד)."""
        k = self._k
        if len(ids) == 3:
            return (ids[0] * k + ids[1]) * k + ids[2]
        return -(ids[0] * k + ids[1]) - 1

    def postings(self, sk_ids) -> list:
        """2–3 מזהי שלד ⇐ קודי הפגיעות (ריק אם לא נמצא או שכיח מדי)."""
        if self._grams is None:
            self._build()
        if any(s < 0 for s in sk_ids):
            return []
        cur = self._grams.get(self._key(sk_ids))
        if cur is None:
            return []
        if isinstance(cur, int):
            return [cur]
        return [] if len(cur) > MAX_POSTINGS[len(sk_ids)] else cur

    def sk_ids(self, words: list) -> list:
        if self._grams is None:
            self._build()
        return [self._sk_id.get(skeleton(w), -1) for w in words]

    # --- פסקאות -------------------------------------------------------------
    @staticmethod
    def paragraph_of(leaf: dict, offset: int) -> int:
        """היסט מילה בעלה ⇐ מספר הפסקה (כמו from/to של api/siddur)."""
        k = bisect_right(leaf["par_off"], offset) - 1
        return leaf["par_n"][max(0, k)]


_CACHE = {}


def load_index(path=None) -> Index:
    """טעינה פעם אחת לתהליך (קונטיינר חם לא טוען שוב)."""
    key = str(path or INDEX_PATH)
    if key not in _CACHE:
        _CACHE[key] = Index.load(path)
    return _CACHE[key]


# --- הזיהוי --------------------------------------------------------------------

def _normalize_asr(asr_words) -> list:
    """מילות התמלול ⇐ [(מילה מנורמלת, start, end)] (מילים בלי אות עברית נזרקות)."""
    from aligner.anchors import normalize_word
    out = []
    for w in asr_words:
        if isinstance(w, str):
            word, start, end = w, None, None
        else:
            word, start, end = w.get("word", ""), w.get("start"), w.get("end")
        nw = normalize_word(word)
        if nw:
            out.append((nw, start, end))
    return out


def _chain(hits: list) -> list:
    """פגיעות (i, off) של עלה אחד ⇐ השרשרת הארוכה ביותר שעולה בשניהם."""
    hits.sort()
    h = len(hits)
    best, prev = [1] * h, [-1] * h
    lo = 0
    for k in range(h):
        ik, ok = hits[k]
        while hits[lo][0] < ik - CHAIN_GAP:
            lo += 1
        bk, pk = 1, -1
        for j in range(lo, k):
            ij, oj = hits[j]
            if ij >= ik or oj >= ok or ok - oj > CHAIN_GAP:
                continue
            di, do = ik - ij, ok - oj
            if abs(do - di) > CHAIN_DRIFT + di // 2:
                continue
            if best[j] + 1 > bk:
                bk, pk = best[j] + 1, j
        best[k], prev[k] = bk, pk
    k = max(range(h), key=lambda x: best[x])
    out = []
    while k >= 0:
        out.append(hits[k])
        k = prev[k]
    out.reverse()
    return out


def _pick_chains(chains: list, n: int, index: "Index") -> list:
    """השרשראות שעוברות לאימות: REFINE_TOP הארוכות, ועוד שרשראות במקומות
    בתמלול שבנוסח שלהן עוד לא נבחרו בהם REGION_MIN שרשראות. בלי זה, פסוקים
    שמופיעים בעשרות עלים ("כי לה' המלוכה") תופסים את כל המקומות, והחלק הבא
    בהקלטה (נשמת באשכנז — עלה נפרד, עם מעט פגיעות) לא נבדק בכלל."""
    # הקלטה ארוכה עוברת בהרבה עלים — יותר מקומות לאימות (‏~100 מילים לעלה)
    top = max(REFINE_TOP, n // 60)
    most = max(REFINE_MAX, n // 20)
    cover = {}
    picked = []
    for item in chains:
        ch = item[2]
        cov = cover.setdefault(index.leaves[item[1]]["nusach"], [0] * n)
        pos = sorted({i + d for i, _ in ch for d in range(GRAM) if i + d < n})
        if len(picked) >= top:
            if (len(picked) >= most
                    or min(cov[i] for i in pos) >= REGION_MIN):
                continue
        picked.append(item)
        for i in pos:
            cov[i] += 1
    # עלה סמוך (הבא/הקודם בקטלוג) לעלה שנבחר — גם אם יש לו מעט פגיעות: כך
    # נבנים רצפים (נשמת אחרי "אז ישיר" באשכנז)
    leaves = {item[1] for item in picked}
    near = {i + d for i in leaves for d in (-2, -1, 1, 2)} - leaves
    extra = [item for item in chains if item[1] in near][:max(NEIGHBOR_MAX, top)]
    return picked + extra


def _refine(norm: list, leaf: dict, chain: list) -> dict:
    """אימות מטושטש של עלה מול התמלול סביב השרשרת ⇐ מועמד, או None."""
    from aligner.anchors import align_sequences
    words = leaf["words"]
    n, m = len(norm), len(words)
    i0, i1 = chain[0][0], chain[-1][0] + GRAM - 1
    o0, o1 = chain[0][1], chain[-1][1] + GRAM - 1
    a0, a1 = max(0, i0 - MARGIN), min(n, i1 + 1 + MARGIN)
    r0, r1 = max(0, o0 - MARGIN), min(m, o1 + 1 + MARGIN)
    asr = [w for w, _, _ in norm[a0:a1]]
    ref = words[r0:r1]
    band = max(40, abs(len(ref) - len(asr)) + 40)
    pairs = align_sequences(asr, ref, band=band)
    matched = [(ai + a0, rj + r0, sim) for ai, rj, sim in pairs
               if ai is not None and rj is not None and sim >= MATCH_SIM]
    if not matched:
        return None
    best = _densest_run(matched)
    if len(best) < MIN_MATCHED:
        return None
    first, last = best[0], best[-1]
    return {
        "leaf": leaf["i"], "nusach": leaf["nusach"],
        "score": round(sum(s for _, _, s in best), 3), "matched": len(best),
        "asr": (first[0], last[0]), "ref": (first[1], last[1]),
    }


def _gap_cost(asr_gap: int, ref_gap: int) -> float:
    """מחיר הפער בין שתי התאמות עוקבות. מילים שהתמלול פספס (פער בטקסט בלבד —
    מליסמה, שירה) זולות; פער בתמלול (דיבור שאינו בטקסט) יקר יותר; פער גדול
    מאוד — חיתוך."""
    if asr_gap > GAP_CUT or ref_gap > GAP_CUT:
        return float("inf")
    return (max(0, ref_gap - GAP_FREE) * REF_GAP_COST
            + max(0, asr_gap - GAP_FREE) * ASR_GAP_COST)


def _densest_run(matched: list) -> list:
    """רצף ההתאמות עם הציון הגבוה ביותר (סכום דמיון פחות מחירי הפערים —
    Kadane). התאמות בודדות רחוקות, שהיישור הגלובלי כפה בקצוות, נשארות בחוץ."""
    best_sum, best_rng = float("-inf"), (0, 0)
    cur_sum, cur_start = float("-inf"), 0
    for k, (ai, rj, sim) in enumerate(matched):
        if k:
            pa, pr, _ = matched[k - 1]
            cont = cur_sum - _gap_cost(ai - pa - 1, rj - pr - 1) + sim
        else:
            cont = float("-inf")
        if cont >= sim:
            cur_sum = cont
        else:
            cur_sum, cur_start = sim, k
        if cur_sum > best_sum:
            best_sum, best_rng = cur_sum, (cur_start, k)
    a, b = best_rng
    # קצוות חלשים (‏"אני"≈"שאדני" בהקדמה המדוברת) לא קובעים את הטווח
    while a < b and matched[a][2] < EDGE_SIM:
        a += 1
    while b > a and matched[b][2] < EDGE_SIM:
        b -= 1
    return matched[a:b + 1]


def _sequences(cands: list, index: Index) -> list:
    """מועמדי עלים ⇐ רצפים (עלה ואחריו העלה הבא בקטלוג) — הטוב ביותר שנגמר
    בכל מועמד. כל רצף: רשימת מועמדי עלים לפי הסדר."""
    leaves = index.leaves
    order = sorted(range(len(cands)), key=lambda c: cands[c]["asr"][0])
    best, prev = {}, {}
    for c in order:
        cc = cands[c]
        lc = leaves[cc["leaf"]]
        best[c], prev[c] = cc["score"], None
        if cc["ref"][0] > SEQ_EDGE:      # לא מתחיל בתחילת העלה — לא המשך
            continue
        for p in order:
            if p == c or p not in best:
                continue
            pc = cands[p]
            lp = leaves[pc["leaf"]]
            if lp["nusach"] != lc["nusach"]:
                continue
            gap = lc["i"] - lp["i"]
            if not 1 <= gap <= SEQ_SKIP + 1:
                continue
            between = leaves[lp["i"] + 1:lc["i"]]
            if any(lf["nusach"] != lc["nusach"] or len(lf["words"]) > SEQ_SKIP_WORDS
                   for lf in between):
                continue
            if len(lp["words"]) - 1 - pc["ref"][1] > SEQ_EDGE:   # לא הגיע לסוף
                continue
            if pc["asr"][1] > cc["asr"][0] + GRAM:              # חפיפה בתמלול
                continue
            if cc["asr"][0] - pc["asr"][1] > SEQ_ASR_GAP:
                continue
            if best[p] + cc["score"] > best[c]:
                best[c], prev[c] = best[p] + cc["score"], p
    seqs = []
    for c in order:
        chain, k = [], c
        while k is not None:
            chain.append(cands[k])
            k = prev[k]
        seqs.append(list(reversed(chain)))
    return seqs


def _part(index: Index, cand: dict, norm: list) -> dict:
    leaf = index.leaves[cand["leaf"]]
    pf = Index.paragraph_of(leaf, cand["ref"][0])
    pt = Index.paragraph_of(leaf, cand["ref"][1])
    a, b = cand["asr"]
    return {
        "path": leaf["path"], "title": leaf["title"],
        "breadcrumb": leaf["crumbs"], "from": pf, "to": pt,
        "total": leaf["total"],
        "first_words": leaf["first"].get(str(pf), ""),
        "last_first_words": leaf["first"].get(str(pt), ""),
        "matched": cand["matched"],
        "ref_words": cand["ref"][1] - cand["ref"][0] + 1,
        "word_range": [cand["ref"][0], cand["ref"][1]],
        "start": norm[a][1], "end": norm[b][2],
    }


def _signature(index: Index, seq: list) -> tuple:
    return tuple(tuple(index.leaves[c["leaf"]]["words"][c["ref"][0]:c["ref"][1] + 1])
                 for c in seq)


def identify(asr_words, index: Index, nusach: str = None, top: int = TOP) -> dict:
    """מילות התמלול ⇐ {"candidates": [...], "asr_words": n}.

    ‏asr_words — רשימת {"word","start","end"} (פלט asr.transcribe) או מחרוזות.
    ‏nusach — הנוסח שהמשתמש בחר (אם בחר): עדיפות קלה בתיקו כמעט.
    כל מועמד: nusach, nusach_title, score, coverage (חלק מילי התמלול שהוסברו),
    confidence (high/medium/low), start/end (שניות), parts (עלה אחד או רצף:
    path, title, breadcrumb, from, to, total, first_words, matched…), also
    (אותו טקסט בעלים אחרים).
    """
    norm = _normalize_asr(asr_words)
    n = len(norm)
    result = {"asr_words": n, "candidates": []}
    if n < GRAM:
        return result
    sk = index.sk_ids([w for w, _, _ in norm])
    hits = {}
    for size in GRAMS:
        for i in range(n - size + 1):
            for code in index.postings(sk[i:i + size]):
                hits.setdefault(code >> _OFF_BITS, set()).add((i, code & _OFF_MASK))
    chains = []
    for leaf_i, hs in hits.items():
        if len(hs) < MIN_CHAIN:
            continue
        ch = _chain(list(hs))
        if len(ch) >= MIN_CHAIN:
            chains.append((len(ch), leaf_i, ch))
    chains.sort(key=lambda x: (-x[0], x[1]))
    cands = []
    for _, leaf_i, ch in _pick_chains(chains, n, index):
        c = _refine(norm, index.leaves[leaf_i], ch)
        if c:
            cands.append(c)
    if not cands:
        return result

    seqs = _sequences(cands, index)
    scored = []
    for seq in seqs:
        score = sum(c["score"] for c in seq)
        scored.append((score, seq))
    # רצף שמכיל מועמד אחר עם ציון גבוה יותר ממנו — המועמד הבודד מיותר
    scored.sort(key=lambda x: -x[0])
    kept = []
    for score, seq in scored:
        ids = {id(c) for c in seq}
        if any(ids <= {id(c) for c in s} for _, s in kept):
            continue
        kept.append((score, seq))

    def rank(item):
        score, seq = item
        bonus = PREFERRED_BONUS if nusach and seq[0]["nusach"] == nusach else 1.0
        return (-score * bonus, seq[0]["leaf"])

    kept.sort(key=rank)
    out, by_sig = [], {}
    for score, seq in kept:
        sig = _signature(index, seq)
        if sig in by_sig:
            dup = by_sig[sig]
            if len(dup["also"]) < 5:
                lf = index.leaves[seq[0]["leaf"]]
                dup["also"].append({"nusach": lf["nusach"], "path": lf["path"],
                                    "title": lf["title"], "breadcrumb": lf["crumbs"]})
            continue
        matched_asr = sum(c["matched"] for c in seq)
        coverage = matched_asr / n
        matched = sum(c["matched"] for c in seq)
        confidence = ("high" if coverage >= 0.45 and matched >= 15
                      else "medium" if coverage >= 0.2 and matched >= 8 else "low")
        parts = [_part(index, c, norm) for c in seq]
        cand = {
            "nusach": seq[0]["nusach"],
            "nusach_title": index.nusach_titles.get(seq[0]["nusach"], ""),
            "score": round(score, 2), "coverage": round(coverage, 3),
            "confidence": confidence,
            "start": parts[0]["start"], "end": parts[-1]["end"],
            "parts": parts, "also": [],
        }
        by_sig[sig] = cand
        out.append(cand)
        if len(out) >= top:
            break
    result["candidates"] = out
    return result


# --- הקלטה ⇐ מועמדים (ה-worker; ייבוא עצל של התמלול) ------------------------------

IDENTIFY_WAV = "identify_16k.wav"


def run_identify(audio_path: str, work_dir: str, nusach: str = None,
                 asr_model: str = None, vad_filter: bool = False,
                 max_sec: float = None, index: Index = None,
                 top: int = TOP) -> dict:
    """הקלטה ⇐ תמלול בלבד (בלי יישור) ⇐ identify.

    ‏vad_filter=False כברירת מחדל: silero מוחק חזנות מהתמלול (בנשמת — כל מה
    שאחרי 58 ש׳; PLAN_TEFILA.md 4.3.5), וזיהוי חייב לעבוד גם על שירה.
    ‏max_sec — רק תחילת ההקלטה מתומללת (‏ffmpeg -t): מספיק לזיהוי, ועלות
    התמלול חסומה גם בהקלטה ארוכה. ‏limited=True בתשובה — ההקלטה ארוכה מזה.
    """
    import subprocess
    import wave

    from aligner import asr as asr_mod

    index = index or load_index()
    wav_path = str(Path(work_dir) / IDENTIFY_WAV)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", audio_path]
    if max_sec:
        cmd += ["-t", str(max_sec)]
    subprocess.run(cmd + ["-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                          wav_path], check=True)
    with wave.open(wav_path, "rb") as wf:
        duration = wf.getnframes() / float(wf.getframerate() or 16000)
    words, model = asr_mod.transcribe(wav_path, model_name=asr_model,
                                      vad_filter=vad_filter)
    res = identify(words, index, nusach=nusach, top=top)
    res.update({"kind": "identify", "duration": round(duration, 1),
                "limited": bool(max_sec) and duration >= max_sec - 1,
                "model": model, "vad_filter": vad_filter,
                "transcript": " ".join(w["word"] for w in words[:40])})
    return res
