# קריאת התורה — כתוביות מסונכרנות

הפקת קובץ כתוביות (SRT) עם טקסט מקראי **מנוקד ומוטעם**, מסונכרן להקלטת קריאה בטעמים,
לייבוא ל-CapCut. הערך של המערכת הוא הטקסט המדויק — לא התזמון (שכלי עריכה כבר עושים, אבל
תוך שיבוש העברית המקראית).

**התוכנית המלאה: [PLAN.md](PLAN.md)** ‏(v6 — הפייפליין ההיברידי).

הסנכרון עובד בשלוש שכבות: תמלול עברי (ivrit.ai) שמוצלב עם טקסט Sefaria ומייצר
"עוגנים", יישור כפוי (MMS) על חלונות קצרים בין העוגנים, והצמדת גבולות לנשימות
(VAD). לצד ה-SRT נוצר דוח איכות שמפרט אילו מקטעים בודדים כדאי לגרור ידנית.

## איך מפיקים כתוביות (הכל מהטלפון)

1. **הקלט** את הקריאה ושמור את הקובץ ב-Google Drive (למשל בתיקייה `kriat`).
2. **פתח את המעבד ב-Colab:**

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/michaelnahmias1/Kriat-Hatora/blob/main/notebooks/worker.ipynb)

   בפעם הראשונה: ‏Runtime ← Change runtime type ← **T4 GPU**.
3. **מלא את תא הפרמטרים** (ספר, פרק, טווח פסוקים, נתיב ההקלטה) ← Runtime ← **Run all**.
4. ה-SRT נשמר ב-Drive ליד ההקלטה (וגם מוצע להורדה ישירה).
5. **CapCut Web** ← ייבוא ה-SRT ← עיצוב ותיקוני גרירה ← Cloud ← אפליקציית CapCut ← פרסום.

## מה יש בריפו

| נתיב | מה זה |
|---|---|
| `PLAN.md` | תוכנית הפעולה המחייבת (v6) |
| `notebooks/worker.ipynb` | **המעבד** — הקלטה מ-Drive ← SRT + דוח איכות ל-Drive (זה מה שמריצים) |
| `notebooks/poc_eval.ipynb` | הערכה: סימון ground truth והשוואת שיטות הסנכרון |
| `notebooks/shelav0_verification.ipynb` | notebook אבחון: אימות טקסט/טעמים/קרי-כתיב/הקלטה |
| `src/chunker/` | חיתוך למקטעים לפי טעמי המקרא — Python טהור, אפס תלויות |
| `src/aligner/` | הצינור ההיברידי: Sefaria ← חיתוך ← תמלול+עוגנים ← יישור ממושכן ← VAD ← SRT |
| `tests/` | 78 בדיקות יחידה (רצות בלי רשת) |

## הרצת הבדיקות (למפתחים)

```bash
python3 -m unittest discover -s tests -v
```
