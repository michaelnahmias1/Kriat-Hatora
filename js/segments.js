"use strict";
/* חלוקת המילים לכתוביות — שכפול מתועד של chunker בצד השרת */

/* ---------- חלוקת המילים לכתוביות ----------
   מקור האמת הוא רצף המילים הפרוזודיות: כל חלוקה היא רשימת גדלים שסכומה
   מספר המילים. אותו רצף בדיוק נבנה גם בשרת (chunker.tokenize), ולכן
   מספיק לשלוח את הגדלים כדי שהעיבוד בענן ייצור בדיוק את אותן כתוביות. */
const HE_LETTER_RE = /[א-ת]/;
const NIQQUD_RE = /[ְ-ׇֽֿׁׂ]/;
const MAQAF = "־";
/* פיצול על רווח רגיל (U+0020) בלבד — לא על \s: רווח קשיח (U+00A0) מצמיד
   פיסוק למילה, והוא חלק מהמילה בדיוק כמו ב-tokenize בשרת */
function tokensOf(display) { return display.split(" ").filter(Boolean); }
/* מילה נשמעת = יש בה חלק מנוקד. חלק שיש בו אותיות בלי ניקוד הוא "כתיב"
   שאינו נקרא — בדיוק ההגדרה שב-chunker.is_ketiv בצד השרת.
   בטקסט חופשי (מצב tefila) אין כתיב: כל חלק עם אות עברית נקרא, גם בלי
   ניקוד (‏is_ketiv עם mode="tefila"). שם ה׳ מטופל רק בשרת.
   חריג בתפילה (8.22, ‏chunker.qere_ketiv_flags): כתיב לא מנוקד שמיד אחריו
   הקרי המנוקד בסוגריים — `הביט [הַבִּ֖יטָה]` — אינו נקרא. ‏next = המילה
   הבאה באותה יחידה (או undefined); כשהכתיב הוא סוף שרשרת מקף, רק הוא יוצא. */
function isQereBracket(tok) {
  /* typeof: isAudible נקרא גם כ-callback של map (next = אינדקס) */
  return typeof tok === "string" && tok.startsWith("[") &&
    NIQQUD_RE.test(tok.slice(1).split("]")[0]);
}
function isAudible(tok, next) {
  if (alignMode() === "tefila") {
    const parts = tok.split(MAQAF).filter(p => HE_LETTER_RE.test(p));
    if (isQereBracket(next) && parts.length && !NIQQUD_RE.test(parts[parts.length - 1]))
      parts.pop();
    return parts.length > 0;
  }
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
  const nextInUnit = k => (words[k + 1] && words[k + 1].verse === words[k].verse
    ? words[k + 1].t : undefined);
  for (const n of sizes) {
    const part = words.slice(i, i + n);
    const i0 = i;
    i += n;
    if (!part.length) continue;
    raw.push({
      display: part.map(w => w.t).join(" "), verse: part[0].verse,
      audible: part.some((w, k) => isAudible(w.t, nextInUnit(i0 + k))),
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
