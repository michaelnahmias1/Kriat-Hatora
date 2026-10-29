# -*- coding: utf-8 -*-
"""חיתוך פסוק מקראי למקטעי כתוביות לפי היררכיית הטעמים.

Python טהור, אפס תלויות, אפס אודיו, אפס AI. ראה PLAN.md סעיף 4.

מונחים:
- "מילה פרוזודית" = טוקן מופרד ברווח. שרשרת מילים מחוברות במקף (־) היא
  מילה פרוזודית אחת, כי היא נושאת טעם אחד — ולעולם לא חותכים בתוכה.
- ספירת "מילים" לצורך גבול המקטע (ברירת מחדל 4) היא ספירת מילים פרוזודיות.
"""

import html
import re
import unicodedata

from . import taamim

# --- ניקוי טקסט שמגיע מ-Sefaria -------------------------------------------

# הערות שוליים של Sefaria — מוסרות עם התוכן שלהן (טקסט זר, לא מהפסוק)
_FOOTNOTE_RE = re.compile(
    r"<sup[^>]*>.*?</sup>|<i\s+class=\"footnote\"[^>]*>.*?</i>", re.S | re.I)
# מעברי שורה — כן הופכים לרווח (מפרידים בין מילים)
_BR_RE = re.compile(r"<br\s*/?>", re.I)
# שאר התגיות מוסרות בלי רווח: MAM עוטף אותיות בודדות בתוך מילה בתגיות
# עיצוב (למשל האות הגדולה של בְּרֵאשִׁית) — רווח במקומן היה שובר את המילה.
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# סימוני פרשה {פ} {ס} וכן (פ) (ס) על וריאציותיהם
_PARASHA_RE = re.compile(r"[{(]\s*[פס]\s*[})]")
# תווי כיווניות ותווים בלתי-נראים שמגיעים לפעמים בטקסטים דיגיטליים
_INVISIBLE_RE = re.compile(r"[‎‏​⁠﻿­]")

# אותיות עבריות (כולל אותיות סופיות)
_HEBREW_LETTER_RE = re.compile(r"[א-ת]")

# טווח טעמי המקרא ב-Unicode
_CANTILLATION_RE = re.compile(r"[֑-֯׀]")  # כולל פסק


def clean_sefaria_text(text: str) -> str:
    """מנקה טקסט פסוק כפי שהוא מגיע מ-Sefaria API.

    מסיר תגיות HTML,‏ entities‏ (כמו &nbsp;), סימוני פרשה {פ}/{ס},
    תווי כיווניות בלתי-נראים, ומנרמל רווחים. לא נוגע בניקוד ובטעמים.
    """
    text = unicodedata.normalize("NFC", text)
    text = _FOOTNOTE_RE.sub(" ", text)
    text = _BR_RE.sub(" ", text)
    text = _HTML_TAG_RE.sub("", text)
    text = html.unescape(text)
    text = _PARASHA_RE.sub(" ", text)
    text = _INVISIBLE_RE.sub("", text)
    text = text.replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


# --- טוקניזציה -------------------------------------------------------------

def tokenize(verse: str) -> list:
    """מפצל פסוק נקי למילים פרוזודיות (טוקנים מופרדים ברווח).

    במקורות תקינים (MAM) מילים מחוברות במקף כתובות בלי רווח, כך שפיצול
    ברווחים שומר שרשרת-מקף כטוקן אחד. טוקנים בלי אף אות עברית נזרקים.
    """
    return [t for t in verse.split(" ") if _HEBREW_LETTER_RE.search(t)]


def letters_only(word: str) -> str:
    """אותיות עבריות בלבד — הבסיס הבטוח לכל השוואת מילים."""
    return "".join(_HEBREW_LETTER_RE.findall(word))


def word_accents(word: str) -> set:
    """קבוצת קודפוינטי הטעמים שעל מילה פרוזודית.

    שימוש בקבוצה (set) מבצע אוטומטית dedupe — קריטי מול MAM, שמוסיף
    עותק שני של טעם פוסט/פרה-פוזיטיבי (פשטא, זרקא, תלישא, סגולתא) כשהוא
    אינו על ההברה המוטעמת. מתג (U+05BD) אינו טעם ומוחרג במפורש.
    """
    return {ch for ch in word if ch in taamim.ALL_ACCENTS and ch != taamim.METEG}


def word_rank(word: str, rank_of: dict = None):
    """דרגת המפסיק החזק ביותר על המילה, או None אם אין עליה מפסיק.

    rank_of — טבלת הדרגות (ברירת מחדל: כ״א ספרים; לספרי אמ״ת מועברת
    taamim.RANK_OF_EMET — ראה rank_table_for).
    """
    if rank_of is None:
        rank_of = taamim.RANK_OF
    ranks = [rank_of[cp] for cp in word_accents(word) if cp in rank_of]
    return min(ranks) if ranks else None


def rank_table_for(words: list) -> dict:
    """בוחר את טבלת הדרגות לפסוק: אמ״ת אם מופיע בו סימן ייחודי-לאמ״ת.

    הזיהוי פר-פסוק (ולא פר-ספר) מטפל אוטומטית באיוב המעורב, ובפסוקי
    אמ״ת קצרים בלי סימן ייחודי הטבלה הרגילה ממילא נותנת חיתוך סביר.
    """
    for w in words:
        if any(ch in taamim.EMET_MARKERS for ch in w):
            return taamim.RANK_OF_EMET
    return taamim.RANK_OF


# --- אלגוריתם החיתוך -------------------------------------------------------

def _best_cut_index(words: list, rank_of: dict):
    """אינדקס המילה שאחריה חותכים, או None אם אין מפסיק פנימי.

    מועמדים: כל המילים חוץ מהאחרונה (המפסיק שעל המילה האחרונה חותם את
    היחידה כולה ואינו חלוקה פנימית). בחירה: הדרגה החזקה ביותר; שוויון —
    הקרוב ביותר לאמצע היחידה.
    """
    n = len(words)
    candidates = []  # (rank, distance_from_middle, index)
    middle = (n - 1) / 2.0
    for i in range(n - 1):
        rank = word_rank(words[i], rank_of)
        if rank is not None:
            candidates.append((rank, abs(i - middle), i))
    if not candidates:
        return None
    return min(candidates)[2]


def split_unit(words: list, max_words: int = 4, rank_of: dict = None) -> list:
    """פיצול רקורסיבי של רשימת מילים פרוזודיות למקטעים של עד max_words.

    אין מפסיק פנימי ביחידה ארוכה מדי → פולבק: חלוקה שווה על גבולות
    המילים הפרוזודיות (לעולם לא בתוך שרשרת מקף, כי היא טוקן אחד).
    """
    if rank_of is None:
        rank_of = rank_table_for(words)
    if len(words) <= max_words:
        return [words]
    cut = _best_cut_index(words, rank_of)
    if cut is None:
        cut = (len(words) // 2) - 1
    left, right = words[: cut + 1], words[cut + 1:]
    return (split_unit(left, max_words, rank_of)
            + split_unit(right, max_words, rank_of))


def verse_to_segments(verse_text: str, max_words: int = 4) -> list:
    """פסוק גולמי (מ-Sefaria) → רשימת מחרוזות-מקטע להצגה."""
    words = tokenize(clean_sefaria_text(verse_text))
    if not words:
        return []
    return [" ".join(seg) for seg in split_unit(words, max_words)]


# --- הפקת טקסט להצגה ולטקסט ליישור -----------------------------------------

# קרי-קבוע: שם ה' נקרא "אדני". החלפה ברמת מילה שלמה (אחרי ניקוי לאותיות).
# הערה מתועדת: בצירוף "אדני יהוה" השם נקרא "אלהים" — טיפול בצירוף הזה
# נדחה לשלב ה-POC (נדיר יחסית בתורה, ייבדק מול הפרקים שמוקלטים בפועל).
_QERE_PERPETUUM_PLAIN = {"יהוה": "אדני"}
_QERE_PERPETUUM_VOCALIZED = {"יהוה": "אֲדֹנָי"}

# קרי/כתיב רגיל (נפוץ מאוד בנביאים ובכתובים): במהדורות מוטעמות ה"כתיב"
# מודפס באותיות בלבד — בלי ניקוד — לצד ה"קרי" המנוקד שנקרא בפועל.
# ב-MAM כל מילה נקראת היא מנוקדת, ולכן "יש בה אות עברית אך אפס סימני
# ניקוד" הוא זיהוי בטוח לכתיב: המילה נשארת בתצוגה (כך היא מודפסת בחומש)
# אבל לא נכנסת לרשימות היישור — הקורא אינו הוגה אותה.
# ‏U+05B0–U+05BD (שווא..מתג), רפה, נקודות שי"ן/שׂי"ן, קמץ קטן — בלי סימני
# הפיסוק שביניהם (מקף U+05BE, פסק U+05C0, סוף פסוק U+05C3).
_NIQQUD_RE = re.compile("[\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C7]")


# --- מצב תפילה (PLAN_TEFILA.md משימה 4.1.2) ---------------------------------
#
# ‏mode="tanakh" (ברירת המחדל) — ההתנהגות הקיימת, בלי שום שינוי.
# ‏mode="tefila" — לסידור ולטקסט חופשי:
# - מילה בלי ניקוד אינה כתיב: בסידור (ובטקסט שמודבק) היא פשוט טקסט לא
#   מנוקד שנאמר בקול, ולכן נכנסת ליישור — באותיות בלבד.
# - שם ה׳ כתוב בסידורים בכמה צורות (ספירות אמיתיות: docs/siddur_survey.md,
#   "ממצאי המשך" סעיף ג; PLAN_TEFILA.md 8.5/8.21):
#   ‏`יהוה` (כל ניקוד, כולל הצורות הקבליות `יִהִוִהִ`/`יֻהֻוֻהֻ`), ‏`יְיָ`/`יי`,
#   ‏`ה'`/`ה׳`/`ה’` — כולן נקראות "אדני"; וגם עם תחילית של 1–3 אותיות
#   מ-ו ב כ ל מ ש ה (`לַיהֹוָה`, ‏`וּבַה'`, ‏`לַייָ`) ⇒ אותה תחילית + "אדני".
#   חריג: `יהוה` בניקוד "אלהים" (`יֱהֹוִה` — חיריק בו״ו וה״א אחרונה בלי
#   תנועה) נקרא "אלהים". ‏`ד'` אינו ממופה (כמעט תמיד המספר 4 או קיצור).
# כל זה בעותקי היישור בלבד — טקסט התצוגה לעולם לא משתנה.
ALIGN_MODES = ("tanakh", "tefila")

_NIQQUD_CLASS = "\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C7"
# תחיליות שנצמדות לשם ה׳ — אות אחת עד שלוש (לַ, וּבַ, שֶׁבַּ, וּלְ...)
_NAME_PREFIX_LETTERS = "ובכלמשה"
_MAX_NAME_PREFIX = 3
# ה׳ בקיצור: תחילית אופציונלית + "ה" + גרש (' ASCII, ‏׳ עברי, ‏’ טיפוגרפי)
# כמילה שלמה — מותרים סביבה רק סימני פיסוק/סוגריים. כך "ה',", "(ה')",
# "לה'" ו-"וַה'" הם השם, אבל לא "ג'", לא "ד'" (מספר), לא "ר'" ולא
# "ה'תשפ"ו" (אותיות אחרי הגרש).
_TEFILA_NAME_ABBR_RE = re.compile(
    f"^[^\u05D0-\u05EA]*(?:[{_NAME_PREFIX_LETTERS}][{_NIQQUD_CLASS}]*)"
    f"{{0,{_MAX_NAME_PREFIX}}}"
    f"\u05D4[{_NIQQUD_CLASS}]*['\u05F3\u2019][^\u05D0-\u05EA]*$")
# כל מה שאינו אות או ניקוד — מוסר מהגרסה המנוקדת במצב תפילה
_NON_VOCALIZED_CHARS_RE = re.compile(f"[^\u05D0-\u05EA{_NIQQUD_CLASS}]")

# תנועות (בלי דגש, מתג, רפה ונקודות שי״ן/שׂי״ן) — לזיהוי ניקוד השם והתחילית
_VOWELS = frozenset("\u05B0\u05B1\u05B2\u05B3\u05B4\u05B5\u05B6\u05B7"
                    "\u05B8\u05B9\u05BA\u05BB\u05C7")
_SHVA, _HIRIQ, _TSERE, _PATAH = "\u05B0", "\u05B4", "\u05B5", "\u05B7"
# יו״ד ראשונה של "יי" עם התנועות/הדגש האלה היא מילה אחרת ולא השם:
# ‏בִּכְיִי, ‏לְוִיַּי, ‏שְׁבוּיֵי (התאמות שווא שנמצאו בסקר)
_NOT_YY_FIRST = frozenset("\u05B4\u05B5\u05B7\u05BC")  # חיריק צירה פתח דגש

# קריאת השם: (מנוקד, מנוקד כשהתחילית בולעת את האל״ף, אותיות). לפי הדקדוק:
# לַ + אֲדֹנָי = לַאדֹנָי, ‏וְ + אֲדֹנָי = וַאדֹנָי; ‏לְ + אֱלֹהִים = לֵאלֹהִים.
_ADONAI = ("אֲדֹנָי", "אדֹנָי", "אדני")
_ELOHIM = ("אֱלֹהִים", "אלֹהִים", "אלהים")
# התנועה שהתחילית מקבלת לפני כל קריאה: שווא בתחילית מתחלף בה, והאל״ף נבלעת
_SWALLOWING_VOWEL = {_ADONAI: _PATAH, _ELOHIM: _TSERE}


def _check_mode(mode: str):
    if mode not in ALIGN_MODES:
        raise ValueError(f"מצב יישור לא מוכר: {mode!r}")


def _letter_clusters(vocalized: str) -> list:
    """"לַיְהֹוָה" → ["לַ", "יְ", "הֹ", "וָ", "ה"]: כל אות עם הניקוד שאחריה."""
    out = []
    for ch in vocalized:
        if "\u05D0" <= ch <= "\u05EA":
            out.append(ch)
        elif out:
            out[-1] += ch
    return out


def _is_name_prefix(clusters: list) -> bool:
    return (len(clusters) <= _MAX_NAME_PREFIX
            and all(c[0] in _NAME_PREFIX_LETTERS for c in clusters))


def _is_elohim_vowels(name: list) -> bool:
    """‏יהוה בניקוד "אלהים" (יֱהֹוִה, יֱהוִֹה, יְהוִה): חיריק בו״ו, ה״א
    אחרונה בלי תנועה ויו״ד בלי חיריק. הצורות הקבליות (יִהִוִהִ — חיריק תחת
    כל אות) נאמרות "אדני", ונבדלות בתנועה שבה״א האחרונה וביו״ד."""
    yod, _he, vav, last = name
    return (_HIRIQ in vav and not _VOWELS.intersection(last)
            and _HIRIQ not in yod)


def _divine_name_parts(piece: str):
    """(אשכולות התחילית, קריאה) אם החלק הוא שם ה׳ בכתיב הסידור, אחרת None.

    ‏piece — מילה אחרי פירוק מקף. הקריאה היא _ADONAI או _ELOHIM.
    """
    bare = strip_taamim(piece)
    clusters = _letter_clusters(_NON_VOCALIZED_CHARS_RE.sub("", bare))
    letters = "".join(c[0] for c in clusters)
    if _TEFILA_NAME_ABBR_RE.match(bare):
        return clusters[:-1], _ADONAI
    if letters.endswith("יהוה") and _is_name_prefix(clusters[:-4]):
        return clusters[:-4], (_ELOHIM if _is_elohim_vowels(clusters[-4:])
                               else _ADONAI)
    if letters == "יי":
        return [], _ADONAI  # ‏יְיָ / יי עומד בפני עצמו — בכל ניקוד, כמו קודם
    if (letters.endswith("יי") and _is_name_prefix(clusters[:-2])
            and not _NOT_YY_FIRST.intersection(clusters[-2])):
        return clusters[:-2], _ADONAI
    return None


def _name_alignment_word(prefix: list, reading: tuple,
                         keep_niqqud: bool) -> str:
    """תחילית + קריאת השם, כפי שהקורא הוגה: לַאדֹנָי, וַאדֹנָי, בַּאדֹנָי,
    שֶׁאֲדֹנָי, וְלֵאלֹהִים. תחילית לא מנוקדת נשארת לא מנוקדת (לה' ⇒
    לאֲדֹנָי) — הרומניזציה מטפלת בה."""
    if not keep_niqqud:
        return "".join(c[0] for c in prefix) + reading[2]
    if not prefix:
        return reading[0]
    *head, last = prefix
    swallow = _SWALLOWING_VOWEL[reading]
    last = last.replace(_SHVA, swallow)
    if swallow in last:
        return "".join(head) + last + reading[1]
    return "".join(head) + last + reading[0]


def is_tefila_divine_name(piece: str) -> bool:
    """האם החלק (מילה אחרי פירוק מקף) הוא שם ה׳ בכתיב של הסידור — כולל
    תחילית (לַיהֹוָה, וה', לַייָ) וקריאת "אלהים" (יֱהֹוִה)."""
    return _divine_name_parts(piece) is not None


def is_ketiv(word: str) -> bool:
    """מילה שמופיעה בטקסט אך אינה נקראת: יש אותיות, אין שום ניקוד."""
    return bool(_HEBREW_LETTER_RE.search(word)) and not _NIQQUD_RE.search(word)


def strip_taamim(word: str) -> str:
    """מסיר טעמים (ומתג) ומשאיר אותיות + ניקוד — למסלול MMS+uroman."""
    word = _CANTILLATION_RE.sub("", word)
    word = word.replace(taamim.METEG, "")
    return word.replace(taamim.SOF_PASUQ, "").strip()


def to_alignment_words(prosodic_word: str, keep_niqqud: bool,
                       mode: str = "tanakh") -> list:
    """מילה פרוזודית → רשימת מילים כפי שהקורא הוגה אותן.

    שרשרת מקף נפתחת למילים נפרדות (הקורא הוגה כל אחת), וקרי-קבוע מוחלף.
    keep_niqqud=True למסלול MMS+uroman (מנוקד), False למודל עברי (אותיות).
    ‏mode="tefila" — בלי זריקת כתיב, ומפת שם ה׳ של הסידור (ראה למעלה).
    """
    _check_mode(mode)
    out = []
    for piece in prosodic_word.split(taamim.MAQAF):
        plain = letters_only(piece)
        if not plain:
            continue
        if mode == "tefila":
            out.append(_tefila_alignment_word(piece, plain, keep_niqqud))
            continue
        if is_ketiv(piece):
            continue  # כתיב לא-נקרא: נשאר בתצוגה, לא ביישור
        if plain in _QERE_PERPETUUM_PLAIN:
            out.append(_QERE_PERPETUUM_VOCALIZED[plain] if keep_niqqud
                       else _QERE_PERPETUUM_PLAIN[plain])
        elif keep_niqqud:
            out.append(strip_taamim(piece))
        else:
            out.append(plain)
    return out


def _tefila_alignment_word(piece: str, plain: str, keep_niqqud: bool) -> str:
    """חלק-מילה אחד במצב תפילה: שם ה׳ ⇒ (תחילית +) אדני/אלהים; אחרת
    המילה כפי שהיא.

    בגרסה המנוקדת נשארים רק אותיות וניקוד — בטקסט חופשי יש פיסוק רגיל
    (פסיקים, גרשיים, סימן פיסוק מודבק) שאין לו מקום ברומניזציה. גם תווי
    הטעמים שמצודה משתמשת בהם כסימני הגייה (U+0592, ‏U+05AF — PLAN_TEFILA
    8.24) נופלים כאן, ב-strip_taamim.
    """
    parts = _divine_name_parts(piece)
    if parts is not None:
        return _name_alignment_word(*parts, keep_niqqud)
    if keep_niqqud:
        return _NON_VOCALIZED_CHARS_RE.sub("", strip_taamim(piece))
    return plain


def build_segment(words: list, mode: str = "tanakh") -> dict:
    """רשימת מילים פרוזודיות → מקטע: טקסט תצוגה ושתי גרסאות יישור.

    זהו האינווריאנט הקריטי של ה-pipeline: שלוש הגרסאות נגזרות מאותם
    טוקנים, ולכן מיושרות מקטע-למקטע מבנייתן.
    """
    return {
        "display": " ".join(words),
        "align_vocalized": [w for pw in words for w in
                            to_alignment_words(pw, True, mode)],
        "align_plain": [w for pw in words for w in
                        to_alignment_words(pw, False, mode)],
    }


def segments_for_pipeline(verse_text: str, max_words: int = 4,
                          mode: str = "tanakh") -> list:
    """הפלט המלא לשלבי ההמשך — חיתוך פסוק יחיד לפי הטעמים."""
    words = tokenize(clean_sefaria_text(verse_text))
    result = [build_segment(seg, mode)
              for seg in (split_unit(words, max_words) if words else [])]
    return _merge_unalignable(result)


def regroup_words(words: list, sizes: list, verse_of: list = None,
                  mode: str = "tanakh") -> list:
    """חלוקה מותאמת אישית: אותן מילים פרוזודיות, קיבוץ שהמשתמש קבע.

    ‏sizes הוא מספר המילים בכל מקטע (סכומו = מספר המילים). סדר המילים
    לעולם אינו משתנה — העריכה בממשק מזיזה גבולות בלבד — ולכן החלוקה
    שנשלחת מהטלפון נבנית כאן מחדש בדיוק כפי שנראתה שם.
    """
    total = sum(sizes)
    if total != len(words):
        raise ValueError(
            f"החלוקה המותאמת אישית מכסה {total} מילים אבל בטקסט {len(words)} — "
            "טען את הקטע מחדש ונסה שוב")
    result, i = [], 0
    for n in sizes:
        if n < 1:
            raise ValueError("כל כתובית חייבת לכלול לפחות מילה אחת")
        seg = build_segment(words[i:i + n], mode)
        if verse_of is not None:
            seg["verse"] = verse_of[i]
        result.append(seg)
        i += n
    return _merge_unalignable(result)


def _merge_unalignable(segments: list) -> list:
    """מקטע בלי אף מילת-יישור (למשל כולו כתיב) מוזג לשכנו.

    שלבי היישור מניחים שלכל מקטע יש לפחות מילה אחת נשמעת — מקטע ריק היה
    שובר את חישוב הגבולות. התצוגה נשמרת במלואה, רק מצטרפת לשכן.
    """
    merged = []
    pending = ""  # תצוגה שממתינה למקטע נושא-מילים (כשאין עדיין קודם)
    for seg in segments:
        if not seg["align_vocalized"]:
            if merged:
                merged[-1]["display"] += " " + seg["display"]
            else:
                pending = (pending + " " + seg["display"]).strip()
            continue
        if pending:
            seg["display"] = pending + " " + seg["display"]
            pending = ""
        merged.append(seg)
    if pending and merged:
        merged[-1]["display"] += " " + pending
    # פסוק שכולו בלתי-נשמע (לא קיים ב-MAM) → ריק, כמו פסוק בלי מילים
    return merged
