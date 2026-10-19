# -*- coding: utf-8 -*-
"""בדיקת ביצועים סינתטית ל-align_sequences (PLAN_TEFILA.md, שאלה 8.19).

תפילה שלמה = אלפי מילים. align_sequences בונה DP ברצועה (band=250) על
מילונים של Python — ~n×(2·band+1) תאים. הסקריפט מודד זמן וזיכרון שיא
(tracemalloc) על רצפים סינתטיים של 1k/3k/5k/10k מילים עם רעש מציאותי:
החלפות (מילה משובשת/אחרת), הוספות (מילים שהתמלול "המציא") ומחיקות
(מילים שהתמלול פספס).

הנתונים סינתטיים לגמרי — מילים אקראיות מאותיות עבריות, לא טקסט אמיתי.
ספריה סטנדרטית בלבד, בלי רשת.

הרצה:
    python3 tools/bench_align.py                  # 1000 3000 5000 10000
    python3 tools/bench_align.py --sizes 1000 --noise 0.2 --seed 7
    python3 tools/bench_align.py --no-tracemalloc  # זמן "נקי" (tracemalloc מאט)
"""

import argparse
import random
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aligner import anchors  # noqa: E402
from aligner.anchors import align_sequences  # noqa: E402

# אותיות רגילות (בלי סופיות) — כמו הפלט של normalize_word
_LETTERS = "אבגדהוזחטיכלמנסעפצקרשת"


def _random_word(rng: random.Random) -> str:
    return "".join(rng.choice(_LETTERS) for _ in range(rng.randint(2, 7)))


def _mutate(word: str, rng: random.Random) -> str:
    """שיבוש קל של מילה: החלפת/מחיקת/הוספת אות אחת (טעות תמלול טיפוסית)."""
    chars = list(word)
    op = rng.choice(("sub", "del", "ins"))
    k = rng.randrange(len(chars))
    if op == "sub":
        chars[k] = rng.choice(_LETTERS)
    elif op == "del" and len(chars) > 2:
        chars.pop(k)
    else:
        chars.insert(k, rng.choice("וי"))  # כתיב מלא — המקרה הנפוץ
    return "".join(chars)


def make_pair(n_words: int, noise: float, seed: int = 0):
    """(asr_words, ref_words) סינתטיים. noise — שיעור הרעש הכולל, שמתחלק
    שווה בשווה בין החלפות, הוספות ומחיקות. חלק מההחלפות שיבוש קל וחלק
    מילה אחרת לגמרי."""
    rng = random.Random(seed)
    # אוצר מילים מוגבל — כדי שיהיו מילים חוזרות כמו בטקסט אמיתי
    vocab = [_random_word(rng) for _ in range(max(50, n_words // 4))]
    ref = [rng.choice(vocab) for _ in range(n_words)]
    asr = []
    p = noise / 3.0
    for w in ref:
        r = rng.random()
        if r < p:                       # מחיקה: התמלול פספס
            continue
        if r < 2 * p:                   # החלפה
            asr.append(_mutate(w, rng) if rng.random() < 0.6
                       else _random_word(rng))
        else:
            asr.append(w)
        if rng.random() < p:            # הוספה: התמלול "המציא" מילה
            asr.append(_random_word(rng))
    return asr, ref


def run_one(n_words: int, noise: float, seed: int, band: int,
            use_tracemalloc: bool = True) -> dict:
    asr, ref = make_pair(n_words, noise, seed)
    anchors._weighted_distance.cache_clear()  # מדידה הוגנת — בלי cache חם
    if use_tracemalloc:
        tracemalloc.start()
    t0 = time.perf_counter()
    pairs = align_sequences(asr, ref, band=band)
    elapsed = time.perf_counter() - t0
    peak = 0
    if use_tracemalloc:
        _cur, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    matched = sum(1 for a, r, s in pairs
                  if a is not None and r is not None and s >= 0.5)
    return {"n_ref": len(ref), "n_asr": len(asr), "seconds": elapsed,
            "peak_mb": peak / 1e6, "matched_frac": matched / len(ref)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sizes", type=int, nargs="+",
                    default=[1000, 3000, 5000, 10000])
    ap.add_argument("--noise", type=float, default=0.15)
    ap.add_argument("--band", type=int, default=250)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-tracemalloc", action="store_true")
    args = ap.parse_args(argv)

    mem_col = "-" if args.no_tracemalloc else "זיכרון שיא (MB)"
    print(f"רעש={args.noise:.0%}  band={args.band}  seed={args.seed}")
    print(f"{'ref':>7} {'asr':>7} {'שניות':>9} {mem_col:>16} {'הותאמו':>8}")
    for n in args.sizes:
        r = run_one(n, args.noise, args.seed, args.band,
                    use_tracemalloc=not args.no_tracemalloc)
        mem = "-" if args.no_tracemalloc else f"{r['peak_mb']:.1f}"
        print(f"{r['n_ref']:>7} {r['n_asr']:>7} {r['seconds']:>9.2f} "
              f"{mem:>16} {r['matched_frac']:>8.1%}")


if __name__ == "__main__":
    main()
