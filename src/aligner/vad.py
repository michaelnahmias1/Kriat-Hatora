# -*- coding: utf-8 -*-
"""זיהוי דיבור/שקט (VAD) והצמדת גבולות כתוביות לתחילות-דיבור.

detect_speech דורש את חבילת silero-vad (רץ ב-Colab); snap_boundaries הוא
Python טהור ונבדק offline. הידע הפרוזודי: קורא בתורה כמעט תמיד נושם בסוף
פסוק — לכן גבול-פסוק מקבל רדיוס הצמדה גדול יותר וקדימות.
"""

from bisect import bisect_left

_EPS = 0.02  # מרווח מונוטוניות מינימלי בין תחילות מקטעים (שניות)


def detect_speech(wav_path: str, sample_rate: int = 16000) -> list:
    """הקלטה → [(start_sec, end_sec)] של קטעי דיבור (silero-vad).

    יבוא עצל: מנסה את חבילת pip‏ silero-vad, ואם אין — torch.hub.
    שמות ה-API מאומתים בפועל ב-Colab (לא מניחים מהזיכרון — PLAN.md).
    """
    try:
        from silero_vad import (get_speech_timestamps, load_silero_vad,
                                read_audio)
        model = load_silero_vad()
        audio = read_audio(wav_path, sampling_rate=sample_rate)
        stamps = get_speech_timestamps(audio, model,
                                       sampling_rate=sample_rate)
    except ImportError:
        import torch
        model, utils = torch.hub.load("snakers4/silero-vad", "silero_vad",
                                      trust_repo=True)
        get_speech_timestamps, _, read_audio = utils[0], utils[1], utils[2]
        audio = read_audio(wav_path, sampling_rate=sample_rate)
        stamps = get_speech_timestamps(audio, model,
                                       sampling_rate=sample_rate)
    return [(s["start"] / sample_rate, s["end"] / sample_rate)
            for s in stamps]


def snap_boundaries(starts: list, speech_regions: list, verse_flags: list,
                    radius: float = 0.35, verse_radius: float = 0.7):
    """מצמיד תחילות-מקטעים לתחילת-דיבור קרובה (= סוף שקט).

    starts — תחילות המקטעים; verse_flags — האם המקטע פותח פסוק (רדיוס גדול,
    מוצמד ראשון); speech_regions — פלט detect_speech.
    מחזיר (starts מעודכן, snap_dists) כאשר snap_dists[i] הוא המרחק שהוצמד
    או None אם לא הוצמד (מזין את ניקוד הביטחון).
    """
    onsets = sorted(s for s, _ in speech_regions)
    new = list(starts)
    dists = [None] * len(starts)
    if not onsets:
        return new, dists

    order = sorted(range(len(starts)),
                   key=lambda i: (not verse_flags[i], i))
    for i in order:
        r = verse_radius if verse_flags[i] else radius
        t = starts[i]
        k = bisect_left(onsets, t)
        best = None
        for cand in (onsets[k - 1] if k > 0 else None,
                     onsets[k] if k < len(onsets) else None):
            if cand is not None and abs(cand - t) <= r:
                if best is None or abs(cand - t) < abs(best - t):
                    best = cand
        if best is not None:
            new[i] = best
            dists[i] = best - t

    # אכיפת מונוטוניות אחרי ההצמדות
    for i in range(1, len(new)):
        if new[i] < new[i - 1] + _EPS:
            new[i] = new[i - 1] + _EPS
            dists[i] = None
    return new, dists
