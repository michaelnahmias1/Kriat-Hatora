# -*- coding: utf-8 -*-
"""הפייפליין ההיברידי: תמלול (עוגנים) → יישור כפוי ממושכן → VAD → SRT + דוח.

זהו מסלול ברירת-המחדל של worker.ipynb. הרעיון (PLAN.md, עדכון v6):
כל שכבה מפצה על חולשת קודמתה —
1. Whisper עברי (ivrit.ai) חסין לסחיפה אבל זמניו גסים → משמש רק לעיגון.
2. יישור CTC ‏(MMS_FA) מדויק אבל סוחף על מליסמות → רץ על חלונות קצרים
   בין עוגנים, כך שסחיפה חסומה לחלון ואין מגבלת אורך הקלטה.
3. ‏VAD יודע שסוף פסוק = נשימה אמיתית → מצמיד גבולות לתחילות-דיבור.
4. חלון שנכשל → אינטרפולציה משוקללת-אותיות + דגל בדוח (המשתמש גורר ידנית).

הטקסט המוצג ב-SRT נשאר תמיד display מה-chunker — טקסט Sefaria המדויק,
מנוקד ומוטעם; כל ההחלפות (קרי, רומניזציה) חיות רק בעותקי היישור.
"""

from pathlib import Path

from . import anchors as anchors_mod
from . import asr as asr_mod
from . import confidence as conf_mod
from . import vad as vad_mod
from . import windows as win_mod
from .pipeline import (TORAH_BOOKS, WAV16K_NAME, MmsAligner, build_ref,
                       build_srt, fetch_verses, find_mam_version,
                       load_audio_16k_mono, romanize_words, segment_bounds,
                       verses_to_segments)

_SAMPLE_RATE = 16000
_FRAME_STRIDE = 320    # MMS: פריים כל 20ms ב-16kHz
_MAX_WORD_SEC = 12.0   # מילה "מיושרת" ארוכה מזה = החלון חשוד ככושל


# --- עזרי-מקטעים טהורים (נבדקים offline) --------------------------------------

def _segment_word_ranges(segments: list) -> list:
    """לכל מקטע — (מילה ראשונה, מילה אחרונה) באינדקס הגלובלי השטוח."""
    ranges, wi = [], 0
    for seg in segments:
        n = len(seg["align_vocalized"])
        ranges.append((wi, wi + n - 1))
        wi += n
    return ranges


def _verse_start_flags(segments: list) -> list:
    """האם המקטע פותח פסוק חדש (שם הקורא כמעט תמיד נושם)."""
    flags, prev = [], None
    for seg in segments:
        flags.append(seg.get("verse") != prev)
        prev = seg.get("verse")
    return flags


def _anchor_dists(word_ranges: list, anchor_refs: list) -> list:
    """מרחק (במילים) מכל מקטע לעוגן הקרוב ביותר; None אם אין עוגנים."""
    if not anchor_refs:
        return [None] * len(word_ranges)
    refs = sorted(anchor_refs)
    out = []
    for lo, hi in word_ranges:
        out.append(min(0 if lo <= r <= hi else min(abs(r - lo), abs(r - hi))
                       for r in refs))
    return out


def _asr_gaps(word_ranges: list, matches: list, word_starts: list) -> list:
    """פער חציוני |זמן ASR − זמן CTC| למילים המוצלבות של כל מקטע."""
    by_ref = {m["ref"]: m["asr_start"] for m in matches}
    out = []
    for lo, hi in word_ranges:
        gaps = sorted(abs(by_ref[r] - word_starts[r])
                      for r in range(lo, hi + 1) if r in by_ref)
        out.append(gaps[len(gaps) // 2] if gaps else None)
    return out


def _segment_ctc_scores(word_ranges: list, spans: list) -> list:
    """ציון ה-CTC הממוצע של מילות כל מקטע."""
    return [sum(spans[r][2] for r in range(lo, hi + 1)) / (hi - lo + 1)
            for lo, hi in word_ranges]


def _segment_interpolated(word_ranges: list, flags: list) -> list:
    """האם זמן של מילה כלשהי במקטע נולד מאינטרפולציה."""
    return [any(flags[lo:hi + 1]) for lo, hi in word_ranges]


# --- הפונקציה הראשית -----------------------------------------------------------

def run_hybrid(book, chapter, audio_path, out_srt_path,
               verse_start=None, chapter_end=None, verse_end=None,
               max_words=4, asr_model=None, work_dir="."):
    """הצינור ההיברידי המלא. מדפיס התקדמות בעברית ומחזיר את נתיב ה-SRT.

    לצד ה-SRT נכתב דוח איכות (<שם>.report.txt) שמפרט אילו מקטעים
    כדאי לגרור ידנית ב-CapCut.
    """
    book = TORAH_BOOKS.get(book, book)
    print(f"1/8 מאתר את גרסת MAM עבור {book}…")
    version = find_mam_version(book)
    ref = build_ref(book, chapter, verse_start, chapter_end, verse_end)
    print(f"    גרסה: «{version}» | טווח: {ref}")

    print("2/8 מושך את הטקסט וחותך לפי טעמים…")
    verses = fetch_verses(ref, version)
    segments = verses_to_segments(verses, max_words)
    flat_vocalized = [w for s in segments for w in s["align_vocalized"]]
    flat_plain = [w for s in segments for w in s["align_plain"]]
    print(f"    {len(verses)} פסוקים → {len(segments)} מקטעים "
          f"({len(flat_plain)} מילים)")

    print("3/8 טוען וממיר את ההקלטה (16kHz מונו)…")
    waveform = load_audio_16k_mono(audio_path, work_dir)
    wav_path = str(Path(work_dir) / WAV16K_NAME)
    audio_dur = waveform.size(1) / _SAMPLE_RATE
    print(f"    משך: {audio_dur / 60:.1f} דקות")

    print("4/8 תמלול עברי (עוגנים בלבד — לא התזמון הסופי)…")
    asr_words, asr_name = asr_mod.transcribe(wav_path, model_name=asr_model)

    print("5/8 הצלבת התמלול עם טקסט Sefaria — איתור עוגנים…")
    found = anchors_mod.find_anchors(asr_words, flat_plain)
    anchor_list, coverage = found["anchors"], found["coverage"]
    print(f"    כיסוי התאמה: {coverage:.0%} | עוגנים: {len(anchor_list)}")
    if coverage < 0.4:
        print("    ⚠️ כיסוי נמוך — התמלול מתקשה בקריאה הזו. ממשיכים עם "
              "חלונות גדולים; בדוק את הדוח בסוף.")

    print("6/8 יישור מאולץ ממושכן (MMS על כל חלון בין עוגנים)…")
    window_list = win_mod.build_windows(anchor_list, len(flat_plain), audio_dur)
    print(f"    {len(window_list)} חלונות")
    aligner = MmsAligner()

    def align_fn(w):
        words = flat_vocalized[w["word_lo"]:w["word_hi"] + 1]
        roman = romanize_words(words)
        s0 = int(w["t_lo"] * _SAMPLE_RATE)
        s1 = int(w["t_hi"] * _SAMPLE_RATE)
        piece = waveform[:, s0:s1]
        n_tokens = sum(len(r) for r in roman)
        if piece.size(1) / _FRAME_STRIDE < n_tokens * 1.1 + 4:
            return None  # פחות פריימים מטוקנים — העוגן כנראה שגוי
        try:
            spans = aligner.align(piece, roman, offset_sec=w["t_lo"])
        except Exception as e:
            print(f"    ⚠️ חלון מילים {w['word_lo']}–{w['word_hi']} נכשל "
                  f"({type(e).__name__}) — מנסה מיזוג/אינטרפולציה")
            return None
        if any(e - s > _MAX_WORD_SEC for s, e, _ in spans):
            return None  # מילה של 12+ שניות = היישור התפרק בחלון
        return spans

    aligned = win_mod.align_windows(window_list, align_fn, flat_plain)
    spans, interp_flags = win_mod.stitch(aligned, len(flat_plain))
    n_interp = sum(interp_flags)
    if n_interp:
        print(f"    {n_interp} מילים קיבלו זמן משוער (אינטרפולציה) — יסומנו בדוח")

    print("7/8 הצמדת גבולות לנשימות (VAD)…")
    word_spans = [(s, e) for s, e, _ in spans]
    starts, _ends = segment_bounds(segments, word_spans)
    verse_flags = _verse_start_flags(segments)
    vad_ran = True
    try:
        speech = vad_mod.detect_speech(wav_path)
        starts, snap_dists = vad_mod.snap_boundaries(starts, speech,
                                                     verse_flags)
        print(f"    הוצמדו {sum(1 for d in snap_dists if d is not None)}"
              f"/{len(starts)} גבולות")
    except Exception as e:
        vad_ran = False
        snap_dists = [None] * len(starts)
        print(f"    ⚠️ VAD לא רץ ({type(e).__name__}) — ממשיכים בלי הצמדה")

    print("8/8 ניקוד ביטחון, SRT ודוח…")
    word_ranges = _segment_word_ranges(segments)
    word_starts = [s for s, _, _ in spans]
    ctc_scores = _segment_ctc_scores(word_ranges, spans)
    anchor_dists = _anchor_dists(word_ranges, [a["ref"] for a in anchor_list])
    interp_segs = _segment_interpolated(word_ranges, interp_flags)
    asr_gaps = _asr_gaps(word_ranges, found["matches"], word_starts)
    infos = [{
        "ctc_score": ctc_scores[i],
        "anchor_dist": anchor_dists[i],
        "interpolated": interp_segs[i],
        "asr_gap": asr_gaps[i],
        "vad_snapped": (snap_dists[i] is not None) if vad_ran else None,
    } for i in range(len(segments))]
    confs = conf_mod.score_segments(infos)

    srt = build_srt(segments, word_spans, starts_override=starts)
    Path(out_srt_path).write_text(srt, encoding="utf-8-sig")
    report = conf_mod.format_report(segments, confs, infos, starts)
    report_path = str(Path(out_srt_path).with_suffix(".report.txt"))
    Path(report_path).write_text(
        f"מודל תמלול: {asr_name} | כיסוי: {coverage:.0%} | "
        f"עוגנים: {len(anchor_list)} | חלונות: {len(window_list)}\n\n" + report,
        encoding="utf-8")
    print(f"✅ נוצר: {out_srt_path}")
    print(f"📋 דוח איכות: {report_path}")
    return out_srt_path
