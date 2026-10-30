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

from collections import Counter
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

# סדר ביצוע (PLAN_TEFILA.md 3.2, ‏4.3.2) — תקרות כמו ב-modal_worker/params.py:
# אורך הרשימה כמו MAX_PERFORMANCE; מילות היישור ברצף הפרוס — ה-worker בודק
# מראש עד 20000 מילים פרוזודיות (MAX_SPLIT_WORDS), ושרשראות מקף נפתחות כאן
# לכמה מילות יישור, ולכן התקרה כאן מעט גבוהה יותר.
MAX_PERFORMANCE = 20000
MAX_PERFORMED_WORDS = 30000

# ‏4.3.4 (הצעה בלבד, תפילה בלבד): יחידה (הופעה של שורה/בית) שיש בה לפחות כך
# מילים ואף אחת מהן לא זוהתה בתמלול בדמיון ≥ ‏_SKIP_MATCH_SIM ⇐ "כנראה דולגה"
# בדוח. בלי שום שינוי אוטומטי — המשתמש מחליט (ומסיר אותה מסדר הביצוע).
_SKIP_MIN_WORDS = 6
_SKIP_MATCH_SIM = 0.7


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
    """האם המקטע פותח יחידה חדשה — פסוק/שורה/בית (שם הקורא כמעט תמיד נושם).

    ברצף פרוס לפי סדר ביצוע (‏seg_index, ראה expand_performance) גם כל קפיצה
    — חזרה אחורה או דילוג — פותחת "הופעה" חדשה, גם בתוך אותה יחידה: פזמון
    של שורה אחת שחוזר פעמיים ברצף הוא שתי הופעות, ושתיהן תחילת שורה.
    """
    flags, prev, prev_idx = [], None, None
    for seg in segments:
        idx = seg.get("seg_index")
        jump = idx is not None and prev_idx is not None and idx != prev_idx + 1
        flags.append(_unit_of(seg) != prev or jump)
        prev, prev_idx = _unit_of(seg), idx
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


def _occurrence_label(label: str, occurrence: int) -> str:
    """"שורה 3" + הופעה 2 ⇐ "שורה 3 · חזרה 2" (תווית הדוח)."""
    tag = f"חזרה {occurrence}"
    return f"{label} · {tag}" if label else tag


def expand_performance(segments: list, performance) -> list:
    """המקטעים לפי סדר הביצוע (PLAN_TEFILA.md 3.2): רשימת אינדקסי כתוביות.

    חזרה = אינדקס שמופיע שוב; דילוג = אינדקס שלא מופיע. כל הופעה היא עותק
    של המקטע עם seg_index (האינדקס המקורי) ו-occurrence (מ-1); מהופעה שנייה
    התווית מקבלת "· חזרה N". רשימות המילים משותפות (קריאה בלבד).
    None ⇐ המקטעים כמו שהם. קלט לא תקין ⇐ ValueError בעברית (ה-worker
    מחזיר אותו כשגיאת עיבוד ברורה).
    """
    if performance is None:
        return segments
    bad = "סדר הביצוע (performance) אינו תקין"
    if not isinstance(performance, (list, tuple)) or not performance:
        raise ValueError(bad + " — צריך רשימה לא ריקה של מספרי כתוביות")
    if len(performance) > MAX_PERFORMANCE:
        raise ValueError(f"סדר הביצוע ארוך מדי (עד {MAX_PERFORMANCE} הופעות)")
    n = len(segments)
    seen, out = Counter(), []
    for i in performance:
        if isinstance(i, bool) or not isinstance(i, int):
            raise ValueError(bad + f" — {i!r} אינו מספר כתובית")
        if not 0 <= i < n:
            raise ValueError(f"סדר הביצוע מפנה לכתובית {i} (הספירה מ-0), "
                             f"אבל בטקסט יש {n} כתוביות (0–{n - 1}) — טענו "
                             "את הקטע מחדש ובנו את סדר הביצוע שוב")
        seen[i] += 1
        seg = dict(segments[i], seg_index=i, occurrence=seen[i])
        if seen[i] > 1:
            seg["label"] = _occurrence_label(seg.get("label", ""), seen[i])
        out.append(seg)
    n_words = sum(len(s["align_vocalized"]) for s in out)
    if n_words > MAX_PERFORMED_WORDS:
        raise ValueError(f"סדר הביצוע ארוך מדי ({n_words} מילים עם החזרות; "
                         f"עד {MAX_PERFORMED_WORDS})")
    return out


def _probably_skipped(segments: list, flags: list, matches: list,
                      min_words: int = _SKIP_MIN_WORDS,
                      min_sim: float = _SKIP_MATCH_SIM) -> list:
    """‏4.3.4: הופעות יחידה (רצף מקטעים מדגל תחילת-יחידה עד הבא) עם
    ≥min_words מילים ואפס מילים שזוהו בתמלול. ⇐ [{"seg", "label", "words",
    "display"}] — seg = אינדקס המקטע הראשון ברצף (הפרוס)."""
    hit = {m["ref"] for m in matches if m["sim"] >= min_sim}
    groups, wi = [], 0
    for i, (seg, flag) in enumerate(zip(segments, flags)):
        n = len(seg["align_vocalized"])
        if flag or not groups:
            groups.append({"seg": i, "lo": wi, "hi": wi + n, "segs": [seg]})
        else:
            groups[-1]["hi"] = wi + n
            groups[-1]["segs"].append(seg)
        wi += n
    out = []
    for g in groups:
        n = g["hi"] - g["lo"]
        if n >= min_words and not any(r in hit for r in range(g["lo"], g["hi"])):
            first = g["segs"][0]
            out.append({"seg": g["seg"], "label": first.get("label", ""),
                        "words": n,
                        "display": " ".join(s["display"] for s in g["segs"])})
    return out


def _skipped_lines(skipped: list) -> list:
    if not skipped:
        return []
    lines = [f"כנראה דולג — יחידות של {_SKIP_MIN_WORDS}+ מילים שאף מילה מהן "
             "לא זוהתה בתמלול (הצעה בלבד; אם באמת דולגו — הסירו אותן מסדר "
             "הביצוע ונסו שוב):"]
    for k in skipped:
        words = k["display"].split()
        text = " ".join(words[:8]) + (" …" if len(words) > 8 else "")
        lines.append(f"  כתובית {k['seg'] + 1} · {k['label'] or '—'} | "
                     f"{k['words']} מילים | {text}")
    return lines


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
    ‏performance — סדר הביצוע (PLAN_TEFILA.md 3.2, ‏4.3.2): אינדקסי הכתוביות
    (אחרי החיתוך/‏splits, מ-0) לפי הסדר שבו נאמרו — חזרה = אינדקס שחוזר,
    דילוג = אינדקס חסר. המקטעים נפרסים לפיו לפני השטחת מילות היישור, וה-SRT
    מכיל כתובית לכל הופעה. רק ב-mode="tefila"; None = ביצוע לינארי מלא.
    ‏profile — "reading" (ברירת המחדל, ההתנהגות הקיימת) או "singing"
    (חזנות/שירה; ערכיו ב-profiles.py). שירה נתמכת רק ב-mode="tefila" —
    לתנ״ך אין פרופיל שירה.
    ‏debug — מילון אופציונלי (ברירת מחדל None = בלי שום שינוי): כשנמסר,
    הצינור ממלא בו את תוצאות הביניים — תמלול, עוגנים, חלונות וסטטוס כל
    ניסיון יישור, זמני מילים, VAD וביטחון (ראה tools/run_local.py).
    """
    if performance is not None and mode != "tefila":
        raise NotImplementedError(
            "סדר ביצוע (performance) נתמך רק בתפילה ובטקסט חופשי "
            "(mode=\"tefila\")")
    prof = profiles_mod.get_profile(profile)
    if prof.name != "reading" and mode != "tefila":
        raise NotImplementedError(
            f"פרופיל {profile!r} נתמך רק בתפילה ובטקסט חופשי (mode=\"tefila\")")
    print("2/8 חותך את הטקסט למקטעים…")
    return _run_units(units, audio_path, out_srt_path, max_words=max_words,
                      splits=splits, mode=mode, work_dir=work_dir,
                      asr_model=asr_model, debug=debug, prof=prof,
                      performance=performance)


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
               work_dir, asr_model, debug=None, prof=None, performance=None):
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
    if performance is not None:
        n_base = len(segments)
        segments = expand_performance(segments, performance)
        n_rep = sum(1 for s in segments if s["occurrence"] > 1)
        n_skip = n_base - len({s["seg_index"] for s in segments})
        print(f"    סדר ביצוע: {len(segments)} הופעות של {n_base} כתוביות "
              f"(חזרות: {n_rep}, דילוגים: {n_skip})")
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
    if mode == "tefila":  # ‏4.3.4 — הצעה בלבד, בלי שינוי אוטומטי
        skipped = _probably_skipped(segments, unit_flags, found["matches"])
        _debug_put(debug, probably_skipped=skipped)
        for line in _skipped_lines(skipped):
            print("    " + line.strip())
        if skipped:
            report += "\n\n" + "\n".join(_skipped_lines(skipped))
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
