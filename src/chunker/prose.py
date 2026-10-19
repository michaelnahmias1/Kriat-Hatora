# -*- coding: utf-8 -*-
"""חיתוך טקסט לא-מוטעם (תפילה, פיוט, טקסט חופשי) למקטעי כתוביות לפי פיסוק.

המקבילה של החיתוך לפי הטעמים (chunker.py) לטקסט שאין בו טעמי מקרא.
ראה PLAN_TEFILA.md משימה 4.1.1. Python טהור, אפס תלויות.

היררכיית החיתוך (דרגה נמוכה = חזק, כמו בטעמים):
1. סוף שורה/פסקה — גבול קשיח: כל שורה נחתכת בנפרד, שורות לא מתאחדות.
2. ‏`.` `:` `׃` `;` `?` `!` בסוף מילה.
3. ‏`,` `–` `—` `-` בסוף מילה.
4. אין מפסיק ביחידה ארוכה מדי ⇒ חלוקה שווה (כמו הפולבק של split_unit).
שובר-שוויון: הקרוב לאמצע. לעולם לא חותכים בתוך שרשרת מקף.

יחידה עם טעמי מקרא (פסוק מצוטט) אינה מגיעה לכאן — הניתוב לחותך הטעמים
נעשה ב-aligner.pipeline לפי שדה chunk של היחידה.
"""

import re
import unicodedata

from . import taamim
from .chunker import (_BR_RE, _FOOTNOTE_RE, _HEBREW_LETTER_RE,
                      _merge_unalignable, build_segment, clean_sefaria_text)

# --- טוקניזציה --------------------------------------------------------------

# טוקן בלי אות עברית (מקף-פיסוק " – ", נקודתיים בודדות, מספר) נדבק לשכנו
# ברווח קשיח (NBSP) במקום להיזרק כמו בחותך הטעמים: הטקסט הוא הערך, והתצוגה
# חייבת להראות אותו. NBSP אינו רווח רגיל — הדפדפן (tokensOf) והשרת סופרים
# את הטוקן המודבק כמילה אחת, ולכן ספירת המילים לא מתפצלת.
_GLUE = "\u00a0"
# טוקן שכולו סימני פתיחה נדבק קדימה (למילה שאחריו), כל טוקן אחר — אחורה
_OPENERS = frozenset("([{„«‹")

# גוף המילה: אותיות + ניקוד וטעמים. מקף, פסק וסוף-פסוק אינם בגוף — הם
# סימני פיסוק ונבדקים בזנב המילה.
_BODY_CHARS = "א-ת֑-ׇֽֿׁׂׅׄ"
_TAIL_RE = re.compile(f"[^{_BODY_CHARS}]*$")

STRONG_PUNCT = frozenset(".:;?!׃")       # דרגה 2
WEAK_PUNCT = frozenset(",–—-")           # דרגה 3
RANK_LINE, RANK_STRONG, RANK_WEAK = 1, 2, 3


def _glue_tokens(raw: list) -> list:
    """טוקנים מופרדי-רווח → טוקנים שבכל אחד אות עברית (הדבקת הפיסוק)."""
    out, prefix = [], ""
    for tok in raw:
        if not tok:
            continue
        if _HEBREW_LETTER_RE.search(tok):
            out.append(prefix + tok)
            prefix = ""
        elif out and not all(ch in _OPENERS for ch in tok):
            out[-1] += _GLUE + tok
        else:
            prefix += tok + _GLUE
    # סימני פתיחה בסוף שורה (נדיר) — נדבקים אחורה, לא הולכים לאיבוד
    if prefix and out:
        out[-1] += _GLUE + prefix.rstrip(_GLUE)
    return out


def prose_lines(text: str) -> list:
    """טקסט גולמי → רשימת שורות, כל שורה רשימת מילים פרוזודיות.

    מעברי שורה (‏\\n או ‏<br>) נשמרים כגבול; כל שורה מנוקה בנפרד עם
    clean_sefaria_text. שורה בלי אף אות עברית נזרקת.
    """
    text = unicodedata.normalize("NFC", text)
    text = _FOOTNOTE_RE.sub(" ", text)  # לפני הפיצול — הערה יכולה לחצות שורה
    text = _BR_RE.sub("\n", text)
    lines = []
    for line in text.splitlines():
        words = _glue_tokens(clean_sefaria_text(line).split(" "))
        if words:
            lines.append(words)
    return lines


def prose_tokens(text: str) -> list:
    """כל המילים הפרוזודיות של הטקסט ברצף אחד — הבסיס לחלוקה מותאמת אישית.

    זהו רצף המילים שהדפדפן רואה (התצוגה מחוברת ברווחים), ולכן splits
    שנשלחים מהטלפון נבנים עליו מחדש בדיוק.
    """
    return [w for line in prose_lines(text) for w in line]


# --- אלגוריתם החיתוך --------------------------------------------------------

def break_rank(word: str):
    """דרגת סימן הפיסוק שבסוף המילה, או None אם אין בה מפסיק."""
    tail = _TAIL_RE.search(word).group()
    if any(ch in STRONG_PUNCT for ch in tail):
        return RANK_STRONG
    if any(ch in WEAK_PUNCT for ch in tail):
        return RANK_WEAK
    return None


def _can_cut_after(words: list, i: int) -> bool:
    """אסור לחתוך בתוך שרשרת מקף — גם כשהוקלד רווח ליד המקף."""
    return (not words[i].endswith(taamim.MAQAF)
            and not words[i + 1].startswith(taamim.MAQAF))


def split_prose(words: list, max_words: int = 4) -> list:
    """פיצול רקורסיבי של שורה אחת למקטעים של עד max_words מילים.

    מועמדים: כל המילים חוץ מהאחרונה (הפיסוק שבסוף השורה חותם אותה ואינו
    חלוקה פנימית). בחירה: הדרגה החזקה; שוויון — הקרוב לאמצע. אין פיסוק ⇒
    חלוקה שווה על הגבול המותר הקרוב לאמצע; אין גבול מותר כלל ⇒ השורה
    נשארת שלמה (שרשרת מקף אחת ארוכה).
    """
    n = len(words)
    if n <= max_words:
        return [words]
    middle = (n - 1) / 2.0
    allowed = [i for i in range(n - 1) if _can_cut_after(words, i)]
    candidates = [(break_rank(words[i]), abs(i - middle), i) for i in allowed
                  if break_rank(words[i]) is not None]
    if candidates:
        cut = min(candidates)[2]
    elif allowed:
        target = (n // 2) - 1  # כמו הפולבק של split_unit
        cut = min(allowed, key=lambda i: (abs(i - target), i))
    else:
        return [words]
    return (split_prose(words[:cut + 1], max_words)
            + split_prose(words[cut + 1:], max_words))


def prose_segments(text: str, max_words: int = 4,
                   mode: str = "tanakh") -> list:
    """טקסט לא-מוטעם → מקטעים לשלבי ההמשך (display + מילות יישור).

    אותו פורמט בדיוק כמו segments_for_pipeline, כולל מיזוג מקטע בלי
    מילה נשמעת לשכנו. לטקסט תפילה/חופשי מעבירים mode="tefila" — אחרת
    מילה לא מנוקדת נחשבת כתיב ונזרקת מהיישור (ההתנהגות של התנ״ך).
    """
    result = [build_segment(seg, mode)
              for line in prose_lines(text)
              for seg in split_prose(line, max_words)]
    return _merge_unalignable(result)
