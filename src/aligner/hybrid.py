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
from . import profiles as profiles_mod
from . import vad as vad_mod
from . import windows as win_mod
from .pipeline import (WAV16K_NAME, MmsAligner, build_ref, build_srt,
                       fetch_verses, find_mam_version, load_audio_16k_mono,
                       romanize_words, segment_bounds, to_english,
                       units_to_segments, verse_units)

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


def _unit_of(seg: dict):
    """יחידת הטקסט של המקטע — unit במסלול היחידות, verse במקטעים הישנים."""
    return seg["unit"] if "unit" in seg else seg.get("verse")


def _unit_start_flags(segments: list) -> list:
    """האם המקטע פותח יחידה חדשה — פסוק/שורה/בית (שם הקורא כמעט תמיד נושם)."""
    flags, prev = [], None
    for seg in segments:
        flags.append(_unit_of(seg) != prev)
        prev = _unit_of(seg)
    return flags


_verse_start_flags = _unit_start_flags  # תאימות לאחור (השם מלפני היחידות)


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


def _debug_put(debug, **values):
    """וו דיבאג: כשנמסר מילון — מעדכן אותו ומחזיר אותו; None ⇒ לא כלום."""
    if debug is not None:
        debug.update(values)
    return debug


# --- הפונקציות הראשיות ---------------------------------------------------------

def run_hybrid(book, chapter, audio_path, out_srt_path,
               verse_start=None, chapter_end=None, verse_end=None,
               max_words=4, asr_model=None, work_dir=".", splits=None):
    """הצינור ההיברידי המלא לתנ״ך. מדפיס התקדמות בעברית ומחזיר את נתיב ה-SRT.

    לצד ה-SRT נכתב דוח איכות (<שם>.report.txt) שמפרט אילו מקטעים
    כדאי לגרור ידנית ב-CapCut. מושך את הפסוקים, בונה מהם יחידות
    verse/taamim, ומכאן — אותו צינור יחידות של run_hybrid_units.
    """
    book = to_english(book)
    print(f"1/8 מאתר את גרסת MAM עבור {book}…")
    version = find_mam_version(book)
    ref = build_ref(book, chapter, verse_start, chapter_end, verse_end)
    print(f"    גרסה: «{version}» | טווח: {ref}")

    print("2/8 מושך את הטקסט וחותך לפי טעמים…")
    verses = fetch_verses(ref, version)
    return _run_units(verse_units(verses), audio_path, out_srt_path,
                      max_words=max_words, splits=splits, mode="tanakh",
                      work_dir=work_dir, asr_model=asr_model)


def run_hybrid_units(units, audio_path, out_srt_path, *, max_words=4,
                     splits=None, performance=None, profile="reading",
                     mode="tanakh", work_dir=".", asr_model=None,
                     debug=None):
    """הצינור ההיברידי על יחידות טקסט (PLAN_TEFILA.md סעיף 3.1).

    ‏units — רשימת {text, label, kind, chunk}; יחידות instruction לא
    נכנסות לכתוביות וליישור. מחזיר את נתיב ה-SRT ומשאיר לצדו דוח איכות.
    ‏performance (סדר ביצוע — חזרות/דילוגים) — משימה 4.3, עוד לא נתמך.
    ‏profile — "reading" (ברירת המחדל, ההתנהגות הקיימת) או "singing"
    (חזנות/שירה; ערכיו ב-profiles.py). שירה נתמכת רק ב-mode="tefila" —
    לתנ״ך אין פרופיל שירה.
    ‏debug — מילון אופציונלי (ברירת מחדל None = בלי שום שינוי): כשנמסר,
    הצינור ממלא בו את תוצאות הביניים — תמלול, עוגנים, חלונות וסטטוס כל
    ניסיון יישור, זמני מילים, VAD וביטחון (ראה tools/run_local.py).
    """
    if performance is not None:
        raise NotImplementedError(
            "תסריט ביצוע (performance) עוד לא נתמך — משימה 4.3")
    prof = profiles_mod.get_profile(profile)
    if prof.name != "reading" and mode != "tefila":
        raise NotImplementedError(
            f"פרופיל {profile!r} נתמך רק בתפילה ובטקסט חופשי (mode=\"tefila\")")
    print("2/8 חותך את הטקסט למקטעים…")
    return _run_units(units, audio_path, out_srt_path, max_words=max_words,
                      splits=splits, mode=mode, work_dir=work_dir,
                      asr_model=asr_model, debug=debug, prof=prof)


def _fmt_clock(sec: float) -> str:
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m):02d}:{s:04.1f}"


def _nontext_line(run: dict) -> str:
    """שורת דוח/יומן לדיבור שאינו בטקסט שזוהה."""
    words = run["text"].split()
    text = " ".join(words[:12]) + (" …" if len(words) > 12 else "")
    return (f"זוהה דיבור שאינו בטקסט {_fmt_clock(run['start'])}–"
            f"{_fmt_clock(run['end'])}: «{text}»")


def _unit_start_words(segments: list) -> list:
    """אינדקסי המילים (השטוחים) שפותחות יחידה — שורה/פסוק/בית."""
    out, wi = [], 0
    for seg, flag in zip(segments, _unit_start_flags(segments)):
        if flag:
            out.append(wi)
        wi += len(seg["align_vocalized"])
    return out


def _run_units(units, audio_path, out_srt_path, *, max_words, splits, mode,
               work_dir, asr_model, debug=None, prof=None):
    """גוף הצינור מהחיתוך והלאה — משותף לתנ״ך וליחידות.

    כותרת שלב 2 מודפסת אצל הקורא, כדי שיומן התנ״ך יישאר כפי שהיה.
    ‏prof — פרופיל הביצוע (profiles.py); None = קריאה. בקריאה כל הקריאות
    וההדפסות זהות להתנהגות שלפני הפרופילים (בדיקת הזהב).
    """
    if prof is None:
        prof = profiles_mod.PROFILES["reading"]
    segments = units_to_segments(units, max_words, splits, mode)
    if splits:
        print("    חלוקת הכתוביות נלקחה מהעריכה הידנית בממשק")
    flat_vocalized = [w for s in segments for w in s["align_vocalized"]]
    flat_plain = [w for s in segments for w in s["align_plain"]]
    n_units = sum(1 for u in units if u.get("kind") != "instruction")
    noun = ("פסוקים" if all(u.get("kind") == "verse" for u in units)
            else "יחידות")
    print(f"    {n_units} {noun} → {len(segments)} מקטעים "
          f"({len(flat_plain)} מילים)")

    _debug_put(debug, segments=segments, flat_plain=flat_plain,
               flat_vocalized=flat_vocalized)

    print("3/8 טוען וממיר את ההקלטה (16kHz מונו)…")
    waveform = load_audio_16k_mono(audio_path, work_dir)
    wav_path = str(Path(work_dir) / WAV16K_NAME)
    audio_dur = waveform.size(1) / _SAMPLE_RATE
    print(f"    משך: {audio_dur / 60:.1f} דקות")

    print("4/8 תמלול עברי (עוגנים בלבד — לא התזמון הסופי)…")
    if prof.asr_vad_filter:
        asr_words, asr_name = asr_mod.transcribe(wav_path,
                                                 model_name=asr_model)
    else:
        print(f"    פרופיל {prof.label}: תמלול בלי סינון VAD (שירה אינה 'דיבור')")
        asr_words, asr_name = asr_mod.transcribe(wav_path,
                                                 model_name=asr_model,
                                                 vad_filter=False)
    _debug_put(debug, audio_dur=audio_dur, asr_words=asr_words,
               asr_name=asr_name, profile=prof.name)

    print("5/8 הצלבת התמלול עם טקסט Sefaria — איתור עוגנים…")
    unit_starts = _unit_start_words(segments)
    if prof.name == "reading":
        found = anchors_mod.find_anchors(asr_words, flat_plain)
    else:
        extra = {"recruit_context": True} if prof.recruit_context else {}
        found = anchors_mod.find_anchors(
            asr_words, flat_plain,
            nontext=(prof.nontext.detect_kwargs() if prof.nontext else None),
            **extra)
    anchor_list, coverage = found["anchors"], found["coverage"]
    runs = found.get("nontext_runs") or []
    if runs:
        anchor_list = anchors_mod.apply_nontext_runs(
            anchor_list, runs, unit_starts, len(flat_plain), audio_dur,
            **prof.nontext.apply_kwargs())
        for run in runs:
            line = _nontext_line(run)
            if run.get("pseudo_ref") is not None:
                line += f" ⇐ «{flat_plain[run['pseudo_ref']]}» מתחילה אחריו"
            print("    " + line)
    exclude = [(r["start"], r["end"]) for r in runs]
    bounds = {a["ref"]: a["start"] for a in anchor_list
              if a.get("lower_bound")}
    _debug_put(debug, anchors=anchor_list, coverage=coverage,
               matches=found["matches"], nontext_runs=runs)
    print(f"    כיסוי התאמה: {coverage:.0%} | עוגנים: {len(anchor_list)}")
    if coverage < 0.4:
        print("    ⚠️ כיסוי נמוך — התמלול מתקשה בקריאה הזו. ממשיכים עם "
              "חלונות גדולים; בדוק את הדוח בסוף.")

    print("6/8 יישור מאולץ ממושכן (MMS על כל חלון בין עוגנים)…")
    window_list = win_mod.build_windows(anchor_list, len(flat_plain), audio_dur)
    print(f"    {len(window_list)} חלונות")
    aligner = MmsAligner(with_star=True) if prof.star else MmsAligner()
    unit_start_set = set(unit_starts)
    max_word_sec = prof.max_word_sec
    attempts = _debug_put(debug, windows=window_list, window_attempts=[])

    def note(w, status, spans=None):
        if attempts is not None:
            attempts["window_attempts"].append(
                {"window": dict(w), "status": status, "spans": spans})

    def align_fn(w):
        words = flat_vocalized[w["word_lo"]:w["word_hi"] + 1]
        roman = romanize_words(words)
        s0 = int(w["t_lo"] * _SAMPLE_RATE)
        s1 = int(w["t_hi"] * _SAMPLE_RATE)
        piece = waveform[:, s0:s1]
        n_tokens = sum(len(r) for r in roman)
        stars = None
        if prof.star:  # "*" בתחילת החלון, לפני כל תחילת יחידה, ובסוף
            stars = [k == 0 or w["word_lo"] + k in unit_start_set
                     for k in range(len(roman))] + [True]
            n_tokens += sum(stars)
        if piece.size(1) / _FRAME_STRIDE < n_tokens * 1.1 + 4:
            note(w, "too_few_frames")
            return None  # פחות פריימים מטוקנים — העוגן כנראה שגוי
        try:
            if stars is None:
                spans = aligner.align(piece, roman, offset_sec=w["t_lo"])
            else:
                spans = aligner.align(piece, roman, offset_sec=w["t_lo"],
                                      stars=stars)
        except Exception as e:
            print(f"    ⚠️ חלון מילים {w['word_lo']}–{w['word_hi']} נכשל "
                  f"({type(e).__name__}) — מנסה מיזוג/אינטרפולציה")
            note(w, f"error:{type(e).__name__}")
            return None
        limit = _MAX_WORD_SEC if max_word_sec is None else max_word_sec
        if any(e - s > limit for s, e, _ in spans):
            note(w, "word_too_long", spans)
            return None  # מילה של 12+ שניות = היישור התפרק בחלון
        gap = prof.max_start_gap_sec
        if gap is not None and any(b[0] - a[0] > gap
                                   for a, b in zip(spans, spans[1:])):
            note(w, "start_gap_too_long", spans)
            return None  # CTC דחס מילים ו"השאיר" מליסמה ארוכה בלי מילה
        note(w, "ok", spans)
        return spans

    if exclude:
        aligned = win_mod.align_windows(window_list, align_fn, flat_plain,
                                        exclude=exclude)
    else:
        aligned = win_mod.align_windows(window_list, align_fn, flat_plain)
    spans, interp_flags = win_mod.stitch(aligned, len(flat_plain))
    _debug_put(debug, aligned=aligned, word_spans=spans,
               interpolated=interp_flags)
    n_interp = sum(interp_flags)
    if n_interp:
        print(f"    {n_interp} מילים קיבלו זמן משוער (אינטרפולציה) — יסומנו בדוח")

    print("7/8 הצמדת גבולות לנשימות (VAD)…")
    word_spans = [(s, e) for s, e, _ in spans]
    starts, _ends = segment_bounds(segments, word_spans)
    unit_flags = _unit_start_flags(segments)
    _debug_put(debug, starts_raw=list(starts), unit_flags=unit_flags)
    vad_ran = True
    try:
        speech = vad_mod.detect_speech(wav_path)
        _debug_put(debug, speech=speech)
        fraction = (sum(e - s for s, e in speech) / audio_dur
                    if audio_dur else 0.0)
        if fraction < prof.vad_snap_min_speech:
            vad_ran = False
            snap_dists = [None] * len(starts)
            print(f"    VAD זיהה רק {fraction:.0%} מההקלטה כדיבור (שירה) — "
                  "בלי הצמדה")
        else:
            starts, snap_dists = vad_mod.snap_boundaries(starts, speech,
                                                         unit_flags)
            print(f"    הוצמדו {sum(1 for d in snap_dists if d is not None)}"
                  f"/{len(starts)} גבולות")
    except Exception as e:
        vad_ran = False
        snap_dists = [None] * len(starts)
        print(f"    ⚠️ VAD לא רץ ({type(e).__name__}) — ממשיכים בלי הצמדה")
    if bounds:  # חסם תחתון (דיבור שאינו בטקסט) גובר גם על ההצמדה
        for i, (lo, _hi) in enumerate(_segment_word_ranges(segments)):
            if lo in bounds and starts[i] < bounds[lo]:
                starts[i] = bounds[lo]
                snap_dists[i] = None

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
    _debug_put(debug, starts=starts, snap_dists=snap_dists, vad_ran=vad_ran,
               infos=infos, confidences=confs)

    if exclude:
        srt = build_srt(segments, word_spans, starts_override=starts,
                        gaps=exclude)
    else:
        srt = build_srt(segments, word_spans, starts_override=starts)
    Path(out_srt_path).write_text(srt, encoding="utf-8-sig")
    report = conf_mod.format_report(segments, confs, infos, starts)
    report_path = str(Path(out_srt_path).with_suffix(".report.txt"))
    header = (f"מודל תמלול: {asr_name} | כיסוי: {coverage:.0%} | "
              f"עוגנים: {len(anchor_list)} | חלונות: {len(window_list)}")
    if prof.name != "reading":
        header += f" | פרופיל: {prof.label}"
        header += "".join("\n" + _nontext_line(r) for r in runs)
    Path(report_path).write_text(header + "\n\n" + report, encoding="utf-8")
    print(f"✅ נוצר: {out_srt_path}")
    print(f"📋 דוח איכות: {report_path}")
    return out_srt_path
