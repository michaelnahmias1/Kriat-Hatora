// בדיקות מנוע התזמון האוטומטי: מייצרים "הקלטת קריאה" סינתטית שבה זמני האמת
// ידועים, ומוודאים שהמנוע משחזר אותם. הרצה: node tests/test_autotime.mjs
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const AutoTime = require("../autotime.js");

const SR = 16000;

// מחולל רעש דטרמיניסטי (כדי שהבדיקה תהיה שחזירה)
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

function makeSegments() {
  // 4 "פסוקים", בכל אחד 3–4 מקטעים עם אורכי אותיות משתנים
  const letters = [
    [12, 9, 16], [8, 14, 11, 10], [15, 7, 13], [10, 12, 9, 14],
  ];
  const segments = [];
  for (const verse of letters) {
    verse.forEach((l, i) => segments.push({
      letters: l, verse_end: i === verse.length - 1,
    }));
  }
  return segments;
}

// בונה אות: דיבור = רעש חזק, שקט = רעש חלש. מחזיר גם את זמני האמת.
function synthesize(segments, opts = {}) {
  const secPerLetter = opts.secPerLetter ?? 0.1;
  const versePause = opts.versePause ?? 0.5;   // הפסקת סוף-פסוק
  const microPause = opts.microPause ?? 0.0;   // הפסקונת בין מקטעים בתוך פסוק
  const lead = opts.lead ?? 1.2, tail = opts.tail ?? 0.8;

  const events = []; // {start, dur} של דיבור לכל מקטע
  let t = lead;
  const trueTimes = [];
  segments.forEach((s, i) => {
    trueTimes.push(t);
    const dur = s.letters * secPerLetter * (0.9 + 0.2 * rand()); // ±10% שונות קצב
    events.push({ start: t, dur });
    t += dur;
    if (i < segments.length - 1) t += s.verse_end ? versePause : microPause;
  });
  const trueEnd = t;
  const total = Math.ceil((t + tail) * SR);
  const x = new Float32Array(total);
  for (let i = 0; i < total; i++) x[i] = (rand() * 2 - 1) * 0.004; // רצפת רעש
  for (const ev of events) {
    const a = Math.round(ev.start * SR), b = Math.min(total, Math.round((ev.start + ev.dur) * SR));
    for (let i = a; i < b; i++) x[i] = (rand() * 2 - 1) * 0.35;
  }
  return { x, trueTimes, trueEnd };
}

function maxErrAt(times, trueTimes, idxs) {
  return Math.max(...idxs.map(i => Math.abs(times[i] - trueTimes[i])));
}

/* --- בדיקה 1: קריאה עם הפסקות סוף-פסוק ברורות --- */
{
  const segments = makeSegments();
  const { x, trueTimes, trueEnd } = synthesize(segments);
  const res = AutoTime.analyze([x], SR, segments);
  const { times, endTime, diagnostics: d } = res;

  assert.equal(times.length, segments.length);
  for (let i = 1; i < times.length; i++) assert.ok(times[i] > times[i - 1], "מונוטוניות");

  // כל עוגני הפסוקים נמצאו והם מדויקים
  assert.equal(d.anchorsTotal, 3);
  assert.equal(d.anchorsMatched, 3, `זוהו ${d.anchorsMatched}/3 עוגנים`);
  const anchorIdxs = [];
  segments.forEach((s, i) => { if (i > 0 && segments[i - 1].verse_end) anchorIdxs.push(i); });
  const anchorErr = maxErrAt(times, trueTimes, anchorIdxs);
  assert.ok(anchorErr < 0.15, `שגיאת עוגן ${anchorErr.toFixed(3)}s`);

  // תחילת הקריאה וסופה
  assert.ok(Math.abs(times[0] - trueTimes[0]) < 0.15, `התחלה: ${times[0]} מול ${trueTimes[0]}`);
  assert.ok(Math.abs(endTime - trueEnd) < 0.3, `סוף: ${endTime} מול ${trueEnd}`);

  // גבולות פנימיים (בלי רמז אקוסטי) — אינטרפולציה לפי משקל, סטייה קטנה
  const inner = times.map((_, i) => i).filter(i => !anchorIdxs.includes(i) && i > 0);
  const meanErr = inner.reduce((a, i) => a + Math.abs(times[i] - trueTimes[i]), 0) / inner.length;
  assert.ok(meanErr < 0.35, `שגיאה פנימית ממוצעת ${meanErr.toFixed(3)}s`);
  console.log(`בדיקה 1 ✓  עוגנים ${d.anchorsMatched}/${d.anchorsTotal}, שגיאת עוגן מרבית ${anchorErr.toFixed(3)}s, פנימית ממוצעת ${meanErr.toFixed(3)}s`);
}

/* --- בדיקה 2: גם נשימות קטנות בין מקטעים בתוך הפסוק — ההצמדה משפרת --- */
{
  seed = 7;
  const segments = makeSegments();
  const { x, trueTimes, trueEnd } = synthesize(segments, { microPause: 0.3 });
  const res = AutoTime.analyze([x], SR, segments);
  const errs = res.times.map((t, i) => Math.abs(t - trueTimes[i]));
  const maxErr = Math.max(...errs);
  assert.ok(maxErr < 0.2, `עם נשימות בין מקטעים כל הגבולות אמורים להיתפס; שגיאה מרבית ${maxErr.toFixed(3)}s`);
  assert.ok(Math.abs(res.endTime - trueEnd) < 0.3);
  console.log(`בדיקה 2 ✓  שגיאה מרבית ${maxErr.toFixed(3)}s כשיש נשימות בין כל המקטעים`);
}

/* --- בדיקה 3: קריאה רצופה בלי אף הפסקה — נסיגה חיננית לחלוקה משוקללת --- */
{
  seed = 99;
  const segments = makeSegments();
  const { x, trueTimes } = synthesize(segments, { versePause: 0.05, microPause: 0 });
  const res = AutoTime.analyze([x], SR, segments);
  for (let i = 1; i < res.times.length; i++) assert.ok(res.times[i] > res.times[i - 1]);
  assert.ok(Math.abs(res.times[0] - trueTimes[0]) < 0.15, "גם בלי הפסקות — ההתחלה מזוהה");
  console.log(`בדיקה 3 ✓  קריאה רצופה: מונוטוני, התחלה ${res.times[0].toFixed(2)}s (אמת ${trueTimes[0].toFixed(2)}s), עוגנים ${res.diagnostics.anchorsMatched}/${res.diagnostics.anchorsTotal}`);
}

/* --- בדיקה 4: קורא שמדלג על הפסקה בפסוק אחד — ה-DP מדלג בלי להתפרק --- */
{
  seed = 3;
  const segments = makeSegments();
  // פסוק שני נקרא ברצף אל השלישי (הפסקה 0.05 בלבד), השאר רגילים
  const secPerLetter = 0.1, lead = 1.0;
  let t = lead; const trueTimes = [];
  const gaps = [];
  segments.forEach((s, i) => {
    trueTimes.push(t);
    const dur = s.letters * secPerLetter;
    t += dur;
    if (i < segments.length - 1) {
      const verseNum = segments.slice(0, i + 1).filter(z => z.verse_end).length;
      const gap = s.verse_end ? (verseNum === 2 ? 0.05 : 0.5) : 0;
      gaps.push(gap); t += gap;
    }
  });
  const total = Math.ceil((t + 0.6) * SR);
  const x = new Float32Array(total);
  for (let i = 0; i < total; i++) x[i] = (rand() * 2 - 1) * 0.004;
  let tt = lead;
  segments.forEach((s, i) => {
    const a = Math.round(tt * SR), dur = s.letters * secPerLetter;
    const b = Math.min(total, Math.round((tt + dur) * SR));
    for (let k = a; k < b; k++) x[k] = (rand() * 2 - 1) * 0.35;
    tt += dur + (i < segments.length - 1 ? gaps[i] : 0);
  });
  const res = AutoTime.analyze([x], SR, segments);
  assert.equal(res.diagnostics.anchorsMatched, 2, "שני עוגנים נתפסו, השלישי דולג בלי לשבש");
  const anchorIdxs = [];
  segments.forEach((s, i) => { if (i > 0 && segments[i - 1].verse_end) anchorIdxs.push(i); });
  // העוגנים שכן נמצאו — מדויקים
  const matchedErrs = anchorIdxs
    .map(i => Math.abs(res.times[i] - trueTimes[i]))
    .sort((a, b) => a - b).slice(0, 2);
  assert.ok(matchedErrs[1] < 0.15, `עוגנים תואמים מדויקים: ${matchedErrs.map(e => e.toFixed(3))}`);
  console.log(`בדיקה 4 ✓  פסוק בלי הפסקה: ${res.diagnostics.anchorsMatched}/3 עוגנים, בלי קריסה`);
}

console.log("כל בדיקות מנוע התזמון עברו ✓");
