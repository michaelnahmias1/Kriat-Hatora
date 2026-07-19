# -*- coding: utf-8 -*-
"""ספרי התנ״ך — מיפוי עברית ← שמות Sefaria באנגלית, לכל 39 הספרים.

מקור האמת היחיד לרשימת הספרים: משרת את ה-API‏ (api/segments, api/structure),
את הצינור (src/aligner) ואת ולידציית ה-worker‏ (modal_worker/params).
תפריט הספרים ב-index.html נבנה ידנית מאותה רשימה (דף סטטי — אין לו import).

שמות הספרים באנגלית הם הכותרות הקנוניות של Sefaria‏ (I Samuel, Song of
Songs וכו') — כך נבנים refs תקינים בלי ניחושים.
"""

# (עברית, אנגלית-Sefaria) לפי סדר המקרא. שמואל/מלכים/דברי-הימים מפוצלים
# כמו ב-Sefaria; עזרא ונחמיה ספרים נפרדים.
TORAH = (
    ("בראשית", "Genesis"), ("שמות", "Exodus"), ("ויקרא", "Leviticus"),
    ("במדבר", "Numbers"), ("דברים", "Deuteronomy"),
)
NEVIIM = (
    ("יהושע", "Joshua"), ("שופטים", "Judges"),
    ("שמואל א", "I Samuel"), ("שמואל ב", "II Samuel"),
    ("מלכים א", "I Kings"), ("מלכים ב", "II Kings"),
    ("ישעיהו", "Isaiah"), ("ירמיהו", "Jeremiah"), ("יחזקאל", "Ezekiel"),
    ("הושע", "Hosea"), ("יואל", "Joel"), ("עמוס", "Amos"),
    ("עובדיה", "Obadiah"), ("יונה", "Jonah"), ("מיכה", "Micah"),
    ("נחום", "Nahum"), ("חבקוק", "Habakkuk"), ("צפניה", "Zephaniah"),
    ("חגי", "Haggai"), ("זכריה", "Zechariah"), ("מלאכי", "Malachi"),
)
KETUVIM = (
    ("תהלים", "Psalms"), ("משלי", "Proverbs"), ("איוב", "Job"),
    ("שיר השירים", "Song of Songs"), ("רות", "Ruth"), ("איכה", "Lamentations"),
    ("קהלת", "Ecclesiastes"), ("אסתר", "Esther"), ("דניאל", "Daniel"),
    ("עזרא", "Ezra"), ("נחמיה", "Nehemiah"),
    ("דברי הימים א", "I Chronicles"), ("דברי הימים ב", "II Chronicles"),
)

ALL_BOOKS = TORAH + NEVIIM + KETUVIM

# כתיבים חלופיים נפוצים — מתקבלים בקלט אבל לא מוצגים בתפריט
_ALIASES = {
    "תהילים": "Psalms", "ישעיה": "Isaiah", "ירמיה": "Jeremiah",
    "קוהלת": "Ecclesiastes", "שיר-השירים": "Song of Songs",
    "דברי-הימים א": "I Chronicles", "דברי-הימים ב": "II Chronicles",
}

HE_TO_EN = {he: en for he, en in ALL_BOOKS}
HE_TO_EN.update(_ALIASES)
EN_TITLES = frozenset(en for _, en in ALL_BOOKS)


def to_english(book: str) -> str:
    """שם ספר (עברית או אנגלית) → הכותרת האנגלית של Sefaria.

    שם לא מוכר מוחזר כמו שהוא — Sefaria עצמה תדחה refs שגויים עם 404,
    וכך גם כותרים חוקיים שאינם ברשימה (למשל וריאציות אנגליות) עוברים.
    """
    return HE_TO_EN.get((book or "").strip(), (book or "").strip())


def is_known(book: str) -> bool:
    """האם השם (עברית/אנגלית, אחרי strip) מוכר לרשימת הקנון."""
    b = (book or "").strip()
    return b in HE_TO_EN or b in EN_TITLES
