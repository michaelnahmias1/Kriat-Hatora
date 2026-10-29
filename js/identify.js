"use strict";
/* "זהה לי את הקטע מההקלטה" — לשונית התפילה (PLAN_TEFILA.md 4.5.2)

   הסדר הפוך מהרגיל: קודם ההקלטה, אחר-כך הטקסט. בוחרים קובץ (או משתמשים
   בקובץ שכבר נבחר בשלב 2) ⇐ הוא עולה ל-worker (‏POST /identify — תמלול בלבד
   וחיפוש בכל הסידור, ‏src/siddur/identify.py) ⇐ התוצאה נמשכת ב-/status כמו
   בסנכרון ⇐ עד 3 מועמדים: נוסח · קטע · טווח פסקאות, עם המילים הראשונות ⇐
   הקשה על קטע טוענת אותו בדיוק כמו בחירה בעץ (‏selectLeaf + loadSiddurLeaf,
   ‏source-siddur.js), וההקלטה כבר בשלב 2 (‏adoptAudioFile) — ממשיכים ישר
   לסנכרון בלי לבחור את הקובץ שוב.

   הקלטה שעוברת מקטע לקטע (באשכנז "נשמת" ו"שוכן עד" הם קטעים נפרדים) —
   מועמד אחד עם כמה קטעים, וכל אחד נטען בנפרד (אין טווח בין קטעים).
   כל טקסט מהענן מוצג כטקסט (textContent), לעולם לא כ-HTML. */

const ID_POLL_MS = 3000;
const ID_SHOW = 3;
const ID_MAX_PARTS = 5;   // הקלטה ארוכה שעוברת בהרבה קטעים — הראשונים בלבד
// מגבלת ה-worker לזיהוי (modal_worker/app.py: IDENTIFY_TIMEOUT_SEC) + מרווח
const ID_LIMIT_MS = 35 * 60 * 1000;
const ID_CONF = { high: "התאמה טובה", medium: "התאמה חלקית", low: "התאמה חלשה" };
const ID = { abort: null, job: null, t0: 0, timer: null, result: null };

function idMsg(html) { $("idMsg").innerHTML = html; }
function idLabel(t) { $("idLabel").textContent = t; }

/* הכפתור — רק כשיש worker בענן; "ההקלטה: …" כשכבר נבחר קובץ */
function renderIdentifyButton() {
  $("idWrap").hidden = !AI_ENDPOINT;
  const f = audioFileObj;
  $("idFileNote").hidden = !f;
  $("idFileName").textContent = f ? f.name : "";
}

function idBusy(on) {
  $("idBtn").disabled = on;
  $("idOther").disabled = on;
  $("idProgress").hidden = !on;
  clearInterval(ID.timer);
  ID.timer = null;
  if (!on) return;
  ID.t0 = Date.now();
  const tick = () => { $("idTime").textContent = fmtClock((Date.now() - ID.t0) / 1000); };
  tick();
  ID.timer = setInterval(tick, 1000);
}

/* worker ישן (לפני שלב 5) — אין לו /identify, ו-FastAPI עונה 404 */
function idDeployError() {
  const e = new Error("הענן עדיין לא עודכן לזיהוי קטעים — נסו שוב בעוד כמה דקות, " +
                      "או בחרו את הקטע בחיפוש או בסידור");
  e.deployWindow = true;
  return e;
}

$("idBtn").addEventListener("click", () => {
  if (ID.abort) return;
  if (audioFileObj) identifyRecording(audioFileObj);
  else $("idFile").click();
});
$("idOther").addEventListener("click", () => { if (!ID.abort) $("idFile").click(); });
$("idFile").addEventListener("change", () => {
  const f = $("idFile").files[0];
  $("idFile").value = "";   // אותו קובץ שוב ⇐ שוב change
  if (!f) return;
  adoptAudioFile(f);        // גם שלב 2 — אחרי הזיהוי לא בוחרים שוב
  renderIdentifyButton();
  identifyRecording(f);
});
$("audioFile").addEventListener("change", renderIdentifyButton);
$("idCancel").addEventListener("click", () => {
  if (ID.job) {   // עוצרים גם בענן — חוסך זמן GPU
    const fd = new FormData();
    fd.append("call_id", ID.job);
    fd.append("token", AI_TOKEN);
    fetch(AI_ENDPOINT + "/cancel", { method: "POST", body: fd }).catch(() => {});
  }
  if (ID.abort) ID.abort.abort();
});

async function identifyRecording(file) {
  if (ID.abort || !AI_ENDPOINT) return;
  ID.result = null;
  $("idResults").innerHTML = "";
  idMsg("");
  const ac = ID.abort = new AbortController();
  idBusy(true);
  idLabel("מכין את ההקלטה…");
  holdWakeLock();
  try {
    // וידאו ⇐ אודיו בלבד במכשיר (כמו בסנכרון)
    let upload = file;
    if (/^video\//i.test(file.type || "")) {
      if (file.size > MAX_DECODE_MB * 1048576)
        throw new Error(`הסרטון כבד מדי להמרה בטלפון (${fmtSize(file.size)}) — ` +
                        "אפשר לקצר אותו באפליקציית התמונות");
      idLabel("ממיר את הווידאו לאודיו במכשיר…");
      try { upload = await extractAudioForUpload(file); }
      catch (e) { upload = file; }
    }
    if (ac.signal.aborted) throw new DOMException("בוטל", "AbortError");
    if (upload.size > MAX_UPLOAD_MB * 1048576)
      throw new Error(`הקובץ גדול מ-${MAX_UPLOAD_MB}MB (${fmtSize(upload.size)})`);
    const fd = new FormData();
    fd.append("file", upload, upload.name);
    fd.append("token", AI_TOKEN);
    if (SD.nusach) fd.append("nusach", SD.nusach);   // עדיפות קלה בתיקו
    idLabel("מעלה את ההקלטה…");
    let sub;
    try {
      sub = await uploadToCloud(fd, ac.signal,
        frac => idLabel(`מעלה את ההקלטה… ${Math.round(frac * 100)}%`), "/identify");
    } catch (e) {
      if (e && (e.status === 404 || e.status === 405)) throw idDeployError();
      throw e;
    }
    releaseWakeLock();
    ID.job = sub.call_id;
    idLabel("מאזין להקלטה ומחפש בסידור… (בדרך כלל דקה-שתיים)");
    const data = await pollIdentify(sub.call_id, ac.signal);
    ID.result = data;
    renderIdentifyResults(data);
  } catch (e) {
    if (e && e.name === "AbortError") idMsg('<p class="hint">הזיהוי בוטל.</p>');
    else if (e && e.deployWindow) idMsg(`<p class="error">⏳ ${escapeHtml(e.message)}</p>`);
    else idMsg(`<p class="error">${escapeHtml("הזיהוי נכשל: " + String(e && e.message || e))}\nנסו שוב בעוד כמה דקות.</p>`);
  } finally {
    releaseWakeLock();
    ID.abort = null;
    ID.job = null;
    idBusy(false);
  }
}

async function pollIdentify(id, signal) {
  const t0 = Date.now();
  for (;;) {
    if (signal.aborted) throw new DOMException("בוטל", "AbortError");
    let res = null;
    try {
      res = await fetch(AI_ENDPOINT + "/status?call_id=" + encodeURIComponent(id), { signal });
    } catch (e) {
      if (signal.aborted) throw e;   // נפילת רשת רגעית — ממשיכים לשאול
    }
    if (res && res.status !== 202) {
      const data = await res.json().catch(() => ({}));
      if (res.status === 404) throw new Error("התוצאה כבר לא שמורה בענן — העלו את ההקלטה שוב");
      if (!res.ok) throw new Error(String(data.error || "שגיאה " + res.status));
      if (!data || !Array.isArray(data.candidates))
        throw new Error("התשובה מהענן אינה תוצאת זיהוי");
      return data;
    }
    if (Date.now() - t0 > ID_LIMIT_MS) throw new Error("הזיהוי נתקע בענן — נסו שוב");
    await cloudSleep(ID_POLL_MS, signal);
  }
}

/* ---------- התוצאות ---------- */
function idRangeText(p) {
  if (!p.total || p.total <= 1 || (p.from === 1 && p.to === p.total)) return "הקטע כולו";
  if (p.from === p.to) return `פסקה ${p.from} מתוך ${p.total}`;
  return `פסקאות ${p.from}–${p.to} מתוך ${p.total}`;
}
function idEl(tag, cls, text) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text != null) el.textContent = text;
  return el;
}

function renderIdentifyResults(data) {
  const box = $("idResults");
  box.innerHTML = "";
  const cands = (data.candidates || []).slice(0, ID_SHOW);
  const heard = String(data.transcript || "").trim();
  if (!cands.length) {
    idMsg('<p class="error">לא זוהה קטע מהסידור בהקלטה.</p>' +
      '<p class="hint">אפשר לחפש את הקטע בתיבת החיפוש למעלה. הזיהוי עובד על הקטעים שבספריית ' +
      "התפילות (שלושת הנוסחים); שיר או פיוט שאינם בסידור — דרך \"טקסט חופשי\".</p>" +
      (heard ? `<p class="hint">התמלול שמע: «${escapeHtml(heard.split(/\s+/).slice(0, 25).join(" "))}…»</p>` : ""));
    return;
  }
  idMsg(`<p class="okline">${cands.length === 1 ? "נמצאה התאמה" : `נמצאו ${cands.length} התאמות`}` +
        " — הקישו על הקטע כדי לטעון אותו</p>" +
        (data.limited ? `<p class="hint">ההקלטה ארוכה — הזיהוי נעשה על ${Math.round((data.duration || 600) / 60)} הדקות הראשונות.</p>` : ""));
  cands.forEach((c, k) => {
    const card = idEl("div", "idCand");
    const head = idEl("div", "idHead");
    head.append(idEl("span", "idNum", String(k + 1)), idEl("b", "", c.nusach_title || c.nusach));
    head.append(idEl("span", "idConf " + (c.confidence || "low"), ID_CONF[c.confidence] || ID_CONF.low));
    if (c.start != null && c.end != null)
      // זמנים משמאל לימין (‏LRI…PDI) — אחרת בעברית "1:58–0:12"
      head.append(idEl("span", "idTimeRange", `\u2066${fmtClock(c.start)}–${fmtClock(c.end)}\u2069 בהקלטה`));
    card.appendChild(head);
    const parts = c.parts || [];
    parts.slice(0, ID_MAX_PARTS).forEach((p, i) => {
      const b = idEl("button", "idPart");
      b.type = "button";
      b.dataset.path = p.path;
      const tt = idEl("span", "tt");
      tt.append(idEl("span", "nm", (i ? "ואחריו: " : "") + p.title));
      const crumbs = (p.breadcrumb || []).join(" › ");
      tt.append(idEl("small", "", [crumbs, idRangeText(p)].filter(Boolean).join(" · ")));
      if (p.first_words) tt.append(idEl("small", "bible fw", "«" + p.first_words + "…»"));
      b.append(tt, idEl("span", "go", "‹"));
      b.addEventListener("click", () => openIdentified(c, p, b));
      card.appendChild(b);
    });
    if (parts.length > ID_MAX_PARTS)
      card.appendChild(idEl("p", "hint", `ועוד ${parts.length - ID_MAX_PARTS} קטעים אחריהם בסידור.`));
    if (parts.length > 1)
      card.appendChild(idEl("p", "hint", "ההקלטה עוברת בין כמה קטעים בסידור — טוענים ומסנכרנים כל אחד בנפרד."));
    if ((c.also || []).length)
      card.appendChild(idEl("p", "hint", `אותו טקסט מופיע גם ב-${c.also.length} מקומות נוספים בסידור.`));
    box.appendChild(card);
  });
}

/* הקשה על קטע: הנוסח שלו, הקטע והטווח — ואז "טען את הקטע" */
async function openIdentified(c, p, btn) {
  if (typeof searchActive === "function" && searchActive()) clearSearch();
  useNusach(c.nusach);
  if (!SD.nusach) { SD.nusach = c.nusach; $("sdNusach").value = c.nusach; }
  SD.path = p.path.split("/").slice(0, -1).join("/");
  const whole = !p.total || (p.from === 1 && p.to === p.total);
  const label = whole ? p.title : `${p.title} (${idRangeText(p).replace(/ מתוך \d+$/, "")})`;
  $("idResults").querySelectorAll(".idPart.on").forEach(x => x.classList.remove("on"));
  btn.classList.add("on");
  const data = await selectLeaf({ path: p.path, title: p.title, label, from: p.from, to: p.to });
  if (!data) return;   // השגיאה כבר מוצגת (source-siddur.js)
  await loadSiddurLeaf();
  if (S.data && S.data.path === p.path) {
    idMsg(`<p class="okline">${escapeHtml(`נטען «${label}» ✓`)}` +
          (audioFileObj ? " — ההקלטה כבר נבחרה, אפשר להמשיך לסנכרון (שלב 3)." : "") + "</p>" +
          '<p class="hint">אפשר לשנות את הטווח ברשימת הפסקאות ולטעון שוב.</p>');
    $("segPreviewWrap").scrollIntoView({ block: "nearest" });
  }
}

renderIdentifyButton();
