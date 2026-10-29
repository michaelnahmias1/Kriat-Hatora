# -*- coding: utf-8 -*-
"""תוספות תלויות-יום — "מה אומרים היום?" (PLAN_TEFILA.md 4.4.2). בלי רשת.

זיהוי (src/siddur/markup.py ‏parse_header / classify_leaf) על תשובות Sefaria
אמיתיות שהוקלטו ב-29.10.2026 (tests/fixtures/siddur — עמידה בכל נוסח ומהדורה,
שיר של יום), בחירת היום (src/siddur/days.py), ו-/api/siddur עם day/season/days.

הרצה:  python3 -m unittest discover -s tests -v
"""

import importlib.util
import json
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "test_api_siddur_shared", Path(__file__).resolve().parent / "test_api_siddur.py")
shared = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(shared)
api = shared.api

from siddur import days, load_catalog  # noqa: E402  (api הוסיף את src)
from siddur.markup import (CONDITIONAL, INSTRUCTION, SPOKEN,  # noqa: E402
                           classify_leaf, classify_paragraph, condition_label,
                           flatten, is_enabled, parse_header)

EDOT_AMIDA = "edot-hamizrach/weekday/weekday-shacharit/amida"
SEFARD_AMIDA = "sefard/weekday/weekday-shacharit/amidah"
ASHK = "ashkenaz/weekday/shacharit/amidah/"
TE_FESTIVAL = "sefard/festivals/holidays/maariv-shacharit-and-mincha-amidah"
SONG = "sefard/weekday/weekday-shacharit/song-of-the-day"


def leaf(name: str) -> list:
    """פסקאות + סיווג של תשובה מוקלטת ⇐ [(kind, טקסט, cond)] לכל פסקה."""
    paras = flatten(shared.fixture(name)["versions"][0]["text"])
    return classify_leaf(paras)


def conds(parts) -> list:
    """[(kind, תחילת הטקסט, התנאי)] — התנאי כ-any (רשימת רשימות) או None."""
    return [(k, b, c and c["any"]) for k, b, c in parts]


# =============================================================================
# אוצר המילים של ההוראות
# =============================================================================

class TestParseHeader(unittest.TestCase):
    def any_of(self, text):
        c = parse_header(text)
        return c and (c["any"], c["negate"], c["names"])

    def test_abbreviations_and_prefixes(self):
        aty = ([["aseret-yemei-teshuva"]], False, [])
        for t in ['בעשי"ת:', "(בעשי״ת", "בעשרת ימי תשובה אומרים:",
                  "בעשרת ימי תשובה מוסיפין:", 'בעשי"ת מסיים:', 'בעשי”ת:']:
            self.assertEqual(self.any_of(t), aty, t)
        self.assertEqual(self.any_of('לר"ח:'), ([["rosh-chodesh"]], False, []))
        self.assertEqual(self.any_of("בראש חדש:"), ([["rosh-chodesh"]], False, []))
        self.assertEqual(self.any_of('בחוה"מ פסח:'), ([["chol-hamoed-pesach"]], False, []))
        self.assertEqual(self.any_of("לסכות:"), ([["sukkot"]], False, []))
        self.assertEqual(self.any_of('(ביו"ט מוסיפים:'), ([["yom-tov"]], False, []))
        self.assertEqual(self.any_of("במנחת תשעה באב:"), ([["tisha-bav"]], False, []))
        self.assertEqual(self.any_of("בשבעה עשר בתמוז אומרים"), ([["taanit"]], False, []))

    def test_or_and(self):
        # "ו" בין ימים — או; צמוד לשבת / "כשחל" — וגם
        self.assertEqual(self.any_of("בראש חדש ובחול המועד אומרים זה:")[0],
                         [["rosh-chodesh"], ["chol-hamoed"]])
        self.assertEqual(self.any_of("בחנוכה ופורים אומרים:")[0], [["chanukah"], ["purim"]])
        self.assertEqual(self.any_of('בשבת חוה"מ פסח:')[0], [["shabbat", "chol-hamoed-pesach"]])
        self.assertEqual(self.any_of("כשחל ראש חודש בשבת אומרים:")[0],
                         [["rosh-chodesh", "shabbat"]])
        self.assertEqual(self.any_of("בראש חודש ביום טוב ובחול המועד אומרים")[0],
                         [["rosh-chodesh"], ["yom-tov"], ["chol-hamoed"]])
        self.assertEqual(self.any_of("בצום גדליה ובעשרה בטבת אומרים")[0], [["taanit"]])

    def test_negation(self):
        self.assertEqual(self.any_of('אין אומרים בשבת ויו"ט:'),
                         ([["shabbat"], ["yom-tov"]], True, []))
        # "ביום שאין אומרים תחנון" הוא הביטוי; "אין אומרים זה" — השלילה
        self.assertEqual(self.any_of("ביום שאין אומרים תחנון אין אומרים זה:"),
                         ([["no-tachanun"]], True, []))
        self.assertEqual(self.any_of("בימים שיש בהם תחנון אומרים זה:"),
                         ([["no-tachanun"]], True, []))
        self.assertEqual(self.any_of("בימים שאין גומרים את ההלל מדלגים"),
                         ([["half-hallel"]], True, []))

    def test_names_seasons_dow(self):
        self.assertEqual(self.any_of('בתענית ציבור אומר כאן הש"ץ עֲנֵֽנוּ'),
                         ([["taanit"]], False, ["עננו"]))
        self.assertEqual(self.any_of("בקיץ:")[0], [["~summer"]])
        self.assertEqual(self.any_of("בימות הגשמים:")[0], [["~winter"]])
        self.assertEqual(self.any_of("בשני בשבת:")[0], [["monday"]])
        self.assertEqual(self.any_of("מזמור ליום שני")[0], [["monday"]])
        self.assertEqual(self.any_of("שיר של יום ששי:")[0], [["friday"]])

    def test_not_headers(self):
        for t in ['בעשי"ת השלום',                      # התחליף כתוב בלי ניקוד
                  "בעשרת ימי תשובה אומרים: המלך הקדוש:",
                  'קריאה לחוה"מ פסח',                    # כותרת של קטע
                  "בשני וחמישי יאמר והוא רחום",
                  "ביום הששי אומר:",                     # יום בסוכות, לא בשבוע
                  "ביום טוב ובשבת חול המועד מדלגים ל:",
                  "אם שכח לומר מי כמוך דינו כמו בזכרנו.",
                  "שליח ציבור:", ""]:
            self.assertIsNone(parse_header(t), t)

    def test_label_and_enabled(self):
        c = parse_header("בראש חדש ובחול המועד אומרים זה:")
        self.assertEqual(condition_label(c), "ראש חודש / חול המועד")
        self.assertTrue(is_enabled(c, {"rosh-chodesh"}))
        self.assertFalse(is_enabled(c, {"shabbat"}))
        neg = parse_header('אין אומרים בשבת ויו"ט:')
        self.assertEqual(condition_label(neg), "לא בשבת / יום טוב")
        self.assertTrue(is_enabled(neg, set()))
        self.assertFalse(is_enabled(neg, {"yom-tov"}))
        both = parse_header('בשבת חוה"מ פסח:')
        self.assertFalse(is_enabled(both, {"shabbat"}))
        self.assertTrue(is_enabled(both, {"shabbat", "chol-hamoed-pesach"}))


# =============================================================================
# היקף התוספת — על טקסט אמיתי בכל נוסח/מהדורה
# =============================================================================

class TestClassifyLeafEdot(unittest.TestCase):
    """עדות המזרח (Shaliehsaboo): התוספות ב-<small>, ההוראה ב-<small> פנימי."""

    @classmethod
    def setUpClass(cls):
        cls.res = leaf("edot_weekday_amida_shaliehsaboo")

    def test_inline_region_ends_with_small(self):
        # "<small><small>בעשרת ימי תשובה אומרים:</small> זָכְרֵנוּ…</small> מֶלֶךְ עוֹזֵר"
        p3 = conds(self.res[2])
        self.assertEqual([k for k, _, _ in p3], [SPOKEN, INSTRUCTION, CONDITIONAL, SPOKEN])
        self.assertTrue(p3[2][1].startswith("זָכְרֵנוּ לְחַיִּים"))
        self.assertTrue(p3[2][1].endswith("אֱלֹהִים חַיִּים."))
        self.assertEqual(p3[2][2], [["aseret-yemei-teshuva"]])
        self.assertTrue(p3[3][1].startswith("מֶֽלֶךְ עוֹזֵר"))

    def test_seasons_resolved_by_text(self):
        p5 = conds(self.res[4])
        self.assertEqual([(k, c) for k, _, c in p5], [
            (INSTRUCTION, None), (CONDITIONAL, [["morid-hatal"]]),
            (INSTRUCTION, None), (CONDITIONAL, [["mashiv-haruach"]])])
        # "בקיץ:" לפני ברכת השנים — ותן ברכה / ותן טל ומטר
        self.assertEqual(conds(self.res[19])[0][2], [["veten-bracha"]])
        self.assertEqual(conds(self.res[21])[0][2], [["tal-umatar"]])

    def test_marked_block_and_nested(self):
        # 34: "בראש חודש ובחול המועד אומרים:" ⇐ 35–39 (כולן ב-<small>)
        rc_chm = [["rosh-chodesh"], ["chol-hamoed"]]
        self.assertEqual(conds(self.res[34]), [(CONDITIONAL, self.res[34][0][1], rc_chm)])
        self.assertEqual(conds(self.res[38])[0][2], rc_chm)
        # "בראש חדש:" בתוכה — ר"ח; "בחוה"מ פסח:" — וגם התנאי של יעלה ויבוא
        self.assertEqual(conds(self.res[35])[1][2], [["rosh-chodesh"]])
        pesach = self.res[36][1][2]
        self.assertEqual(condition_label(pesach), "חול המועד פסח")
        self.assertTrue(is_enabled(pesach, days.PRESETS["chol-hamoed-pesach"][1]))
        self.assertFalse(is_enabled(pesach, days.PRESETS["rosh-chodesh"][1]))
        self.assertEqual(self.res[39][0][0], SPOKEN)   # "וְאַתָּה בְּרַחֲמֶיךָ" — רגיל

    def test_al_hanisim_and_avinu_malkenu(self):
        self.assertEqual(conds(self.res[46])[0][2], [["chanukah"], ["purim"]])
        self.assertEqual(conds(self.res[47])[1][2], [["chanukah"]])
        self.assertEqual(self.res[49][0][0], SPOKEN)   # "וְעַל כֻּלָּם"
        for n in (75, 90, 106):   # אבינו מלכנו של עשי"ת — 32 פסקאות
            self.assertEqual(conds(self.res[n - 1])[0][2], [["aseret-yemei-teshuva"]], n)
        self.assertEqual(conds(self.res[107])[0][2], [["no-tachanun"]])


class TestClassifyLeafMetsudah(unittest.TestCase):
    """מצודה (ספרד ואשכנז): הוראה ב-<small> בפסקה משלה, הטקסט לא מסומן."""

    def test_sefard_next_paragraph_blocks(self):
        res = leaf("sefard_weekday_amidah_metsudah")
        self.assertEqual(conds(res[10])[0][2], [["morid-hatal"]])
        self.assertEqual(conds(res[56])[0][2], [["veten-bracha"]])
        self.assertEqual(conds(res[58])[0][2], [["tal-umatar"]])
        self.assertEqual(res[35][0][0], SPOKEN)   # "…הָאֵל הַקָּדוֹשׁ:" נשאר (תחליף — 8.28)
        self.assertEqual(conds(res[37])[0][2], [["aseret-yemei-teshuva"]])
        # יעלה ויבוא מתפצל ל-85–89: כל הפסקאות עד "…וְרַחוּם אָתָּה"
        for n in (85, 89):
            self.assertEqual(conds(res[n - 1])[-1][2], [["rosh-chodesh"], ["chol-hamoed"]], n)
        self.assertEqual(conds(res[85])[1][2], [["rosh-chodesh"]])
        # הלכה ארוכה שמתחילה ב"בחנוכה ופורים אומרים על הנסים." ⇐ פסקה 98
        self.assertEqual(conds(res[97])[0][2], [["chanukah"], ["purim"]])
        self.assertEqual(res[102][0][0], SPOKEN)   # "וְעַל כֻּלָּם"

    def test_ashkenaz_inline_series(self):
        res = leaf("ashkenaz_temple_service_metsudah")
        p3 = [(k, b.split()[0], c and condition_label(c)) for k, b, c in res[2]]
        self.assertEqual(p3, [
            (CONDITIONAL, "אֱלֹהֵֽינוּ", "ראש חודש / חול המועד"),
            (INSTRUCTION, 'לר"ח:', None), (CONDITIONAL, "רֹאשׁ", "ראש חודש"),
            (INSTRUCTION, "לפסח:", None), (CONDITIONAL, "חַג", "פסח"),
            (INSTRUCTION, "לסכות:", None), (CONDITIONAL, "חַג", "סוכות"),
            (CONDITIONAL, "זָכְרֵֽנוּ", "ראש חודש / חול המועד")])
        self.assertEqual(res[4][0][0], SPOKEN)   # "וְתֶחֱזֶינָה"

    def test_ashkenaz_single_header_takes_whole_paragraph(self):
        res = leaf("ashkenaz_thanksgiving_metsudah")
        self.assertEqual(conds(res[5])[0][2], [["chanukah"], ["purim"]])
        purim = [(k, c) for k, _, c in conds(res[7])]
        self.assertEqual(purim, [(INSTRUCTION, None), (CONDITIONAL, [["purim"]])],
                         "נקודתיים באמצע 'בימי מרדכי' לא קוטעות את התוספת")
        self.assertEqual(res[8][0][0], SPOKEN)
        self.assertEqual(conds(res[9])[1][2], [["aseret-yemei-teshuva"]])
        res = leaf("ashkenaz_divine_might_metsudah")
        self.assertEqual(conds(res[2])[0][2], [["morid-hatal"]])
        self.assertEqual(conds(res[4])[0][2], [["mashiv-haruach"]])
        res = leaf("ashkenaz_prosperity_metsudah")
        self.assertEqual([conds(res[n])[0][2] for n in (2, 4)],
                         [[["veten-bracha"]], [["tal-umatar"]]])

    def test_song_of_the_day_sections(self):
        res = leaf("sefard_song_of_the_day_metsudah")
        self.assertEqual(conds(res[2])[0][2], [["sunday"]])
        self.assertEqual(conds(res[3])[0][2], [["sunday"]])   # המזמור עצמו
        self.assertEqual(res[4][0][0], INSTRUCTION)            # "(הושיענו וכו')" — עוצר
        self.assertEqual(conds(res[7])[0][2], [["monday"]])


class TestClassifyLeafOtherEditions(unittest.TestCase):
    def test_torat_emet_festival(self):
        res = leaf("sefard_festival_amidah_torat_emet")
        # "כשחל יו"ט במוצאי שבת אומרים ותודיענו:" ⇐ רק הפסקה שמתחילה "וַתּוֹדִיעֵנוּ"
        self.assertEqual(conds(res[19])[0][2], [["yom-tov", "motzei-shabbat"]])
        self.assertEqual(res[20][0][0], SPOKEN)
        # "(לשבת שַׁבָּתוֹת לִמְנוּחָה וּ)" בתוך <small> של כל הפסקה — רק הסוגריים
        p21 = conds(res[20])
        self.assertEqual([k for k, _, _ in p21],
                         [SPOKEN, INSTRUCTION, CONDITIONAL, SPOKEN, INSTRUCTION, CONDITIONAL])
        self.assertEqual(p21[2][1], "שַׁבָּתוֹת לִמְנוּחָה וּ)")
        self.assertEqual([conds(res[n])[1][2] for n in (21, 22, 23, 24)],
                         [[["pesach"]], [["shavuot"]], [["sukkot"]], [["shemini-atzeret"]]])
        self.assertEqual(res[26][0][0], SPOKEN)   # יעלה ויבוא — ביו"ט תמיד נאמר

    def test_daat_dash_headers(self):
        res = leaf("ashkenaz_shabbat_temple_service_daat")
        p2 = [(k, c and condition_label(c)) for k, _, c in res[1]]
        self.assertEqual(p2, [
            (INSTRUCTION, None), (CONDITIONAL, "ראש חודש / חול המועד"),
            (INSTRUCTION, None), (CONDITIONAL, "ראש חודש"),
            (INSTRUCTION, None), (CONDITIONAL, "פסח"),
            (INSTRUCTION, None), (CONDITIONAL, "סוכות"),
            (CONDITIONAL, "ראש חודש / חול המועד")])
        self.assertEqual(res[2][0][0], SPOKEN)

    def test_leaf_without_conditions_is_unchanged(self):
        for name in ("ashkenaz_ashrei_metsudah", "ashkenaz_shabbat_ashrei_daat"):
            paras = flatten(shared.fixture(name)["versions"][0]["text"])
            self.assertEqual([[(k, b) for k, b, _ in ps] for ps in classify_leaf(paras)],
                             [classify_paragraph(p) for p in paras], name)


# =============================================================================
# בחירת היום
# =============================================================================

class TestDays(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = load_catalog()

    def test_leaf_day(self):
        cases = {EDOT_AMIDA: "weekday", "sefard/shabbat/kabbalat-shabbat": "shabbat",
                 TE_FESTIVAL: "yom-tov",
                 "ashkenaz/festivals/prayer-for-dew": "pesach"}
        for path, want in cases.items():
            keys = path.split("/")
            if self.cat.node(keys) is None:
                continue
            self.assertEqual(days.leaf_day(self.cat, keys), want, path)
        rc = next(p for p, _ in self.cat.leaves("sefard/rosh-chodesh"))
        self.assertEqual(days.leaf_day(self.cat, rc.split("/")), "rosh-chodesh")

    def resolve(self, **q):
        return days.resolve(q, self.cat, EDOT_AMIDA.split("/"))

    def test_resolve(self):
        sel = self.resolve()
        self.assertEqual((sel["day"], sel["auto"], sel["explicit"], sel["enabled"]),
                         ("weekday", True, False, set()))
        sel = self.resolve(day="rosh-chodesh", season="winter", days="chanukah,-half-hallel")
        self.assertEqual(sel["enabled"], {"rosh-chodesh", "no-tachanun", "chanukah",
                                          "mashiv-haruach", "tal-umatar"})
        self.assertTrue(sel["explicit"])
        sel = self.resolve(day="auto", season="between")
        self.assertEqual(sel["enabled"], {"mashiv-haruach", "veten-bracha"})
        self.assertEqual(self.resolve(days="purim")["enabled"], {"purim"})
        for bad in ({"day": "tuesday-ish"}, {"season": "spring"}, {"days": "nope"},
                    {"days": "-nope"}):
            with self.assertRaises(ValueError):
                self.resolve(**bad)


# =============================================================================
# ‏/api/siddur?path=…&day=&season=&days=
# =============================================================================

class TestApiDays(shared.SiddurTestCase):
    def by_text(self, payload, start):
        return next(u for u in payload["units"] if u["text"].startswith(start))

    def test_default_is_backward_compatible(self):
        payload, _ = self.ok(path=EDOT_AMIDA)
        self.assertEqual(payload["day"], {"key": "weekday", "label": "יום חול רגיל", "auto": True})
        self.assertIsNone(payload["season"])
        self.assertEqual(payload["days"], [])
        rc = self.by_text(payload, "רֹאשׁ חֹֽדֶשׁ")
        # בלי day/days/season (ממשק ישן) — תוספת כבויה היא "instruction"
        self.assertEqual(rc["kind"], "instruction")
        self.assertEqual((rc["condition"], rc["conditions"], rc["condition_label"]),
                         ("rosh-chodesh", ["rosh-chodesh"], "ראש חודש"))
        self.assertEqual(rc["label"], "עמידה · 36 · ראש חודש")
        self.assertNotIn("chunk", rc)
        self.assertEqual({u["kind"] for u in payload["units"]},
                         {"paragraph", "instruction"})
        # התוספת לא במקטעים
        self.assertNotIn(payload["units"].index(rc), {s["unit"] for s in payload["segments"]})
        self.assertEqual([n["group"] for n in payload["needs_choice"]], ["season"])
        c = {c["slug"]: c for c in payload["conditions"]}
        self.assertEqual(c["aseret-yemei-teshuva"]["count"], 39)
        self.assertFalse(any(x["enabled"] for x in payload["conditions"]))
        self.assertEqual(c["morid-hatal"]["group"], "season")
        self.assertEqual(payload["paragraphs"][35]["conditions"], ["rosh-chodesh"])
        self.assertEqual(payload["paragraphs"][35]["condition_label"], "ראש חודש")
        self.assertEqual(payload["paragraphs"][35]["kind"], "conditional")  # הוראה + תוספת
        self.assertIn({"key": "rosh-chodesh", "label": "ראש חודש"}, payload["presets"])

    def test_enabled_becomes_spoken(self):
        off, _ = self.ok(path=EDOT_AMIDA, day="weekday")
        rc_off = self.by_text(off, "רֹאשׁ חֹֽדֶשׁ")
        self.assertEqual(rc_off["kind"], "conditional")   # ממשק חדש — kind חדש
        on, _ = self.ok(path=EDOT_AMIDA, day="rosh-chodesh", season="winter")
        rc = self.by_text(on, "רֹאשׁ חֹֽדֶשׁ")
        self.assertEqual(rc["kind"], "paragraph")
        self.assertEqual(rc["chunk"], "punct")
        self.assertIn(on["units"].index(rc), {s["unit"] for s in on["segments"]})
        self.assertEqual(self.by_text(on, "מַשִּׁיב הָרֽוּחַ")["kind"], "paragraph")
        self.assertEqual(self.by_text(on, "מוֹרִיד הַטָּל")["kind"], "conditional")
        self.assertEqual(self.by_text(on, "חַג הַמַּצּוֹת")["kind"], "conditional")
        self.assertEqual(on["needs_choice"], [])
        self.assertEqual(on["season"], "winter")
        self.assertGreater(len(on["segments"]), len(off["segments"]))
        # הדלקה וכיבוי ידניים מעל סוג היום
        tweak, _ = self.ok(path=EDOT_AMIDA, day="rosh-chodesh", days="-rosh-chodesh,chanukah")
        self.assertEqual(self.by_text(tweak, "רֹאשׁ חֹֽדֶשׁ")["kind"], "conditional")
        self.assertEqual(self.by_text(tweak, "בִּימֵי מַתִּתְיָה")["kind"], "paragraph")
        self.assertNotIn("rosh-chodesh", tweak["days"])

    def test_negated_lamnatzeach(self):
        # אשרי (עדות): "ביום שאין אומרים בו תחנון מדלגים למנצח"
        path = shared.EDOT_ASHREI
        base, _ = self.ok(path=path)
        lam = self.by_text(base, "לַמְנַצֵּ֗חַ")
        self.assertEqual((lam["kind"], lam.get("negate")), ("paragraph", True))
        self.assertEqual(lam["condition_label"], "לא ביום שאין בו תחנון")
        rc, _ = self.ok(path=path, day="rosh-chodesh")
        self.assertEqual(self.by_text(rc, "לַמְנַצֵּ֗חַ")["kind"], "conditional")

    def test_range_only_conditional_auto_day(self):
        # הקיצור "אבינו מלכנו" בעדות — פסקאות עשי"ת בתוך העמידה: ברירת המחדל
        # (‏auto) עוברת ליום שבו אומרים אותן
        payload, _ = self.ok(path=EDOT_AMIDA, **{"from": "75", "to": "106"})
        self.assertEqual(payload["day"]["key"], "aseret-yemei-teshuva")
        self.assertTrue(payload["day"]["auto"])
        self.assertEqual({u["kind"] for u in payload["units"] if u.get("condition")},
                         {"paragraph"})
        # בחירה מפורשת של יום חול — 400 עם המתגים, כדי לבחור יום
        payload, status, headers = self.get(path=EDOT_AMIDA, day="weekday",
                                            **{"from": "75", "to": "106"})
        self.assertEqual(status, 400)
        self.assertIn("מה אומרים היום", payload["error"])
        self.assertEqual([c["slug"] for c in payload["conditions"]], ["aseret-yemei-teshuva"])
        self.assertTrue(payload["units"])
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_bad_params_before_network(self):
        for q in ({"day": "someday"}, {"season": "spring"}, {"days": "x"}):
            payload, status, _ = self.get(path=EDOT_AMIDA, **q)
            self.assertEqual(status, 400, q)
            self.assertRegex(payload["error"], "[א-ת]")
        self.assertEqual(self.fake.calls, [])

    def test_every_recorded_amidah_has_conditions(self):
        cat = api.load_catalog()
        for path in (EDOT_AMIDA, SEFARD_AMIDA, ASHK + "temple-service",
                     ASHK + "divine-might", ASHK + "thanksgiving", ASHK + "prosperity",
                     TE_FESTIVAL, "ashkenaz/shabbat/shacharit/amidah/temple-service"):
            src = cat.source(path)
            self.assertIn((src["ref"], src["version"]), shared.RECORDED, path)
            payload, _ = self.ok(path=path)
            self.assertTrue(payload["conditions"], path)
            self.assertTrue(payload["segments"], path)
            units = json.dumps(payload["units"], ensure_ascii=False)
            self.assertNotIn('"conditional"', units, "בלי day — ממשק ישן")

    def test_song_of_the_day_asks_for_weekday(self):
        # שיר של יום: כל הטקסט תלוי ביום בשבוע — לא מנחשים יום, מבקשים לבחור
        src = api.load_catalog().source(SONG)
        self.assertIn((src["ref"], src["version"]), shared.RECORDED)
        payload, status, _ = self.get(path=SONG)
        self.assertEqual(status, 400)
        self.assertEqual([n["group"] for n in payload["needs_choice"]], ["dow"])
        self.assertEqual([c["group"] for c in payload["conditions"]], ["dow"] * 6)
        monday, _ = self.ok(path=SONG, day="auto", days="monday")
        spoken = [u["text"] for u in monday["units"] if u["kind"] == "paragraph"]
        self.assertTrue(spoken[0].startswith("הַיּוֹם יוֹם שֵׁנִי"))
        self.assertTrue(spoken[1].startswith("שִׁיר מִזְמוֹר לִבְנֵי קֹֽרַח"))
        self.assertEqual(len(spoken), 2)


if __name__ == "__main__":
    unittest.main()
