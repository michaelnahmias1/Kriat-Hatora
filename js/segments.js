"use strict";
/* חלוקת המילים לכתוביות — שכפול מתועד של chunker בצד השרת */

/* ---------- חלוקת המילים לכתוביות ----------
   מקור האמת הוא רצף המילים הפרוזודיות: כל חלוקה היא רשימת גדלים שסכומה
   מספר המילים. אותו רצף בדיוק נבנה גם בשרת (chunker.tokenize), ולכן
   מספיק לשלוח את הגדלים כדי שהעיבוד בענן ייצור בדיוק את אותן כתוביות. */
const HE_LETTER_RE = /[א-ת]/;
const NIQQUD_RE = /[ְ-ׇֽֿׁׂ]/;
const MAQAF = "־";
function tokensOf(display) { return display.split(" ").filter(Boolean); }
/* מילה נשמעת = יש בה חלק מנוקד. חלק שיש בו אותיות בלי ניקוד הוא "כתיב"
   שאינו נקרא — בדיוק ההגדרה שב-chunker.is_ketiv בצד השרת. */
function isAudible(tok) {
  return tok.split(MAQAF).some(p => HE_LETTER_RE.test(p) && NIQQUD_RE.test(p));
}
function flatWords() {
  const out = [];
  for (const s of S.data.segments)
    for (const t of tokensOf(s.display)) out.push({ t, verse: s.verse });
  return out;
}
/* רצף מילים + גדלים → כתוביות. כולל אותו מיזוג של מקטע בלי מילה נשמעת
   שהשרת עושה (chunker._merge_unalignable) — אחרת ספירת הכתוביות תיפרד. */
function segmentsFromSplits(words, sizes) {
  const raw = [];
  let i = 0;
  for (const n of sizes) {
    const part = words.slice(i, i + n);
    i += n;
    if (!part.length) continue;
    raw.push({
      display: part.map(w => w.t).join(" "), verse: part[0].verse,
      audible: part.some(w => isAudible(w.t)),
    });
  }
  const out = [];
  let pending = "";
  for (const seg of raw) {
    if (!seg.audible) {
      if (out.length) out[out.length - 1].display += " " + seg.display;
      else pending = (pending + " " + seg.display).trim();
      continue;
    }
    if (pending) { seg.display = pending + " " + seg.display; pending = ""; }
    out.push(seg);
  }
  if (pending && out.length) out[out.length - 1].display += " " + pending;
  return out.map(s => ({ display: s.display, verse: s.verse }));
}
function currentSplits() {
  return S.data.segments.map(s => tokensOf(s.display).length);
}
/* החלת חלוקה חדשה — הזמנים הישנים כבר לא תקפים (מספר הכתוביות השתנה) */
function applySplits(sizes) {
  const words = flatWords();
  S.data.segments = segmentsFromSplits(words, sizes);
  S.splits = sizes.slice();
  S.times = null; S.endTime = null; S.report = null;
  renderTextLoaded();
  refreshTimingSteps();
  save();
}
