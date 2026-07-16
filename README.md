# קריאת התורה — כתוביות מסונכרנות

הפקת קובץ כתוביות (SRT) עם טקסט מקראי **מנוקד ומוטעם**, מסונכרן להקלטת קריאה בטעמים,
לייבוא ל-CapCut. הערך של המערכת הוא הטקסט המדויק — לא התזמון (שכלי עריכה כבר עושים, אבל
תוך שיבוש העברית המקראית).

**התוכנית המלאה: [PLAN.md](PLAN.md)** ‏(v5.2).

## הממשק הקבוע — הכל מהטלפון, בלי Colab

**‏https://kriat-hatora.vercel.app**

1. **בחר קטע** — ספר, פרק, טווח פסוקים. הטקסט (גרסת MAM, מנוקד ומוטעם) נטען מ-Sefaria
   ונחתך למקטעים לפי טעמי המקרא.
2. **בחר את ההקלטה** מהטלפון — הקובץ נשאר במכשיר, שום דבר לא מועלה לשרת.
3. **תזמן** — או בהקשות תוך כדי האזנה (מקישים כשכל מקטע מתחיל; דיוק של עשיריות שנייה),
   או חלוקה אוטומטית לפי אורך הטקסט.
4. **בדוק ותקן** — נגינה מכל נקודת כניסה, כוונון של ±0.2 שניות.
5. **ייצא SRT** (הורדה / שיתוף / העתקה) ← CapCut Web ← Cloud ← אפליקציית CapCut ← פרסום.

הממשק רץ על Vercel (פרויקט `kriat-hatora`): דף סטטי + פונקציית Python אחת
(`api/segments.py`) שמושכת את הטקסט מ-Sefaria וחותכת אותו עם `src/chunker`.
**אין צורך באחסון ענן** (Supabase וכד') — ההקלטה לא עוזבת את הטלפון והתזמון קורה בדפדפן.

## מסלול היישור האוטומטי (AI, ‏Colab + GPU)

להקלטות שבהן רוצים יישור CTC מדויק בלי הקשות:

1. **הקלט** ושמור את הקובץ ב-Google Drive (למשל בתיקייה `kriat`).
2. **פתח את המעבד ב-Colab:**

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/michaelnahmias1/Kriat-Hatora/blob/claude/poc-permanent-interface-lttvyo/notebooks/worker.ipynb)

   בפעם הראשונה: ‏Runtime ← Change runtime type ← **T4 GPU**.
3. **מלא את תא הפרמטרים** (ספר, פרק, טווח פסוקים, נתיב ההקלטה) ← Runtime ← **Run all**.
4. ה-SRT נשמר ב-Drive ליד ההקלטה (וגם מוצע להורדה ישירה).

## מה יש בריפו

| נתיב | מה זה |
|---|---|
| `PLAN.md` | תוכנית הפעולה המחייבת (v5.2) |
| `index.html` | **הממשק הקבוע** — דף אחד, עברית, מותאם לטלפון (נפרס ל-Vercel) |
| `api/segments.py` | פונקציית ה-API: ‏Sefaria ← ניקוי ← חיתוך ← JSON (Vercel Python) |
| `vercel.json` | תצורת הפריסה |
| `notebooks/worker.ipynb` | מסלול ה-AI — הקלטה מ-Drive ← יישור MMS ← SRT ל-Drive |
| `notebooks/shelav0_verification.ipynb` | notebook אבחון: אימות טקסט/טעמים/קרי-כתיב/הקלטה |
| `src/chunker/` | חיתוך למקטעים לפי טעמי המקרא — Python טהור, אפס תלויות (משרת את שני המסלולים) |
| `src/aligner/` | הצינור המלא ל-Colab: ‏Sefaria ← חיתוך ← יישור MMS ← SRT |
| `tests/` | 42 בדיקות יחידה (רצות בלי רשת) |

## פריסה מחדש (למפתחים)

הפריסה נעשית לפרויקט `kriat-hatora` ב-Vercel (לא לגעת בפרויקטים אחרים בחשבון).
הקבצים שנפרסים: `index.html`, ‏`api/segments.py`, ‏`vercel.json`, ‏`src/chunker/`.

## הרצת הבדיקות (למפתחים)

```bash
python3 -m unittest discover -s tests -v
```
