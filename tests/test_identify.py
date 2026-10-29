# -*- coding: utf-8 -*-
"""בדיקות לזיהוי הקטע מההקלטה — src/siddur/identify.py ו-tools/build_identify_index.py
(PLAN_TEFILA.md 4.5.1). בלי רשת ובלי מודלים: אינדקס סינתטי קטן, האינדקס האמיתי
שבמאגר, ותמלול אמיתי שמור של samples/nishmat."""

import gzip
import importlib.util
import json
import random
import sys
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from aligner.anchors import normalize_word  # noqa: E402
from aligner.pipeline import units_to_segments  # noqa: E402
from siddur import identify as idm  # noqa: E402
from siddur import load_catalog  # noqa: E402
from siddur.identify import Index, identify, skeleton  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


builder = _load("build_identify_index", ROOT / "tools" / "build_identify_index.py")

# --- אינדקס סינתטי -------------------------------------------------------------

N = normalize_word
# טקסטים קצרים (מנורמלים כמו בצינור): נשמת וסופו, "כי לה' המלוכה", קדיש
KI_LASHEM = [N(w) for w in (
    "כי לאדני המלוכה ומשל בגוים ועלו מושעים בהר ציון לשפט את הר עשו "
    "והיתה לאדני המלוכה והיה אדני למלך על כל הארץ ביום ההוא יהיה אדני "
    "אחד ושמו אחד").split()]
NISHMAT = [N(w) for w in (
    "נשמת כל חי תברך את שמך אדני אלהינו ורוח כל בשר תפאר ותרומם זכרך "
    "מלכנו תמיד מן העולם ועד העולם אתה אל ומבלעדיך אין לנו מלך גואל "
    "ומושיע פודה ומציל ועונה ומרחם בכל עת צרה וצוקה אין לנו מלך עוזר "
    "וסומך אלא אתה").split()]
SHOCHEN = [N(w) for w in (
    "שוכן עד מרום וקדוש שמו וכתוב רננו צדיקים באדני לישרים נאוה תהלה "
    "בפי ישרים תתהלל ובדברי צדיקים תתברך ובלשון חסידים תתרומם ובקרב "
    "קדושים תתקדש").split()]
KADDISH = [N(w) for w in (
    "יתגדל ויתקדש שמה רבא בעלמא די ברא כרעותה וימליך מלכותה בחייכון "
    "וביומיכון ובחיי דכל בית ישראל בעגלא ובזמן קריב ואמרו אמן").split()]
ASHREI = [N(w) for w in (
    "אשרי יושבי ביתך עוד יהללוך סלה אשרי העם שככה לו אשרי העם שאדני "
    "אלהיו תהלה לדוד ארוממך אלוהי המלך ואברכה שמך לעולם ועד בכל יום "
    "אברכך ואהללה שמך לעולם ועד גדול אדני ומהלל מאד ולגדלתו אין חקר").split()]


def _leaf(nusach, path, title, paragraphs, total=None, crumbs=None):
    """paragraphs: [(מספר פסקה, מילים)] ⇐ רשומת עלה בפורמט הקובץ (לפני vocab)."""
    words, starts, first = [], [], {}
    for n, ws in paragraphs:
        starts.append([n, len(words)])
        words.extend(ws)
        first[str(n)] = " ".join(ws[:5])
    return {"n": nusach, "p": path, "t": title, "c": crumbs or [],
            "P": total or paragraphs[-1][0], "s": starts, "f": first, "_w": words}


def synthetic_data():
    leaves = [
        # אשכנז: "אז ישיר" (שבסופו כי לה' המלוכה) ⇐ נשמת ⇐ שוכן עד — עלים סמוכים
        _leaf("ashkenaz", "ashkenaz/shabbat/az-yashir", "אז ישיר",
              [(1, ASHREI[:20]), (2, KI_LASHEM)], crumbs=["שבת", "שחרית"]),
        _leaf("ashkenaz", "ashkenaz/shabbat/nishmat", "נשמת כל חי",
              [(1, NISHMAT)], crumbs=["שבת", "שחרית"]),
        _leaf("ashkenaz", "ashkenaz/shabbat/shochen-ad", "שוכן עד",
              [(2, SHOCHEN)], total=3, crumbs=["שבת", "שחרית"]),
        # עדות: הכול בעלה אחד, עם פסקת הוראה (3) שאין בה מילים נאמרות
        _leaf("edot", "edot/shabbat/pesukei", "פסוקי דזמרה",
              [(1, ASHREI), (2, KI_LASHEM), (4, NISHMAT), (5, SHOCHEN)],
              total=6, crumbs=["שבת"]),
        # קדיש — אותו טקסט בשני עלים של אותו נוסח
        _leaf("edot", "edot/weekday/kaddish", "קדיש", [(1, KADDISH)]),
        _leaf("edot", "edot/shabbat/kaddish", "קדיש", [(1, KADDISH)]),
        _leaf("sefard", "sefard/weekday/kaddish", "קדיש", [(1, KADDISH)]),
    ]
    vocab = sorted({w for lf in leaves for w in lf["_w"]})
    vid = {w: i for i, w in enumerate(vocab)}
    for lf in leaves:
        lf["w"] = [vid[w] for w in lf.pop("_w")]
    return {"format": idm.FORMAT, "vocab": vocab, "leaves": leaves,
            "nusachim": {"ashkenaz": "אשכנז", "edot": "עדות המזרח", "sefard": "ספרד"}}


def asr(words, t0=0.0, step=0.5):
    return [{"word": w, "start": t0 + i * step, "end": t0 + i * step + 0.4}
            for i, w in enumerate(words)]


class TestSynthetic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.idx = Index(synthetic_data())

    def top(self, words, **kw):
        res = identify(asr(words), self.idx, **kw)
        self.assertTrue(res["candidates"], "אין מועמד")
        return res, res["candidates"][0]

    def test_skeleton(self):
        self.assertEqual(skeleton("ומושיע"), "משע")
        self.assertEqual(skeleton("כוהנים"), skeleton("כהנים"))
        self.assertEqual(skeleton("וי"), "וי")  # מילה שכולה ו/י נשארת

    def test_exact_span_with_paragraph_range(self):
        _, c = self.top(NISHMAT[5:30], nusach="edot")
        self.assertEqual(c["nusach"], "edot")
        self.assertEqual(len(c["parts"]), 1)
        p = c["parts"][0]
        self.assertEqual((p["path"], p["from"], p["to"], p["total"]),
                         ("edot/shabbat/pesukei", 4, 4, 6))
        self.assertEqual(p["first_words"], " ".join(NISHMAT[:5]))
        self.assertEqual(c["confidence"], "high")
        self.assertEqual(c["start"], 0.0)

    def test_noisy_transcript(self):
        """שגיאות תמלול: מילה שגויה, השמטה, כתיב מלא, ו' מיותרת, שם ה' ("אדוני")."""
        words = list(NISHMAT)
        words[1] = "קול"                  # כל ⇐ קול
        del words[8]                      # השמטה
        words[3] = "תבארך"                # שגיאת אות
        words[16] = "ומן"                 # ו' מיותרת
        words[6] = "אדוני"                # כך התמלול כותב את שם ה׳
        words.insert(20, "אמן")           # מילה שאינה בטקסט
        res, c = self.top(words, nusach="ashkenaz")
        self.assertEqual(c["parts"][0]["path"], "ashkenaz/shabbat/nishmat")
        self.assertGreater(c["coverage"], 0.8)
        # אותו טקסט בדיוק בעדות ⇐ אותו מועמד, ב-also
        self.assertEqual([a["path"] for a in c["also"]], ["edot/shabbat/pesukei"])

    def test_sequence_across_adjacent_leaves(self):
        """אשכנז: "כי לה' המלוכה" (סוף עלה) ואחריו נשמת (עלה הבא) ⇐ מועמד אחד
        עם שני חלקים; בעדות — עלה אחד עם טווח פסקאות 2–4 (כולל פסקת ההוראה)."""
        words = ["שלום", "לכם", "אני", "רוצה", "להקריא"] + KI_LASHEM + ["ניגון"] + NISHMAT[:20]
        res = identify(asr(words), self.idx)
        by_n = {c["nusach"]: c for c in res["candidates"]}
        ash = by_n["ashkenaz"]
        self.assertEqual([(p["path"], p["from"], p["to"]) for p in ash["parts"]],
                         [("ashkenaz/shabbat/az-yashir", 2, 2),
                          ("ashkenaz/shabbat/nishmat", 1, 1)])
        self.assertLess(ash["parts"][0]["end"], ash["parts"][1]["start"])
        edot = by_n["edot"]
        self.assertEqual([(p["path"], p["from"], p["to"]) for p in edot["parts"]],
                         [("edot/shabbat/pesukei", 2, 4)])
        # החלקים הבודדים לא מוצגים שוב כמועמדים נפרדים
        singles = [c for c in res["candidates"] if c["nusach"] == "ashkenaz"]
        self.assertEqual(len(singles), 1)

    def test_no_sequence_when_first_leaf_not_finished(self):
        """אמצע "אז ישיר" ואז נשמת — לא רצף (ההתאמה בעלה הראשון לא הגיעה לסופו)."""
        words = ASHREI[:20] + NISHMAT[:20]
        res = identify(asr(words), self.idx)
        for c in res["candidates"]:
            if c["nusach"] == "ashkenaz":
                self.assertEqual(len(c["parts"]), 1)

    def test_identical_text_collapsed_with_also(self):
        res, c = self.top(KADDISH, nusach="sefard")
        self.assertEqual(c["parts"][0]["path"], "sefard/weekday/kaddish")
        also = {a["path"] for a in c["also"]}
        self.assertEqual(also, {"edot/weekday/kaddish", "edot/shabbat/kaddish"})
        self.assertEqual(len(res["candidates"]), 1)

    def test_preferred_nusach_breaks_near_tie(self):
        _, c1 = self.top(KADDISH, nusach="edot")
        self.assertEqual(c1["nusach"], "edot")
        _, c2 = self.top(KADDISH)  # בלי העדפה — לפי סדר האינדקס
        self.assertEqual(c2["parts"][0]["path"], "edot/weekday/kaddish")

    def test_nothing_found(self):
        res = identify(asr("שלום לכם מה שלומכם היום בבוקר הזה".split()), self.idx)
        self.assertEqual(res["candidates"], [])
        self.assertEqual(identify(asr(["נשמת", "כל"]), self.idx)["candidates"], [])
        self.assertEqual(identify([], self.idx), {"asr_words": 0, "candidates": []})

    def test_plain_strings_and_punctuation(self):
        words = [w + "," for w in SHOCHEN]
        res = identify(words, self.idx)
        c = res["candidates"][0]
        self.assertIn(c["parts"][0]["path"], {"ashkenaz/shabbat/shochen-ad",
                                              "edot/shabbat/pesukei"})
        self.assertIsNone(c["start"])  # בלי זמנים — None

    def test_paragraph_of(self):
        lf = self.idx.leaves[3]  # עדות: פסקאות 1,2,4,5
        self.assertEqual(Index.paragraph_of(lf, 0), 1)
        self.assertEqual(Index.paragraph_of(lf, len(ASHREI)), 2)
        self.assertEqual(Index.paragraph_of(lf, len(ASHREI) + len(KI_LASHEM)), 4)

    def test_bad_format(self):
        with self.assertRaises(ValueError):
            Index({"format": 99, "vocab": [], "leaves": []})


class TestBuilder(unittest.TestCase):
    """הבונה מנרמל בדיוק כמו הצינור: אותן יחידות שה-API מחזיר ⇐ אותן מילים."""

    def test_divine_name_and_maqaf(self):
        got = builder.paragraph_words("בָּרוּךְ אַתָּה יְיָ אֱלֹהֵינוּ, עַל־כָּל <small>(בשבת)</small> לַה' הַמְּלוּכָה")
        self.assertEqual(got, ["ברוכ", "אתה", "אדני", "אלהינו", "על", "כל",
                               "לאדני", "המלוכה"])

    def test_instruction_only_paragraph_empty(self):
        self.assertEqual(builder.paragraph_words("<small>אומרים קדיש</small>"), [])

    def test_leaf_record_matches_api_units(self):
        api = _load("api_siddur_for_identify", ROOT / "api" / "siddur.py")
        tests = _load("t_api_siddur_for_identify", ROOT / "tests" / "test_api_siddur.py")
        path = "sefard/shabbat/kabbalat-shabbat"
        with mock.patch.object(api, "_get_json", side_effect=tests.FakeSefaria()):
            payload, status, _ = api.respond(urllib.parse.urlencode({"path": path}))
        self.assertEqual(status, 200)
        fx = json.loads((ROOT / "tests" / "fixtures" / "siddur"
                         / "sefard_kabbalat_shabbat_torat_emet.json").read_text(encoding="utf-8"))
        rec = builder.leaf_record(builder.flatten(fx["versions"][0]["text"]))
        segs = units_to_segments(payload["units"], 4, None, "tefila")
        pipeline_words = [w for w in (normalize_word(x) for s in segs
                                      for x in s["align_plain"]) if w]
        self.assertEqual(rec["words"], pipeline_words)
        self.assertEqual(rec["total"], payload["range"]["total"])
        info = {p["n"]: p for p in payload["paragraphs"]}
        for n, off in rec["starts"]:
            self.assertIn(info[n]["kind"], ("paragraph", "mixed"))
            self.assertEqual(rec["first"].get(str(n)), info[n]["first_words"])
        spoken = [p["n"] for p in payload["paragraphs"] if p["kind"] in ("paragraph", "mixed")]
        self.assertEqual([n for n, _ in rec["starts"]], spoken)


class TestRealIndex(unittest.TestCase):
    """האינדקס שבמאגר (data/siddur/identify_index.json.gz) — נאפה ב-image של ה-worker."""

    @classmethod
    def setUpClass(cls):
        cls.idx = idm.load_index()
        with gzip.open(idm.INDEX_PATH, "rt", encoding="utf-8") as fh:
            cls.raw = json.load(fh)

    def test_size_and_format(self):
        self.assertLess(idm.INDEX_PATH.stat().st_size, 10 * 1024 * 1024)
        self.assertEqual(self.raw["format"], idm.FORMAT)
        self.assertEqual(set(self.raw["nusachim"]), {"edot-hamizrach", "sefard", "ashkenaz"})
        self.assertGreater(len(self.idx.leaves), 700)

    def test_paths_are_available_catalog_leaves(self):
        cat = load_catalog()
        for lf in self.idx.leaves:
            node = cat.leaf(lf["path"])
            self.assertIsNotNone(node, lf["path"])
            self.assertTrue(node.get("v") and not node.get("unavailable"), lf["path"])
            self.assertEqual(lf["title"], node.get("heTitle", ""))
            self.assertLessEqual(max(lf["par_n"]), lf["total"])

    def test_built_from_current_catalog(self):
        """נבנה מהקטלוג הנוכחי — אחרי בנייה מחדש של הקטלוג צריך לבנות גם אותו
        (‏python3 tools/build_identify_index.py)."""
        cat = load_catalog()
        self.assertEqual(self.raw["catalog_generated"], cat.data.get("generated"))

    def test_popular_shortcut_leaves_indexed(self):
        pop = json.loads((ROOT / "data" / "siddur" / "popular.json").read_text(encoding="utf-8"))
        paths = {lf["path"] for lf in self.idx.leaves}
        for nus, items in pop["nusachim"].items():
            for it in items:
                self.assertIn(it["path"], paths, it["label"])

    def test_nishmat_recording_cached_transcript(self):
        """תמלול אמיתי שמור של samples/nishmat (בלי vad_filter, כמו /identify):
        "כי לה' המלוכה" ⇐ נשמת, שבת שחרית — שלושת הנוסחים ב-3 המובילים."""
        words = json.loads((ROOT / "samples" / "nishmat" / "asr" / "turbo_novad.json")
                           .read_text(encoding="utf-8"))["words"]
        res = identify(words, self.idx)
        top3 = res["candidates"][:3]
        self.assertEqual({c["nusach"] for c in top3}, {"edot-hamizrach", "sefard", "ashkenaz"})
        for c in top3:
            self.assertIn("/shabbat/", c["parts"][0]["path"])
            self.assertIn(c["confidence"], ("high", "medium"))
        ash = next(c for c in top3 if c["nusach"] == "ashkenaz")
        self.assertEqual([p["title"] for p in ash["parts"]], ["אז ישיר", "נשמת כל חי"])
        edot = next(c for c in top3 if c["nusach"] == "edot-hamizrach")
        p = edot["parts"][0]
        self.assertEqual(p["path"], "edot-hamizrach/shabbat/shabbat-shacharit/pesukei-dzimra")
        self.assertTrue(p["from"] <= 20 <= p["to"])   # פסקה 20 — "נשמת כל חי"

    def test_synthetic_accuracy_floor(self):
        """רצפת דיוק (הערכה מלאה: tools/eval_identify.py): 40 קטעים, 15–25% שגיאות."""
        ev = _load("eval_identify", ROOT / "tools" / "eval_identify.py")
        s = ev.run(self.idx, 40, 0.15, 0.25, seed=3)
        self.assertGreaterEqual(s["text1"], 36)
        self.assertGreaterEqual(s["top3"], 30)


if __name__ == "__main__":
    unittest.main()
