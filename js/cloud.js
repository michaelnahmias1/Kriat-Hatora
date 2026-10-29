"use strict";
/* שלב 3 — סנכרון בענן: העלאה, מעקב, ביטול, התראות, wake lock וחידוש עבודה */

/* ---------- קליטת הזמנים מה-SRT שחוזר מהענן ---------- */
/* ‏order — סדר הביצוע שנשלח עם העבודה (performance): ה-SRT חוזר עם רשומה לכל
   הופעה. בלעדיו — רשומה לכל כתובית, כמו תמיד */
function applySrtTimes(text, mismatchHint, order) {
  const re = /(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)/g;
  const starts = [], ends = [];
  let m;
  while ((m = re.exec(text))) {
    starts.push(+m[1] * 3600 + +m[2] * 60 + +m[3] + +m[4] / 1000);
    ends.push(+m[5] * 3600 + +m[6] * 60 + +m[7] + +m[8] / 1000);
  }
  order = order || null;
  if (order && !validTimesOrder(order, S.data.segments.length))
    throw new Error("סדר הביצוע שנשלח לא תואם את הטקסט שנטען — טען את הקטע מחדש ונסה שוב");
  const n = order ? order.length : S.data.segments.length;
  if (!starts.length) throw new Error("לא חזרו חותמות זמן מהעיבוד");
  if (starts.length !== n)
    throw new Error(`חזרו ${starts.length} כתוביות אבל ${order ? "בסדר הביצוע" : "בקטע שנטען"} ${n} — ${mismatchHint}`);
  S.times = starts;
  S.timesOrder = order;
  S.endTime = ends[ends.length - 1];
}

/* ---------- שלב 3א: תזמון AI בענן (Modal — הפייפליין ההיברידי) ----------
   שני שלבים נפרדים במכוון:
   1. העלאה — החלק היחיד שדורש שהאפליקציה תישאר פתוחה (עם מד אחוזים ו-wake-lock).
   2. עיבוד בענן — מנותק לגמרי מהטלפון: ה-call_id נשמר ב-localStorage, אפשר
      לסגור את האפליקציה, והתוצאה נמשכת אוטומטית בכניסה הבאה (Modal שומר
      תוצאות כשבוע). אם המשתמש אישר התראות — נשלח Web Push בסיום. */
const CLOUD_POLL_MS = 5000;
// גבול זהירות למעקב: מגבלת הריצה של ה-worker ‏(modal_worker/app.py:
// WORKER_TIMEOUT_SEC, שעתיים) + מרווח — עבודה שעברה אותו כבר בוטלה בענן.
const CLOUD_JOB_LIMIT_MS = (2 * 60 + 10) * 60 * 1000;
// מגבלת ה-worker על ה-JSON של היחידות (modal_worker/params.py: MAX_UNITS_BYTES;
// בדיקה שומרת על הסנכרון) — נבדק לפני ההעלאה, לא אחרי הקלטה שלמה
const MAX_UNITS_BYTES = 200 * 1024;
if (AI_ENDPOINT) $("startCloud").hidden = false;

/* האזהרה היחידה שנשארה בשלב 3: אדומה כל עוד ההעלאה רצה, ירוקה ברגע
   שהיא נגמרה — מאותו רגע העיבוד ממשיך בענן בלי תלות בטלפון. */
function setStayNotice(mode) {
  const el = $("stayNotice");
  if (!mode) { el.hidden = true; return; }
  el.hidden = false;
  el.className = "notice " + (mode === "ok" ? "ok" : "warn");
  el.querySelector(".ico").textContent = mode === "ok" ? "✅" : "⚠️";
  $("stayText").textContent = mode === "ok"
    ? "ההעלאה הסתיימה — אפשר לצאת מהאפליקציה. העיבוד ממשיך בענן."
    : "אין לצאת מהאפליקציה עד לסיום ההעלאה.";
}

let cloudAbort = null;      // מאפשר לכפתור הביטול לעצור את הבקשות
let cloudTimerInt = null;   // הטיימר החלק (מתעדכן כל שנייה)
const CLOUD_BTN_LABEL = $("startCloud").textContent;
function cloudBusy(on) {
  const b = $("startCloud");
  b.disabled = on;
  b.textContent = on ? "⏳ מעבד בענן…" : CLOUD_BTN_LABEL;
}

/* הערכת זמן מותאמת לקובץ שהועלה: חימום ה-GPU (קבוע) + עיבוד שגדל עם אורך
   ההקלטה + זמן העלאה משוער לפי גודל הקובץ — ולא הערכה גסה קבועה. */
function estimateCloudSeconds() {
  const warmup = 40;                     // עליית ה-GPU וטעינת המודלים (cold start)
  const perSecAudio = 0.75;              // תמלול+יישור+VAD לכל שניית אודיו (T4)
  const dur = audioDurationSec || 180;   // אם המשך לא ידוע — בררת מחדל
  let secs = warmup + perSecAudio * dur;
  if (audioFileObj) {
    // וידאו מומר ל-WAV 16k מונו (≈32KB/ש') לפני ההעלאה — לכן מעריכים לפי המשך, לא הגודל הגולמי
    const isVideo = /^video\//i.test(audioFileObj.type || "");
    const uploadBytes = isVideo ? dur * 32000 : audioFileObj.size;
    secs += uploadBytes / (1.5 * 1024 * 1024);   // ~1.5MB/ש' — העלאה סלולרית טיפוסית
  }
  return Math.max(60, Math.round(secs));
}
function startCloudTimer(estSec, startedAt) {  // startedAt — לחידוש מעקב אחרי חזרה
  if (cloudTimerInt) { clearInterval(cloudTimerInt); cloudTimerInt = null; }
  $("cloudProgress").hidden = false;
  $("procBar").style.width = "0";
  const t0 = startedAt || Date.now();
  const render = () => {
    const el = (Date.now() - t0) / 1000;
    $("procTime").textContent = `${fmtClock(el)} / ~${fmtClock(estSec)}`;
    // התקדמות אסימפטוטית — מתקרבת ל-95% ולא עוברת, כדי לא "לשקר" שהסתיים
    const frac = 1 - Math.exp(-el / (estSec * 0.7));
    $("procBar").style.width = Math.min(95, frac * 100).toFixed(1) + "%";
  };
  render();
  cloudTimerInt = setInterval(render, 1000);
}
function stopCloudTimer(done) {
  if (cloudTimerInt) { clearInterval(cloudTimerInt); cloudTimerInt = null; }
  if (done) $("procBar").style.width = "100%";
  setTimeout(() => { $("cloudProgress").hidden = true; $("procBar").style.width = "0"; }, done ? 600 : 0);
}
function setProcLabel(t) { $("procLabel").textContent = t; }
function cloudSleep(ms, signal) {
  return new Promise((resolve, reject) => {
    const to = setTimeout(resolve, ms);
    signal.addEventListener("abort", () => { clearTimeout(to); reject(new DOMException("בוטל", "AbortError")); }, { once: true });
  });
}

/* המסך נשאר דולק בזמן ההעלאה — שהטלפון לא יירדם באמצע החלק היחיד
   שדורש שהאפליקציה תישאר פתוחה. */
let wakeLock = null;
function holdWakeLock() {
  if (navigator.wakeLock)
    navigator.wakeLock.request("screen").then(l => { wakeLock = l; }).catch(() => {});
}
function releaseWakeLock() {
  if (wakeLock) { wakeLock.release().catch(() => {}); wakeLock = null; }
}

/* התראת הסיום: מחזיר JSON של PushSubscription, או null כשאין תמיכה/הרשאה —
   הכל עובד גם בלי (התוצאה ממילא נטענת אוטומטית בכניסה הבאה). באייפון
   ההתראות זמינות רק כשהאפליקציה מותקנת למסך הבית (iOS 16.4+). */
function b64urlToBytes(s) {
  const b64 = (s + "=".repeat((4 - s.length % 4) % 4)).replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
}
async function ensurePushSubscription() {
  if (!VAPID_PUBLIC_KEY || !("Notification" in window) ||
      !("serviceWorker" in navigator) || !("PushManager" in window)) return null;
  try {
    const reg = await Promise.race([
      navigator.serviceWorker.ready,
      new Promise(res => setTimeout(() => res(null), 3000)),
    ]);
    if (!reg || !reg.pushManager) return null;
    if (Notification.permission !== "granted" &&
        (await Notification.requestPermission()) !== "granted") return null;
    const sub = (await reg.pushManager.getSubscription()) ||
      (await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: b64urlToBytes(VAPID_PUBLIC_KEY),
      }));
    return JSON.stringify(sub);
  } catch (e) { return null; }
}

/* העלאה עם מד אחוזים אמיתי (fetch לא חושף התקדמות העלאה — לכן XHR) */
function uploadToCloud(fd, signal, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", AI_ENDPOINT + "/submit");
    xhr.responseType = "json";
    xhr.upload.onprogress = ev => {
      if (ev.lengthComputable && onProgress) onProgress(ev.loaded / ev.total);
    };
    xhr.onload = () => {
      const data = xhr.response || {};
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);
      else reject(new Error(data.error || "שגיאה " + xhr.status));
    };
    xhr.onerror = () => reject(new Error("ההעלאה נכשלה — בדוק את החיבור ונסה שוב"));
    xhr.onabort = () => reject(new DOMException("בוטל", "AbortError"));
    signal.addEventListener("abort", () => xhr.abort(), { once: true });
    xhr.send(fd);
  });
}

/* קו פרשת המים: מכאן מותר לצאת מהאפליקציה — האזהרה מתחלפת לירוקה */
function announceCloudProcessing() {
  setProcLabel("מסנכרן…");
  $("timingMsg").innerHTML = "";
  setStayNotice("ok");
}

/* לולאת המעקב: שואלת לשלום העבודה עד תוצאה/שגיאה. העבודה נמחקת מהזיכרון
   המתמיד ברגע שיש תשובה סופית — שלא ננסה שוב לנצח אחרי כישלון. */
async function pollCloudJob(signal) {
  const job = S.cloudJob;
  for (;;) {
    if (signal.aborted) throw new DOMException("בוטל", "AbortError");
    let res = null;
    try {
      res = await fetch(AI_ENDPOINT + "/status?call_id=" + encodeURIComponent(job.id), { signal });
    } catch (e) {
      if (signal.aborted) throw e;
      // נפילת רשת רגעית בטלפון — ממשיכים לשאול
    }
    if (res && res.status !== 202) {
      const data = await res.json().catch(() => ({}));
      S.cloudJob = null; save();
      if (res.status === 404)
        throw new Error("התוצאה כבר לא שמורה בענן (נשמרת כשבוע מסיום העיבוד) — העלה את ההקלטה שוב");
      if (!res.ok) throw new Error(data.error || "שגיאה " + res.status);
      applySrtTimes(data.srt, isUnitsSource() ? "ודא שהטקסט תואם את ההקלטה"
                                           : "ודא שטווח הפסוקים תואם את ההקלטה", job.perf);
      S.report = (data.report || "").trim() || null;
      stopCloudTimer(true);
      setStayNotice(null);
      $("timingMsg").innerHTML = '<p class="okline">הסנכרון הושלם ✓</p>';
      if (!audioReady) {
        // ההנחיה גם בשלב 2 שנשאר פתוח — שלב 3 ננעל שוב כשאין קובץ אודיו
        showFileChip(S.audioName || "ההקלטה",
          "בחר את הקובץ שוב כדי להאזין");
      }
      refreshTimingSteps(); save();
      return;
    }
    // עדיין רץ (202) או שהרשת נפלה. תוצאה מוכנה נמשכת תמיד — גם ימים אחרי;
    // מוותרים רק על עבודה ש"רצה" מעבר למגבלת ה-worker (זומבי) ולא תסתיים.
    if (Date.now() - job.t0 > CLOUD_JOB_LIMIT_MS) {
      S.cloudJob = null; save();
      throw new Error("העיבוד נתקע בענן מעבר למגבלת הזמן — נסה להעלות שוב");
    }
    await cloudSleep(CLOUD_POLL_MS, signal);
  }
}

/* עטיפת המעקב המשותפת (כפתור + שגיאות) — גם אחרי העלאה וגם בחידוש */
async function trackCloudJob() {
  cloudBusy(true);
  cloudAbort = new AbortController();
  try {
    await pollCloudJob(cloudAbort.signal);
  } catch (e) {
    stopCloudTimer(false);
    setStayNotice(null);
    if (e && e.name === "AbortError")
      $("timingMsg").innerHTML = '<p class="hint">הסנכרון בוטל.</p>';
    else
      $("timingMsg").innerHTML =
        `<p class="error">הסנכרון נכשל: ${escapeHtml(String(e.message || e))}\nנסה שוב בעוד כמה דקות.</p>`;
  } finally {
    cloudAbort = null;
    cloudBusy(false);
  }
}

/* חידוש אחרי חזרה לאפליקציה: נקרא בטעינה כשיש עבודה שמורה — אם העיבוד
   הסתיים בינתיים התוצאה נמשכת מיד, ואם לא ממשיכים לעקוב מאותה נקודה. */
function resumeCloudJob() {
  if (!AI_ENDPOINT || !S.cloudJob) return;
  if (!S.data) { S.cloudJob = null; save(); return; }  // אין למה להצמיד זמנים
  refreshTimingSteps();  // פותח את שלב 3 — אחרת פס ההתקדמות והביטול נעולים
  // ‏ts — תחילת הטיימר בלחיצה המקורית (כולל ההעלאה), שהזמן לא יקפוץ אחורה
  startCloudTimer(S.cloudJob.est || 300, S.cloudJob.ts || S.cloudJob.t0);
  announceCloudProcessing();
  trackCloudJob();
}

async function runCloudTiming() {
  if (!audioFileObj) {
    $("timingMsg").innerHTML = '<p class="error">יש לבחור את קובץ ההקלטה מחדש (הדפדפן לא שומר קבצים בין ביקורים).</p>';
    return;
  }
  const unitsJson = isUnitsSource() ? JSON.stringify(S.data.units) : null;
  if (unitsJson && new TextEncoder().encode(unitsJson).length > MAX_UNITS_BYTES) {
    $("timingMsg").innerHTML =
      `<p class="error">הטקסט ארוך מדי לסנכרון (עד ${MAX_UNITS_BYTES / 1024}KB) — פצלו את הטקסט לכמה חלקים.</p>`;
    return;
  }
  cloudBusy(true);
  cloudAbort = new AbortController();
  const signal = cloudAbort.signal;
  const est = estimateCloudSeconds();
  const timerStart = Date.now();   // נשמר בעבודה — להמשכיות הטיימר אחרי סגירה
  startCloudTimer(est);
  $("timingMsg").innerHTML = "";
  setStayNotice("warn");
  holdWakeLock();
  let subData, pushSub = null, sentPerf = null;
  try {
    // הרשאת ההתראות מתבקשת עכשיו — צמוד ללחיצת המשתמש
    setProcLabel("מכין את ההעלאה…");
    pushSub = await ensurePushSubscription();
    if (signal.aborted) throw new DOMException("בוטל", "AbortError");

    // שכבת ההמרה: וידאו הופך לאודיו בלבד עוד במכשיר — מעלים רק את הקול
    let upload = audioFileObj;
    if (/^video\//i.test(audioFileObj.type || "")) {
      if (audioFileObj.size > MAX_DECODE_MB * 1048576)
        throw new Error(
          `הסרטון כבד מדי להמרה בטלפון (${fmtSize(audioFileObj.size)}). ` +
          "אפשר לקצר אותו באפליקציית התמונות, או להקליט את הקריאה " +
          "ב\"תזכורות קוליות\" ולהעלות את קובץ הקול.");
      setProcLabel("ממיר את הווידאו לאודיו במכשיר…");
      try { upload = await extractAudioForUpload(audioFileObj); }
      catch (e) { upload = audioFileObj; }  // ההמרה נכשלה — מעלים כמו שהוא, ffmpeg בשרת יסתדר
    }
    if (signal.aborted) throw new DOMException("בוטל", "AbortError");
    if (upload.size > MAX_UPLOAD_MB * 1048576)
      throw new Error(
        `הקובץ גדול מ-${MAX_UPLOAD_MB}MB (${fmtSize(upload.size)}) — ` +
        "פצל את ההקלטה לפי עליות והעלה כל חלק בנפרד.");
    const fd = new FormData();
    fd.append("file", upload, upload.name);
    fd.append("token", AI_TOKEN);
    if (pushSub) fd.append("push_sub", pushSub);
    if (isUnitsSource()) {
      // טקסט חופשי / סידור: היחידות עצמן, בדיוק כפי שחזרו מה-API והוצגו —
      // כולל יחידות ההוראה, שה-worker מדלג עליהן כמו ה-API (PLAN_TEFILA.md 3.3).
      // ה-mode נגזר בשרת מ-source (text/siddur ⇒ tefila)
      fd.append("source", dataSource());
      fd.append("units", unitsJson);
      if (S.data.max_words) fd.append("max_words", String(S.data.max_words));
      const title = sourceTitle().slice(0, 120);  // MAX_TITLE ב-params.py
      if (title) fd.append("title", title);
      // מבנה הביצוע (חזרות/פזמון/דילוגים, PLAN_TEFILA.md 3.2) — רק כשאינו סדר
      // הטקסט, ורק כשהסנכרון של חזרות פעיל ב-worker (PERFORMANCE_ENABLED)
      sentPerf = sentPerformance();
      if (sentPerf) fd.append("performance", JSON.stringify(sentPerf));
    } else {
      for (const [k, v] of Object.entries(readQuery())) if (v) fd.append(k, v);
    }
    // חלוקה מותאמת אישית — השרת יקבץ את אותן מילים בדיוק לפי הגדלים האלה
    if (S.splits) fd.append("splits", JSON.stringify(S.splits));

    // ── שלב ההעלאה: החלק היחיד שבו האפליקציה חייבת להישאר פתוחה ──
    setProcLabel("מעלה את ההקלטה…");
    subData = await uploadToCloud(fd, signal, frac =>
      setProcLabel(`מעלה את ההקלטה… ${Math.round(frac * 100)}%`));
  } catch (e) {
    releaseWakeLock();
    stopCloudTimer(false);
    setStayNotice(null);
    cloudAbort = null;
    cloudBusy(false);
    if (e && e.name === "AbortError")
      $("timingMsg").innerHTML = '<p class="hint">ההעלאה בוטלה.</p>';
    else
      $("timingMsg").innerHTML =
        `<p class="error">ההעלאה נכשלה: ${escapeHtml(String(e.message || e))}\nנסה שוב בעוד כמה דקות.</p>`;
    return;
  }
  releaseWakeLock();
  cloudAbort = null;

  // ── שלב העיבוד: העבודה רשומה ב-localStorage — שורדת סגירה וחזרה ──
  // ‏t0 — סיום ההעלאה (בסיס למגבלת הזמן); ts — תחילת הטיימר בתצוגה
  S.cloudJob = { id: subData.call_id, t0: Date.now(), ts: timerStart, est, push: !!pushSub };
  if (sentPerf) S.cloudJob.perf = sentPerf;   // התוצאה תחזור עם כתובית לכל הופעה
  save();
  announceCloudProcessing();
  await trackCloudJob();
}
$("startCloud").addEventListener("click", runCloudTiming);
$("cancelCloud").addEventListener("click", () => {
  const job = S.cloudJob;
  if (job) {
    // עוצרים את העבודה גם בענן, לא רק את המעקב — חוסך זמן GPU
    const fd = new FormData();
    fd.append("call_id", job.id);
    fd.append("token", AI_TOKEN);
    fetch(AI_ENDPOINT + "/cancel", { method: "POST", body: fd }).catch(() => {});
    S.cloudJob = null; save();
  }
  setStayNotice(null);
  if (cloudAbort) cloudAbort.abort();
});
