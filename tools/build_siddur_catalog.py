# -*- coding: utf-8 -*-
"""בונה את קטלוג הסידור — PLAN_TEFILA.md משימה 4.2.1.

    python3 tools/build_siddur_catalog.py              # בנייה מלאה מול sefaria.org
    python3 tools/build_siddur_catalog.py --offline    # רק מה-cache, בלי רשת
    python3 tools/build_siddur_catalog.py --nusach sefard --out /tmp/c.json

קלט: ‏data/siddur/overrides.json (מיפוי ידני: נוסחים, גרסאות, מדיניות בחירת
גרסה וסוג היום של כל צומת). פלט: ‏data/siddur/catalog.json (נשמר בגיט, מוגש
ע״י ה-API בהמשך), בלי גוף טקסט — הטקסט נמשך בזמן ריצה.

מה נעשה, ומאיפה כל נתון (שום דבר לא מהזיכרון):
1. ה-schema של כל סידור — ‏/api/v2/raw/index/{title}. ה-ref של עלה נבנה
   מהכותרים הראשיים (לא מה-key), **כמו שהם, כולל רווח בסוף** — ‏Sefaria דוחה
   (400) את ‏"Siddur Sefard, Additional Prayers, …" ומקבל רק ‏"Additional Prayers , …".
2. סוג היום של כל עלה — לפי הכלל עם הקידומת הארוכה ביותר ב-overrides.json.
   עלה בלי כלל ⇐ הבנייה נכשלת (צומת חדש ב-Sefaria לא ייעלם בשקט).
3. זמינות גרסאות לכל עלה — ‏/api/v3/texts/{ref} בלי version: ‏available_versions
   (רשימת הגרסאות שיש להן טקסט בעלה, לפי ה-API) + הטקסט של גרסת ברירת המחדל.
   כל גרסה מהמדיניות שמופיעה שם ושאינה ברירת המחדל נמשכת במפורש
   (‏version=hebrew|<title>) כדי לוודא שבאמת יש בה טקסט (גרסה בלי טקסט בעלה
   מחזירה 200 עם versions ריק). הגרסה שנבחרת = הראשונה במדיניות שיש לה טקסט.
   עלה בלי אף גרסה מהמדיניות ⇐ unavailable (וגרסאות אחרות שנמצאו נרשמות ב-note).
4. "מילים ראשונות" לכל עלה — מהטקסט של הגרסה שנבחרה (5 המילים הנאמרות
   הראשונות; הוראות לא מנוקדות ב-<small>/בסוגריים מדולגות). זה זול: הטקסט
   כבר נמשך בשלב 3.
5. ‏cache בדיסק לכל תשובה, השהיה בין בקשות וניסיונות חוזרים — הלקוח של
   tools/survey_siddur.py (מימוש יחיד). שגיאת רשת ⇐ לא נכתב פלט.

הפונקציות הטהורות (schema_leaves, match_rule, slugify, first_words, build_tree,
choose_version, dump_catalog) נבדקות בלי רשת ב-tests/test_siddur_catalog.py.
"""

import argparse
import importlib.util
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OVERRIDES_PATH = ROOT / "data" / "siddur" / "overrides.json"
CATALOG_OUT = ROOT / "data" / "siddur" / "catalog.json"
FIRST_WORDS = 5
SCHEMA_VERSION = 1

_SPEC = importlib.util.spec_from_file_location(
    "survey_siddur", Path(__file__).resolve().parent / "survey_siddur.py")
sv = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sv)


# =============================================================================
# טהור (בלי רשת)
# =============================================================================

def schema_leaves(schema: dict, index_title: str) -> list:
    """schema (מורכב) ⇐ רשימת עלים לפי הסדר.

    לכל עלה: ‏path — הכותרים האנגליים מהשורש (בלי השורש, בלי צמתי default),
    כמו שהם; ‏he — הכותרים העבריים המקבילים; ‏ids — מזהה ייחודי לכל צומת בנתיב
    (שני אחים עם אותו כותר הם צמתים שונים); ‏ref; ‏depth — עומק הטקסט בעלה.
    """
    out = []
    counter = [0]

    def visit(node, path, he, ids):
        counter[0] += 1
        nid = counter[0]
        children = node.get("nodes")
        if node is not schema and not sv.is_default_node(node):
            en, he_t = sv.node_titles(node)
            path, he, ids = path + [en], he + [he_t], ids + [nid]
        if isinstance(children, list) and children:
            for ch in children:
                visit(ch, path, he, ids)
            return
        out.append({"path": path, "he": he, "ids": ids,
                    "ref": sv.build_ref(index_title, path),
                    "depth": node.get("depth") or 1})

    visit(schema, [], [], [])
    return out


def match_rule(rules: list, path: list):
    """הכלל עם הקידומת הארוכה ביותר של path (השוואה מדויקת של כותרים), או None."""
    best = None
    for r in rules:
        rp = r["path"]
        if len(rp) <= len(path) and path[:len(rp)] == rp:
            if best is None or len(rp) > len(best["path"]):
                best = r
    return best


def slugify(title: str) -> str:
    """כותר אנגלי ⇐ מפתח ASCII יציב: ‏"Mourner's Kaddish" ⇐ "mourners-kaddish"."""
    s = unicodedata.normalize("NFKD", title or "")
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = s.replace("&", " and ").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "node"


def unique_key(base: str, taken: set) -> str:
    key, n = base, 2
    while key in taken:
        key, n = f"{base}-{n}", n + 1
    taken.add(key)
    return key


def has_text(text) -> bool:
    return any(s.strip() for s in sv.flatten_strings(text))


_TAG_RE = re.compile(r"<[^>]+>")
_SMALL_RE = re.compile(r"<small[^>]*>(.*?)</small>", re.S | re.I)
_PAREN_RE = re.compile(r"\(([^()]*)\)")
_BRACKET_RE = re.compile(r"\[([^\[\]]*)\]")
_NIQQUD_RE = re.compile(r"[ְ-ׇּׁׂ]")
_TAAMIM_RE = re.compile(r"[֑-֯]")
_HEB_RE = re.compile(r"[א-ת]")
# שם ה׳ לא מנוקד (גם עם תחילית) — בדעת אשכנז נאמר בפועל (8.4, ‏8.21)
_SPOKEN_UNVOCALIZED_RE = re.compile(r"^[ובכלמשה]{0,2}(ה'|יי)$")
_EDGE_PUNCT = ".,:;?!()[]{}\"“”״-–—\u05C3\u05C0"


def _keep_if_vocalized(m) -> str:
    inner = m.group(1)
    return " " + inner + " " if _NIQQUD_RE.search(_TAG_RE.sub("", inner)) else " "


def first_words(text, n: int = FIRST_WORDS) -> str:
    """המילים הנאמרות הראשונות בטקסט של עלה (לחיפוש "לפי מילים ראשונות").

    מדלג על הוראות לפי הכלל מהסקר (8.4): תוכן <small>/סוגריים לא מנוקד ⇐
    הוראה; מילה נספרת רק אם יש בה ניקוד (או שהיא ‏ה'/יי — שם ה׳ שנאמר).
    הטעמים מוסרים (הניקוד נשמר) — זו תצוגה, לא טקסט יישור.
    """
    words = []
    for s in sv.flatten_strings(text):
        s = unicodedata.normalize("NFC", s)
        s = _SMALL_RE.sub(_keep_if_vocalized, s)
        s = _TAG_RE.sub(" ", s).replace("&nbsp;", " ")
        s = _PAREN_RE.sub(_keep_if_vocalized, s)
        s = _BRACKET_RE.sub(_keep_if_vocalized, s)
        for tok in s.split():
            tok = _TAAMIM_RE.sub("", tok).strip(_EDGE_PUNCT).lstrip("'׳")
            if not _HEB_RE.search(tok):
                continue
            bare = sv.strip_marks(tok).replace("׳", "'")
            if _NIQQUD_RE.search(tok) or _SPOKEN_UNVOCALIZED_RE.match(bare):
                words.append(tok)
                if len(words) >= n:
                    return " ".join(words)
    return " ".join(words)


def choose_version(policy: dict, day: str, with_text: list):
    """(הגרסה שנבחרה או None, שאר הגרסאות מהמדיניות שיש בהן טקסט, לפי הסדר)."""
    prefs = policy.get(day) or policy["*"]
    avail = [v for v in prefs if v in with_text]
    return (avail[0] if avail else None), avail[1:]


def build_tree(leaves: list, day_types: list) -> list:
    """עלים (עם day/strip/meta שכבר הוצמדו) ⇐ ילדי הנוסח: סוגי יום ← תפילה ← ….

    leaves: [{path, he, ids, ref, depth, day, strip, leaf: {...שדות העלה}}].
    הסדר — סדר סוגי היום ב-day_types, ובתוך כל סוג יום סדר ההופעה ב-Sefaria.
    צומת ביניים מזוהה לפי ids (לא לפי כותר), כך שאחים עם אותו כותר נשארים
    נפרדים; המפתח מקבל סיומת ‎-2/-3 כשצריך.
    """
    days = {}
    for lf in leaves:
        day = lf["day"]
        if day not in days:
            dt = next(d for d in day_types if d["key"] == day)
            days[day] = {"node": {"key": dt["key"], "title": dt["title"],
                                  "heTitle": dt["heTitle"], "children": []},
                         "taken": set(), "by_id": {}}
        cur = days[day]
        strip = lf.get("strip", 0)
        if strip >= len(lf["path"]):
            raise ValueError(f"strip={strip} בולע את העלה עצמו: {lf['ref']}")
        steps = list(zip(lf["path"], lf["he"], lf["ids"]))[strip:]
        parent, taken, by_id = cur["node"], cur["taken"], cur["by_id"]
        for i, (en, he, nid) in enumerate(steps):
            last = i == len(steps) - 1
            if nid in by_id:
                parent, taken, by_id = by_id[nid]
                continue
            key = unique_key(slugify(en), taken)
            node = {"key": key, "title": en.strip(), "heTitle": he.strip()}
            if last:
                node.update(lf["leaf"])
                parent["children"].append(node)
            else:
                node["children"] = []
                parent["children"].append(node)
                sub = (node, set(), {})
                by_id[nid] = sub
                parent, taken, by_id = sub
    order = [d["key"] for d in day_types]
    return [days[k]["node"] for k in order if k in days]


def _dump(node, indent, out):
    pad = " " * indent
    if "children" not in node:
        out.append(pad + json.dumps(node, ensure_ascii=False))
        return
    head = {k: v for k, v in node.items() if k != "children"}
    body = json.dumps(head, ensure_ascii=False)[:-1]
    out.append(pad + body + ', "children": [')
    for i, ch in enumerate(node["children"]):
        _dump(ch, indent + 1, out)
        if i < len(node["children"]) - 1:
            out[-1] += ","
    out.append(pad + "]}")


def dump_catalog(catalog: dict) -> str:
    """JSON קומפקטי וקריא לסקירה: כל עלה בשורה אחת, הזחה לפי עומק."""
    head = {k: v for k, v in catalog.items() if k != "nusachim"}
    lines = ["{"]
    for k, v in head.items():
        lines.append(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},")
    lines.append(' "nusachim": [')
    for i, n in enumerate(catalog["nusachim"]):
        _dump(n, 2, lines)
        if i < len(catalog["nusachim"]) - 1:
            lines[-1] += ","
    lines.append(" ]")
    lines.append("}")
    text = "\n".join(lines) + "\n"
    json.loads(text)  # הגנה: הפלט חייב להיות JSON תקין וזהה
    return text


# =============================================================================
# רשת
# =============================================================================

class BuildError(RuntimeError):
    pass


def fetch_schema(client, index_title: str) -> dict:
    data, src = sv.fetch_index_record(client, index_title)
    if not data or not isinstance(data.get("schema"), dict):
        raise BuildError(f"לא הושג schema ל-{index_title} ({src})")
    return data["schema"]


class NoText(Exception):
    """‏Sefaria עונה 404 "We have no text for <ref>" — העלה קיים ב-schema אבל
    אין לו טקסט באף גרסה. זה מצב נתונים (⇐ unavailable), לא תקלה."""


def _v3(client, ref, version_title=None):
    st, data = sv.fetch_text(client, ref, version_title)
    if (st == 404 and isinstance(data, dict)
            and str(data.get("error", "")).startswith("We have no text for")):
        raise NoText(data["error"])
    if st != 200 or not isinstance(data, dict):
        raise BuildError(f"api/v3/texts נכשל ({st}) ל-{ref!r}"
                         + (f" [{version_title!r}]" if version_title else ""))
    return data


def probe_leaf(client, ref: str, versions: dict, policy_ids: list) -> dict:
    """בדיקת זמינות אמיתית לעלה אחד.

    מחזיר {with_text: [ids], texts: {id: text}, listed: [ids], other: [titles],
    licenses: {id: license}, he_titles: {id: …}, warnings: [...]}.
    """
    try:
        data = _v3(client, ref)
    except NoText:
        return {"with_text": [], "texts": {}, "listed": [], "other": [],
                "licenses": {}, "he_titles": {}, "warnings": [],
                "no_text": True}
    he_avail = {}
    for v in data.get("available_versions") or []:
        if isinstance(v, dict) and v.get("language") == "he":
            he_avail[v.get("versionTitle")] = v
    title_to_id = {versions[i]: i for i in policy_ids}
    res = {"with_text": [], "texts": {}, "listed": [], "other": [],
           "licenses": {}, "he_titles": {}, "warnings": []}
    res["other"] = sorted(t for t in he_avail if t not in title_to_id)
    default = (data.get("versions") or [None])[0]
    for vid in policy_ids:
        vt = versions[vid]
        if vt not in he_avail:
            continue
        res["listed"].append(vid)
        lic = he_avail[vt].get("license")
        if lic:
            res["licenses"][vid] = lic
        if isinstance(default, dict) and default.get("versionTitle") == vt:
            vobj = default
        else:
            try:
                d2 = _v3(client, ref, vt)
            except NoText:
                d2 = {}
            vs = d2.get("versions") or []
            vobj = vs[0] if vs and isinstance(vs[0], dict) else None
        if vobj and vobj.get("versionTitle") == vt and has_text(vobj.get("text")):
            res["with_text"].append(vid)
            res["texts"][vid] = vobj.get("text")
            if vobj.get("versionTitleInHebrew"):
                res["he_titles"][vid] = vobj["versionTitleInHebrew"]
            if vobj.get("license"):
                res["licenses"][vid] = vobj["license"]
        else:
            res["warnings"].append(f"{vt!r} ב-available_versions אך בלי טקסט")
    return res


def build_nusach(client, cfg: dict, day_types: list, log) -> tuple:
    index = cfg["index"]
    schema = fetch_schema(client, index)
    leaves = schema_leaves(schema, index)
    versions = cfg["versions"]
    policy = cfg["policy"]
    policy_ids = list(versions)
    lic_seen, he_seen = {}, {}
    unmatched, warnings, unavailable = [], [], []
    for n, lf in enumerate(leaves, 1):
        rule = match_rule(cfg["rules"], lf["path"])
        if rule is None:
            unmatched.append(" › ".join(lf["path"]))
            continue
        lf["day"], lf["strip"] = rule["day"], rule.get("strip", 0)
        pr = probe_leaf(client, lf["ref"], versions, policy_ids)
        for vid, lic in pr["licenses"].items():
            lic_seen.setdefault(vid, set()).add(lic)
        he_seen.update(pr["he_titles"])
        warnings += [f"{lf['ref']}: {w}" for w in pr["warnings"]]
        chosen, alt = choose_version(policy, lf["day"], pr["with_text"])
        leaf = {"ref": lf["ref"], "v": chosen}
        if alt:
            leaf["alt"] = alt
        if chosen:
            fw = first_words(pr["texts"][chosen])
            if fw:
                leaf["first"] = fw
        else:
            leaf["unavailable"] = True
            if pr.get("no_text"):
                leaf["note"] = "Sefaria: 404 'We have no text' — אין טקסט באף גרסה"
            elif pr["other"]:
                leaf["note"] = "יש טקסט רק בגרסאות שמחוץ למדיניות: " + ", ".join(
                    repr(t) for t in pr["other"])
            unavailable.append(lf["ref"])
        if lf["depth"] != 1:
            leaf["depth"] = lf["depth"]
        lf["leaf"] = leaf
        if n % 50 == 0:
            log(f"  {index}: {n}/{len(leaves)} עלים")
    if unmatched:
        raise BuildError(f"{index}: עלים בלי כלל סוג-יום ב-overrides.json:\n  "
                         + "\n  ".join(unmatched))
    for vid, lics in lic_seen.items():
        if len(lics) > 1:
            warnings.append(f"{index}: לגרסה {versions[vid]!r} כמה רישיונות: {sorted(lics)}")
    days = build_tree(leaves, day_types)
    ver_out = {}
    for vid, vt in versions.items():
        ver_out[vid] = {"title": vt,
                        "license": ", ".join(sorted(lic_seen.get(vid, []))) or "unknown"}
        if vid in he_seen:
            ver_out[vid]["heTitle"] = he_seen[vid]
    # refs משותפים (אחים עם אותו כותר ב-Sefaria — ה-ref מחזיר את הראשון)
    by_ref = {}
    for lf in leaves:
        by_ref.setdefault(lf["ref"], 0)
        by_ref[lf["ref"]] += 1
    shared = sorted(r for r, c in by_ref.items() if c > 1)
    node = {"key": cfg["key"], "title": cfg["title"], "heTitle": cfg["heTitle"],
            "index": index, "versions": ver_out, "policy": policy,
            "children": days}
    return node, {"warnings": warnings, "unavailable": unavailable,
                  "shared_refs": shared}


def nusach_stats(node: dict) -> dict:
    def leaves(n):
        if "children" not in n:
            yield n
            return
        for c in n["children"]:
            yield from leaves(c)

    days = {}
    for d in node["children"]:
        ls = list(leaves(d))
        per_v = {}
        for lf in ls:
            per_v[lf.get("v") or "-"] = per_v.get(lf.get("v") or "-", 0) + 1
        days[d["key"]] = {"prayers": len(d["children"]), "leaves": len(ls),
                          "by_version": per_v}
    all_l = list(leaves(node))
    per_v = {}
    for lf in all_l:
        per_v[lf.get("v") or "-"] = per_v.get(lf.get("v") or "-", 0) + 1
    with_alt = {}
    for lf in all_l:
        for a in [lf.get("v")] + lf.get("alt", []):
            if a:
                with_alt[a] = with_alt.get(a, 0) + 1
    return {"day_types": len(node["children"]),
            "prayers": sum(len(d["children"]) for d in node["children"]),
            "leaves": len(all_l),
            "available": sum(1 for lf in all_l if lf.get("v")),
            "chosen_by_version": per_v, "has_text_by_version": with_alt,
            "with_first_words": sum(1 for lf in all_l if lf.get("first")),
            "days": days}


def main(argv=None):
    ap = argparse.ArgumentParser(description="בניית קטלוג הסידור (PLAN_TEFILA.md 4.2.1)")
    ap.add_argument("--overrides", default=str(OVERRIDES_PATH))
    ap.add_argument("--out", default=str(CATALOG_OUT))
    ap.add_argument("--nusach", help="רק נוסח אחד (לפי key) — לבדיקה")
    ap.add_argument("--delay", type=float, default=0.5,
                    help="שניות בין בקשות רשת (נימוס כלפי Sefaria)")
    ap.add_argument("--cache-dir", default=str(Path.home() / ".cache"
                                               / "kriat-hatora-sefaria-catalog"))
    ap.add_argument("--offline", action="store_true", help="רק מה-cache")
    ap.add_argument("--base", default=sv.SEFARIA_BASE)
    args = ap.parse_args(argv)

    cfg = json.loads(Path(args.overrides).read_text(encoding="utf-8"))
    client = sv.Client(args.base, args.cache_dir, delay=args.delay,
                       offline=args.offline)
    log = lambda m: print(m, flush=True)  # noqa: E731
    nusachim, report = [], {}
    try:
        for ncfg in cfg["nusachim"]:
            if args.nusach and ncfg["key"] != args.nusach:
                continue
            log(f"⏳ {ncfg['index']}")
            node, rep = build_nusach(client, ncfg, cfg["day_types"], log)
            nusachim.append(node)
            report[ncfg["key"]] = rep
    except BuildError as e:
        print(f"✗ {e}\nבקשות רשת: {client.n_network}, מה-cache: {client.n_cached}")
        print("✗ לא נכתב פלט.")
        return 1

    stats = {n["key"]: nusach_stats(n) for n in nusachim}
    catalog = {
        "schema_version": SCHEMA_VERSION,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": args.base,
        "about": ("קטלוג הסידור (PLAN_TEFILA.md 4.2.1): נוסח ← סוג יום ← תפילה ← קטע. "
                  "ref + גרסה לכל קטע; הטקסט נמשך בזמן ריצה, עלה אחרי עלה. "
                  "נבנה ע״י tools/build_siddur_catalog.py מתוך data/siddur/overrides.json. "
                  "מדיניות הגרסאות = ההמלצה בשלב 2 — טרם הוכרעה ע״י בעל הפרויקט."),
        "day_types": cfg["day_types"],
        "shared_refs": sorted(r for rep in report.values() for r in rep["shared_refs"]),
        "stats": stats,
        "nusachim": nusachim,
    }
    text = dump_catalog(catalog)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    log(f"✅ נכתב: {args.out} ({len(text.encode('utf-8')):,} בתים)")
    for key, st in stats.items():
        log(f"• {key}: סוגי יום {st['day_types']}, תפילות {st['prayers']}, "
            f"עלים {st['leaves']}, זמינים {st['available']}, "
            f"נבחרו {st['chosen_by_version']}, יש טקסט {st['has_text_by_version']}")
        rep = report[key]
        for r in rep["unavailable"]:
            log(f"    לא זמין: {r}")
        for r in rep["shared_refs"]:
            log(f"    ref משותף לכמה צמתים: {r}")
        for w in rep["warnings"]:
            log(f"    ⚠️ {w}")
    log(f"בקשות רשת: {client.n_network}, מה-cache: {client.n_cached}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
