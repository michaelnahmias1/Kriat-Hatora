# -*- coding: utf-8 -*-
"""בדיקת שקילות: align_sequences המהיר (PLAN_TEFILA 8.19) מול המימוש הקודם.

המימוש הקודם מועתק לכאן כמו שהוא ("קפוא") — מילון לכל שורה, ‏lru_cache
על מרחק העריכה. על אלפי רצפים אקראיים (כולל קצוות הרצועה, רצפים ריקים,
זהים, אי-התאמה מלאה, יחס אורכים קיצוני, band=0) הפלט חייב להיות זהה
לגמרי: אותם זוגות, באותו סדר, ו-sim זהה עד הביט (משווים float.hex).
בלי רשת, ספריה סטנדרטית בלבד.
"""

import random
import sys
import unittest
from functools import lru_cache
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "tools"))

from aligner import anchors  # noqa: E402
from aligner.anchors import align_sequences  # noqa: E402

# --- המימוש הקודם (עד 8.19), מועתק מילה במילה -------------------------------

_CHEAP_CHARS = frozenset("וי")
_CHEAP_COST = 0.25


@lru_cache(maxsize=1 << 18)
def _old_weighted_distance(a: str, b: str) -> float:
    prev = [0.0] * (len(b) + 1)
    for j, cb in enumerate(b, 1):
        prev[j] = prev[j - 1] + (_CHEAP_COST if cb in _CHEAP_CHARS else 1.0)
    for ca in a:
        cur = [prev[0] + (_CHEAP_COST if ca in _CHEAP_CHARS else 1.0)]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j - 1] + (0.0 if ca == cb else 1.0),
                prev[j] + (_CHEAP_COST if ca in _CHEAP_CHARS else 1.0),
                cur[j - 1] + (_CHEAP_COST if cb in _CHEAP_CHARS else 1.0)))
        prev = cur
    return prev[-1]


def _old_word_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if abs(len(a) - len(b)) > 3:
        return 0.0
    return max(0.0, 1.0 - _old_weighted_distance(a, b) / max(len(a), len(b)))


_GAP = -0.4
_MISMATCH = -0.5
_MATCH_FLOOR = 0.5


def _old_align_sequences(asr_words: list, ref_words: list,
                         band: int = 250) -> list:
    n, m = len(asr_words), len(ref_words)
    if n == 0 or m == 0:
        return ([(i, None, 0.0) for i in range(n)]
                + [(None, j, 0.0) for j in range(m)])

    ratio = m / n
    NEG = float("-inf")

    def j_range(i):
        center = round(i * ratio)
        return max(0, center - band), min(m, center + band)

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
                    sim = _old_word_similarity(aw, ref_words[j - 1])
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

    i, j = n, max(k for k in scores[n])
    pairs = []
    while i > 0 or j > 0:
        move = ptrs[i].get(j)
        if move == "d":
            sim = _old_word_similarity(asr_words[i - 1], ref_words[j - 1])
            pairs.append((i - 1, j - 1, sim))
            i, j = i - 1, j - 1
        elif move == "u" or (move is None and i > 0):
            pairs.append((i - 1, None, 0.0))
            i -= 1
        else:
            pairs.append((None, j - 1, 0.0))
            j -= 1
    pairs.reverse()
    covered = {p[1] for p in pairs if p[1] is not None}
    for j in range(m):
        if j not in covered:
            pairs.append((None, j, 0.0))
    return pairs


# --- מחוללי קלט ---------------------------------------------------------------

# אלפבית מוטה ל-ו/י (מקרי הקצה של המחיר הזול) ולאותיות נפוצות
_ALPHA = "ווווייייאבגדהזחטכלמנסעפצקרשת"
_ODD = "ab-1 "   # תווים שאינם אותיות עבריות — הפונקציה מקבלת כל מחרוזת


def _word(rng, max_len=8):
    w = "".join(rng.choice(_ALPHA) for _ in range(rng.randint(0, max_len)))
    if rng.random() < 0.03:
        w += rng.choice(_ODD)
    return w


def _mutate(w, rng):
    chars = list(w)
    for _ in range(rng.randint(1, 3)):
        op = rng.random()
        if op < 0.35 and chars:
            chars[rng.randrange(len(chars))] = rng.choice(_ALPHA)
        elif op < 0.6 and chars:
            chars.pop(rng.randrange(len(chars)))
        else:
            chars.insert(rng.randint(0, len(chars)), rng.choice("ויוי" + _ALPHA))
    return "".join(chars)


def _pair(rng, n_ref, noise):
    vocab = [_word(rng) for _ in range(max(2, n_ref // 3 + 1))]
    ref = [rng.choice(vocab) for _ in range(n_ref)]
    asr = []
    for w in ref:
        r = rng.random()
        if r < noise / 3:
            continue
        asr.append(_mutate(w, rng) if r < 2 * noise / 3 else w)
        if rng.random() < noise / 3:
            asr.append(rng.choice(vocab) if rng.random() < 0.5 else _word(rng))
    return asr, ref


def _canon(pairs):
    """זוגות ⇒ צורה שמשווה גם את ביטי ה-float (‏-0.0 מול 0.0 וכו')."""
    return [(a, r, type(s).__name__, s.hex()) for a, r, s in pairs]


class TestAlignEquivalence(unittest.TestCase):
    def assertSame(self, asr, ref, band, msg=""):
        old = _old_align_sequences(asr, ref, band=band)
        new = align_sequences(asr, ref, band=band)
        self.assertEqual(_canon(new), _canon(old),
                         f"{msg} band={band} asr={asr!r} ref={ref!r}")

    def test_random_small(self):
        rng = random.Random(819)
        for case in range(1500):
            n_ref = rng.randint(0, 40)
            asr, ref = _pair(rng, n_ref, rng.choice((0.0, 0.2, 0.5, 0.9)))
            band = rng.choice((0, 1, 2, 3, 4, 7, 15, 250,
                               abs(len(asr) - len(ref)),
                               abs(len(asr) - len(ref)) + 1))
            self.assertSame(asr, ref, band, f"case {case}")

    def test_random_band_edges(self):
        """רצועה צרה מהפרש האורכים — התא (n, m) מחוץ לרצועה, תאים בלי אף
        שכן (נפילה ל-i·GAP + j·GAP), השלמת עמודות בסוף."""
        rng = random.Random(1919)
        for case in range(600):
            asr = [_word(rng, 5) for _ in range(rng.randint(1, 30))]
            ref = [_word(rng, 5) for _ in range(rng.randint(1, 90))]
            if rng.random() < 0.5:
                asr, ref = ref, asr
            band = rng.randint(0, max(1, abs(len(asr) - len(ref)) + 2))
            self.assertSame(asr, ref, band, f"case {case}")

    def test_random_medium(self):
        rng = random.Random(2026)
        for case in range(12):
            asr, ref = _pair(rng, rng.randint(150, 400), 0.3)
            self.assertSame(asr, ref, rng.choice((5, 20, 60, 250)),
                            f"case {case}")

    def test_bench_data(self):
        """אותם רצפים סינתטיים של tools/bench_align.py (בקטן)."""
        from bench_align import make_pair
        for seed in (0, 1):
            asr, ref = make_pair(700, 0.15, seed)
            for band in (250, 30):
                self.assertSame(asr, ref, band, f"seed {seed}")

    def test_empty(self):
        for band in (0, 5, 250):
            self.assertSame([], [], band)
            self.assertSame(["אב", "גד"], [], band)
            self.assertSame([], ["אב", "גד", "הו"], band)

    def test_identical(self):
        rng = random.Random(7)
        for n in (1, 2, 5, 50, 300):
            ref = [_word(rng) for _ in range(n)]
            for band in (0, 1, 250):
                self.assertSame(list(ref), ref, band)

    def test_all_mismatch(self):
        """אלפביתים זרים — אף זוג לא מגיע ל-0.5."""
        rng = random.Random(11)
        for n, m in ((1, 1), (3, 9), (40, 25), (120, 120)):
            asr = ["".join(rng.choice("אבגד") for _ in range(4))
                   for _ in range(n)]
            ref = ["".join(rng.choice("כלמנ") for _ in range(4))
                   for _ in range(m)]
            for band in (0, 2, 250):
                self.assertSame(asr, ref, band)

    def test_empty_words_inside(self):
        """מילה ריקה ברשימה (מילת טקסט בלי אותיות עבריות) — דמיון 0.0."""
        self.assertSame(["", "אב", ""], ["אב", "", "", "גד"], 250)
        self.assertSame(["", ""], ["", ""], 1)

    def test_negative_band_raises_like_before(self):
        with self.assertRaises(ValueError):
            _old_align_sequences(["אב"], ["אב"], band=-1)
        with self.assertRaises(ValueError):
            align_sequences(["אב"], ["אב"], band=-1)


class TestSimilarityFilter(unittest.TestCase):
    """הסינון שלפני ה-DP אינו פוסל זוג דומה, וה-DP עם עצירה מוקדמת מחזיר
    בדיוק את מרחק העריכה הקודם."""

    def test_filter_and_exact_distance(self):
        rng = random.Random(4242)
        words = [_word(rng, 9) for _ in range(500)]
        words += [_mutate(w, rng) for w in words[:300]]
        words += ["", "ו", "י", "וי", "ויו", "יייי", "א", "אוי"]
        vocab = sorted(set(words))
        sigs = anchors._multiset_signatures(vocab)
        ref_sigs = [sigs[w] for w in vocab]
        for aw in vocab[::3]:
            good = anchors._similar_refs(aw, sigs[aw], range(len(vocab)),
                                         vocab, ref_sigs)
            for k, rw in enumerate(vocab):
                sim = _old_word_similarity(aw, rw)
                if sim >= _MATCH_FLOOR:
                    self.assertIn(k, good, (aw, rw))
                    self.assertEqual(good[k].hex(), sim.hex(), (aw, rw))
                else:
                    self.assertNotIn(k, good, (aw, rw))

    def test_distance_within(self):
        rng = random.Random(5)
        for _ in range(3000):
            a, b = _word(rng, 9), _word(rng, 9)
            if rng.random() < 0.5:
                b = _mutate(a, rng)
            d = _old_weighted_distance(a, b)
            limit = rng.choice((0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 100.0))
            got = anchors._weighted_distance_within(a, b, limit)
            if got is None:
                self.assertGreater(d, limit, (a, b))
            else:
                self.assertEqual(got.hex(), d.hex(), (a, b))
            self.assertEqual(anchors._weighted_distance_raw(a, b).hex(),
                             d.hex())

    def test_word_similarity_unchanged(self):
        rng = random.Random(6)
        for _ in range(2000):
            a, b = _word(rng), _word(rng)
            if rng.random() < 0.5:
                b = _mutate(a, rng)
            self.assertEqual(anchors.word_similarity(a, b).hex(),
                             _old_word_similarity(a, b).hex())


if __name__ == "__main__":
    unittest.main()
