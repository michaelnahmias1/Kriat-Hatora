# -*- coding: utf-8 -*-
"""ולידציית הפרמטרים של ה-worker בענן — Python טהור, נבדק בלי modal.

מקבל את שדות הטופס שהאפליקציה שולחת (מחרוזות) ומחזיר בדיוק את הארגומנטים
ש-run_hybrid מצפה להם. ריק/0 = None, כמו בתא הפרמטרים של worker.ipynb.

מקור הטקסט (PLAN_TEFILA.md 3.3): ‏source ריק/‏tanakh ⇒ הוולידציה של היום
כלשונה, והמילון שחוזר זהה לזה של היום (דפדפן ישן שלא מכיר את השדות
החדשים מקבל בדיוק את אותה התנהגות). ‏source=text/siddur ⇒ הדפדפן שולח את
יחידות הטקסט עצמן (‏units, ‏JSON) והן עוברות ל-run_hybrid_units.
"""

import json
import re
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


MAX_SPLIT_WORDS = 20000  # תקרת שפיות: הרבה מעבר לכל טווח קריאה אמיתי

# --- מקור טקסט: יחידות (PLAN_TEFILA.md 3.1–3.3) ---------------------------
SOURCES = ("tanakh", "text", "siddur")
# העתק של src/aligner/pipeline.py‏ (UNIT_KINDS / CHUNK_MODES) — לא מייבאים
# משם כי ה-image של ה-web לא אמור לטעון את הצינור; בדיקה שומרת על הסנכרון
UNIT_KINDS = ("verse", "line", "paragraph", "stanza", "refrain", "instruction")
CHUNK_MODES = ("taamim", "punct")
PROFILES = ("reading", "singing")
MAX_UNITS_BYTES = 200 * 1024   # ה-JSON הגולמי של units (תפילה ארוכה ≈ עשרות KB)
MAX_UNITS = 3000               # מעבר לכל תפילה/מחזור שמסנכרנים בהקלטה אחת
MAX_UNIT_TEXT = 20000          # תווים ביחידה אחת
MAX_LABEL = 200
MAX_TITLE = 120
MAX_PERFORMANCE = 20000        # כמו MAX_SPLIT_WORDS — כולל חזרות פזמון
_HEBREW_LETTER = re.compile(r"[\u05D0-\u05EA]")


def _parse_max_words(value) -> int:
    max_words = _int_or_none(value, "מקסימום מילים במקטע")
    if max_words is None:
        max_words = MAX_WORDS_DEFAULT
    lo, hi = MAX_WORDS_RANGE
    if not lo <= max_words <= hi:
        raise ValueError(f"מקסימום מילים במקטע חייב להיות בין {lo} ל-{hi}")
    return max_words


def parse_splits(raw):
    """שדה ה-splits מהטופס → רשימת גדלי כתוביות (int), או None.

    זו החלוקה שהמשתמש ערך ידנית בממשק. חלוקה פגומה היא שגיאת קלט ולא
    "מתעלמים ממנה בשקט": ריצה עם החלוקה האוטומטית הייתה מחזירה כתוביות
    שלא תואמות את מה שהמשתמש רואה על המסך.
    """
    if raw is None or not str(raw).strip():
        return None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raise ValueError("חלוקת הכתוביות שנשלחה אינה תקינה")
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError("חלוקת הכתוביות שנשלחה אינה תקינה")
    sizes = []
    for n in raw:
        if isinstance(n, bool) or not isinstance(n, int):
            raise ValueError("חלוקת הכתוביות שנשלחה אינה תקינה")
        if n < 1:
            raise ValueError("כל כתובית חייבת לכלול לפחות מילה אחת")
        sizes.append(n)
    if sum(sizes) > MAX_SPLIT_WORDS:
        raise ValueError("חלוקת הכתוביות ארוכה מדי")
    return sizes


def parse_params(form: dict) -> dict:
    """שדות הטופס → ארגומנטים לצינור. זורק ValueError עם הודעה בעברית.

    בלי source (או tanakh) — בדיוק המילון של היום (‏run_hybrid). עם
    text/siddur — מילון יחידות (‏run_hybrid_units, ראה _parse_units_params).
    """
    source = str(form.get("source") or "").strip() or "tanakh"
    if source not in SOURCES:
        raise ValueError("מקור טקסט לא מוכר: " + source
                         + " — נתמכים: תנ״ך, תפילה (siddur) וטקסט חופשי (text)")
    if source != "tanakh":
        return _parse_units_params(form, source)
    params = _parse_tanakh_params(form)
    # שדות התפילה לא קיימים במסלול התנ״ך — עדיף שגיאה ברורה מהתעלמות שקטה
    if parse_performance(form.get("performance")) is not None:
        raise ValueError("סדר ביצוע (performance) נתמך רק בתפילה ובטקסט חופשי")
    if parse_profile(form.get("profile")) != "reading":
        raise ValueError("פרופיל שירה נתמך רק בתפילה ובטקסט חופשי")
    title = parse_title(form.get("title"))
    if title:
        params["title"] = title  # תווית להתראה בלבד; לא נוגע בצינור
    return params


def _parse_tanakh_params(form: dict) -> dict:
    """מסלול התנ״ך — הוולידציה של לפני הרחבת התפילה, ללא שינוי."""
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

    max_words = _parse_max_words(form.get("max_words"))

    return {
        "book": book,
        "chapter": chapter,
        "verse_start": verse_start,
        "verse_end": verse_end,
        "chapter_end": chapter_end,
        "max_words": max_words,
        "splits": parse_splits(form.get("splits")),
    }


def parse_title(raw) -> str:
    """כותרת חופשית (תווית להתראה ולשם הקובץ) → מחרוזת מקוצצת, או ""."""
    if raw is None:
        return ""
    title = " ".join(str(raw).split())
    if len(title) > MAX_TITLE:
        raise ValueError(f"הכותרת ארוכה מדי (עד {MAX_TITLE} תווים)")
    return title


def parse_profile(raw) -> str:
    """פרופיל הביצוע: ריק ⇒ reading (ההתנהגות של היום)."""
    profile = str(raw or "").strip() or "reading"
    if profile not in PROFILES:
        raise ValueError("פרופיל לא מוכר: " + profile
                         + " — נתמכים reading (קריאה) ו-singing (שירה)")
    return profile


def parse_performance(raw):
    """סדר הביצוע (PLAN_TEFILA.md 3.2) → רשימת אינדקסי כתוביות, או None.

    כאן נבדקת רק הצורה (מספרים שלמים אי-שליליים, לא ריק, תקרת אורך). הטווח
    מול מספר הכתוביות נבדק ב-_parse_units_params כשה-splits ידוע מראש,
    ואחרת — רק אחרי החיתוך, בצינור עצמו (run_hybrid_units, משימה 4.3).
    """
    if raw is None or not str(raw).strip():
        return None
    bad = "סדר הביצוע (performance) שנשלח אינו תקין"
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raise ValueError(bad)
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError(bad)
    if len(raw) > MAX_PERFORMANCE:
        raise ValueError("סדר הביצוע ארוך מדי")
    order = []
    for n in raw:
        if isinstance(n, bool) or not isinstance(n, int):
            raise ValueError(bad)
        if n < 0:
            raise ValueError("אינדקס בסדר הביצוע חייב להיות 0 ומעלה")
        order.append(n)
    return order


def parse_units(raw) -> list:
    """שדה ה-units מהטופס (JSON) → רשימת יחידות מנורמלת (PLAN_TEFILA.md 3.1).

    כל יחידה: ‏text (חובה), ‏label / ‏kind / ‏chunk (אופציונליים, מערכים
    מוכרים בלבד). שדות אחרים נזרקים. חייבת להיות אות עברית ביחידה נשמעת
    כלשהי — אחרת אין מה ליישר.
    """
    if raw is None or not str(raw).strip():
        raise ValueError("חסר הטקסט (units) — לתפילה ולטקסט חופשי שולחים "
                         "את יחידות הטקסט עצמן")
    if isinstance(raw, str):
        if len(raw.encode("utf-8")) > MAX_UNITS_BYTES:
            raise ValueError(f"הטקסט ארוך מדי (עד {MAX_UNITS_BYTES // 1024}KB)")
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raise ValueError("יחידות הטקסט (units) שנשלחו אינן JSON תקין")
    if not isinstance(raw, list) or not raw:
        raise ValueError("יחידות הטקסט (units) חייבות להיות רשימה לא ריקה")
    if len(raw) > MAX_UNITS:
        raise ValueError(f"יותר מדי יחידות טקסט (עד {MAX_UNITS})")
    units, has_hebrew = [], False
    for i, u in enumerate(raw, 1):
        where = f"יחידה {i}: "
        if not isinstance(u, dict):
            raise ValueError(where + "חייבת להיות אובייקט")
        text = u.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(where + "חסר טקסט")
        if len(text) > MAX_UNIT_TEXT:
            raise ValueError(where + f"ארוכה מדי (עד {MAX_UNIT_TEXT} תווים)")
        unit = {"text": text}
        label = u.get("label")
        if label is not None:
            if not isinstance(label, str) or len(label) > MAX_LABEL:
                raise ValueError(where + "תווית (label) לא תקינה")
            unit["label"] = label
        kind = u.get("kind")
        if kind is not None:
            if kind not in UNIT_KINDS:
                raise ValueError(where + f"סוג (kind) לא מוכר: {kind!r}")
            unit["kind"] = kind
        chunk = u.get("chunk")
        if chunk is not None:
            if chunk not in CHUNK_MODES:
                raise ValueError(where + f"מצב חיתוך (chunk) לא מוכר: {chunk!r}")
            unit["chunk"] = chunk
        if kind != "instruction" and _HEBREW_LETTER.search(text):
            has_hebrew = True
        units.append(unit)
    if not has_hebrew:
        raise ValueError("לא נמצאה אף אות עברית בטקסט לסנכרון")
    return units


def _parse_units_params(form: dict, source: str) -> dict:
    """מסלול היחידות (text/siddur) → ארגומנטים ל-run_hybrid_units.

    ‏mode הוא תמיד "tefila" (מילות יישור לתפילה — משימה 4.1.2). סכום
    ה-splits מול מספר המילים נבדק בצינור (regroup_words), אחרי החיתוך.
    """
    splits = parse_splits(form.get("splits"))
    performance = parse_performance(form.get("performance"))
    if performance is not None and splits:
        if max(performance) >= len(splits):
            raise ValueError("סדר הביצוע מפנה לכתובית שאינה קיימת "
                             f"(יש {len(splits)} כתוביות)")
    return {
        "source": source,
        "units": parse_units(form.get("units")),
        "title": parse_title(form.get("title")),
        "max_words": _parse_max_words(form.get("max_words")),
        "splits": splits,
        "performance": performance,
        "profile": parse_profile(form.get("profile")),
        "mode": "tefila",
    }


def pipeline_call(params: dict, audio_path: str, out_srt_path: str,
                  work_dir: str):
    """ניתוב ב-process: הפרמטרים → (שם פונקציית הצינור, kwargs).

    פונקציה טהורה כדי שהניתוב ייבדק בלי modal/torch. מילון בלי source
    (מה-worker של היום, או דפדפן ישן) הוא תנ״ך — בדיוק הקריאה של היום.
    """
    if params.get("source", "tanakh") == "tanakh":
        return "run_hybrid", {
            "book": params["book"],
            "chapter": params["chapter"],
            "audio_path": audio_path,
            "out_srt_path": out_srt_path,
            "verse_start": params["verse_start"],
            "chapter_end": params["chapter_end"],
            "verse_end": params["verse_end"],
            "max_words": params["max_words"],
            "work_dir": work_dir,
            "splits": params.get("splits"),
        }
    return "run_hybrid_units", {
        "units": params["units"],
        "audio_path": audio_path,
        "out_srt_path": out_srt_path,
        "max_words": params["max_words"],
        "splits": params.get("splits"),
        "performance": params.get("performance"),
        "profile": params.get("profile") or "reading",
        "mode": params.get("mode") or "tefila",
        "work_dir": work_dir,
    }


def notify_label(params: dict) -> str:
    """התווית בהתראת ה-push: ה-title כשנשלח, אחרת "ספר פרק" כמו היום."""
    title = params.get("title")
    if title:
        return title
    if params.get("source", "tanakh") != "tanakh":
        return "טקסט חופשי" if params["source"] == "text" else "תפילה"
    return " ".join(str(params.get(k) or "")
                    for k in ("book", "chapter")).strip()


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
