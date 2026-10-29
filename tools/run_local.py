# -*- coding: utf-8 -*-
"""הרצה מקומית (CPU) של צינור הענן על הקלטה + טקסט חופשי, עם דאמפ דיבאג מלא.

משחזר בדיוק את מסלול "טקסט חופשי" של ה-worker: היחידות נבנות ב-
‏api/text_segments.py::build_payload (מצב tefila, ‏max_words ברירת מחדל 4 —
מה שהדפדפן שולח), ועוברות ל-src/aligner/hybrid.py::run_hybrid_units —
אותו קוד שרץ ב-Modal, רק על CPU (תמלול int8, ‏MMS על CPU).

פלט בתיקיית --out-dir:
    <שם>.srt, ‏<שם>.report.txt   — מה שהמשתמש היה מקבל
    run.log                      — כל היומן המודפס (stdout + stderr)
    asr.json                     — התמלול (לשימוש חוזר עם --asr-json)
    debug.json                   — תמלול, זוגות ההצלבה, עוגנים (איזו מילת
                                   טקסט ↔ איזו מילת תמלול, זמנים), כיסוי לכל
                                   שורה, חלונות + סטטוס כל ניסיון יישור, זמני
                                   מילים, VAD והצמדה, ביטחון — ובדיקה מול
                                   ground truth / ‏SRT קודם אם נמסרו.

הרצה (מהשורש של המאגר, בסביבה עם torch/torchaudio/faster-whisper/
silero-vad/uroman — כמו ה-image ב-modal_worker/app.py):
    HF_HOME=… TORCH_HOME=… python tools/run_local.py \\
        --audio samples/nishmat/nishmat.m4a \\
        --text-file samples/nishmat/text.txt \\
        --ground-truth samples/nishmat/ground_truth.json \\
        --compare-srt samples/nishmat/received_v1.srt --out-dir /tmp/run1

ניסויים (מקומיים בלבד — לא משנים את הקוד בענן):
    --asr-json PATH        תמלול שמור במקום להריץ Whisper שוב (חוסך דקות)
    --rate-range LO HI     ‏rate_range של select_anchors (ברירת מחדל 0.12 4.0)
    --max-word-sec X       ‏_MAX_WORD_SEC של hybrid (ברירת מחדל 12)
    --src DIR              תיקיית src חלופית — למשל הגרסה שרצה בענן:
                           git archive <commit> src | tar -x -C /tmp/old
                           ואז --src /tmp/old/src (בלי וו הדיבאג: רק SRT/דוח/יומן)

ספריה סטנדרטית + הצינור עצמו; התלויות הכבדות נטענות רק בתוך הצינור.
"""

import argparse
import contextlib
import functools
import inspect
import json
import re
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent


# --- טעינת הצינור ----------------------------------------------------------------

def _load_pipeline(src_dir=None):
    """מייבא את hybrid ואת build_payload — מ-src חלופית אם נמסרה.

    הסדר חשוב: aligner נטען קודם מה-src המבוקשת; text_segments מוסיף את
    src של המאגר ל-sys.path, אבל המודולים כבר במטמון ולכן לא מוחלפים.
    """
    src = Path(src_dir).resolve() if src_dir else _REPO / "src"
    sys.path.insert(0, str(src))
    from aligner import hybrid
    sys.path.insert(0, str(_REPO / "api"))
    from text_segments import build_payload
    return hybrid, build_payload


# --- יומן: stdout+stderr גם למסך וגם לקובץ ----------------------------------------

class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
        return len(data)

    def flush(self):
        for s in self.streams:
            s.flush()

    def isatty(self):
        return False


# --- עזרים טהורים (נבדקים offline) -----------------------------------------------

def _r(x, nd=3):
    return None if x is None else round(float(x), nd)


def parse_srt(text: str) -> list:
    """תוכן SRT → [{"start","end","text"}]."""
    ts = r"(\d+):(\d+):(\d+)[,.](\d+)"
    out = []
    for block in re.split(r"\n\s*\n", text.replace("﻿", "").strip()):
        lines = [ln for ln in block.strip().splitlines() if ln.strip()]
        for k, ln in enumerate(lines):
            m = re.match(ts + r"\s*-->\s*" + ts, ln.strip())
            if m:
                g = [int(v) for v in m.groups()]
                out.append({
                    "start": g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                    "end": g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000,
                    "text": " ".join(lines[k + 1:])})
                break
    return out


def _word_index(segments: list) -> list:
    """לכל מילת יישור (שטוח) — (אינדקס מקטע, אינדקס יחידה)."""
    out = []
    for si, seg in enumerate(segments):
        out += [(si, seg.get("unit"))] * len(seg["align_plain"])
    return out


def _normalized_asr(anchors_mod, asr_words: list):
    """כמו find_anchors: רק מילות תמלול שנשאר בהן משהו אחרי נורמליזציה.

    ‏anchor["asr"] מצביע לרשימה המסוננת הזו — מחזירים גם את המיפוי לאינדקס
    המקורי.
    """
    norm, orig = [], []
    for i, w in enumerate(asr_words):
        nw = anchors_mod.normalize_word(w["word"])
        if nw:
            norm.append(nw)
            orig.append(i)
    return norm, orig


def build_dump(debug: dict, units: list, anchors_mod) -> dict:
    """מילון הדיבאג של הצינור → מבנה JSON קריא (בלי אובייקטים של torch)."""
    segments = debug["segments"]
    plain, voc = debug["flat_plain"], debug["flat_vocalized"]
    where = _word_index(segments)
    asr_words = debug.get("asr_words") or []
    norm, orig = _normalized_asr(anchors_mod, asr_words)
    ref_norm = [anchors_mod.normalize_word(w) for w in plain]
    pairs = anchors_mod.align_sequences(norm, ref_norm)

    transcription = []
    norm_of = {o: n for n, o in enumerate(orig)}
    for i, w in enumerate(asr_words):
        transcription.append({
            "i": i, "word": w["word"], "start": _r(w["start"]),
            "end": _r(w["end"]), "prob": _r(w.get("prob")),
            "norm": anchors_mod.normalize_word(w["word"]),
            "norm_i": norm_of.get(i)})

    match_of = {}
    pair_rows = []
    for ai, rj, sim in pairs:
        row = {"asr_norm_i": ai,
               "asr_word": asr_words[orig[ai]]["word"] if ai is not None else None,
               "asr_start": _r(asr_words[orig[ai]]["start"]) if ai is not None else None,
               "ref": rj, "text_word": plain[rj] if rj is not None else None,
               "sim": _r(sim)}
        pair_rows.append(row)
        if ai is not None and rj is not None:
            match_of[rj] = row

    anchors = []
    anchor_refs = set()
    for a in debug.get("anchors") or []:
        anchor_refs.add(a["ref"])
        ai = a.get("asr")
        anchors.append({
            "ref": a["ref"], "text_word": plain[a["ref"]],
            "segment": where[a["ref"]][0], "unit": where[a["ref"]][1],
            "asr_norm_i": ai,
            "asr_word": (asr_words[orig[ai]]["word"]
                         if ai is not None and ai < len(orig) else None),
            "start": _r(a["start"]), "end": _r(a["end"]), "sim": _r(a["sim"])})

    spans = debug.get("word_spans") or []
    interp = debug.get("interpolated") or [False] * len(spans)
    words = []
    for j, w in enumerate(plain):
        m = match_of.get(j)
        words.append({
            "i": j, "plain": w, "vocalized": voc[j], "norm": ref_norm[j],
            "segment": where[j][0], "unit": where[j][1],
            "start": _r(spans[j][0]) if spans else None,
            "end": _r(spans[j][1]) if spans else None,
            "ctc_score": _r(spans[j][2]) if spans else None,
            "interpolated": bool(interp[j]) if spans else None,
            "anchor": j in anchor_refs,
            "asr_match": ({"asr_word": m["asr_word"], "asr_start": m["asr_start"],
                           "sim": m["sim"]} if m else None)})

    per_unit = []
    for ui, unit in enumerate(units):
        idx = [j for j, (_, u) in enumerate(where) if u == ui]
        if not idx:
            continue
        unit_anchors = [a for a in anchors if a["unit"] == ui]
        matched = [j for j in idx if match_of.get(j)
                   and (match_of[j]["sim"] or 0) >= 0.7]
        per_unit.append({
            "unit": ui, "label": unit.get("label"), "n_words": len(idx),
            "n_anchors": len(unit_anchors),
            "n_matched_sim07": len(matched),
            "anchor_times": [a["start"] for a in unit_anchors],
            "first_word_start": words[idx[0]]["start"],
            "last_word_end": words[idx[-1]]["end"]})

    def win(w):
        return {"word_lo": w["word_lo"], "word_hi": w["word_hi"],
                "t_lo": _r(w["t_lo"]), "t_hi": _r(w["t_hi"]),
                "text": " ".join(plain[w["word_lo"]:w["word_hi"] + 1])}

    initial = {(w["word_lo"], w["word_hi"]) for w in debug.get("windows") or []}
    attempts = []
    for a in debug.get("window_attempts") or []:
        row = win(a["window"])
        row["status"] = a["status"]
        if a.get("spans"):
            row["spans"] = [[_r(s), _r(e), _r(sc)] for s, e, sc in a["spans"]]
            row["longest_word_sec"] = _r(max(e - s for s, e, _ in a["spans"]))
        attempts.append(row)
    final = []
    for item in debug.get("aligned") or []:
        row = win(item["window"])
        row["interpolated"] = item["interpolated"]
        row["merged"] = (item["window"]["word_lo"],
                         item["window"]["word_hi"]) not in initial
        final.append(row)

    starts = debug.get("starts") or []
    raw = debug.get("starts_raw") or []
    snaps = debug.get("snap_dists") or []
    infos = debug.get("infos") or []
    confs = debug.get("confidences") or []
    seg_rows = []
    j = 0
    for si, seg in enumerate(segments):
        n = len(seg["align_plain"])
        seg_rows.append({
            "i": si, "unit": seg.get("unit"), "label": seg.get("label"),
            "display": seg["display"], "word_lo": j, "word_hi": j + n - 1,
            "start_raw": _r(raw[si]) if si < len(raw) else None,
            "start": _r(starts[si]) if si < len(starts) else None,
            "last_word_end": words[j + n - 1]["end"],
            "unit_start": (debug.get("unit_flags") or [None] * len(segments))[si],
            "vad_snap": _r(snaps[si]) if si < len(snaps) else None,
            "confidence": confs[si] if si < len(confs) else None,
            "info": infos[si] if si < len(infos) else None})
        j += n

    speech = debug.get("speech") or []
    dur = debug.get("audio_dur") or 0
    return {
        "asr_name": debug.get("asr_name"),
        "audio_dur": _r(dur),
        "coverage": _r(debug.get("coverage")),
        "n_text_words": len(plain),
        "units": units,
        "transcription": transcription,
        "alignment_pairs": pair_rows,
        "anchors": anchors,
        "anchor_coverage_per_unit": per_unit,
        "windows_initial": [win(w) for w in debug.get("windows") or []],
        "window_attempts": attempts,
        "windows_final": final,
        "words": words,
        "segments": seg_rows,
        "vad": {
            "ran": debug.get("vad_ran"),
            "n_regions": len(speech),
            "speech_fraction": _r(sum(e - s for s, e in speech) / dur) if dur else None,
            "regions": [[_r(s), _r(e)] for s, e in speech]},
    }


def evaluate(srt_cues: list, segments: list, words: list, truth: dict) -> dict:
    """השוואה ל-ground truth: שגיאת תחילת שורה, ומילים שנבלעו בדיבור שאינו בטקסט.

    ‏segments — שורות "segments" מהדאמפ (unit לכל כתובית, אותו סדר כמו ה-SRT);
    ‏words — שורות "words" (אפשר ריק — אז אין בדיקת בליעה).
    """
    out = {"line_starts": [], "non_text_speech": []}
    for ls in truth.get("line_starts", []):
        unit = ls["line"] - 1
        idx = next((i for i, s in enumerate(segments) if s["unit"] == unit),
                   None)
        got = srt_cues[idx]["start"] if idx is not None and idx < len(srt_cues) else None
        out["line_starts"].append({
            "line": ls["line"], "first_words": ls.get("first_words"),
            "truth": ls["start"], "got": _r(got),
            "error": _r(got - ls["start"]) if got is not None else None})
    for region in truth.get("non_text_speech", []):
        lo, hi = region["start"], region["end"]
        inside = [w["plain"] for w in words
                  if w.get("start") is not None and w.get("end") is not None
                  and lo <= (w["start"] + w["end"]) / 2 < hi]
        cues = [i + 1 for i, c in enumerate(srt_cues)
                if c["start"] < hi and c["end"] > lo]
        out["non_text_speech"].append({
            "start": lo, "end": hi, "what": region.get("what"),
            "text_words_inside": inside, "cues_overlapping": cues})
    return out


def compare_srts(local: list, other: list) -> dict:
    """הפרש תחילות כתוביות (אותו אינדקס) בין שתי ריצות."""
    n = min(len(local), len(other))
    diffs = [round(local[i]["start"] - other[i]["start"], 3) for i in range(n)]
    absd = sorted(abs(d) for d in diffs)
    return {"n_local": len(local), "n_other": len(other),
            "start_diffs": diffs,
            "median_abs": absd[len(absd) // 2] if absd else None,
            "max_abs": absd[-1] if absd else None}


# --- הרצה ------------------------------------------------------------------------

def _parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--audio", required=True)
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--max-words", default=None,
                    help="כמו בדפדפן; ריק ⇒ ברירת המחדל של build_payload (4)")
    ap.add_argument("--mode", default="tefila")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--asr-model", default=None)
    ap.add_argument("--asr-json", default=None)
    ap.add_argument("--rate-range", nargs=2, type=float, default=None)
    ap.add_argument("--max-word-sec", type=float, default=None)
    ap.add_argument("--src", default=None)
    ap.add_argument("--ground-truth", default=None)
    ap.add_argument("--compare-srt", default=None)
    return ap.parse_args(argv)


def main(argv=None) -> dict:
    args = _parse_args(argv)
    audio = Path(args.audio).resolve()
    out_dir = Path(args.out_dir or Path(tempfile.gettempdir())
                   / "kriat_hatora_run_local" / audio.stem).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_srt = out_dir / f"{audio.stem}.srt"
    log_path = out_dir / "run.log"

    with open(log_path, "w", encoding="utf-8") as log, \
            contextlib.redirect_stdout(_Tee(sys.stdout, log)), \
            contextlib.redirect_stderr(_Tee(sys.stderr, log)):
        return _run(args, audio, out_dir, out_srt)


def _run(args, audio, out_dir, out_srt) -> dict:
    t0 = time.time()
    H, build_payload = _load_pipeline(args.src)
    text = Path(args.text_file).read_text(encoding="utf-8")
    payload = build_payload({"text": text, "max_words": args.max_words,
                             "mode": args.mode})
    units = payload["units"]
    print(f"run_local: {len(units)} יחידות | max_words={payload['max_words']}"
          f" | mode={payload['mode']} | src={Path(H.__file__).parent.parent}")

    # תמלול: שמור (--asr-json) או אמיתי — ובכל מקרה נשמר ל-asr.json
    captured = {}
    real_transcribe = H.asr_mod.transcribe
    cached = (json.loads(Path(args.asr_json).read_text(encoding="utf-8"))
              if args.asr_json else None)

    def transcribe(wav_path, model_name=None, **kw):
        t = time.time()
        if cached is not None:
            print(f"    תמלול שמור: {args.asr_json}")
            words, name = cached["words"], cached["model"]
        else:
            words, name = real_transcribe(wav_path, model_name=model_name, **kw)
        captured.update(words=words, model=name, sec=round(time.time() - t, 1))
        return words, name

    overrides = {}
    patches = [(H.asr_mod, "transcribe", transcribe)]
    if args.rate_range:
        overrides["rate_range"] = tuple(args.rate_range)
        patches.append((H.anchors_mod, "find_anchors", functools.partial(
            H.anchors_mod.find_anchors, rate_range=tuple(args.rate_range))))
    if args.max_word_sec is not None:
        overrides["max_word_sec"] = args.max_word_sec
        patches.append((H, "_MAX_WORD_SEC", args.max_word_sec))
    if overrides:
        print(f"run_local: ⚠️ ניסוי — פרמטרים שונים מהענן: {overrides}")

    has_debug = "debug" in inspect.signature(H.run_hybrid_units).parameters
    debug = {} if has_debug else None
    kwargs = dict(max_words=payload["max_words"], mode=payload["mode"],
                  work_dir=str(out_dir), asr_model=args.asr_model)
    if has_debug:
        kwargs["debug"] = debug
    else:
        print("run_local: ⚠️ ל-src הזו אין וו דיבאג — רק SRT/דוח/יומן")

    saved = [(mod, name, getattr(mod, name)) for mod, name, _ in patches]
    try:
        for mod, name, value in patches:
            setattr(mod, name, value)
        H.run_hybrid_units(units, str(audio), str(out_srt), **kwargs)
    finally:
        for mod, name, value in saved:
            setattr(mod, name, value)

    if captured:
        (out_dir / "asr.json").write_text(json.dumps(
            {"model": captured["model"], "words": captured["words"]},
            ensure_ascii=False, indent=1), encoding="utf-8")

    if debug:
        dump = build_dump(debug, units, H.anchors_mod)
    else:  # src בלי וו דיבאג — לפחות המקטעים, לבדיקה מול ground truth
        segs = H.units_to_segments(units, payload["max_words"],
                                   mode=payload["mode"])
        dump = {"units": units, "segments": [
            {"i": i, "unit": s["unit"], "label": s["label"],
             "display": s["display"]} for i, s in enumerate(segs)]}
    dump["meta"] = {"audio": str(audio), "text_file": str(args.text_file),
                    "max_words": payload["max_words"], "mode": payload["mode"],
                    "src": str(Path(H.__file__).parent.parent),
                    "overrides": overrides, "asr_sec": captured.get("sec"),
                    "total_sec": round(time.time() - t0, 1)}
    cues = parse_srt(out_srt.read_text(encoding="utf-8-sig"))
    if args.ground_truth:
        truth = json.loads(Path(args.ground_truth).read_text(encoding="utf-8"))
        dump["evaluation"] = evaluate(cues, dump.get("segments", []),
                                      dump.get("words", []), truth)
        if args.compare_srt:
            other = parse_srt(Path(args.compare_srt).read_text(encoding="utf-8-sig"))
            dump["evaluation_compare_srt"] = evaluate(
                other, dump.get("segments", []), [], truth)
    if args.compare_srt:
        other = parse_srt(Path(args.compare_srt).read_text(encoding="utf-8-sig"))
        dump["compare_srt"] = compare_srts(cues, other)
    (out_dir / "debug.json").write_text(
        json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"run_local: הסתיים ב-{dump['meta']['total_sec']} שניות "
          f"(תמלול {captured.get('sec')}) → {out_dir}")
    for row in dump.get("evaluation", {}).get("line_starts", []):
        print(f"    שורה {row['line']}: אמת {row['truth']} | התקבל {row['got']}"
              f" | שגיאה {row['error']}")
    if "compare_srt" in dump:
        c = dump["compare_srt"]
        print(f"    מול {args.compare_srt}: {c['n_local']}/{c['n_other']} כתוביות,"
              f" הפרש תחילות חציוני {c['median_abs']} מרבי {c['max_abs']}")
    return dump


if __name__ == "__main__":
    main()
