# -*- coding: utf-8 -*-
"""תמלול עברי עם חותמות-זמן למילה — faster-whisper עם מודל ivrit.ai.

רץ ב-Colab (GPU). שמות המודלים אינם מובטחים מהזיכרון (כלל PLAN.md) — לכן
רשימת מועמדים שנוסים לפי הסדר, והשם שנטען בפועל מודפס ומוחזר.

הפרמטרים הקריטיים נגד קריאה-בטעמים (חצי-שירה):
- condition_on_previous_text=False — ההגנה המרכזית מלולאות-הזיה במליסמות.
- vad_filter=True — מדלג על שתיקות ארוכות (סופי פסוקים).
התמלול משמש לעיגון טקסטואלי בלבד; הדיוק הסופי מגיע מהיישור הכפוי הממושכן.
"""

import gc

CANDIDATE_MODELS = [
    "ivrit-ai/whisper-large-v3-turbo-ct2",
    "ivrit-ai/whisper-large-v3-ct2",
    "ivrit-ai/faster-whisper-v2-d4",
]


def transcribe(wav_path: str, model_name: str = None, device: str = None,
               compute_type: str = "float16", beam_size: int = 5):
    """הקלטה (wav 16kHz) → (רשימת מילים, שם המודל שנטען).

    כל מילה: {"word","start","end","prob"} בשניות מתחילת הקובץ.
    """
    import torch
    from faster_whisper import WhisperModel

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        compute_type = "int8"

    candidates = [model_name] if model_name else CANDIDATE_MODELS
    model, loaded = None, None
    for name in candidates:
        try:
            print(f"    מנסה לטעון מודל תמלול: {name}…")
            model = WhisperModel(name, device=device,
                                 compute_type=compute_type)
            loaded = name
            break
        except Exception as e:
            print(f"    ⚠️ {name} לא נטען ({type(e).__name__}) — ממשיך למועמד הבא")
    if model is None:
        raise RuntimeError(
            "אף מודל תמלול לא נטען. בדוק חיבור ל-HuggingFace או ציין "
            "model_name ידנית.")
    print(f"    ✅ מודל תמלול: {loaded}")

    segments, _info = model.transcribe(
        wav_path, language="he", word_timestamps=True,
        condition_on_previous_text=False, vad_filter=True,
        beam_size=beam_size)

    words = []
    for seg in segments:
        for w in seg.words or []:
            token = w.word.strip()
            if token:
                words.append({"word": token, "start": float(w.start),
                              "end": float(w.end),
                              "prob": float(getattr(w, "probability", 1.0))})

    # פריקה מפורשת — MMS נטען מיד אחר-כך ו-T4 לא מכיל את שניהם בנוחות
    del model
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    print(f"    {len(words)} מילים תומללו; המודל נפרק מהזיכרון")
    return words, loaded
