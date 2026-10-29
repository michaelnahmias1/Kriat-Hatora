"use strict";
/* שלב 2 — בחירת ההקלטה, נעילת השלבים, והמרת וידאו לאודיו במכשיר */

/* ---------- שלב 2: ההקלטה ---------- */
const player = $("player");
let audioReady = false;
let audioFileObj = null;   // הקובץ עצמו — נדרש לניתוח האוטומטי
let audioDurationSec = 0;  // משך ההקלטה — בסיס להערכת זמן העיבוד בענן
let lastObjectUrl = null;

function fmtSize(b) {
  return b >= 1024 * 1024 * 1024 ? (b / 1073741824).toFixed(1) + "GB"
       : b >= 1024 * 1024 ? Math.round(b / 1048576) + "MB"
       : Math.max(1, Math.round(b / 1024)) + "KB";
}
function showFileChip(name, meta) {
  $("audioInfo").hidden = false;
  $("audioInfo").innerHTML =
    `<span class="ico">🎧</span><span class="nm">${escapeHtml(name)}</span>` +
    `<span class="meta">${escapeHtml(meta || "")}</span>`;
}
$("pickAudio").addEventListener("click", () => $("audioFile").click());
/* הקובץ הנבחר מתקבל תמיד — גם כשהדפדפן מסרב לקרוא ממנו מטא-דאטה.
   באייפון (Low Power Mode, וידאו בקודק שספארי לא מנגן) האירוע
   loadedmetadata פשוט לא נורה לעולם; כשההמשך היה תלוי בו, שלב 3 נשאר
   נעול בלי שום הודעה וזה נראה כאילו "אי אפשר להעלות קובץ". המשך
   התהליך לא באמת צריך את המשך — הוא משמש רק להערכת זמן ולהאזנה. */
$("audioFile").addEventListener("change", () => {
  const f = $("audioFile").files[0];
  if (!f) return;
  audioFileObj = f;
  S.audioName = f.name;
  audioReady = true;
  audioDurationSec = 0;
  $("done2").hidden = false;
  showFileChip(f.name, fmtSize(f.size));
  refreshTimingSteps();
  save();
  probeDuration(f);
});
/* קריאת המשך והנגן — best-effort לגמרי, עם טיימאאוט ועם טיפול בשגיאה */
function probeDuration(f) {
  if (lastObjectUrl) { URL.revokeObjectURL(lastObjectUrl); lastObjectUrl = null; }
  lastObjectUrl = URL.createObjectURL(f);
  player.hidden = true;
  player.src = lastObjectUrl;
  let settled = false;
  const done = ok => {
    if (settled) return;
    settled = true;
    clearTimeout(to);
    if (ok && isFinite(player.duration) && player.duration > 0) {
      audioDurationSec = player.duration;
      player.hidden = false;
      showFileChip(f.name, `${fmtClock(player.duration)} · ${fmtSize(f.size)}`);
    } else {
      // אין תצוגה מקדימה — ההעלאה והסנכרון עובדים בדיוק כרגיל
      showFileChip(f.name, fmtSize(f.size) + " · ללא נגן");
    }
    save();
  };
  const to = setTimeout(() => done(false), 8000);
  player.addEventListener("loadedmetadata", () => done(true), { once: true });
  player.addEventListener("error", () => done(false), { once: true });
  try { player.load(); } catch (e) { done(false); }
}
function refreshTimingSteps() {
  // עבודת ענן פעילה משאירה את שלב 3 פתוח גם בלי קובץ האודיו — אחרי סגירה
  // מלאה של האפליקציה הקובץ אבד, אבל פס ההתקדמות וכפתור הביטול חייבים להגיב
  const ready = !!(S.data && (audioReady || S.cloudJob));
  setLocked("step3", !ready);
  // התוצאה לא תלויה בקובץ האודיו: דוח, זמנים וייצוא SRT נפתחים ברגע שיש
  // זמנים — גם אחרי סגירה מלאה, כשהקובץ אבד. רק ההאזנה דורשת אותו מחדש.
  // ‏cueCount — כתובית לכל הופעה בסדר הביצוע שנשלח (performance.js); בלעדיו = מספר הכתוביות
  const timed = !!(S.data && S.times && S.times.length === cueCount() && S.endTime != null);
  setLocked("stepReport", !timed);
  setLocked("step4", !timed);
  setLocked("step5", !timed);
  $("noAudioHint").hidden = !timed || audioReady;
  if (timed) { $("done3").hidden = false; renderReport(); renderTimeList(); }
}

/* ---------- המרה לאודיו בלבד לפני ההעלאה לענן ----------
   וידאו מפורק במכשיר ל-WAV מונו 16kHz (כל מה שהתמלול צריך) —
   ההעלאה קטנה והשרת לא נוגע בקובצי וידאו כבדים. */
const MAX_UPLOAD_MB = 300;   // תואם ל-MAX_UPLOAD_MB ב-modal_worker/app.py
// מעבר לגודל הזה פענוח הווידאו במכשיר מפיל את הלשונית באייפון (מגבלת
// זיכרון קשיחה) — עדיף להגיד את זה מראש מאשר "להיתקע" באמצע ההעלאה.
const MAX_DECODE_MB = 350;
function encodeWav16(samples, rate) {
  const buf = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(buf);
  const wstr = (off, s) => { for (let i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i)); };
  wstr(0, "RIFF"); v.setUint32(4, 36 + samples.length * 2, true); wstr(8, "WAVE");
  wstr(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true);
  v.setUint16(34, 16, true); wstr(36, "data"); v.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
  return buf;
}
/* ‏decodeAudioData: ספארי הישן מכיר רק את גרסת ה-callback */
function decodeAudio(ac, buf) {
  return new Promise((resolve, reject) => {
    let p;
    try { p = ac.decodeAudioData(buf, resolve, reject); }
    catch (e) { reject(e); return; }
    if (p && typeof p.then === "function") p.then(resolve, reject);
  });
}
/* דגימה-מחדש פשוטה ל-16kHz — פולבק לספארי שלא בונה OfflineAudioContext
   בקצב נמוך. התמלול ממילא לא מרוויח מיותר מזה. */
function downsampleTo16k(data, rate) {
  if (rate === 16000) return data;
  const ratio = rate / 16000;
  const out = new Float32Array(Math.floor(data.length / ratio));
  for (let i = 0; i < out.length; i++) out[i] = data[Math.floor(i * ratio)];
  return out;
}
async function extractAudioForUpload(file) {
  if (!/^video\//i.test(file.type || "")) return file;  // כבר אודיו — אין מה להמיר
  const buf = await file.arrayBuffer();
  const AC = window.AudioContext || window.webkitAudioContext;
  const ac = new AC();
  let decoded;
  try { decoded = await decodeAudio(ac, buf); }
  finally { ac.close && ac.close().catch(() => {}); }
  const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
  let data, rate = 16000;
  let off = null;
  try { off = new OAC(1, Math.ceil(decoded.duration * 16000), 16000); }
  catch (e) { off = null; }
  if (!off) {  // קצב נמוך לא נתמך — מרנדרים בקצב המקורי ומדללים ידנית
    rate = decoded.sampleRate;
    off = new OAC(1, Math.ceil(decoded.duration * rate), rate);
  }
  const src = off.createBufferSource();
  src.buffer = decoded; src.connect(off.destination); src.start();
  const rendered = await off.startRendering();
  data = downsampleTo16k(rendered.getChannelData(0), rate);
  const name = (file.name || "recording").replace(/\.[^.]+$/, "") + ".wav";
  return new File([encodeWav16(data, 16000)], name, { type: "audio/wav" });
}
