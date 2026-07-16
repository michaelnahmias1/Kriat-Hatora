/* מנוע התזמון האוטומטי — רץ כולו בדפדפן, בלי שרת ובלי העלאת ההקלטה.
 *
 * הרעיון: בקריאת התורה יש הפסקות אמיתיות (סוף פסוק, אתנחתא, נשימה).
 * המנוע מזהה אותן מתוך עקומת האנרגיה של ההקלטה, מתאים אותן לגבולות
 * הפסוקים הידועים מהטקסט (התאמה מונוטונית בתכנות דינמי), ומחלק את
 * המקטעים הפנימיים לפי משקל הטקסט בין נקודות העיגון — עם הצמדה
 * להפסקות קטנות כשהן קרובות מספיק.
 *
 * הקובץ טהור (ללא DOM) כדי שירוץ גם ב-Node לבדיקות: tests/test_autotime.mjs
 */
"use strict";
(function (root) {

const DEFAULTS = {
  hopMs: 10,           // קפיצת פריים לחישוב האנרגיה
  winMs: 25,           // חלון האנרגיה
  minSpeechMs: 60,     // הבלחת קול קצרה מזה אינה דיבור (קליק/רשרוש)
  minPauseSec: 0.22,   // שקט קצר מזה אינו הפסקה
  speechPadSec: 0.06,  // הכתובית נכנסת רגע לפני חידוש הדיבור
  minGapSec: 0.05,     // מרווח מינימלי בין כניסות עוקבות
  skipPenaltySec: 2.0, // "מחיר" גבול-פסוק שלא נמצאה לו הפסקה (DP)
  snapTolSec: 0.5,     // טולרנס מרבי להצמדת גבול פנימי להפסקה
};

/* --- שלב א: עקומת אנרגיה (RMS ב-dB) על פריימים קצרים --- */
function frameDb(channels, sampleRate, opts) {
  const hop = Math.max(1, Math.round(sampleRate * opts.hopMs / 1000));
  const win = Math.max(hop, Math.round(sampleRate * opts.winMs / 1000));
  const n = channels[0].length;
  const nFrames = Math.max(0, Math.floor((n - win) / hop) + 1);
  const db = new Float32Array(nFrames);
  for (let f = 0; f < nFrames; f++) {
    const off = f * hop;
    let sum = 0;
    for (let c = 0; c < channels.length; c++) {
      const ch = channels[c];
      for (let j = 0; j < win; j++) { const v = ch[off + j]; sum += v * v; }
    }
    const rms = Math.sqrt(sum / (win * channels.length));
    db[f] = 20 * Math.log10(rms + 1e-8);
  }
  return { db, hopSec: hop / sampleRate };
}

/* --- שלב ב: סף אדפטיבי דיבור/שקט --- */
function speechThreshold(db) {
  const sorted = Array.from(db).sort((a, b) => a - b);
  const q = p => sorted[Math.min(sorted.length - 1, Math.round(p * (sorted.length - 1)))];
  const floor = q(0.05);   // רצפת הרעש (החלקים השקטים)
  const loud = q(0.90);    // עוצמת הדיבור האופיינית
  // 30% מהדרך בין הרצפה לדיבור, ולפחות 6dB מעל הרצפה
  return Math.max(floor + 6, floor + 0.3 * (loud - floor));
}

function speechMask(db, hopSec, opts) {
  const th = speechThreshold(db);
  const mask = new Uint8Array(db.length);
  for (let i = 0; i < db.length; i++) mask[i] = db[i] > th ? 1 : 0;
  // הבלחות קול קצרות (קליק) נחשבות שקט — אחרת הן שוברות הפסקה לשתיים
  const minSpeech = Math.max(1, Math.round(opts.minSpeechMs / 1000 / hopSec));
  let i = 0;
  while (i < mask.length) {
    if (mask[i]) {
      let j = i;
      while (j < mask.length && mask[j]) j++;
      if (j - i < minSpeech) mask.fill(0, i, j);
      i = j;
    } else i++;
  }
  return mask;
}

/* --- שלב ג: גבולות הדיבור והפסקות --- */
function findPauses(mask, hopSec, opts) {
  let first = -1, last = -1;
  for (let i = 0; i < mask.length; i++) if (mask[i]) { if (first < 0) first = i; last = i; }
  if (first < 0) return { speechStart: 0, speechEnd: 0, pauses: [] };
  const speechStart = first * hopSec;
  const speechEnd = (last + 1) * hopSec;
  const pauses = [];
  let i = first;
  while (i <= last) {
    if (!mask[i]) {
      let j = i;
      while (j <= last && !mask[j]) j++;
      const dur = (j - i) * hopSec;
      if (dur >= opts.minPauseSec) pauses.push({ start: i * hopSec, end: j * hopSec, dur });
      i = j;
    } else i++;
  }
  return { speechStart, speechEnd, pauses };
}

/* --- שלב ד: משקלי טקסט (זהים לחלוקה לפי אורך שהייתה קיימת) --- */
function textWeights(segments) {
  return segments.map(s => (s.letters || 1) + 2 + (s.verse_end ? 5 : 0));
}

function interpolate(times, cum, total, i0, t0, i1, t1) {
  // ממלא גבולות (i0,i1) לא כולל, לפי המשקל המצטבר בין שתי נקודות עיגון
  const c0 = cum[i0], c1 = cum[i1];
  for (let i = i0 + 1; i < i1; i++) {
    const f = c1 > c0 ? (cum[i] - c0) / (c1 - c0) : (i - i0) / (i1 - i0);
    times[i] = t0 + f * (t1 - t0);
  }
}

/* --- שלב ה: התאמת גבולות להפסקות (יישור מונוטוני, תכנות דינמי) ---
 * expectedOf(k): הזמן הצפוי של הגבול ה-k; onset: זמני חידוש-הדיבור של ההפסקות.
 * skip: מחיר השארת גבול בלי הפסקה; דילוג על הפסקה חינם (נשימה סתם). */
function matchAnchors(expectedOf, K, onset, skip, durBonus) {
  const P = onset.length;
  const cost = (k, j) => Math.max(0, Math.abs(expectedOf(k) - onset[j].t) - durBonus * Math.min(onset[j].dur, 1.5));
  // D[k][j] = העלות המזערית לשיבוץ k העוגנים הראשונים עם j ההפסקות הראשונות
  const D = [];
  for (let k = 0; k <= K; k++) D.push(new Float64Array(P + 1));
  for (let k = 1; k <= K; k++) D[k][0] = k * skip;
  const choice = [];
  for (let k = 0; k <= K; k++) choice.push(new Uint8Array(P + 1));
  for (let k = 1; k <= K; k++) {
    for (let j = 1; j <= P; j++) {
      let best = D[k][j - 1], ch = 0;               // ההפסקה לא שובצה
      const m = D[k - 1][j - 1] + cost(k - 1, j - 1); // התאמה
      if (m < best) { best = m; ch = 1; }
      const s = D[k - 1][j] + skip;                  // העוגן נשאר בלי הפסקה
      if (s < best) { best = s; ch = 2; }
      D[k][j] = best; choice[k][j] = ch;
    }
  }
  const match = new Array(K).fill(-1);
  let k = K, j = P;
  while (k > 0) {
    if (j === 0) { k--; continue; }
    const ch = choice[k][j];
    if (ch === 0) j--;
    else if (ch === 1) { match[k - 1] = j - 1; k--; j--; }
    else k--;
  }
  return match;
}

/* --- הציבור: analyze --- */
function analyze(channels, sampleRate, segments, userOpts) {
  const opts = Object.assign({}, DEFAULTS, userOpts || {});
  const n = segments.length;
  const duration = channels[0].length / sampleRate;
  const { db, hopSec } = frameDb(channels, sampleRate, opts);
  const mask = speechMask(db, hopSec, opts);
  let { speechStart, speechEnd, pauses } = findPauses(mask, hopSec, opts);
  if (speechEnd <= speechStart) { speechStart = 0; speechEnd = duration; }

  const w = textWeights(segments);
  const total = w.reduce((a, b) => a + b, 0);
  const cum = new Float64Array(n + 1);
  for (let i = 0; i < n; i++) cum[i + 1] = cum[i] + w[i];

  const span = speechEnd - speechStart;
  const expected = new Float64Array(n + 1);
  for (let i = 0; i <= n; i++) expected[i] = speechStart + span * cum[i] / total;

  // עוגנים: תחילת כל פסוק חדש (הגבול שאחרי מקטע המסיים פסוק)
  const anchorIdx = [];
  for (let i = 1; i < n; i++) if (segments[i - 1].verse_end) anchorIdx.push(i);

  const times = new Array(n).fill(null);
  const fixed = new Uint8Array(n + 1); // גבולות שנקבעו מהאודיו (לא מאינטרפולציה)
  times[0] = Math.max(0, speechStart - opts.speechPadSec);
  fixed[0] = 1; fixed[n] = 1;
  let endTime = Math.min(duration, speechEnd + 0.15);
  const boundTime = i => (i === n ? speechEnd : times[i]);

  const onset = pauses.map(p => ({ t: Math.max(p.start, p.end - opts.speechPadSec), dur: p.dur }));
  const usedPause = new Uint8Array(onset.length);

  // מעבר א: עיגון גבולות-פסוק להפסקות הבולטות (העדפה קלה להפסקות ארוכות)
  let matched = 0;
  if (onset.length && anchorIdx.length) {
    const match = matchAnchors(k => expected[anchorIdx[k]], anchorIdx.length,
      onset, opts.skipPenaltySec, 0.4);
    for (let k = 0; k < anchorIdx.length; k++) {
      if (match[k] >= 0) {
        times[anchorIdx[k]] = onset[match[k]].t;
        fixed[anchorIdx[k]] = 1; usedPause[match[k]] = 1; matched++;
      }
    }
  }

  const reinterpolate = () => {
    let prev = 0;
    for (let i = 1; i <= n; i++) {
      if (!fixed[i]) continue;
      interpolate(times, cum, total, prev, boundTime(prev), i, boundTime(i));
      prev = i;
    }
  };
  reinterpolate();

  // מעבר ב: בתוך כל טווח מעוגן הציפיות כבר מדויקות — מתאימים את הגבולות
  // הפנימיים להפסקות שנותרו (נשימות בין מקטעים), שוב ביישור מונוטוני.
  // חוזרים עד התכנסות: כל הצמדה מעדכנת את הציפיות ומקרבת את השכנות שלה.
  let snapped = 0;
  for (let round = 0; round < 4 && onset.length; round++) {
    let roundSnapped = 0;
    const fixedIdx = [];
    for (let i = 0; i <= n; i++) if (fixed[i]) fixedIdx.push(i);
    for (let f = 0; f + 1 < fixedIdx.length; f++) {
      const a = fixedIdx[f], b = fixedIdx[f + 1];
      const inner = []; // גבולות פנימיים בטווח
      for (let i = a + 1; i < b; i++) inner.push(i);
      const tA = boundTime(a), tB = boundTime(b);
      const free = [];
      for (let j = 0; j < onset.length; j++)
        if (!usedPause[j] && onset[j].t > tA + opts.minGapSec && onset[j].t < tB - opts.minGapSec)
          free.push(j);
      if (!inner.length || !free.length) continue;
      const match = matchAnchors(k => times[inner[k]], inner.length,
        free.map(j => onset[j]), opts.snapTolSec, 0);
      for (let k = 0; k < inner.length; k++) {
        if (match[k] >= 0) {
          times[inner[k]] = onset[free[match[k]]].t;
          fixed[inner[k]] = 1; usedPause[free[match[k]]] = 1; roundSnapped++;
        }
      }
    }
    if (!roundSnapped) break;
    snapped += roundSnapped;
    reinterpolate();
  }

  // מונוטוניות ותחומים — כמו במצב ההקשות
  for (let i = 1; i < n; i++) times[i] = Math.max(times[i], times[i - 1] + opts.minGapSec);
  endTime = Math.max(endTime, times[n - 1] + 0.3);
  for (let i = n - 1; i >= 1; i--) times[i] = Math.min(times[i], endTime - (n - i) * opts.minGapSec);

  return {
    times, endTime,
    diagnostics: {
      duration, speechStart, speechEnd,
      pausesFound: pauses.length,
      anchorsTotal: anchorIdx.length,
      anchorsMatched: matched,
      innerSnapped: snapped,
    },
  };
}

const AutoTime = { analyze, frameDb, speechMask, findPauses, textWeights, DEFAULTS };
root.AutoTime = AutoTime;
if (typeof module !== "undefined" && module.exports) module.exports = AutoTime;

})(typeof globalThis !== "undefined" ? globalThis : this);
