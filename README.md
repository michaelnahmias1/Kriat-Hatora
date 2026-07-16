# קריאת התורה — כתוביות מסונכרנות

הפקת קובץ כתוביות (SRT) עם טקסט מקראי **מנוקד ומוטעם**, מסונכרן להקלטת קריאה בטעמים,
לייבוא ל-CapCut. הערך של המערכת הוא הטקסט המדויק — לא התזמון (שכלי עריכה כבר עושים, אבל
תוך שיבוש העברית המקראית).

**התוכנית המלאה, כולל הביקורת על הגרסאות הקודמות: [PLAN.md](PLAN.md)** ‏(v5).

## מה יש בריפו

| נתיב | מה זה |
|---|---|
| `PLAN.md` | תוכנית הפעולה המחייבת (v5) — קרא אותה קודם |
| `src/chunker/` | פונקציית החיתוך לפי טעמי המקרא — Python טהור, אפס תלויות |
| `tests/` | בדיקות יחידה לחיתוך (רצות בלי רשת) |
| `notebooks/shelav0_verification.ipynb` | notebook האימותים של שלב 0 — להרצה ב-Colab |

## הצעד הבא (מהטלפון)

1. העלה את ההקלטה ל-Google Drive.
2. פתח את notebook האימותים ב-Colab:

   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/michaelnahmias1/Kriat-Hatora/blob/claude/project-action-plan-review-kyrf5x/notebooks/shelav0_verification.ipynb)

3. מלא את תא הפרמטרים (ספר, פרק, נתיב ההקלטה) ← Runtime ← **Run all** ← קרא את הפלט.

## הרצת הבדיקות (למפתחים)

```bash
python3 -m unittest discover -s tests -v
```
