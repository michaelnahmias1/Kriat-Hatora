# -*- coding: utf-8 -*-
""""מה אומרים היום?" — בחירת היום לתוספות תלויות-יום (PLAN_TEFILA.md 4.4.2).

אין כאן מנוע לוח שנה (8.14 — הוחלט: מתגים ידניים). המשתמש בוחר סוג יום
(‏preset) ועונה, ויכול להדליק/לכבות כל תנאי לבד; התוצאה היא קבוצת התנאים
(‏slugs של src/siddur/markup.py) שמתקיימים היום. התוספות עצמן וזיהוין —
markup.classify_leaf; ההחלטה אם תוספת נאמרת — markup.is_enabled.

ברירת המחדל (בלי בחירה): לפי סוג היום של הקטע בקטלוג (ימי חול ⇐ יום חול
רגיל, שבת ⇐ שבת, ראש חודש ⇐ ראש חודש, חגים ⇐ יום טוב / החג שבשם הקטע,
חנוכה ופורים ⇐ לפי השם, תעניות ⇐ תענית ציבור / תשעה באב). **עונה — אין
ברירת מחדל**: קיץ/חורף נבחרים במפורש; עד אז שני הנוסחים (מוריד הטל / משיב
הרוח, ותן ברכה / ותן טל ומטר) מוצגים באפור ולא מסונכרנים, והתשובה מבקשת
לבחור (‏needs_choice). כך גם יום בשבוע (שיר של יום) וחג (כשנבחר "יום טוב"
או "חול המועד" בלי לומר איזה).
"""

from .markup import CONDITION_GROUPS, CONDITION_LABELS, GROUP_OF

# (מפתח, תווית, התנאים שמתקיימים ביום כזה) — הסדר הוא סדר התפריט
DAY_PRESETS = [
    ("weekday", "יום חול רגיל", ()),
    ("shabbat", "שבת", ("shabbat", "no-tachanun")),
    ("rosh-chodesh", "ראש חודש", ("rosh-chodesh", "no-tachanun", "half-hallel")),
    ("aseret-yemei-teshuva", "עשרת ימי תשובה (יום חול)", ("aseret-yemei-teshuva",)),
    ("chanukah", "חנוכה", ("chanukah", "no-tachanun")),
    ("purim", "פורים", ("purim", "no-tachanun")),
    ("taanit", "תענית ציבור", ("taanit",)),
    ("tisha-bav", "תשעה באב", ("tisha-bav", "taanit", "no-tachanun")),
    ("chol-hamoed", "חול המועד", ("chol-hamoed", "no-tachanun")),
    ("chol-hamoed-pesach", "חול המועד פסח",
     ("chol-hamoed", "chol-hamoed-pesach", "pesach", "no-tachanun", "half-hallel")),
    ("chol-hamoed-sukkot", "חול המועד סוכות",
     ("chol-hamoed", "chol-hamoed-sukkot", "sukkot", "no-tachanun")),
    ("yom-tov", "יום טוב", ("yom-tov", "no-tachanun")),
    ("pesach", "פסח (יום טוב)", ("yom-tov", "pesach", "no-tachanun")),
    ("shavuot", "שבועות", ("yom-tov", "shavuot", "no-tachanun")),
    ("sukkot", "סוכות (יום טוב)", ("yom-tov", "sukkot", "no-tachanun")),
    ("shemini-atzeret", "שמיני עצרת / שמחת תורה",
     ("yom-tov", "shemini-atzeret", "no-tachanun")),
    ("rosh-hashana", "ראש השנה",
     ("rosh-hashana", "aseret-yemei-teshuva", "yom-tov", "no-tachanun")),
    ("yom-kippur", "יום כיפור", ("yom-kippur", "aseret-yemei-teshuva", "no-tachanun")),
]
PRESETS = {k: (label, frozenset(slugs)) for k, label, slugs in DAY_PRESETS}

# עונה: מוריד הטל/משיב הרוח מתחלפים בפסח ובשמיני עצרת; ותן ברכה/ותן טל ומטר
# — בפסח ובז' בחשוון (בחו"ל ב-4/5 בדצמבר). בין שמיני עצרת לז' בחשוון: משיב
# הרוח + ותן ברכה.
SEASONS = [
    ("summer", "קיץ — מוריד הטל, ותן ברכה", ("morid-hatal", "veten-bracha")),
    ("winter", "חורף — משיב הרוח, ותן טל ומטר", ("mashiv-haruach", "tal-umatar")),
    ("between", "משמיני עצרת עד ז׳ בחשוון — משיב הרוח, ותן ברכה",
     ("mashiv-haruach", "veten-bracha")),
]
SEASON_SLUGS = {k: frozenset(s) for k, _, s in SEASONS}
SEASON_GROUPS = ("gevurot", "barech")
CHOICE_LABELS = {
    "season": "קיץ או חורף? (מוריד הטל / משיב הרוח, ותן ברכה / ותן טל ומטר)",
    "dow": "איזה יום בשבוע? (שיר של יום)",
    "chag": "איזה חג?",
}


def _titles(cat, keys) -> str:
    out = []
    for i in range(1, len(keys) + 1):
        node = cat.node(keys[:i]) or {}
        out += [node.get("heTitle", ""), node.get("title", "").lower(),
                keys[i - 1]]
    return " ".join(out)


def leaf_day(cat, keys) -> str:
    """סוג היום שמתאים לקטע לפי מקומו בקטלוג — ברירת המחדל של "מה היום"."""
    day_type = keys[1] if len(keys) > 1 else ""
    t = _titles(cat, keys)

    def has(*words):
        return any(w in t for w in words)

    if day_type == "shabbat":
        return "shabbat"
    if day_type == "rosh-chodesh":
        return "rosh-chodesh"
    if day_type == "chanukah-purim":
        return "purim" if has("פורים", "purim") else "chanukah"
    if day_type == "fasts":
        return "tisha-bav" if has("תשעה באב", "ט' באב", "tisha") else "taanit"
    if day_type == "festivals":
        if has("שמיני עצרת", "שמחת תורה", "shemini", "simchat", "גשם", "rain"):
            return "shemini-atzeret"
        if has("סוכות", "סכות", "sukkot", "לולב", "lulav", "הושענות"):
            return "sukkot"
        if has("שבועות", "shavuot"):
            return "shavuot"
        if has("פסח", "pesach", "passover", "טל", "dew"):
            return "pesach"
        return "yom-tov"
    return "weekday"


def _split(raw) -> list:
    return [x.strip() for x in str(raw or "").split(",") if x.strip()]


def resolve(q: dict, cat, keys) -> dict:
    """פרמטרי השאילתה ⇐ היום שנבחר. ‏ValueError (עברית) על ערך לא מוכר.

    ‏day=<preset>|auto — סוג יום (בלי / auto ⇐ לפי הקטע); ‏season=summer|
    winter|between — עונה; ‏days=a,b,-c — תנאים להדליק (a) ולכבות (-c) מעל
    סוג היום. ‏days בלי day ⇐ הקבוצה המדויקת (בלי ברירת מחדל של הקטע).
    ‏explicit — הבקשה הגיעה מממשק שמכיר את התוספות (יש day/days/season)."""
    raw_day = (q.get("day") or "").strip()
    day_items = _split(q.get("days"))
    season = (q.get("season") or "").strip() or None
    explicit = any(k in q for k in ("day", "days", "season"))
    if season is not None and season not in SEASON_SLUGS:
        raise ValueError(f"עונה לא מוכרת: {season}")
    auto = raw_day in ("", "auto")
    if not auto and raw_day not in PRESETS:
        raise ValueError(f"סוג יום לא מוכר: {raw_day}")
    for item in day_items:
        slug = item[1:] if item.startswith("-") else item
        if slug not in CONDITION_LABELS:
            raise ValueError(f"תנאי לא מוכר: {slug}")
    if auto and day_items and "day" not in q:
        day, enabled = None, set()          # ‏days לבד — הקבוצה המדויקת
    else:
        day = leaf_day(cat, keys) if auto else raw_day
        enabled = set(PRESETS[day][1])
    if season:
        enabled -= {s for g in SEASON_GROUPS for s in CONDITION_GROUPS[g]}
        enabled |= SEASON_SLUGS[season]
    for item in day_items:
        if item.startswith("-"):
            enabled.discard(item[1:])
        else:
            enabled.add(item)
    return {"day": day, "auto": auto and day is not None, "season": season,
            "enabled": enabled, "explicit": explicit}


def auto_for_range(any_alts: list, sel: dict) -> dict:
    """ברירת מחדל (‏auto) כשכל הטקסט הנאמר בטווח הוא תוספת — למשל הקיצור
    "אבינו מלכנו" בעדות המזרח, שהוא פסקאות של עשי"ת בתוך העמידה: מי שבחר
    בו רוצה לסנכרן אותו. היום ⇐ סוג היום הקטן ביותר שמדליק את התוספת
    הראשונה (‏any_alts — ה-"any" של התנאי שלה); אין כזה (עונה) ⇐ התנאים
    שלה עצמם. תוספת מקבוצה של בחירה אחת (שיר של יום, קיץ/חורף) — לא
    מנחשים."""
    if not sel["auto"] or not any_alts:
        return sel
    if any(GROUP_OF.get(s) for alt in any_alts for s in alt):
        # בחירה אחת מתוך כמה (יום בשבוע, עונה, איזה חג) — לא מנחשים; התשובה
        # מבקשת לבחור (‏needs_choice)
        return sel
    best = None
    for alt in any_alts:
        for key, _, slugs in DAY_PRESETS:
            if set(alt) <= set(slugs) and (best is None or len(slugs) < len(best[1])):
                best = (key, slugs)
    if best:
        enabled = set(best[1]) | (sel["enabled"] & {
            s for g in SEASON_GROUPS for s in CONDITION_GROUPS[g]})
        return dict(sel, day=best[0], enabled=enabled)
    return dict(sel, enabled=sel["enabled"] | set(any_alts[0]))


def summary(conds: list, sel: dict) -> dict:
    """התנאים של התוספות בטווח (‏conds — רשימת slugs לכל יחידה) ⇐ השדות
    בתשובה: ‏conditions (מתג לכל תנאי), ‏needs_choice, ‏day, ‏season, ‏days."""
    count = {}
    for slugs in conds:
        for s in slugs:
            count[s] = count.get(s, 0) + 1
    enabled = sel["enabled"]
    conditions = [{"slug": s, "label": CONDITION_LABELS[s], "count": count[s],
                   "enabled": s in enabled,
                   **({"group": g} if (g := _group(s)) else {})}
                  for s in CONDITION_LABELS if s in count]
    present = set(count)
    needs = []
    if any(present & set(CONDITION_GROUPS[g]) and
           not enabled & set(CONDITION_GROUPS[g]) for g in SEASON_GROUPS):
        needs.append("season")
    if present & set(CONDITION_GROUPS["dow"]) and \
            not enabled & set(CONDITION_GROUPS["dow"]):
        needs.append("dow")
    if present & set(CONDITION_GROUPS["chag"]) and \
            not enabled & set(CONDITION_GROUPS["chag"]) and \
            enabled & {"yom-tov", "chol-hamoed"}:
        needs.append("chag")
    day = sel["day"]
    return {
        "day": day and {"key": day, "label": PRESETS[day][0], "auto": sel["auto"]},
        "season": sel["season"],
        "days": sorted(enabled),
        "conditions": conditions,
        "needs_choice": [{"group": g, "label": CHOICE_LABELS[g]} for g in needs],
        "presets": [{"key": k, "label": label} for k, label, _ in DAY_PRESETS],
        "seasons": [{"key": k, "label": label} for k, label, _ in SEASONS],
    }


def _group(slug: str):
    for g, members in CONDITION_GROUPS.items():
        if slug in members:
            return "season" if g in SEASON_GROUPS else g
    return None
