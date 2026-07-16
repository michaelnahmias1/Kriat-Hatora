# -*- coding: utf-8 -*-
"""טבלת טעמי המקרא — כ״א ספרים (לא ספרי אמ״ת).

דרגות המפסיקים לפי ההיררכיה המסורתית (קיסרים/מלכים/משנים/שלישים).
דרגה נמוכה יותר = מפסיק חזק יותר.

הערות קידוד קריטיות:
- זרקא: בגלל החלפת-שמות היסטורית ב-Unicode, זרקא של כ״א ספרים מקודדת
  בטקסטים אמיתיים לעיתים כ-U+05AE (ZINOR) ולעיתים כ-U+0598 (ZARQA).
  שני הקודפוינטים נכללים בדרגה 3. איזה מהם מופיע בפועל ב-MAM — מוכרע
  אמפירית בתא ספירת-התדירויות ב-notebook האימותים.
- סילוק (סוף פסוק) חולק קודפוינט עם מתג (U+05BD) — לכן U+05BD לעולם
  אינו נקודת חיתוך. החיתוך בסוף פסוק נעשה על סוף-פסוק U+05C3.
"""

# ---- מפסיקים -------------------------------------------------------------

SOF_PASUQ = "׃"        # ׃ סימן פיסוק, לא טעם — מסמן את הסילוק בבטחה
ETNAHTA = "֑"          # אתנחתא

SEGOLTA = "֒"          # סגולתא
SHALSHELET = "֓"       # שלשלת
ZAQEF_QATAN = "֔"      # זקף קטן
ZAQEF_GADOL = "֕"      # זקף גדול
TIPEHA = "֖"           # טפחא

REVIA = "֗"            # רביע
ZARQA = "֘"            # "ZARQA" בשמות Unicode (בפועל לרוב צינורית)
ZINOR = "֮"            # "ZINOR" — בפועל לרוב הזרקא של כ״א ספרים
PASHTA = "֙"           # פשטא
YETIV = "֚"            # יתיב
TEVIR = "֛"            # תביר

GERESH = "֜"           # גרש
GERSHAYIM = "֞"        # גרשיים
QARNEY_PARA = "֟"      # קרני פרה
TELISHA_GEDOLA = "֠"   # תלישא גדולה
PAZER = "֡"            # פזר

# ---- משרתים — לעולם לא נקודת חיתוך ---------------------------------------

MUNAH = "֣"            # מונח
MAHAPAKH = "֤"         # מהפך
MERKHA = "֥"           # מרכא
MERKHA_KEFULA = "֦"    # מרכא כפולה
DARGA = "֧"            # דרגא
QADMA = "֨"            # קדמא
TELISHA_QETANA = "֩"   # תלישא קטנה
YERAH_BEN_YOMO = "֪"   # ירח בן יומו
GERESH_MUQDAM = "֝"    # גרש מוקדם (נדיר)

SERVANTS = frozenset({
    MUNAH, MAHAPAKH, MERKHA, MERKHA_KEFULA, DARGA,
    QADMA, TELISHA_QETANA, YERAH_BEN_YOMO, GERESH_MUQDAM,
})

# ---- סימנים שאינם טעמים אך רלוונטיים -------------------------------------

METEG = "ֽ"            # מתג / סילוק — אף פעם לא חיתוך
MAQAF = "־"            # מקף — מחבר מילים ליחידה פרוזודית אחת
PASEQ = "׀"            # פסק (לגרמיה = משרת + פסק; מתעלמים ב-v1)

# ---- דרגות ---------------------------------------------------------------

DISJUNCTIVES_BY_RANK = {
    1: frozenset({SOF_PASUQ, ETNAHTA}),
    2: frozenset({SEGOLTA, SHALSHELET, ZAQEF_QATAN, ZAQEF_GADOL, TIPEHA}),
    3: frozenset({REVIA, ZARQA, ZINOR, PASHTA, YETIV, TEVIR}),
    4: frozenset({GERESH, GERSHAYIM, QARNEY_PARA, TELISHA_GEDOLA, PAZER}),
}

# מיפוי הפוך: קודפוינט -> דרגה
RANK_OF = {cp: rank for rank, cps in DISJUNCTIVES_BY_RANK.items() for cp in cps}

# כלל טעמי המקרא של כ״א ספרים (לזיהוי/הסרה), בלי מתג שהוא נקודת ניקוד
ALL_ACCENTS = frozenset(RANK_OF) | SERVANTS | {PASEQ}
