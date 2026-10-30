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
   הראשונות; הוראות מדולגות לפי src/siddur/markup.py — אותו מימוש שמסווג
   הוראות ב-api/siddur.py). זה זול: הטקסט כבר נמשך בשלב 3.
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
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OVERRIDES_PATH = ROOT / "data" / "siddur" / "overrides.json"
CATALOG_OUT = ROOT / "data" / "siddur" / "catalog.json"
FIRST_WORDS = 5
SCHEMA_VERSION = 1

sys.path.insert(0, str(ROOT / "src"))
from siddur import markup  # noqa: E402
from siddur import wikisource as ws  # noqa: E402

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


def first_words(text, n: int = FIRST_WORDS) -> str:
    """המילים הנאמרות הראשונות בטקסט של עלה (לחיפוש "לפי מילים ראשונות").

    המימוש היחיד חי ב-src/siddur/markup.py (משותף ל-api/siddur.py): הוראות
    מדולגות לפי הכלל מהסקר (8.4), ונספרות רק מילים מנוקדות או שם ה׳.
    הטעמים מוסרים (הניקוד נשמר) — זו תצוגה, לא טקסט יישור.
    """
    return markup.first_words(text, n)


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
            if lf.get("collection") and lf["collection"][0] == i:
                node["collection"] = lf["collection"][1]  # אוסף (4.4.1)
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
        if rule.get("collection"):  # הצומת של הכלל הוא אוסף (הגדה בסידור ספרד)
            lf["collection"] = (len(rule["path"]) - lf["strip"] - 1,
                                rule["collection"])
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


# =============================================================================
# אוספים: מחזורים, סליחות, קינות והגדה (PLAN_TEFILA.md 4.4.1)
# =============================================================================
#
# אוסף = ספר שלם (מחזור לראש השנה, סליחות…) שנכנס לנוסח כתת-עץ מתחת לסוג יום,
# מספר מקורות ("parts"): אינדקס של Sefaria, או דף בוויקיטקסט בגרסה קבועה. כל
# אוסף מקבל מהדורה משלו (‏collection_versions ב-overrides.json) — עם רישיון,
# מקור וקישור, כי כל עלה באפליקציה מציג שורת מקור ורישיון.
#
# כלל הכיסוי (החלטת בעל הפרויקט, 29.10.2026): אוסף נכנס **רק** אם יש לו מהדורה
# ברישיון פתוח בעדות המזרח **וגם** באשכנז או בספרד (‏check_coverage — הבנייה
# נכשלת אחרת). רישיון שאינו CC0 / Public Domain / CC-BY / CC-BY-SA ⇐ נכשלת.

ALLOWED_LICENSES = ("CC0", "Public Domain", "CC-BY", "CC-BY-SA")
WIKISOURCE_BASE = "https://he.wikisource.org"
WIKISOURCE_API_PATH = "/w/api.php"
CHAPTER_TITLE_WORDS = 4

_TRANSLIT = {"א": "a", "ב": "b", "ג": "g", "ד": "d", "ה": "h", "ו": "v",
             "ז": "z", "ח": "ch", "ט": "t", "י": "y", "כ": "k", "ך": "k",
             "ל": "l", "מ": "m", "ם": "m", "נ": "n", "ן": "n", "ס": "s",
             "ע": "a", "פ": "p", "ף": "p", "צ": "tz", "ץ": "tz", "ק": "k",
             "ר": "r", "ש": "sh", "ת": "t"}
_MARKS_RE = re.compile("[֑-ׇ]")
# "א. פתיחה. מיוסד על פי א"ב" ⇐ סוג הסליחה, לכותרת העלה
_SELICHA_KIND_RE = re.compile(r'^\s*[א-ת"׳״]{1,4}\.\s*([א-ת]+)')
_SELICHA_KINDS = frozenset("פתיחה שניה שלישיה שלמונית פזמון עקדה תחנה חטאנו "
                           "פיוט סליחה תוכחה גמר מוסתג".split())


def he_slug(title: str) -> str:
    """כותרת עברית ⇐ מפתח ASCII יציב (תעתיק פשוט): ‏"כל נדרי" ⇐ "kl-ndry"."""
    s = _MARKS_RE.sub("", unicodedata.normalize("NFC", title or ""))
    return slugify("".join(_TRANSLIT.get(ch, ch if ch.isascii() else " ")
                           for ch in s))


def plain_title(text: str) -> str:
    """בלי ניקוד וטעמים, רווחים אחידים — כמו שאר הכותרות בקטלוג."""
    s = unicodedata.normalize("NFC", text or "").replace("־", " ")  # מקף ⇐ רווח
    s = re.sub("[\u200b-\u200f\u2060\ufeff]", "", _MARKS_RE.sub("", s))
    return re.sub(r"\s+", " ", s).strip()


def chapter_title(paragraphs, n: int = CHAPTER_TITLE_WORDS) -> str:
    """כותרת לפרק של סליחות/קינות (ב-Sefaria לפרקים אין שם): המילים הנאמרות
    הראשונות של הפסקה הנאמרת הראשונה שיש בה לפחות n מילים (כך "אֱלֹהֵינוּ
    וֵאלֹהֵי אֲבוֹתֵינוּ" שלפני כל סליחה לא נהיה שם של כולן), ובראשה סוג הסליחה
    כשהוראת הכותרת אומרת אותו ("פתיחה: …")."""
    kind, words, fallback = None, None, None
    for para in markup.flatten(paragraphs):
        for k, body in markup.classify_paragraph(para):
            if k != markup.SPOKEN:
                if kind is None and words is None:
                    m = _SELICHA_KIND_RE.match(body)
                    if m and m.group(1) in _SELICHA_KINDS:
                        kind = m.group(1)
                continue
            ws = [w for w in (markup.display_word(t) for t in body.split())
                  if markup._word_class(w) in ("S", "N")]
            if fallback is None and ws:
                fallback = ws[:n]
            if len(ws) >= n:
                words = ws[:n]
                break
        if words:
            break
    words = words or fallback
    if not words:
        return ""
    title = plain_title(" ".join(words))
    return f"{kind}: {title}" if kind else title


def chapter_leaves(ref: str, vid: str, chapters: list) -> list:
    """עלה בעומק 2 (יום של סליחות, קינות) ⇐ עלה לכל פרק: ‏ref ‏"<עלה> N".
    פרק ריק (קיים במבנה של Sefaria בלי טקסט) — מושמט."""
    out = []
    for i, ch in enumerate(chapters if isinstance(chapters, list) else [], 1):
        paras = markup.flatten(ch)
        if not has_text(paras):
            continue
        leaf = {"key": str(i), "title": f"{i}",
                "heTitle": chapter_title(paras) or f"פרק {i}",
                "auto_title": True,  # בחיפוש — כמו מילים ראשונות, לא כשם
                "ref": f"{ref} {i}", "v": vid}
        fw = first_words(paras)
        if fw:
            leaf["first"] = fw
        out.append(leaf)
    return out


def _tree_children(leaves: list) -> list:
    """עלים (path/he/ids/leaf) ⇐ ילדי צומת, באותו build_tree של הסידור."""
    if not leaves:
        return []
    for lf in leaves:
        lf["day"] = "_"
    root = build_tree(leaves, [{"key": "_", "title": "_", "heTitle": "_"}])
    return root[0]["children"]


def build_sefaria_part(client, part: dict, vid: str, ver: dict, log) -> tuple:
    """חלק של אוסף מאינדקס של Sefaria ⇐ (ילדים, רישיונות, דוח).

    ‏skip — נתיבי כותרים שלא נכנסים; ‏chapters — עלה בעומק 2 מתפצל לעלה לכל
    פרק (סליחות: פרק = סליחה; קינות: פרק = קינה)."""
    index = ver["index"]
    leaves = schema_leaves(fetch_schema(client, index), index)
    skip = [list(p) for p in part.get("skip", [])]
    out, lics, rep = [], set(), {"unavailable": [], "warnings": [], "he": None}
    for lf in leaves:
        if not lf["path"]:  # ספר פשוט (בלי צמתים) — עלה אחד בשם החלק
            lf["path"], lf["he"], lf["ids"] = [part["title"]], [part["heTitle"]], [0]
        if any(lf["path"][:len(s)] == s for s in skip):
            continue
        pr = probe_leaf(client, lf["ref"], {vid: ver["title"]}, [vid])
        lics.update(pr["licenses"].values())
        rep["he"] = rep["he"] or pr["he_titles"].get(vid)
        rep["warnings"] += [f"{lf['ref']}: {w}" for w in pr["warnings"]]
        if vid not in pr["with_text"]:
            leaf = {"ref": lf["ref"], "v": None, "unavailable": True,
                    "note": ("Sefaria: 404 'We have no text'" if pr.get("no_text")
                             else "אין טקסט בעלה במהדורה של האוסף")}
            rep["unavailable"].append(lf["ref"])
        elif lf["depth"] >= 2 and part.get("chapters"):
            leaf = {"children": chapter_leaves(lf["ref"], vid, pr["texts"][vid])}
            if not leaf["children"]:
                continue
        else:
            leaf = {"ref": lf["ref"], "v": vid}
            fw = first_words(pr["texts"][vid])
            if fw:
                leaf["first"] = fw
            if lf["depth"] != 1:
                leaf["depth"] = lf["depth"]
        lf["leaf"] = leaf
        out.append(lf)
    log(f"  {index}: {len(out)} עלים/צמתים")
    return _tree_children(out), lics, rep


class WikisourceClient:
    """הדף המוצג של ויקיטקסט (/wiki/<דף>) — מוגש מה-CDN, בניגוד ל-API שמגביל
    קצב (429) לפי כתובת IP. ‏cache בדיסק לפי מספר הגרסה, השהיה בין בקשות,
    כיבוד Retry-After. הדף חייב להיות בדיוק בגרסה הקבועה שבקטלוג (‏rev): דף
    שנערך מאז ⇐ BuildError (מעדכנים rev ב-overrides.json אחרי בדיקה)."""

    def __init__(self, cache_dir, delay=2.0, offline=False, retries=6):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.delay, self.offline, self.retries = delay, offline, retries
        self._last = 0.0
        self.n_network = self.n_cached = 0

    def fetched(self, rev: int) -> str:
        """תאריך המשיכה של הדף (מה-cache) — נרשם בצילום שבגיט."""
        f = self.cache_dir / f"{int(rev)}.html"
        return datetime.fromtimestamp(f.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")

    def page_html(self, page: str, rev: int) -> str:
        f = self.cache_dir / f"{int(rev)}.html"
        if f.exists():
            self.n_cached += 1
            return f.read_text(encoding="utf-8")
        if self.offline:
            raise BuildError(f"ויקיטקסט: אין ב-cache את {page!r} (גרסה {rev}) — "
                             "הריצו בלי --offline")
        url = f"{WIKISOURCE_BASE}/wiki/" + urllib.parse.quote(page.replace(" ", "_"))
        for attempt in range(self.retries):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            req = urllib.request.Request(url, headers={"User-Agent": sv.USER_AGENT})
            try:
                self.n_network += 1
                with urllib.request.urlopen(req, timeout=60) as resp:
                    text = resp.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    time.sleep(int(e.headers.get("Retry-After") or 30) + 5)
                    continue
                raise BuildError(f"ויקיטקסט: HTTP {e.code} ל-{page!r}")
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                time.sleep(10 * (attempt + 1))
                last = e
                continue
            got = ws.page_revision(text)
            if got != int(rev):
                raise BuildError(f"ויקיטקסט: {page!r} בגרסה {got}, לא {rev} — הדף "
                                 "נערך; בדקו את השינוי ועדכנו rev ב-overrides.json")
            f.write_text(text, encoding="utf-8")
            return text
        raise BuildError(f"ויקיטקסט: לא הושג {page!r} (429/רשת) — נסו שוב מאוחר יותר")


def ws_section_tree(sections: list, include=None, under=None, skip=()) -> list:
    """רשימת הסעיפים של דף (‏action=parse&prop=sections) ⇐ עץ [{s, children}].

    ‏include — מספרי סעיפים עליונים שנכנסים (עם כל צאצאיהם); ‏under — מספר
    סעיף שילדיו הם השורש (הוא עצמו לא מוצג); ‏skip — כותרות שלא נכנסות (עם
    צאצאיהן)."""
    def num(s):
        return s["number"]

    def inside(n, top):
        return n == top or n.startswith(top + ".")

    sel = []
    for s in sections:
        n = num(s)
        if under is not None:
            if not n.startswith(under + "."):
                continue
        elif include is not None and not any(inside(n, t) for t in include):
            continue
        sel.append(s)
    skipped = [num(s) for s in sel if s["line"] in skip]
    sel = [s for s in sel if not any(inside(num(s), t) for t in skipped)]
    roots, stack = [], []
    for s in sel:
        node = {"s": s, "children": []}
        while stack and not num(s).startswith(num(stack[-1]["s"]) + "."):
            stack.pop()
        (stack[-1]["children"] if stack else roots).append(node)
        stack.append(node)
    return roots


def build_wikisource_part(wclient, part: dict, vid: str, log) -> tuple:
    """חלק של אוסף מדף בוויקיטקסט, בגרסה קבועה (‏rev) ⇐ (ילדים, דוח).

    כל סעיף ⇐ צומת: סעיף בלי תת-סעיפים ⇐ עלה; סעיף עם תת-סעיפים ⇐ תיקייה, ואם
    יש לו טקסט נאמר לפני תת-הסעיף הראשון — עלה "תחילת …" ראשון בתיקייה (ה-API
    מושך את הסעיף ועוצר בכותרת הבאה — אותו מימוש, src/siddur/wikisource.py).
    סעיף בלי שום מילה מנוקדת (דינים) — מושמט ונרשם בדוח."""
    page, rev = part["page"], int(part["rev"])
    # הדף המוצג, בגרסה הקבועה, מפוצל כאן לפי הכותרות. ה-API מושך סעיף-סעיף
    # (action=parse&oldid=…&section=…); split_page_sections מחזיר אותן פסקאות
    # (נבדק על 32 סעיפים של דף ראש השנה, 29.10.2026), ו-sections_from_html את
    # אותם מספרי סעיפים (נבדק מול prop=sections בארבעת הדפים).
    content = ws.content_html(wclient.page_html(page, rev))
    all_sections = ws.sections_from_html(content)
    try:
        texts = ws.split_page_sections(content, all_sections)
    except ws.WikisourceError as e:
        raise BuildError(f"{page}: {e}")
    tree = ws_section_tree(all_sections, part.get("include"),
                           part.get("under"), set(part.get("skip", [])))
    rep = {"skipped_no_text": [], "leaves": 0, "big": []}
    used = {}  # הסעיפים שהקטלוג משתמש בהם ⇐ צילום בגיט (ה-API לא פונה לוויקיטקסט)

    def paragraphs(s):
        return texts[str(s["index"])]

    def leaf_for(s, paras, title=None):
        leaf = {"title": s["line"], "heTitle": title or plain_title(s["line"]),
                "ref": f"{page}#{s['anchor']}", "v": vid,
                "ws": {"page": page, "rev": rev, "section": str(s["index"]),
                       "heading": s["line"], "anchor": s["anchor"]}}
        fw = first_words(paras)
        if fw:
            leaf["first"] = fw
        used[str(s["index"])] = (s["line"], paras)
        rep["leaves"] += 1
        if len(paras) > 300:
            rep["big"].append(f"{s['line']} ({len(paras)} פסקאות)")
        return leaf

    def visit(nodes, taken):
        out = []
        for nd in nodes:
            s = nd["s"]
            paras = paragraphs(s)
            spoken = markup.has_vocalized(paras)
            kids = visit(nd["children"], set())
            if nd["children"]:
                if spoken:
                    intro = leaf_for(s, paras, "תחילת " + plain_title(s["line"]))
                    intro["key"] = "intro"
                    kids.insert(0, intro)
                if not kids:
                    continue
                out.append({"key": unique_key(he_slug(s["line"]), taken),
                            "title": s["line"], "heTitle": plain_title(s["line"]),
                            "children": kids})
            elif spoken:
                leaf = leaf_for(s, paras)
                out.append({"key": unique_key(he_slug(s["line"]), taken), **leaf})
            else:
                rep["skipped_no_text"].append(s["line"])
        return out

    children = visit(tree, {"intro"})
    rep["snapshot"] = ws.make_snapshot(page, rev, wclient.fetched(rev), used)
    log(f"  ויקיטקסט {page} (גרסה {rev}): {rep['leaves']} עלים")
    return children, rep


def build_collections(client, wclient, ncfg: dict, cfg: dict, log) -> tuple:
    """האוספים של נוסח אחד ⇐ ([(סוג יום, צומת אוסף)], מהדורות לקטלוג, דוח)."""
    defs = {c["key"]: c for c in cfg.get("collections", {}).get("list", [])}
    vers = ncfg.get("collection_versions", {})
    ver_out, nodes, report = {}, [], {"warnings": [], "unavailable": [],
                                      "skipped_no_text": [], "big": []}
    for entry in ncfg.get("collections", []):
        cdef = defs.get(entry["collection"])
        if cdef is None:
            raise BuildError(f"{ncfg['key']}: אוסף לא מוגדר: {entry['collection']}")
        parts_out = []
        for part in entry["parts"]:
            vid = part["version"]
            ver = vers[vid]
            if ver["source"] == "sefaria":
                kids, lics, rep = build_sefaria_part(client, part, vid, ver, log)
                if len(lics) != 1:
                    raise BuildError(f"{ver['index']}: רישיון לא חד-משמעי {sorted(lics)}")
                lic = lics.pop()
                report["warnings"] += rep["warnings"]
                report["unavailable"] += rep["unavailable"]
                he = rep["he"]
            elif ver["source"] == "wikisource":
                kids, rep = build_wikisource_part(wclient, part, vid, log)
                lic, he = ws.LICENSE, None
                report["skipped_no_text"] += [f"{part['page']}: {t}"
                                              for t in rep["skipped_no_text"]]
                report["big"] += rep["big"]
                report.setdefault("snapshots", []).append(rep["snapshot"])
            else:
                raise BuildError(f"מקור לא מוכר: {ver['source']}")
            if lic not in ALLOWED_LICENSES:
                raise BuildError(f"{ncfg['key']}/{entry['collection']}: רישיון "
                                 f"{lic!r} אינו פתוח — לא נכנס (8.15)")
            out = {k: v for k, v in ver.items() if not k.startswith("_")}
            out["license"] = lic
            if he and "heTitle" not in out:
                out["heTitle"] = he
            prev = ver_out.get(vid)
            if prev and prev != out:
                raise BuildError(f"מהדורה {vid} מוגדרת פעמיים אחרת")
            ver_out[vid] = out
            parts_out.append((part, kids))
        if len(parts_out) == 1 and not parts_out[0][0].get("key"):
            children = parts_out[0][1]
        else:
            children = [{"key": p["key"], "title": p["title"], "heTitle": p["heTitle"],
                         "children": kids} for p, kids in parts_out]
        node = {"key": cdef["key"], "title": cdef["title"], "heTitle": cdef["heTitle"],
                "collection": cdef["key"], "children": children}
        nodes.append((cdef["day"], node))
    return nodes, ver_out, report


def attach_collections(nusach: dict, nodes: list, day_types: list):
    """מכניס את צמתי האוספים מתחת לסוג היום שלהם (יוצר אותו אם אין), בסדר
    הקבוע של סוגי היום; האוסף נכנס בסוף הרשימה של סוג היום."""
    order = [d["key"] for d in day_types]
    days = {d["key"]: d for d in nusach["children"]}
    for day, node in nodes:
        if day not in days:
            dt = next(d for d in day_types if d["key"] == day)
            days[day] = {"key": dt["key"], "title": dt["title"],
                         "heTitle": dt["heTitle"], "children": []}
        if any(c["key"] == node["key"] for c in days[day]["children"]):
            raise BuildError(f"{nusach['key']}/{day}: כבר יש צומת {node['key']}")
        days[day]["children"].append(node)
    nusach["children"] = [days[k] for k in order if k in days]


def collections_by_nusach(nusachim: list) -> dict:
    """{אוסף: [נוסחים שיש בהם צומת עם "collection" כזה ועלה זמין מתחתיו]}."""
    out = {}

    def has_leaf(n):
        if "children" not in n:
            return bool(n.get("v"))
        return any(has_leaf(c) for c in n["children"])

    def visit(n, nus):
        if n.get("collection") and has_leaf(n):
            out.setdefault(n["collection"], [])
            if nus not in out[n["collection"]]:
                out[n["collection"]].append(nus)
        for c in n.get("children", []):
            visit(c, nus)

    for nus in nusachim:
        visit(nus, nus["key"])
    return out


def check_coverage(nusachim: list, rule: dict) -> list:
    """כלל הכיסוי ⇐ רשימת הפרות (ריקה = תקין): כל אוסף בקטלוג קיים בכל
    הנוסחים של all_of ובאחד לפחות מ-any_of."""
    bad = []
    for coll, have in sorted(collections_by_nusach(nusachim).items()):
        missing = [k for k in rule.get("all_of", []) if k not in have]
        any_of = rule.get("any_of", [])
        if missing or (any_of and not any(k in have for k in any_of)):
            bad.append(f"{coll}: יש ב-{have}; נדרש {rule}")
    return bad


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
    ap.add_argument("--wikisource-cache-dir",
                    default=str(Path.home() / ".cache" / "kriat-hatora-wikisource"))
    ap.add_argument("--wikisource-snapshot-dir", default=str(ws.SNAPSHOT_DIR),
                    help="צילום הטקסט של עלי ויקיטקסט בגיט (נקרא ע״י api/siddur.py)")
    ap.add_argument("--wikisource-delay", type=float, default=2.0,
                    help="שניות בין בקשות לוויקיטקסט (מגבלת קצב — 429)")
    args = ap.parse_args(argv)

    cfg = json.loads(Path(args.overrides).read_text(encoding="utf-8"))
    client = sv.Client(args.base, args.cache_dir, delay=args.delay,
                       offline=args.offline)
    wclient = WikisourceClient(args.wikisource_cache_dir, args.wikisource_delay,
                               args.offline)
    log = lambda m: print(m, flush=True)  # noqa: E731
    nusachim, report = [], {}
    try:
        for ncfg in cfg["nusachim"]:
            if args.nusach and ncfg["key"] != args.nusach:
                continue
            log(f"⏳ {ncfg['index']}")
            node, rep = build_nusach(client, ncfg, cfg["day_types"], log)
            # אוספים (4.4.1): מחזורים, סליחות, קינות, הגדה — מתחת לסוג היום
            colls, cvers, crep = build_collections(client, wclient, ncfg, cfg, log)
            attach_collections(node, colls, cfg["day_types"])
            node["versions"].update(cvers)
            rep["warnings"] += crep["warnings"]
            rep["unavailable"] += crep["unavailable"]
            rep["collections"] = crep
            nusachim.append(node)
            report[ncfg["key"]] = rep
        if not args.nusach:
            bad = check_coverage(nusachim, cfg["collections"]["rule"])
            if bad:
                raise BuildError("כלל הכיסוי של האוספים לא מתקיים (4.4.1):\n  "
                                 + "\n  ".join(bad))
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
                  "מהדורות ברישיון פתוח בלבד (8.15). אוספים (4.4.1): מחזורים, סליחות, "
                  "קינות והגדה — מ-Sefaria או מוויקיטקסט (גרסה קבועה), רק אם קיימים "
                  "בעדות המזרח וגם באשכנז או בספרד (collections.rule)."),
        "collections": cfg["collections"]["list"],
        "coverage_rule": cfg["collections"]["rule"],
        "day_types": cfg["day_types"],
        "shared_refs": sorted(r for rep in report.values() for r in rep["shared_refs"]),
        "stats": stats,
        "nusachim": nusachim,
    }
    text = dump_catalog(catalog)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    log(f"✅ נכתב: {args.out} ({len(text.encode('utf-8')):,} בתים)")
    # צילומי ויקיטקסט (4.4.1): ה-API מגיש מהם, בלי רשת
    snaps = [sn for rep in report.values()
             for sn in (rep.get("collections") or {}).get("snapshots", [])]
    keep = set()
    for sn in snaps:
        p = ws.write_snapshot(sn, args.wikisource_snapshot_dir)
        keep.add(p.name)
        log(f"✅ צילום ויקיטקסט: {p} ({p.stat().st_size:,} בתים, "
            f"{len(sn['sections'])} סעיפים, גרסה {sn['rev']})")
    if not args.nusach:  # צילום של גרסה שכבר לא בקטלוג — נמחק
        for old in Path(args.wikisource_snapshot_dir).glob("*.json.gz"):
            if old.name not in keep:
                old.unlink()
                log(f"   נמחק צילום ישן: {old}")
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
        crep = rep.get("collections") or {}
        for t in crep.get("skipped_no_text", []):
            log(f"    הושמט (בלי ניקוד — דינים): {t}")
        for t in crep.get("big", []):
            log(f"    עלה גדול (בחירת טווח): {t}")
    log(f"אוספים לפי נוסח: {collections_by_nusach(nusachim)}")
    log(f"בקשות רשת: {client.n_network}, מה-cache: {client.n_cached}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
