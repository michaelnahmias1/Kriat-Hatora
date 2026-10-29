# -*- coding: utf-8 -*-
"""בדיקה חיה של רשימת הקטעים הנפוצים (data/siddur/popular.json) מול Sefaria.

לכל רשומה: טוען את העלה דרך api/siddur.py האמיתי (רשת!) עם הטווח שלה, ומדפיס
את המילים הראשונות של פסקת from ושל פסקת to, ואת הכתובית הראשונה והאחרונה —
כדי לבדוק בעין שהטווח מתחיל ונגמר במקום הנכון. ‏--write רושם בקובץ לכל
רשומה paragraph_count, ‏first, ‏last (מה שנמצא עכשיו), ואת הבדיקה הלא-מקוונת
‏tests/test_siddur_popular.py משתמשת בהם.

    python3 tools/verify_siddur_popular.py [--write] [--cache DIR] [nusach...]

יציאה 1 אם רשומה לא נטענה (לא 200) או שהטווח מחוץ לעלה.
"""

import argparse
import hashlib
import importlib.util
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POPULAR = ROOT / "data" / "siddur" / "popular.json"


def load_api(cache_dir=None):
    spec = importlib.util.spec_from_file_location("api_siddur", ROOT / "api" / "siddur.py")
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    if cache_dir:
        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        orig = api._get_json

        def cached(url, params=None):
            key = hashlib.sha1((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
            f = cache / key
            if f.exists():
                return json.loads(f.read_text(encoding="utf-8"))
            data = orig(url, params)
            f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return data
        api._get_json = cached
    return api


def dump(popular: dict) -> str:
    """כמו הקובץ בגיט: רשומה בשורה אחת (קל לסקירה ול-diff)."""
    lines = ["{"]
    head = {k: v for k, v in popular.items() if k != "nusachim"}
    for k, v in head.items():
        lines.append(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},")
    lines.append(' "nusachim": {')
    nus = list(popular["nusachim"].items())
    for i, (key, entries) in enumerate(nus):
        lines.append(f"  {json.dumps(key)}: [")
        for j, e in enumerate(entries):
            comma = "," if j + 1 < len(entries) else ""
            lines.append("   " + json.dumps(e, ensure_ascii=False) + comma)
        lines.append("  ]" + ("," if i + 1 < len(nus) else ""))
    lines.append(" }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--cache")
    ap.add_argument("nusach", nargs="*")
    args = ap.parse_args()
    api = load_api(args.cache)
    popular = json.loads(POPULAR.read_text(encoding="utf-8"))
    bad = 0
    for nusach, entries in popular["nusachim"].items():
        if args.nusach and nusach not in args.nusach:
            continue
        print(f"\n=== {nusach}")
        for e in entries:
            q = {"path": e["path"]}
            if e.get("from"):
                q["from"], q["to"] = e["from"], e["to"]
            payload, status, _ = api.respond(urllib.parse.urlencode(q))
            if status != 200:
                bad += 1
                print(f"✗ {e['label']}: {status} {payload.get('error')}")
                continue
            r, paras = payload["range"], payload["paragraphs"]
            first = paras[r["from"] - 1]["first_words"]
            last = paras[r["to"] - 1]["first_words"]
            segs = payload["segments"]
            print(f"✓ {e['label']}  [{r['from']}–{r['to']} / {r['total']}]  "
                  f"{len(segs)} כתוביות · {payload['version'].strip()}\n"
                  f"    from: {first}\n    to:   {last}\n"
                  f"    ⟵ {segs[0]['display']}\n    ⟶ {segs[-1]['display']}")
            e["paragraph_count"] = r["total"]
            e["first"], e["last"] = first, last
    if args.write:
        POPULAR.write_text(dump(popular), encoding="utf-8")
        print(f"\nנכתב: {POPULAR}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
