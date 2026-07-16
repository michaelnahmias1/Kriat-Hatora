# -*- coding: utf-8 -*-
"""ניקוד ביטחון לכל מקטע כתובית + דוח איכות בעברית.

Python טהור. הביטחון משוקלל מארבעה אותות בלתי-תלויים:
ציון ה-CTC של מילות המקטע, קרבת עוגן ASR, הסכמת זמני ASR/CTC, והצמדת VAD.
מקטע שזמנו נולד מאינטרפולציה מוגבל ל-0.3 — שידוע שהוא הערכה בלבד.
"""

# משקולות האותות (סכומן 1)
_W_CTC, _W_ANCHOR, _W_ASR, _W_VAD = 0.35, 0.25, 0.2, 0.2

_ANCHOR_FAR = 50      # מילים; מעבר לזה אות-העוגן מתאפס
_ASR_AGREE = 0.5      # שניות; עד כאן הסכמה מלאה
_ASR_DISAGREE = 2.0   # שניות; מכאן אי-הסכמה מלאה
_CAP_INTERPOLATED = 0.3


def score_segment(info: dict) -> float:
    """info: ctc_score∈[0,1]|None, anchor_dist(מילים)|None, interpolated,
    asr_gap(שניות)|None, vad_snapped(bool)|None. מחזיר ביטחון ∈[0,1]."""
    ctc = info.get("ctc_score")
    ctc = 0.5 if ctc is None else max(0.0, min(1.0, ctc))

    dist = info.get("anchor_dist")
    anchor = 0.0 if dist is None else max(0.0, 1.0 - dist / _ANCHOR_FAR)

    gap = info.get("asr_gap")
    if gap is None:
        asr = 0.5
    elif gap <= _ASR_AGREE:
        asr = 1.0
    else:
        asr = max(0.0, 1.0 - (gap - _ASR_AGREE) / (_ASR_DISAGREE - _ASR_AGREE))

    snapped = info.get("vad_snapped")
    vad = 0.5 if snapped is None else (1.0 if snapped else 0.4)

    conf = _W_CTC * ctc + _W_ANCHOR * anchor + _W_ASR * asr + _W_VAD * vad
    if info.get("interpolated"):
        conf = min(conf, _CAP_INTERPOLATED)
    return round(conf, 3)


def score_segments(infos: list) -> list:
    return [score_segment(i) for i in infos]


def _reasons(info: dict) -> str:
    out = []
    if info.get("interpolated"):
        out.append("זמן משוער (יישור נכשל בחלון)")
    if info.get("anchor_dist") is None or info.get("anchor_dist", 0) >= _ANCHOR_FAR:
        out.append("אין עוגן ASR בקרבת מקום")
    gap = info.get("asr_gap")
    if gap is not None and gap > _ASR_DISAGREE:
        out.append(f"פער ASR/CTC ‏{gap:.1f} שניות")
    if info.get("vad_snapped") is False:
        out.append("הגבול באמצע דיבור (לא הוצמד לנשימה)")
    ctc = info.get("ctc_score")
    if ctc is not None and ctc < 0.2:
        out.append("ציון יישור נמוך")
    return "; ".join(out) or "—"


def format_report(segments: list, confidences: list, infos: list,
                  starts: list, threshold: float = 0.5) -> str:
    """דוח בעברית: אילו מקטעים כדאי לבדוק/לגרור ידנית ב-CapCut."""
    low = [i for i, c in enumerate(confidences) if c < threshold]
    lines = [
        "דוח איכות הסנכרון",
        "=" * 40,
        f"מקטעים: {len(segments)} | ביטחון חציוני: "
        f"{sorted(confidences)[len(confidences) // 2]:.2f} | "
        f"לבדיקה ידנית: {len(low)}",
        "",
    ]
    if not low:
        lines.append("כל המקטעים בביטחון סביר — ייבא ל-CapCut ובדוק בעין.")
    else:
        lines.append(f"מקטעים בביטחון נמוך (<{threshold}) — מומלץ לגרור ידנית:")
        for i in low:
            seg = segments[i]
            m, s = divmod(int(starts[i]), 60)
            lines.append(
                f"  [{m:02d}:{s:02d}] פסוק {seg.get('verse', '?')} | "
                f"ביטחון {confidences[i]:.2f} | {seg['display']}")
            lines.append(f"        סיבה: {_reasons(infos[i])}")
    return "\n".join(lines)
