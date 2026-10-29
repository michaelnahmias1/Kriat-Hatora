# -*- coding: utf-8 -*-
"""הערכה סינתטית של זיהוי הקטע (PLAN_TEFILA.md 4.5) — בלי רשת ובלי מודלים.

    python3 tools/eval_identify.py                     # 100 קטעים, 15–25% שגיאות
    python3 tools/eval_identify.py --n 300 --err 0.3 --seed 7

לוקחים קטעים אקראיים (30–80 מילים) מהטקסטים שבאינדקס עצמו, מקלקלים אותם כמו
תמלול רועש — החלפת אות במילה, החלפת מילה במילה אקראית, השמטה, הוספה, ו/ה'
החיבור — ומריצים identify. נכון = העלה האמיתי הוא המועמד (או ב-also, כשאותו
טקסט בדיוק מופיע בכמה עלים) והטווח שהוחזר חופף לטווח האמיתי. "טווח מדויק" =
גם from/to זהים לפסקאות האמיתיות.
"""

import argparse
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from siddur.identify import Index, load_index, identify  # noqa: E402

LETTERS = "אבגדהוזחטיכלמנסעפצקרשת"


def corrupt_word(w: str, rng: random.Random) -> str:
    """שגיאת תמלול "קרובה": החלפה/השמטה/הוספה של אות אחת."""
    if len(w) < 2:
        return w + rng.choice(LETTERS)
    i = rng.randrange(len(w))
    op = rng.random()
    if op < 0.5:
        return w[:i] + rng.choice(LETTERS) + w[i + 1:]
    if op < 0.75:
        return w[:i] + w[i + 1:]
    return w[:i] + rng.choice(LETTERS) + w[i:]


def simulate_asr(words: list, err: float, vocab: list, rng: random.Random) -> list:
    """מילים ⇐ "תמלול": ‏err = שיעור ההחלפות + ההשמטות; ועוד ~5% הוספות."""
    out = []
    for w in words:
        r = rng.random()
        if r < err * 0.35:            # השמטה (מליסמה, מילה שלא נשמעה)
            continue
        if r < err * 0.7:             # שגיאת אות
            out.append(corrupt_word(w, rng))
        elif r < err:                 # מילה אחרת לגמרי
            out.append(rng.choice(vocab))
        elif r < err + 0.05:          # ו' החיבור / ה' הידיעה שנוספו או נשמטו
            out.append(w[1:] if w[0] in "וה" and len(w) > 2 else "ו" + w)
        else:
            out.append(w)
        if rng.random() < 0.05:       # מילה נוספת (דיבור, "אמן")
            out.append(rng.choice(vocab))
    return out


def _grams(words: list) -> set:
    return {tuple(words[i:i + 3]) for i in range(len(words) - 2)}


def run(index: Index, n: int, err_lo: float, err_hi: float, seed: int,
        min_len: int = 30, max_len: int = 80, verbose: bool = False) -> dict:
    rng = random.Random(seed)
    pool = [lf for lf in index.leaves if len(lf["words"]) >= min_len]
    by_path = {(lf["nusach"], lf["path"]): lf for lf in index.leaves}
    stats = {"n": 0, "top1": 0, "top3": 0, "range_exact": 0, "none": 0,
             "text1": 0, "text3": 0, "leaf_hit1": 0,
             "conf": {}, "seconds": 0.0}
    for _ in range(n):
        lf = rng.choice(pool)
        length = rng.randint(min_len, min(max_len, len(lf["words"])))
        start = rng.randrange(len(lf["words"]) - length + 1)
        truth = lf["words"][start:start + length]
        t_from = Index.paragraph_of(lf, start)
        t_to = Index.paragraph_of(lf, start + length - 1)
        err = rng.uniform(err_lo, err_hi)
        asr = simulate_asr(truth, err, index.vocab, rng)
        t0 = time.time()
        res = identify(asr, index)
        stats["seconds"] += time.time() - t0
        stats["n"] += 1
        cands = res["candidates"]
        if not cands:
            stats["none"] += 1
        rank = None
        for k, c in enumerate(cands[:3]):
            paths = [(p["path"], p["from"], p["to"]) for p in c["parts"]]
            hit = next(((f, t) for p, f, t in paths
                        if p == lf["path"] and f <= t_to and t >= t_from), None)
            same_text = any(a["path"] == lf["path"] for a in c["also"])
            if hit or same_text:
                rank = k
                if k == 0 and hit:
                    stats["leaf_hit1"] += 1
                    stats["range_exact"] += hit == (t_from, t_to)
                break
        # "אותו טקסט": הטקסט שהמועמד הצביע עליו מכיל את רוב ה-3-gramים של הקטע
        # האמיתי (קדיש/אבות/עלינו מופיעים זהים בעלים רבים — אין דרך להבחין)
        trank = None
        tg = _grams(truth)
        for k, c in enumerate(cands[:3]):
            got = set()
            for p in c["parts"]:
                cl = by_path[(c["nusach"], p["path"])]
                a, b = p["word_range"]
                got |= _grams(cl["words"][max(0, a - 5):b + 6])
            if tg and len(tg & got) >= 0.8 * len(tg):
                trank = k
                break
        if rank is not None and (trank is None or rank < trank):
            trank = rank
        stats["text1"] += trank == 0
        stats["text3"] += trank is not None
        if rank == 0:
            stats["top1"] += 1
        if rank is not None:
            stats["top3"] += 1
        if cands:
            conf = cands[0]["confidence"]
            d = stats["conf"].setdefault(conf, [0, 0])
            d[0] += 1
            d[1] += rank == 0
        if verbose and trank != 0:
            top = cands[0]["parts"][0] if cands else {}
            print(f"✗ {lf['path']} {t_from}-{t_to} ({length} מילים, err {err:.2f}) ⇐ "
                  f"{top.get('path')} {top.get('from')}-{top.get('to')} "
                  f"[rank {rank}]")
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description="הערכה סינתטית של זיהוי הקטע")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--err", type=float, nargs=2, default=(0.15, 0.25),
                    metavar=("LO", "HI"))
    ap.add_argument("--len", type=int, nargs=2, default=(30, 80),
                    metavar=("MIN", "MAX"))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    index = load_index()
    s = run(index, args.n, args.err[0], args.err[1], args.seed,
            args.len[0], args.len[1], args.verbose)
    n = s["n"]
    print(f"קטעים: {n} · שגיאות {args.err[0]:.0%}–{args.err[1]:.0%} · "
          f"אורך {args.len[0]}–{args.len[1]} מילים · seed {args.seed}")
    print(f"העלה המדויק — top-1: {s['top1']}/{n} ({s['top1'] / n:.0%}) · "
          f"top-3: {s['top3']}/{n} ({s['top3'] / n:.0%})")
    print(f"אותו טקסט (גם בעלה אחר) — top-1: {s['text1']}/{n} ({s['text1'] / n:.0%}) · "
          f"top-3: {s['text3']}/{n} ({s['text3'] / n:.0%})")
    print(f"טווח פסקאות זהה (כשהעלה עצמו ב-top-1): {s['range_exact']}/{s['leaf_hit1']} · "
          f"בלי מועמד: {s['none']}")
    for conf, (cnt, ok) in sorted(s["conf"].items()):
        print(f"  ביטחון {conf}: {cnt} קטעים, {ok} נכונים ב-top-1")
    print(f"זמן ממוצע לזיהוי: {s['seconds'] / max(1, n) * 1000:.0f}ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
