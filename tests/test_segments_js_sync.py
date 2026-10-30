# -*- coding: utf-8 -*-
"""הדפדפן (js/segments.js) והשרת (chunker) חייבים לחלק את אותן מילים
לאותן כתוביות — כולל מיזוג כתובית בלי מילה נשמעת (‏isAudible מול
_merge_unalignable) וכלל הכתיב/קרי בסוגריים בתפילה (8.22). אחרת מספר
הכתוביות בטלפון ובענן נפרד, ואינדקסי סדר הביצוע (performance) מצביעים
על כתוביות אחרות.

מריץ את segmentsFromSplits האמיתי ב-node (tests/segments_js_harness.mjs,
בלי דפדפן) על אותם קלטים כמו units_to_segments. נדלג אם node לא מותקן.
"""

import json
import random
import shutil
import subprocess
import sys
import unicodedata
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from aligner.pipeline import (_unit_words, split_mixed_unit,  # noqa: E402
                              units_to_segments)


def nfc(text):
    return unicodedata.normalize("NFC", text)


# יחידות עם כל המקרים: כתיב/קרי (טעמים ופיסוק, גם בשרשרת מקף), סוגריים
# שאינם קרי, מילים לא מנוקדות רגילות, וכתיב בסוף יחידה (לא חוצה יחידות)
TEFILA_UNITS = [
    {"text": nfc("כִּֽי־הִשְׁקִ֖יף מִמְּר֣וֹם קׇדְשׁ֑וֹ הביט [הַבִּ֖יטָה] "
                 "יְ֝הֹוָ֗ה מִשָּׁמַ֥יִם אֶל־אֶ֥רֶץ הִבִּֽיט׃"),
     "label": "א", "kind": "paragraph", "chunk": "taamim"},
    {"text": nfc("מגדל [מַגְדִּיל] יְשׁוּעוֹת מַלְכּוֹ, עַל־במותי [בָּמֳתֵי] "
                 "וְעוֹד [אָמֵן] ברוך הוא [אמן]"),
     "label": "ב", "kind": "paragraph", "chunk": "punct"},
    {"text": nfc("וְעֹשֶׂה חֶסֶד לִמְשִׁיחוֹ הביט"),
     "label": "ג", "kind": "line", "chunk": "punct"},
    {"text": nfc("[הַבִּיטָה] אֶל עַמְּךָ"), "label": "ד", "kind": "line",
     "chunk": "punct"},
]
TANAKH_UNITS = [
    {"text": nfc("וַיֹּ֣אמֶר אֵלָ֗יו ידו [יָד֥וֹ] עַל־הָאָ֖רֶץ׃"),
     "label": "פסוק 1", "kind": "verse", "chunk": "taamim"},
]


def _words(units):
    out = []
    for ui, unit in enumerate(units):
        out += [{"t": t, "verse": ui + 1} for t in _unit_words(unit)]
    return out


def _cases(units, mode, seed):
    n = len(_words(units))
    rng = random.Random(seed)
    sizes = [[1] * n]  # כל מילה כתובית — כל החלטת "נשמע" נבדקת לבד
    for _ in range(25):
        cur, left = [], n
        while left:
            k = min(left, rng.randint(1, 4))
            cur.append(k)
            left -= k
        sizes.append(cur)
    return [{"mode": mode, "units": units, "sizes": s} for s in sizes]


def _run_js(cases):
    payload = {"cases": [{"mode": c["mode"], "words": _words(c["units"]),
                          "sizes": c["sizes"]} for c in cases]}
    res = subprocess.run(["node", str(_ROOT / "tests/segments_js_harness.mjs")],
                         input=json.dumps(payload, ensure_ascii=False),
                         capture_output=True, text=True, timeout=60,
                         check=True)
    return json.loads(res.stdout)


@unittest.skipUnless(shutil.which("node"), "node לא מותקן")
class TestSegmentsJsSync(unittest.TestCase):
    def _check(self, cases):
        js = _run_js(cases)
        for case, got in zip(cases, js):
            py = units_to_segments(case["units"], splits=case["sizes"],
                                   mode=case["mode"])
            want = [{"display": s["display"], "verse": s["unit"] + 1}
                    for s in py]
            self.assertEqual(got, want, case["sizes"])

    def test_tefila_with_qere_ketiv(self):
        cases = _cases(TEFILA_UNITS, "tefila", 1)
        self._check(cases)
        # הבדיקה לא ריקה: בחלוקת מילה-לכתובית הכתיבים התמזגו לשכניהם
        n_words = len(_words(TEFILA_UNITS))
        n_segs = len(units_to_segments(TEFILA_UNITS, splits=[1] * n_words,
                                       mode="tefila"))
        # הביט ומגדל; לא עַל־במותי (עַל נשמע) ולא הביט שבסוף יחידה ג
        self.assertEqual(n_words - n_segs, 2)

    def test_tanakh_ketiv(self):
        self._check(_cases(TANAKH_UNITS, "tanakh", 2))

    def test_mixed_paragraph_split_units(self):
        """פסקה מעורבת שפוצלה (‏split_mixed_unit — תפילה בלי טעמים + פסוק
        מוטעם, סוף כל נדרי): שתי יחידות באותה תווית — אותה ספירה בשני הצדדים."""
        kn = nfc("וְדִי אֲסָרְנָא עַל נַפְשָׁתָנָא וְדִי נֶאְסַר. יְהֵא רַעֲוָא דִי "
                 "יְהוֹן שְׁבִיתִין וּשְׁבִיקִין לָא שְׁרִירִין וְלָא קַיָּמִין. "
                 "וְנִסְלַ֗ח לְכׇל־עֲדַת֙ בְּנֵ֣י יִשְׂרָאֵ֔ל וְלַגֵּ֖ר הַגָּ֣ר "
                 "בְּתוֹכָ֑ם כִּ֥י לְכׇל־הָעָ֖ם בִּשְׁגָגָֽה׃")
        units = split_mixed_unit({"text": kn, "label": "כל נדרי · 6",
                                  "kind": "paragraph"})
        self.assertEqual([u["chunk"] for u in units], ["punct", "taamim"])
        self._check(_cases(units, "tefila", 3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
