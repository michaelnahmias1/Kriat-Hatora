# -*- coding: utf-8 -*-
"""צינור העיבוד המלא: טקסט מ-Sefaria → חיתוך → יישור CTC → קובץ SRT.

מיועד לרוץ ב-Colab עם GPU (ראה notebooks/worker.ipynb). התלויות הכבדות
(torch/torchaudio/uroman) מיובאות בתוך הפונקציות כדי שהמודול ייטען גם
בסביבה בלעדיהן (למשל להרצת בדיקות על החלקים הקלים).

מסלול היישור: MMS_FA של torchaudio + רומניזציה עם uroman על הטקסט
המנוקד (alignment_vocalized מה-chunker) — ראה PLAN.md סעיף 3.
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chunker import segments_for_pipeline  # noqa: E402

SEFARIA_BASE = "https://www.sefaria.org"
TORAH_BOOKS = {
    "בראשית": "Genesis", "שמות": "Exodus", "ויקרא": "Leviticus",
    "במדבר": "Numbers", "דברים": "Deuteronomy",
}


# --- שלב 1: טקסט ------------------------------------------------------------

def find_mam_version(book: str) -> str:
    """מאתר את שם גרסת MAM המדויק בספר — לא מניחים שם מהזיכרון."""
    import requests
    versions = requests.get(
        f"{SEFARIA_BASE}/api/texts/versions/{book}", timeout=60).json()
    for v in versions:
        title = v.get("versionTitle", "")
        if v.get("language") == "he" and (
                "masorah" in title.lower() or "מסורה" in title):
            return title
    raise RuntimeError(
        f"לא נמצאה גרסת MAM לספר {book}. גרסאות עבריות: "
        + ", ".join(v.get("versionTitle", "?") for v in versions
                    if v.get("language") == "he"))


def _flatten(nested):
    """טקסט מ-Sefaria יכול להגיע מקונן (טווח חוצה-פרקים) — משטחים לפי הסדר."""
    if isinstance(nested, str):
        return [nested]
    out = []
    for item in nested:
        out.extend(_flatten(item))
    return out


def build_ref(book, chapter, verse_start=None, chapter_end=None, verse_end=None):
    """בונה ref של Sefaria: פרק שלם, טווח בתוך פרק, או טווח חוצה-פרקים (עלייה)."""
    ref = f"{book} {chapter}"
    if verse_start:
        ref += f":{verse_start}"
        if chapter_end and chapter_end != chapter:
            ref += f"-{chapter_end}:{verse_end or 1}"
        elif verse_end:
            ref += f"-{verse_end}"
    return ref


def fetch_verses(ref: str, version_title: str) -> list:
    """מושך את פסוקי ה-ref בגרסת MAM ומחזיר רשימת מחרוזות-פסוק."""
    import requests
    try:
        data = requests.get(
            f"{SEFARIA_BASE}/api/v3/texts/{ref}",
            params={"version": f"hebrew|{version_title}"}, timeout=60).json()
        verses = _flatten(data["versions"][0]["text"])
    except Exception as e:  # פולבק ל-API הישן
        print(f"אזהרה: API v3 נכשל ({e}) — עובר ל-API הישן")
        data = requests.get(
            f"{SEFARIA_BASE}/api/texts/{ref.replace(' ', '.')}",
            params={"vhe": version_title}, timeout=60).json()
        verses = _flatten(data["he"])
    verses = [v for v in verses if v and v.strip()]
    if not verses:
        raise RuntimeError(f"לא הגיעו פסוקים עבור {ref}")
    return verses


# --- שלב 2: חיתוך -----------------------------------------------------------

def verses_to_segments(verses: list, max_words: int = 4) -> list:
    """כל הפסוקים → רשימה שטוחה של מקטעים (display + מילות יישור)."""
    segments = []
    for vi, verse in enumerate(verses, 1):
        for seg in segments_for_pipeline(verse, max_words):
            seg["verse"] = vi
            segments.append(seg)
    return segments


# --- שלב 3: יישור -----------------------------------------------------------

def load_audio_16k_mono(audio_path: str, work_dir: str = "."):
    """ממיר כל פורמט ל-wav 16kHz מונו (ffmpeg) וטוען כ-tensor."""
    import torchaudio
    wav_path = str(Path(work_dir) / "aligned_input_16k.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", audio_path,
         "-ar", "16000", "-ac", "1", wav_path], check=True)
    waveform, sr = torchaudio.load(wav_path)
    assert sr == 16000
    return waveform


_NON_LATIN = re.compile(r"[^a-z' ]")


def romanize_words(words: list) -> list:
    """רומניזציה של מילים עבריות מנוקדות עם uroman + נורמליזציה ל-MMS."""
    import uroman as ur
    rom = ur.Uroman()
    out = []
    for w in words:
        r = _NON_LATIN.sub("", rom.romanize_string(w).lower())
        out.append(r if r.strip() else "a")  # מילה ריקה מפילה את המיישר
    return out


def align_words(waveform, romanized_words: list) -> list:
    """יישור מאולץ עם MMS_FA. מחזיר [(start_sec, end_sec)] לכל מילה.

    הערת גבול: על GPU T4 היישור בטוח עד ~6 דקות אודיו ברצף. הקלטה ארוכה
    משמעותית עלולה לגמור את הזיכרון — לפצל את ההקלטה לפי עליות.
    """
    import torch
    from torchaudio.pipelines import MMS_FA as bundle

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = bundle.get_model(with_star=False).to(device)
    tokenizer = bundle.get_tokenizer()
    aligner = bundle.get_aligner()

    with torch.inference_mode():
        emission, _ = model(waveform.to(device))
        token_spans = aligner(emission[0], tokenizer(romanized_words))

    num_frames = emission.size(1)
    sec_per_frame = waveform.size(1) / num_frames / bundle.sample_rate
    spans = []
    for word_spans in token_spans:
        start = word_spans[0].start * sec_per_frame
        end = word_spans[-1].end * sec_per_frame
        spans.append((start, end))
    return spans


# --- שלב 4: דגימת גבולות + SRT ----------------------------------------------

def _fmt_ts(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(segments: list, word_spans: list, tail_pad: float = 0.25) -> str:
    """גבולות מקטעים בלבד (שאר חותמות המילים נזרקות) → תוכן קובץ SRT.

    לכל מקטע: התחלה = תחילת מילתו הראשונה; סוף = תחילת המקטע הבא
    (רציף, בלי חורים — נוח יותר לצפייה), ולמקטע האחרון סוף-מילה + ריפוד.
    """
    starts, ends = [], []
    wi = 0
    for seg in segments:
        n = len(seg["align_vocalized"])
        starts.append(word_spans[wi][0])
        ends.append(word_spans[wi + n - 1][1])
        wi += n
    if wi != len(word_spans):
        raise RuntimeError(
            f"אי-התאמה: {len(word_spans)} מילים יושרו אבל המקטעים מכסים {wi}")

    lines = []
    for i, seg in enumerate(segments):
        start = starts[i]
        end = starts[i + 1] if i + 1 < len(segments) else ends[i] + tail_pad
        end = max(end, start + 0.3)  # כתובית לעולם לא קצרה מ-0.3 שניות
        lines += [str(i + 1), f"{_fmt_ts(start)} --> {_fmt_ts(end)}",
                  seg["display"], ""]
    return "\n".join(lines)


# --- הפונקציה הראשית ----------------------------------------------------------

def run(book, chapter, audio_path, out_srt_path,
        verse_start=None, chapter_end=None, verse_end=None, max_words=4):
    """הצינור המלא. מדפיס התקדמות בעברית ומחזיר את נתיב ה-SRT."""
    book = TORAH_BOOKS.get(book, book)
    print(f"1/5 מאתר את גרסת MAM עבור {book}…")
    version = find_mam_version(book)
    ref = build_ref(book, chapter, verse_start, chapter_end, verse_end)
    print(f"    גרסה: «{version}» | טווח: {ref}")

    print("2/5 מושך את הטקסט וחותך לפי טעמים…")
    verses = fetch_verses(ref, version)
    segments = verses_to_segments(verses, max_words)
    n_words = sum(len(s["align_vocalized"]) for s in segments)
    print(f"    {len(verses)} פסוקים → {len(segments)} מקטעים ({n_words} מילים)")

    print("3/5 טוען וממיר את ההקלטה (16kHz מונו)…")
    waveform = load_audio_16k_mono(audio_path)
    dur = waveform.size(1) / 16000
    print(f"    משך: {dur / 60:.1f} דקות")
    if dur > 390:
        print("    ⚠️ הקלטה ארוכה מ-6.5 דקות — ייתכן חוסר זיכרון ב-GPU. אם"
              " הריצה נופלת, פצל את ההקלטה לפי עליות.")

    print("4/5 יישור מאולץ (MMS + רומניזציה של הטקסט המנוקד)…")
    flat_words = [w for s in segments for w in s["align_vocalized"]]
    spans = align_words(waveform, romanize_words(flat_words))

    print("5/5 בונה SRT…")
    srt = build_srt(segments, spans)
    Path(out_srt_path).write_text(srt, encoding="utf-8-sig")
    print(f"✅ נוצר: {out_srt_path}")
    return out_srt_path
