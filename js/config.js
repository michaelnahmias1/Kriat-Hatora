"use strict";
/* קבועי התצורה — כתובת ה-worker בענן, ה-token, מפתח ההתראות ומפתח השמירה */

const STORE_KEY = "kriat-hatora-v1";

/* מסלול ה-AI בענן (Modal) — ממלאים אחרי `modal deploy` (ראה README).
   כשה-URL ריק הכפתור מוסתר, ונשאר רק ייבוא SRT ידני. */
const AI_ENDPOINT = "https://michaelnahmias1--kriat-hatora-web.modal.run";   // למשל: "https://<user>--kriat-hatora-web.modal.run"
const AI_TOKEN = "hdkue38hf6Gfjl96XMre";      // אותו token שהוגדר ב-secret ‏kriat-hatora ב-Modal
/* המפתח הציבורי להתראות Web Push (ריק = בלי התראות, הכל עובד כרגיל).
   נוצר פעם אחת עם `npx web-push generate-vapid-keys`; המפתח הפרטי נשמר
   ב-secret‏ kriat-hatora ב-Modal‏ (VAPID_PRIVATE_KEY) — ראה README. */
const VAPID_PUBLIC_KEY = "";

/* סנכרון לפי מבנה הביצוע — חזרות, פזמון ודילוגים (PLAN_TEFILA.md 4.3.1–4.3.2).
   העורך ("מבנה הביצוע") זמין תמיד בתפילה ובטקסט חופשי; כשהדגל דולק השדה
   performance נשלח ל-worker (4.3.2 — ממוזג; פעיל מרגע שה-worker נפרס מחדש).
   worker ישן בחלון הפריסה זורק NotImplementedError — cloud.js מציג אז "הענן
   עדיין לא עודכן". כבוי ⇒ העורך מציג "בקרוב" והסנכרון לינארי. */
const PERFORMANCE_ENABLED = true;
