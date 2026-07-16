# -*- coding: utf-8 -*-
"""חלונות יישור בין עוגנים: בנייה, הרצה עם retry, אינטרפולציה ותפירה.

Python טהור — פונקציית היישור עצמה מוזרקת (align_fn), ולכן כל הלוגיקה כאן
נבדקת offline עם stub (ראה tests/test_windows.py).

חלון = {"word_lo","word_hi","t_lo","t_hi","sim_left","sim_right"}.
חלונות שכנים חופפים במילת-העוגן המשותפת (word_hi של האחד = word_lo של הבא);
בתפירה זמן העוגן נלקח מהחלון השמאלי והעותק הימני נזרק — כך ארטיפקטים של
קצה-חלון ב-CTC לא מזהמים את התוצאה.
"""

_EPS = 0.02  # מרווח מונוטוניות מינימלי בין תחילות מילים (שניות)


# --- בניית חלונות -------------------------------------------------------------

def _window(word_lo, word_hi, t_lo, t_hi, sim_left, sim_right):
    return {"word_lo": word_lo, "word_hi": word_hi,
            "t_lo": t_lo, "t_hi": t_hi,
            "sim_left": sim_left, "sim_right": sim_right}


def merge_windows(w1: dict, w2: dict) -> dict:
    """מיזוג שני חלונות סמוכים (w1 משמאל ל-w2)."""
    return _window(w1["word_lo"], w2["word_hi"], w1["t_lo"], w2["t_hi"],
                   w1["sim_left"], w2["sim_right"])


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

    windows = []
    first, last = anchors[0], anchors[-1]
    if first["ref"] > 0:
        windows.append(_window(0, first["ref"],
                               0.0, min(audio_dur, first["end"] + pad),
                               None, first["sim"]))
    for a, b in zip(anchors, anchors[1:]):
        if b["ref"] <= a["ref"]:
            continue
        windows.append(_window(a["ref"], b["ref"],
                               max(0.0, a["start"] - pad),
                               min(audio_dur, b["end"] + pad),
                               a["sim"], b["sim"]))
    if last["ref"] < n_ref_words - 1 or not windows:
        windows.append(_window(last["ref"], n_ref_words - 1,
                               max(0.0, last["start"] - pad), audio_dur,
                               last["sim"], None))

    # מיזוג חלונות קצרים מדי
    merged = True
    while merged and len(windows) > 1:
        merged = False
        for i, w in enumerate(windows):
            if w["t_hi"] - w["t_lo"] >= min_dur:
                continue
            if i + 1 < len(windows):
                windows[i:i + 2] = [merge_windows(w, windows[i + 1])]
            else:
                windows[i - 1:i + 1] = [merge_windows(windows[i - 1], w)]
            merged = True
            break
    return windows


# --- אינטרפולציה משוקללת-אותיות (fallback) ------------------------------------

def interpolate_words(t_lo: float, t_hi: float, plain_words: list) -> list:
    """חלוקת [t_lo, t_hi] בין מילים באורך יחסי (אותיות) → [(start, end, 0.0)].

    זהו ה-fallback לחלון שהיישור נכשל בו — טוב מחלוקה שווה כי אורכי מילים
    בעברית נעים בין 2 ל-10 אותיות.
    """
    if not plain_words:
        return []
    weights = [max(1, len(w)) for w in plain_words]
    total = sum(weights)
    span = max(0.0, t_hi - t_lo)
    out, acc = [], 0
    for w in weights:
        start = t_lo + span * acc / total
        acc += w
        out.append((start, t_lo + span * acc / total, 0.0))
    return out


# --- הרצת חלונות עם retry -----------------------------------------------------

def _weaker_side(w: dict) -> str:
    """הצד שעוגנו חלש יותר — המועמד הראשון למיזוג כשהחלון נכשל."""
    sl = w["sim_left"] if w["sim_left"] is not None else -1.0
    sr = w["sim_right"] if w["sim_right"] is not None else -1.0
    return "left" if sl <= sr else "right"


def align_windows(windows: list, align_fn, plain_words: list) -> list:
    """מריץ align_fn על כל חלון; כשל → מיזוג עם שכן דרך העוגן החלש וניסיון
    נוסף; כשל שני → אינטרפולציה. מחזיר [{"window","spans","interpolated"}].

    align_fn(window) → [(start, end, score)] באורך המילים שבחלון, או None בכשל.
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
                if (prev is None or prev["interpolated"]
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
                if i + 1 >= len(windows) or results[i + 1] is None:
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
            out.append({"window": w,
                        "spans": interpolate_words(w["t_lo"], w["t_hi"], words),
                        "interpolated": True})
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
