# קריאת התורה — כתוביות מסונכרנות

הפקת קובץ כתוביות (SRT) עם טקסט מקראי **מנוקד ומוטעם**, מסונכרן להקלטת קריאה בטעמים,
לייבוא ל-CapCut. הערך של המערכת הוא הטקסט המדויק — לא התזמון (שכלי עריכה כבר עושים, אבל
תוך שיבוש העברית המקראית).

**התוכנית המלאה: [PLAN.md](PLAN.md)** ‏(v5.1).

## איך מפיקים כתוביות (הכל מהטלפון)

1. **הקלט** את הקריאה ושמור את הקובץ ב-Google Drive (למשל בתיקייה `kriat`).
2. **פתח את המעבד ב-Colab:**

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/michaelnahmias1/Kriat-Hatora/blob/claude/project-action-plan-review-kyrf5x/notebooks/worker.ipynb)

   בפעם הראשונה: ‏Runtime ← Change runtime type ← **T4 GPU**.
3. **מלא את תא הפרמטרים** (ספר, פרק, טווח פסוקים, נתיב ההקלטה) ← Runtime ← **Run all**.
4. ה-SRT נשמר ב-Drive ליד ההקלטה (וגם מוצע להורדה ישירה).
5. **CapCut Web** ← ייבוא ה-SRT ← עיצוב ותיקוני גרירה ← Cloud ← אפליקציית CapCut ← פרסום.

## מה יש בריפו

| נתיב | מה זה |
|---|---|
| `PLAN.md` | תוכנית הפעולה המחייבת (v5.1) |
| `notebooks/worker.ipynb` | **המעבד** — הקלטה מ-Drive ← SRT ל-Drive (זה מה שמריצים) |
| `notebooks/shelav0_verification.ipynb` | notebook אבחון: אימות טקסט/טעמים/קרי-כתיב/הקלטה |
| `src/chunker/` | חיתוך למקטעים לפי טעמי המקרא — Python טהור, אפס תלויות |
| `src/aligner/` | הצינור המלא: Sefaria ← חיתוך ← יישור MMS ← SRT |
| `tests/` | 28 בדיקות יחידה (רצות בלי רשת) |

## הרצת הבדיקות (למפתחים)

```bash
python3 -m unittest discover -s tests -v
```
