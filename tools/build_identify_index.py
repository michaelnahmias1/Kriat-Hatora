# -*- coding: utf-8 -*-
"""בונה את אינדקס הזיהוי של הסידור — PLAN_TEFILA.md משימה 4.5.1.

    python3 tools/build_identify_index.py              # מה-cache של בונה הקטלוג, ורשת למה שחסר
    python3 tools/build_identify_index.py --offline    # רק מה-cache, בלי רשת

קלט: ‏data/siddur/catalog.json (העלים, ה-ref והמהדורה שנבחרה לכל עלה). הטקסט
נמשך עם הלקוח של tools/survey_siddur.py (‏cache בדיסק — אותו cache של
tools/build_siddur_catalog.py, כך שבדרך כלל אין שום בקשת רשת). עלים מוויקיטקסט
(אוספים, 4.4.1) — מהצילום שבגיט (data/siddur/wikisource), כמו ה-API.

פלט: ‏data/siddur/identify_index.json.gz — הטקסט הנאמר של כל עלה זמין
(3 הנוסחים), כמילים מנורמלות **בדיוק כמו בצינור**: יחידות כמו ב-api/siddur.py
(‏markup.classify_leaf — הוראות בחוץ; **תוספות תלויות-יום בפנים** (4.4.2): הן
נאמרות בחלק מהימים, וההקלטה עשויה להיות מיום כזה), מילות יישור במצב tefila
(‏units_to_segments ⇐ align_plain: שם ה׳ ⇐ אדני, מקף ⇐ מילים נפרדות, כתיב
שהקרי שלו בסוגריים בחוץ), ואז anchors.normalize_word — אותה נורמליזציה
שהמיישר מפעיל על התמלול. ה-n-gramים עצמם לא נשמרים: src/siddur/identify.py
בונה אותם בזיכרון בטעינה (שנייה-שתיים), כך שהקובץ קטן.

הקובץ נאפה ב-image של ה-worker (modal_worker/app.py) ואינו מוגש ע״י Vercel
(‏.vercelignore). בונים מחדש אחרי בנייה מחדש של הקטלוג או שינוי ב-markup.py.
"""

import argparse
import gzip
import importlib.util
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from aligner.anchors import normalize_word  # noqa: E402
from aligner.pipeline import split_mixed_unit, units_to_segments  # noqa: E402
from siddur import load_catalog  # noqa: E402
from siddur import sources, wikisource  # noqa: E402  (אוספים, 4.4.1)
from siddur.identify import FORMAT, INDEX_PATH  # noqa: E402
from siddur.markup import (CONDITIONAL, SPOKEN, classify_leaf,  # noqa: E402
                           first_words, flatten)

_SPEC = importlib.util.spec_from_file_location(
    "survey_siddur", Path(__file__).resolve().parent / "survey_siddur.py")
sv = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sv)

DEFAULT_CACHE = Path.home() / ".cache" / "kriat-hatora-sefaria-catalog"
FIRST_WORDS = 5


_SAID = (SPOKEN, CONDITIONAL)   # נאמר תמיד / בחלק מהימים


def paragraph_words(paragraph, parts=None) -> list:
    """פסקה אחת (HTML מ-Sefaria) ⇐ המילים הנאמרות (גם תוספות תלויות-יום),
    מנורמלות כמו בצינור. ‏parts — הסיווג שלה מ-classify_leaf, אם כבר חושב
    (תוספת שהכותרת שלה בפסקה הקודמת מזוהה רק בסיווג של העלה כולו)."""
    if parts is None:
        parts = classify_leaf([paragraph])[0]
    units = []
    for kind, body, _ in parts:
        if kind not in _SAID:
            continue
        # כמו api/siddur.py — גם פיצול פסקה מעורבת (המילים עצמן לא משתנות)
        units.extend(split_mixed_unit({"text": body, "kind": "paragraph"}))
    if not units:
        return []
    out = []
    for seg in units_to_segments(units, 10, None, "tefila"):
        for w in seg["align_plain"]:
            nw = normalize_word(w)
            if nw:
                out.append(nw)
    return out


def leaf_record(paragraphs: list) -> dict:
    """פסקאות העלה ⇐ {words, starts: [[מספר פסקה, היסט המילה הראשונה]],
    first: {מספר פסקה: מילים ראשונות}, total}. פסקה בלי מילים נאמרות (הוראה)
    לא נכנסת ל-starts — הטווח שיוחזר לעולם לא מתחיל או נגמר בה."""
    words, starts, first = [], [], {}
    for n, (para, parts) in enumerate(zip(paragraphs, classify_leaf(paragraphs)), 1):
        pw = paragraph_words(para, parts)
        if not pw:
            continue
        starts.append([n, len(words)])
        words.extend(pw)
        # כמו first_words של /api/siddur: הנאמר תמיד, ואם אין — התוספת
        spoken = [b for k, b, _ in parts if k == SPOKEN] or \
            [b for k, b, _ in parts if k == CONDITIONAL]
        fw = first_words(spoken, FIRST_WORDS)
        if fw:
            first[str(n)] = fw
    return {"words": words, "starts": starts, "first": first,
            "total": len(paragraphs)}


def fetch_paragraphs(client, ref: str, version_title: str):
    """הטקסט של עלה במהדורה שנבחרה ⇐ פסקאות (כמו api/siddur.fetch_leaf), או
    None. קודם הבקשה בלי version (כך בונה הקטלוג משך את ברירת המחדל — אולי
    כבר ב-cache), ואם המהדורה שחזרה אחרת — הבקשה המפורשת."""
    for vt in (None, version_title):
        st, data = sv.fetch_text(client, ref, vt)
        if st != 200 or not isinstance(data, dict):
            continue
        vs = data.get("versions") or []
        if vs and isinstance(vs[0], dict) and vs[0].get("versionTitle") == version_title:
            return flatten(vs[0].get("text"))
    return None


def source_paragraphs(client, src: dict):
    """הפסקאות של עלה לפי המקור שלו — כמו api/siddur._fetch_leaf_text (4.4.1):
    ויקיטקסט ⇐ הצילום שבגיט (data/siddur/wikisource);
    מהדורה לינארית ⇐ שורות מאוחדות לפסקאות. ⇐ None כשאין ב-cache."""
    if src.get("source") == "wikisource":
        # הצילום שבגיט — בדיוק מה ש-api/siddur.py מגיש (בלי רשת)
        return wikisource.snapshot_paragraphs(src["ws"])
    paras = fetch_paragraphs(client, src["ref"], src["version"])
    if paras is not None and src.get("lines"):
        paras = sources.merge_lines(paras)
    return paras


def build(cat, client, log=print) -> tuple:
    leaves, missing, seen_refs = [], [], set()
    vocab_count = Counter()
    for nus in cat.nusachim:
        nkey = nus["key"]
        for path, node in cat.leaves(nkey):
            src = cat.source(path)
            if src is None:
                continue
            if (nkey, src["ref"]) in seen_refs:   # shared_refs — אותו טקסט בדיוק
                continue
            seen_refs.add((nkey, src["ref"]))
            paras = source_paragraphs(client, src)
            if paras is None:
                missing.append(path)
                continue
            rec = leaf_record(paras)
            if not rec["words"]:
                continue
            crumbs = cat.breadcrumb(path)
            rec.update({"nusach": nkey, "path": path,
                        "title": node.get("heTitle", ""),
                        "crumbs": crumbs[1:-1]})
            vocab_count.update(rec["words"])
            leaves.append(rec)
        log(f"  {nkey}: {sum(1 for lf in leaves if lf['nusach'] == nkey)} עלים")
    # מילים שכיחות ⇐ מזהים קצרים (JSON קטן יותר)
    vocab = [w for w, _ in vocab_count.most_common()]
    vid = {w: i for i, w in enumerate(vocab)}
    out_leaves = []
    for lf in leaves:
        out_leaves.append({
            "n": lf["nusach"], "p": lf["path"], "t": lf["title"],
            "c": lf["crumbs"], "P": lf["total"], "s": lf["starts"],
            "f": lf["first"], "w": [vid[w] for w in lf["words"]],
        })
    index = {
        "format": FORMAT,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "about": ("אינדקס הזיהוי (PLAN_TEFILA.md 4.5.1): הטקסט הנאמר של כל עלה "
                  "זמין בקטלוג, כמילים מנורמלות כמו בצינור. נבנה ע״י "
                  "tools/build_identify_index.py"),
        "catalog_generated": cat.data.get("generated", ""),
        "nusachim": {n["key"]: n.get("heTitle", "") for n in cat.nusachim},
        "vocab": vocab,
        "leaves": out_leaves,
    }
    return index, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description="בניית אינדקס הזיהוי (PLAN_TEFILA.md 4.5.1)")
    ap.add_argument("--out", default=str(INDEX_PATH))
    ap.add_argument("--cache-dir", default=str(DEFAULT_CACHE))
    ap.add_argument("--offline", action="store_true", help="רק מה-cache")
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--base", default=sv.SEFARIA_BASE)
    args = ap.parse_args(argv)

    cat = load_catalog()
    client = sv.Client(args.base, args.cache_dir, delay=args.delay,
                       offline=args.offline)
    index, missing = build(cat, client)
    if missing:
        print(f"✗ {len(missing)} עלים בלי טקסט (offline / רשת):")
        for p in missing[:20]:
            print("   ", p)
        print("✗ לא נכתב פלט.")
        return 1
    raw = json.dumps(index, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 — אותו קלט ⇐ אותו קובץ בדיוק (diff נקי בגיט)
    with open(out, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=0,
                           compresslevel=9) as gz:
            gz.write(raw)
    n_words = sum(len(lf["w"]) for lf in index["leaves"])
    print(f"✅ נכתב: {out} ({out.stat().st_size:,} בתים; JSON ‏{len(raw):,})")
    print(f"   עלים: {len(index['leaves'])}, מילים: {n_words:,}, "
          f"אוצר מילים: {len(index['vocab']):,}")
    print(f"   בקשות רשת: {client.n_network}, מה-cache: {client.n_cached}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
