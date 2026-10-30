# -*- coding: utf-8 -*-
"""פרופילי ביצוע לצינור ההיברידי: קריאה (ברירת המחדל) ושירה.

כל ערכי הכיול של פרופיל במקום אחד, כדי שכיול עתידי (PLAN_TEFILA.md 4.3.5,
‏8.12) יהיה שינוי של מספר כאן ולא חיפוש בקוד. Python טהור.

‏reading — ההתנהגות הקיימת, בלי שום שינוי (כל השדות בערכי "כבוי").
‏singing — חזנות/שירה בתפילה ובטקסט חופשי. כויל על הקלטה אחת
(samples/nishmat, ‏results.md) — ⚠️ לאמת על הקלטות נוספות (8.27):
- א. תמלול בלי vad_filter: silero מסווג חזנות כ"לא דיבור" (20% בלבד בנשמת)
  וה-ASR איבד את כל השירה אחרי 58 ש׳.
- ב. זיהוי "דיבור שאינו בטקסט" (הקדמה, הכרזה, שם ניגון) מתוך התמלול: עוגנים
  בתוכו נזרקים, ותחילת השורה שאחריו חסומה מלמטה בסוף הדיבור.
- ג. טוקן כוכב (*) של MMS בקצות חלון ולפני תחילות שורה — בולע אודיו שאינו
  בטקסט שהתמלול לא תפס. לא בין כל המילים (מילה קצרה נצמדת לדומה לה בדיבור).
- ד. גם עוגני הגיוס השני צריכים הקשר (שם הניגון "אני" נכנס כעוגן ל"אֵין").
- ה. חלון נכשל כשבין תחילות מילים עוקבות יותר מ-20 ש׳ (CTC דוחס מילים על
  מליסמה ארוכה) ⇒ מיזוג ⇒ אינטרפולציה משוקללת-אותיות מחוץ לדיבור שזוהה.
- ו. ‏_MAX_WORD_SEC ‏12→20; בלי הצמדת VAD אלא אם ≥50% מההקלטה זוהו כדיבור.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NonTextParams:
    """זיהוי ריצות של דיבור שאינו בטקסט (ב) — ראה anchors.nontext_runs."""
    text_sim: float = 0.6        # מילת תמלול עם זוג בדמיון ≥ זה = "טקסט"
    max_word_sec: float = 0.6    # דיבור: כל מילה קצרה מזה (מילה מושרת 0.7–2 ש׳)
    min_words: int = 3           # ריצה: לפחות כך מילים לא-טקסט רצופות
    min_total_sec: float = 0.8   # ובאורך כולל של לפחות כך
    split_gap_sec: float = 1.0   # מרווח גדול מזה בין מילים חותך ריצה
    merge_gap_sec: float = 3.0   # ריצות סמוכות בלי מילת טקסט ביניהן — מתאחדות
    drop_before_sec: float = 1.0  # עוגן שמתחיל עד כך לפני הריצה (או בתוכה) — נזרק
    min_sec_per_word: float = 0.15  # חסם-דמה רק אם יש מקום סביר למילים משני צדיו

    def detect_kwargs(self) -> dict:
        return {"text_sim": self.text_sim, "max_word_sec": self.max_word_sec,
                "min_words": self.min_words,
                "min_total_sec": self.min_total_sec,
                "split_gap_sec": self.split_gap_sec,
                "merge_gap_sec": self.merge_gap_sec}

    def apply_kwargs(self) -> dict:
        return {"drop_before_sec": self.drop_before_sec,
                "min_sec_per_word": self.min_sec_per_word}


@dataclass(frozen=True)
class Profile:
    name: str
    label: str                                 # לדוח, בעברית
    asr_vad_filter: bool = True                # א
    nontext: Optional[NonTextParams] = None    # ב (None = כבוי)
    star: bool = False                         # ג
    recruit_context: bool = False              # ד
    max_start_gap_sec: Optional[float] = None  # ה (None = כבוי)
    max_word_sec: Optional[float] = None       # ו (None = hybrid._MAX_WORD_SEC)
    vad_snap_min_speech: float = 0.0           # ו (0 = תמיד מצמידים)


PROFILES = {
    "reading": Profile("reading", "קריאה"),
    "singing": Profile(
        "singing", "שירה",
        asr_vad_filter=False,
        nontext=NonTextParams(),
        star=True,
        recruit_context=True,
        max_start_gap_sec=20.0,
        max_word_sec=20.0,
        vad_snap_min_speech=0.5,
    ),
}


def get_profile(name: str) -> Profile:
    try:
        return PROFILES[name]
    except KeyError:
        raise ValueError(f"פרופיל לא מוכר: {name!r} — נתמכים: "
                         + ", ".join(PROFILES)) from None
