# -*- coding: utf-8 -*-
"""ולידציית הפרמטרים של ה-worker בענן — Python טהור, נבדק בלי modal.

מקבל את שדות הטופס שהאפליקציה שולחת (מחרוזות) ומחזיר בדיוק את הארגומנטים
ש-run_hybrid מצפה להם. ריק/0 = None, כמו בתא הפרמטרים של worker.ipynb.
"""

import json
import sys
from pathlib import Path

# רשימת הספרים חיה ב-src/chunker/books.py (מקור אמת יחיד). שני מיקומים:
# פריסת הריפו (../src) והקונטיינר של Modal‏ (src/ לצד הקובץ, ראה app.py).
for _cand in (Path(__file__).resolve().parent.parent / "src",
              Path(__file__).resolve().parent / "src"):
    if _cand.is_dir():
        sys.path.insert(0, str(_cand))
try:
    from chunker.books import is_known as _book_is_known
except ImportError:
    # בלי הרשימה לא חוסמים: הצינור עצמו ייכשל עם הודעה ברורה מול Sefaria
    _book_is_known = None

MAX_WORDS_DEFAULT = 4
MAX_WORDS_RANGE = (1, 10)


def _int_or_none(value, name, minimum=1):
    """מחרוזת/מספר → int, או None עבור ריק/0 (מוסכמת "השאר 0" מה-notebook)."""
    if value is None or str(value).strip() in ("", "0"):
        return None
    try:
        n = int(str(value).strip())
    except ValueError:
        raise ValueError(f"{name} חייב להיות מספר שלם")
    if n < minimum:
        raise ValueError(f"{name} חייב להיות לפחות {minimum}")
    return n


def parse_params(form: dict) -> dict:
    """שדות הטופס → ארגומנטים ל-run_hybrid. זורק ValueError עם הודעה בעברית."""
    book = str(form.get("book") or "").strip()
    if not book:
        raise ValueError("חסר שם ספר")
    if _book_is_known is not None and not _book_is_known(book):
        raise ValueError(
            "ספר לא מוכר: " + book
            + " — נתמכים כל ספרי התנ״ך (בשמם העברי או בשם Sefaria באנגלית)")

    chapter = _int_or_none(form.get("chapter"), "פרק")
    if chapter is None:
        raise ValueError("חסר מספר פרק")

    verse_start = _int_or_none(form.get("verse_start"), "פסוק התחלה")
    verse_end = _int_or_none(form.get("verse_end"), "פסוק סיום")
    chapter_end = _int_or_none(form.get("chapter_end"), "פרק סיום")
    if chapter_end is not None and chapter_end < chapter:
        raise ValueError("פרק הסיום קטן מפרק ההתחלה")
    if (verse_end is not None and chapter_end is None and verse_start is not None
            and verse_end < verse_start):
        raise ValueError("פסוק הסיום קטן מפסוק ההתחלה")

    max_words = _int_or_none(form.get("max_words"), "מקסימום מילים במקטע")
    if max_words is None:
        max_words = MAX_WORDS_DEFAULT
    lo, hi = MAX_WORDS_RANGE
    if not lo <= max_words <= hi:
        raise ValueError(f"מקסימום מילים במקטע חייב להיות בין {lo} ל-{hi}")

    return {
        "book": book,
        "chapter": chapter,
        "verse_start": verse_start,
        "verse_end": verse_end,
        "chapter_end": chapter_end,
        "max_words": max_words,
    }


def parse_push_sub(raw):
    """שדה ה-push_sub מהטופס → dict של PushSubscription, או None.

    ההתראות הן best-effort: כל קלט שאינו subscription תקין פשוט מתעלמים
    ממנו בשקט — העיבוד עצמו לעולם לא נכשל בגלל שדה ההתראה.
    """
    if not raw or not str(raw).strip():
        return None
    try:
        sub = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(sub, dict):
        return None
    endpoint = sub.get("endpoint")
    if not isinstance(endpoint, str) or not endpoint.startswith("https://"):
        return None
    keys = sub.get("keys")
    if not isinstance(keys, dict) or not keys.get("p256dh") or not keys.get("auth"):
        return None
    return {"endpoint": endpoint, "keys": {"p256dh": keys["p256dh"],
                                           "auth": keys["auth"]}}
