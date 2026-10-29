"use strict";
/* מצב האפליקציה (S), שמירה ב-localStorage ועזרי תצוגה */

const $ = id => document.getElementById(id);

const S = {
  data: null,        // תשובת ה-API: ref, version, segments[]
  times: null,       // זמן כניסה (שניות) לכל מקטע
  endTime: null,     // סוף המקטע האחרון
  audioName: null,
  report: null,      // דוח האיכות ממסלול ה-AI בענן (טקסט)
  cloudJob: null,    // עבודת ענן פעילה {id, t0, est, push} — שורדת סגירת האפליקציה
  splits: null,      // חלוקה מותאמת אישית: גודל כל כתובית במילים (null = לפי הטעמים)
  baseSplits: null,  // החלוקה המקורית לפי הטעמים — לכפתור האיפוס
  source: "tanakh",  // הלשונית הפעילה: tanakh | siddur | text (מקור הטקסט שנטען — dataSource())
  perf: null,        // מבנה הביצוע — חזרות, פזמון, דילוגים (performance.js); null = סדר הטקסט
  timesOrder: null,  // סדר הכתוביות ש-times שייכים אליו (מה שנשלח לענן); null = סדר הטקסט
};

/* ---------- עזרי תצוגה ---------- */
/* מספר → אותיות (גימטריה) לתצוגת פרק/פסוק: 15→ט״ו, 16→ט״ז, 25→כ״ה */
function heNumeral(n) {
  n = +n;
  if (!Number.isInteger(n) || n < 1) return String(n);
  const ones = ["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"];
  const tens = ["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"];
  const hundreds = ["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"];
  let s = hundreds[Math.floor(n / 100)] || "";
  const r = n % 100;
  if (r === 15) s += "טו";
  else if (r === 16) s += "טז";
  else s += tens[Math.floor(r / 10)] + ones[r % 10];
  if (s.length === 1) return s + "׳";              // גרש לאות בודדת
  return s.slice(0, -1) + "״" + s.slice(-1);       // גרשיים לפני האות האחרונה
}
function fmtClock(t) {
  t = Math.max(0, t || 0);
  const m = Math.floor(t / 60), s = Math.floor(t % 60);
  return m + ":" + String(s).padStart(2, "0");
}
function fmtSrt(t) {
  const ms = Math.max(0, Math.round(t * 1000));
  const h = Math.floor(ms / 3600000), m = Math.floor(ms % 3600000 / 60000);
  const s = Math.floor(ms % 60000 / 1000), r = ms % 1000;
  const p = (n, w) => String(n).padStart(w, "0");
  return `${p(h,2)}:${p(m,2)}:${p(s,2)},${p(r,3)}`;
}
function setLocked(stepId, locked) {
  $(stepId).classList.toggle("locked", locked);
}
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function save() {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify({
      query: readQuery(), data: S.data, times: S.times,
      endTime: S.endTime, audioName: S.audioName, report: S.report,
      cloudJob: S.cloudJob, splits: S.splits, baseSplits: S.baseSplits,
      // ‏source חדש — מצב שמור בלי source משוחזר כתנ״ך (main.js)
      source: S.source, freeText: readFreeText(),
      // הבחירה בסידור (נוסח, מיקום בעץ, קטע וטווח) — source-siddur.js
      siddur: siddurSaved(),
      // מבנה הביצוע וסדר הזמנים — חדשים; מצב שמור בלעדיהם = סדר הטקסט
      perf: S.perf, timesOrder: S.timesOrder,
    }));
  } catch (e) {}
}
