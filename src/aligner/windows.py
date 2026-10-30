# -*- coding: utf-8 -*-
"""חלונות יישור בין עוגנים: בנייה, הרצה עם retry, אינטרפולציה ותפירה.

Python טהור — פונקציית היישור עצמה מוזרקת (align_fn), ולכן כל הלוגיקה כאן
נבדקת offline עם stub (ראה tests/test_windows.py).

חלון = {"word_lo","word_hi","t_lo","t_hi","sim_left","sim_right"}.
חלונות שכנים חופפים במילת-העוגן המשותפת (word_hi של האחד = word_lo של הבא);
בתפירה זמן העוגן נלקח מהחלון השמאלי והעותק הימני נזרק — כך ארטיפקטים של
קצה-חלון ב-CTC לא מזהמים את התוצאה.

עוגן עם חסם תחתון (‏"lower_bound", פרופיל שירה — anchors.apply_nontext_runs)
יוצר גבול קשיח: החלון שמשמאלו מסתיים במילה שלפניו ובתחילת הדיבור שאינו
בטקסט (‏run_start), והחלון שמימינו (‏"hard_left") מתחיל בדיוק בסוף הדיבור —
בלי ריפוד לאחור. כך מילת העוגן תמיד מהחלון הימני, ולא תתחיל לפני החסם.
חלונות לא ממוזגים מעל גבול קשיח (לא במיזוג הקצרים ולא ב-retry).
"""

_EPS = 0.02  # מרווח מונוטוניות מינימלי בין תחילות מילים (שניות)


# --- בניית חלונות -------------------------------------------------------------

def _window(word_lo, word_hi, t_lo, t_hi, sim_left, sim_right):
    return {"word_lo": word_lo, "word_hi": word_hi,
            "t_lo": t_lo, "t_hi": t_hi,
            "sim_left": sim_left, "sim_right": sim_right}


def merge_windows(w1: dict, w2: dict) -> dict:
    """מיזוג שני חלונות סמוכים (w1 משמאל ל-w2)."""
    merged = _window(w1["word_lo"], w2["word_hi"], w1["t_lo"], w2["t_hi"],
                     w1["sim_left"], w2["sim_right"])
    if w1.get("hard_left"):
        merged["hard_left"] = True
    return merged


def _lo_time(anchor: dict, pad: float) -> float:
    """תחילת חלון שנפתח בעוגן — בלי ריפוד לאחור אם לעוגן חסם תחתון."""
    if anchor.get("lower_bound"):
        return anchor["start"]
    return max(0.0, anchor["start"] - pad)


def _with_hard_left(window: dict, anchor: dict) -> dict:
    if anchor.get("lower_bound"):
        window["hard_left"] = True
    return window


def build_windows(anchors: list, n_ref_words: int, audio_dur: float,
                  min_dur: float = 8.0, pad: float = 0.5) -> list:
    """עוגנים → רשימת חלונות המכסה את כל המילים [0..n_ref_words-1].

    כל חלון תחום בזמן סביב העוגנים שלו (עם ריפוד), מילות העוגן בפנים.
    חלונות קצרים מ-min_dur ממוזגים לשכן (חלון זעיר = תקורה + ארטיפקטים).
    בלי עוגנים בכלל — חלון יחיד על כל ההקלטה (ההתנהגות הקיימת).
    """
    if n_ref_words <= 0:
        return []
    if not anchors:
        return [_window(0, n_ref_words - 1, 0.0, audio_dur, None, None)]

    def right_end(b):
        """(מילה אחרונה, סוף זמן) של חלון שנסגר בעוגן b."""
        if b.get("lower_bound"):  # עד המילה שלפניו ועד תחילת הדיבור
            return b["ref"] - 1, min(audio_dur, b["run_start"] + pad)
        return b["ref"], min(audio_dur, b["end"] + pad)

    windows = []
    first, last = anchors[0], anchors[-1]
    if first["ref"] > 0:
        hi_ref, t_hi = right_end(first)
        windows.append(_window(0, hi_ref, 0.0, t_hi, None, first["sim"]))
    for a, b in zip(anchors, anchors[1:]):
        if b["ref"] <= a["ref"]:
            continue
        hi_ref, t_hi = right_end(b)
        windows.append(_with_hard_left(
            _window(a["ref"], hi_ref, _lo_time(a, pad), t_hi,
                    a["sim"], b["sim"]), a))
    if (last["ref"] < n_ref_words - 1 or not windows
            or last.get("lower_bound")):
        windows.append(_with_hard_left(
            _window(last["ref"], n_ref_words - 1, _lo_time(last, pad),
                    audio_dur, last["sim"], None), last))

    # מיזוג חלונות קצרים מדי — לעולם לא מעל גבול קשיח (hard_left)
    merged = True
    while merged and len(windows) > 1:
        merged = False
        for i, w in enumerate(windows):
            if w["t_hi"] - w["t_lo"] >= min_dur:
                continue
            if i + 1 < len(windows) and not windows[i + 1].get("hard_left"):
                windows[i:i + 2] = [merge_windows(w, windows[i + 1])]
            elif i > 0 and not w.get("hard_left"):
                windows[i - 1:i + 1] = [merge_windows(windows[i - 1], w)]
            else:
                continue
            merged = True
            break
    return windows


# --- אינטרפולציה משוקללת-אותיות (fallback) ------------------------------------

def _free_intervals(t_lo: float, t_hi: float, exclude: list) -> list:
    """[t_lo, t_hi] פחות קטעי exclude → רשימת קטעים פנויים, לפי הסדר."""
    free = [(t_lo, t_hi)]
    for x0, x1 in sorted(exclude):
        nxt = []
        for a, b in free:
            if x1 <= a or x0 >= b:
                nxt.append((a, b))
                continue
            if x0 > a:
                nxt.append((a, x0))
            if x1 < b:
                nxt.append((x1, b))
        free = nxt
    return [(a, b) for a, b in free if b > a]


def interpolate_words(t_lo: float, t_hi: float, plain_words: list,
                      exclude: list = None) -> list:
    """חלוקת [t_lo, t_hi] בין מילים באורך יחסי (אותיות) → [(start, end, 0.0)].

    זהו ה-fallback לחלון שהיישור נכשל בו — טוב מחלוקה שווה כי אורכי מילים
    בעברית נעים בין 2 ל-10 אותיות. ‏exclude — קטעי זמן שאין בהם טקסט (דיבור
    שאינו בטקסט, פרופיל שירה): המילים מחולקות רק על הזמן הפנוי.
    """
    if not plain_words:
        return []
    weights = [max(1, len(w)) for w in plain_words]
    total = sum(weights)
    free = _free_intervals(t_lo, t_hi, exclude) if exclude else None
    if not free:
        span = max(0.0, t_hi - t_lo)
        out, acc = [], 0
        for w in weights:
            start = t_lo + span * acc / total
            acc += w
            out.append((start, t_lo + span * acc / total, 0.0))
        return out
    free_total = sum(b - a for a, b in free)

    def at(frac, is_end):
        """נקודה בשבר frac של הזמן הפנוי → זמן אמיתי. נקודה שנופלת בדיוק
        על גבול קטע מוחרג: סוף מילה — לפניו; תחילת מילה — אחריו."""
        left = frac * free_total
        for a, b in free:
            span = b - a
            if left < span - 1e-9 or (is_end and left <= span + 1e-9):
                return a + left
            left -= span
        return free[-1][1]

    out, acc = [], 0
    for w in weights:
        start = at(acc / total, False)
        acc += w
        out.append((start, at(acc / total, True), 0.0))
    return out


# --- הרצת חלונות עם retry -----------------------------------------------------

def _weaker_side(w: dict) -> str:
    """הצד שעוגנו חלש יותר — המועמד הראשון למיזוג כשהחלון נכשל."""
    sl = w["sim_left"] if w["sim_left"] is not None else -1.0
    sr = w["sim_right"] if w["sim_right"] is not None else -1.0
    return "left" if sl <= sr else "right"


def align_windows(windows: list, align_fn, plain_words: list,
                  exclude: list = None) -> list:
    """מריץ align_fn על כל חלון; כשל → מיזוג עם שכן דרך העוגן החלש וניסיון
    נוסף; כשל שני → אינטרפולציה. מחזיר [{"window","spans","interpolated"}].

    align_fn(window) → [(start, end, score)] באורך המילים שבחלון, או None בכשל.
    לא ממזגים מעל גבול קשיח (hard_left). ‏exclude — קטעי זמן שהאינטרפולציה
    מדלגת עליהם (ראה interpolate_words).
    """
    results = [align_fn(w) for w in windows]
    out, i = [], 0
    while i < len(windows):
        w, r = windows[i], results[i]
        if r is not None:
            out.append({"window": w, "spans": r, "interpolated": False})
            i += 1
            continue

        sides = (["left", "right"] if _weaker_side(w) == "left"
                 else ["right", "left"])
        handled = False
        for side in sides:
            if side == "left":
                prev = out[-1] if out else None
                if (prev is None or prev["interpolated"] or w.get("hard_left")
                        or prev["window"]["word_hi"] != w["word_lo"]):
                    continue
                merged = merge_windows(prev["window"], w)
                mr = align_fn(merged)
                if mr is not None:
                    out[-1] = {"window": merged, "spans": mr,
                               "interpolated": False}
                    i += 1
                    handled = True
                    break
            else:
                if (i + 1 >= len(windows) or results[i + 1] is None
                        or windows[i + 1].get("hard_left")):
                    continue
                merged = merge_windows(w, windows[i + 1])
                mr = align_fn(merged)
                if mr is not None:
                    out.append({"window": merged, "spans": mr,
                                "interpolated": False})
                    i += 2
                    handled = True
                    break
        if not handled:
            words = plain_words[w["word_lo"]:w["word_hi"] + 1]
            spans = (interpolate_words(w["t_lo"], w["t_hi"], words, exclude)
                     if exclude else
                     interpolate_words(w["t_lo"], w["t_hi"], words))
            out.append({"window": w, "spans": spans, "interpolated": True})
            i += 1
    return out


# --- תפירה --------------------------------------------------------------------

def stitch(aligned: list, n_ref_words: int):
    """מחבר את תוצאות החלונות לרצף גלובלי אחד של זמני-מילים.

    מחזיר (spans, interpolated_flags) — לכל מילה (start, end, score) ודגל האם
    זמנה נולד מאינטרפולציה. אוכף מונוטוניות ואת אינווריאנט ספירת המילים.
    """
    spans, flags = [], []
    next_word = 0
    for item in aligned:
        w = item["window"]
        skip = next_word - w["word_lo"]
        if skip < 0:
            raise RuntimeError(
                f"חור בכיסוי החלונות: מילה {next_word} מול חלון {w['word_lo']}")
        for span in item["spans"][skip:]:
            spans.append(span)
            flags.append(item["interpolated"])
        next_word = w["word_hi"] + 1
    if len(spans) != n_ref_words:
        raise RuntimeError(
            f"אי-התאמה בתפירה: {len(spans)} זמני-מילים מול {n_ref_words} מילים")

    # אכיפת מונוטוניות
    fixed = []
    prev_start = None
    for start, end, score in spans:
        if prev_start is not None and start < prev_start + _EPS:
            start = prev_start + _EPS
        end = max(end, start)
        fixed.append((start, end, score))
        prev_start = start
    return fixed, flags
