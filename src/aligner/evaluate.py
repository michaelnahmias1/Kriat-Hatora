# -*- coding: utf-8 -*-
"""רתמת הערכה: שגיאות גבול מול ground truth והשוואת שיטות.

Python טהור. המדדים כמוגדר ב-PLAN.md שלב 2: התפלגות שגיאת נקודת-כניסה
בחתך מוקדם/מאוחר (הצופה סולח למוקדם, לא למאוחר), ואחוז בטווח 0.5/1.0 שניות.
"""


def boundary_errors(pred_starts: list, truth_starts: list) -> list:
    """שגיאה לכל גבול: חיובי = הכתובית מאחרת, שלילי = מקדימה."""
    if len(pred_starts) != len(truth_starts):
        raise RuntimeError(
            f"אי-התאמה: {len(pred_starts)} גבולות חזויים מול "
            f"{len(truth_starts)} ב-ground truth")
    return [p - t for p, t in zip(pred_starts, truth_starts)]


def error_metrics(errors: list) -> dict:
    """מדדי איכות על רשימת שגיאות גבול (שניות)."""
    if not errors:
        return {"n": 0}
    abs_sorted = sorted(abs(e) for e in errors)
    n = len(errors)
    return {
        "n": n,
        "median_abs": abs_sorted[n // 2],
        "max_abs": abs_sorted[-1],
        "pct_within_05": 100.0 * sum(1 for e in abs_sorted if e <= 0.5) / n,
        "pct_within_10": 100.0 * sum(1 for e in abs_sorted if e <= 1.0) / n,
        "early": sum(1 for e in errors if e < -0.2),
        "late": sum(1 for e in errors if e > 0.2),
    }


def comparison_table(methods: dict, truth_starts: list) -> str:
    """{שם שיטה: רשימת גבולות} → טבלת השוואה בעברית."""
    header = (f"{'שיטה':<24} {'בטווח 0.5s':>10} {'בטווח 1.0s':>10} "
              f"{'חציון':>8} {'מקס':>8} {'מקדים':>6} {'מאחר':>6}")
    lines = ["השוואת שיטות סנכרון", "=" * len(header), header,
             "-" * len(header)]
    for name, starts in methods.items():
        m = error_metrics(boundary_errors(starts, truth_starts))
        lines.append(
            f"{name:<24} {m['pct_within_05']:>9.1f}% {m['pct_within_10']:>9.1f}% "
            f"{m['median_abs']:>7.2f}s {m['max_abs']:>7.2f}s "
            f"{m['early']:>6} {m['late']:>6}")
    lines.append("")
    lines.append("יעד PLAN.md: ‏~90% בטווח 1 שנייה, ובפער משמעותי מעל ה-baseline.")
    return "\n".join(lines)


def equal_split_baseline(segments: list, audio_dur: float) -> list:
    """ה-baseline: חלוקת כל ההקלטה לפי אורך אותיות — גבולות תחילת-מקטע."""
    weights = [max(1, sum(len(w) for w in s["align_plain"])) for s in segments]
    total = sum(weights)
    starts, acc = [], 0
    for w in weights:
        starts.append(audio_dur * acc / total)
        acc += w
    return starts
