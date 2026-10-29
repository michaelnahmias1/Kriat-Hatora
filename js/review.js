"use strict";
/* שלבים 4–5 — דוח האיכות, רשימת הזמנים וכוונון */

/* ---------- שלב 4: דוח איכות העיבוד ---------- */
function parseReport(text) {
  const head = text.match(/מקטעים:\s*(\d+)\s*\|\s*ביטחון חציוני:\s*([\d.]+)\s*\|\s*לבדיקה ידנית:\s*(\d+)/);
  if (!head) return null;
  const items = [];
  // התווית: "פסוק 4" בתנ״ך, "שורה 3" בטקסט חופשי (confidence.format_report)
  const re = /\[(\d+):(\d+)\]\s*([^|\n]*?)\s*\|\s*ביטחון\s*([\d.]+)\s*\|\s*([^\n]*)(?:\n\s*סיבה:\s*([^\n]*))?/g;
  let m;
  while ((m = re.exec(text))) {
    items.push({
      t: (+m[1]) * 60 + (+m[2]), label: m[3], conf: +m[4],
      text: m[5].trim(), reason: (m[6] || "").trim(),
    });
  }
  return { total: +head[1], median: +head[2], low: +head[3], items };
}

/* שורות הדוח של תפילה (PLAN_TEFILA.md 4.3.4–4.3.5, ‏hybrid.py): הפרופיל
   בשורת הכותרת ("… | פרופיל: שירה"), דיבור שאינו בטקסט שזוהה ("זוהה דיבור
   שאינו בטקסט 00:57.5–00:58.4: «…»") ו"כנראה דולג" ("  כתובית 7 · בית 2 |
   8 מילים | …"). דוח ישן / תנ״ך — הכול ריק. */
function parseReportExtras(text) {
  const prof = text.match(/\|\s*פרופיל:\s*([^|\n]+?)\s*(?:\||\n|$)/);
  const nontext = [];
  const reN = /זוהה דיבור שאינו בטקסט\s+(\d+):(\d+(?:\.\d+)?)\s*[–-]\s*(\d+):(\d+(?:\.\d+)?):\s*«([^»\n]*)»/g;
  let m;
  while ((m = reN.exec(text)))
    nontext.push({ t0: +m[1] * 60 + +m[2], t1: +m[3] * 60 + +m[4], text: m[5].trim() });
  const skipped = [];
  const at = text.search(/^כנראה דולג/m);
  if (at >= 0) {
    const reS = /^\s*כתובית\s+(\d+)\s*·\s*([^|\n]*?)\s*\|\s*(\d+)\s*מילים\s*\|\s*([^\n]*)$/gm;
    const tail = text.slice(at);
    while ((m = reS.exec(tail)))
      skipped.push({ cue: +m[1], label: m[2], words: +m[3], text: m[4].trim() });
  }
  return { profile: prof ? prof[1] : "", nontext, skipped };
}

/* הצעה "נראה שזו שירה" (PLAN_TEFILA.md 8.27) — רק בתפילה/טקסט חופשי שסונכרנו
   כקריאה. ה-worker לא שולח מדד קצב, ולכן מחשבים מהזמנים שחזרו: חציון השניות
   למילה בכתובית (מתחילתה עד תחילת הבאה). נשמת המושרת שסונכרנה כקריאה: 1.16
   (בשירה 1.31; tests/fixtures/singing). קריאה מהירה לפי 8.27 ‏~0.25–0.5 למילה —
   ⚠️ הסף לא נבדק על הקלטת קריאה אמיתית. הצעה בלבד, בלי שינוי אוטומטי. */
const SINGING_HINT_SEC_PER_WORD = 0.9;
const SINGING_HINT_MIN_CUES = 6;
function secPerWordMedian() {
  if (!S.times || !S.data) return null;
  const cues = cueList(), n = Math.min(S.times.length, cues.length);
  const rates = [];
  for (let k = 0; k < n; k++) {
    const end = k + 1 < n ? S.times[k + 1] : S.endTime;
    const w = tokensOf(S.data.segments[cues[k].i].display).length;
    if (w && end > S.times[k]) rates.push((end - S.times[k]) / w);
  }
  if (rates.length < SINGING_HINT_MIN_CUES) return null;
  rates.sort((a, b) => a - b);
  const h = rates.length >> 1;
  return rates.length % 2 ? rates[h] : (rates[h - 1] + rates[h]) / 2;
}
function looksLikeSinging(ex) {
  if (!isUnitsSource() || ex.profile) return null;   // תנ״ך, או שכבר סונכרן בשירה
  const r = secPerWordMedian();
  return r != null && r >= SINGING_HINT_SEC_PER_WORD ? r : null;
}

function renderReportExtras(ex) {
  let html = "";
  const seek = t => `<button class="time" data-t="${t}" title="נגן מכאן">▶ ${fmtClock(t)}</button>`;
  const rate = looksLikeSinging(ex);
  if (rate != null) {
    html += `<div class="repHint" id="repSingHint">💡 נראה שההקלטה מושרת — כ-${rate.toFixed(1)} שניות למילה ` +
      "(בקריאה רגילה כחצי שנייה). אם זו שירה או חזנות, הדליקו \"שירה / חזנות\" בשלב 3 והריצו את הסנכרון שוב." +
      (singingAvailable() && !S.singing
        ? '<button type="button" class="secondary mt" id="repSingOn">🎵 הדלקת "שירה / חזנות"</button>' : "") +
      "</div>";
  }
  if (ex.nontext.length) {
    html += '<div class="repExtra" id="repNontext"><h4>🗣️ זוהה דיבור שאינו בטקסט</h4>' +
      '<p class="sub">פתיחה, הכרזה או שם המנגינה — המערכת דילגה עליהם, והם לא נכנסו לכתוביות.</p>' +
      ex.nontext.map(r => `<div class="repNote">${seek(r.t0)}<div class="body">` +
        `<span class="meta">עד ${fmtClock(r.t1)}</span>«${escapeHtml(r.text)}»</div></div>`).join("") +
      "</div>";
  }
  if (ex.skipped.length) {
    html += '<div class="repExtra" id="repSkipped"><h4>⏭ כנראה דולג</h4>' +
      '<p class="sub">אף מילה מהשורות האלה לא נשמעה בהקלטה. אם באמת לא נאמרו — סמנו אותן "דלג" ' +
      'ב"מבנה הביצוע" (שלב 1) והריצו את הסנכרון שוב; אם נאמרו — האזינו להן בשלב 5.</p>' +
      ex.skipped.map(k => {
        const t = S.times && S.times[k.cue - 1];
        const label = k.label && k.label !== "—" ? ` · ${escapeHtml(k.label)}` : "";
        return `<div class="repNote">${t != null ? seek(t) : ""}<div class="body">` +
          `<span class="meta">כתובית ${k.cue}${label} · ${k.words} מילים</span>` +
          `<span class="bible">${escapeHtml(k.text)}</span></div></div>`;
      }).join("") + "</div>";
  }
  return html;
}
function renderReport() {
  const view = $("reportView");
  if (!S.report) {
    view.innerHTML = '<p class="hint" style="margin:0">הדוח נוצר בסיום הסנכרון ומראה באילו מקומות ' +
      'ודאות הסנכרון נמוכה יותר.</p>';
    $("doneR").hidden = true;
    return;
  }
  const rep = parseReport(S.report);
  if (!rep) {  // פורמט לא מוכר — מציגים את הטקסט כמו שהוא
    view.innerHTML = `<div class="report">${escapeHtml(S.report)}</div>`;
    $("doneR").hidden = false;
    return;
  }
  const pct = Math.round(rep.median * 100);
  let html =
    '<p class="hint" style="margin:0 0 10px">כך המערכת מדרגת את ודאות הסנכרון של כל מקטע. ' +
    'מקטעים שמופיעים למטה — כדאי להאזין להם בשלב 5 ולכוון אם צריך.</p>' +
    `<div class="repSummary">
      <div class="repTile"><span class="v">${rep.total}</span><span class="l">מקטעים</span></div>
      <div class="repTile"><span class="v" style="color:${pct >= 70 ? "var(--ok)" : pct >= 50 ? "var(--gold)" : "var(--err)"}">${pct}%</span><span class="l">ודאות כללית</span></div>
      <div class="repTile"><span class="v" style="color:${rep.low ? "var(--gold)" : "var(--ok)"}">${rep.low}</span><span class="l">לבדיקה ידנית</span></div>
    </div>`;
  const ex = parseReportExtras(S.report);
  if (ex.profile) html += `<span class="repProfile">🎵 פרופיל: ${escapeHtml(ex.profile)}</span>`;
  // מה עוד זוהה (הצעת שירה, דיבור שאינו בטקסט, "כנראה דולג") — לפני רשימת המקטעים
  html += renderReportExtras(ex);
  if (!rep.items.length) {
    html += '<div class="repAllOk">✅ <span>כל המקטעים סונכרנו בוודאות טובה — אפשר לעבור ישר לייצוא, ' +
      'ומומלץ רק להעיף מבט בשלב 5.</span></div>';
  } else {
    html += rep.items.map(it => {
      const p = Math.round(it.conf * 100);
      return `<div class="repItem${it.conf < 0.3 ? " bad" : ""}">
        <div class="head">
          <button class="time" data-t="${it.t}" title="נגן מכאן">▶ ${fmtClock(it.t)}</button>
          <span class="badge">${escapeHtml(it.label)}</span>
          <span class="conf">ודאות ${p}%</span>
        </div>
        <div class="repBar"><i style="width:${p}%"></i></div>
        <div class="txt bible">${escapeHtml(it.text)}</div>
        ${it.reason && it.reason !== "—" ? `<div class="why">💡 ${escapeHtml(it.reason)}</div>` : ""}
      </div>`;
    }).join("");
  }
  view.innerHTML = html;
  view.onclick = e => {
    if (e.target.closest("#repSingOn")) {   // ההצעה "נראה שזו שירה" — מדליקה את המתג בשלב 3
      S.singing = true;
      renderSingToggle(); save();
      e.target.closest("#repSingOn").remove();
      $("step3").scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const b = e.target.closest("button.time"); if (!b) return;
    player.currentTime = +b.dataset.t; player.play();
  };
  $("doneR").hidden = false;
}

/* ---------- שלב 4: בדיקה ותיקון ---------- */
function nudge(i, delta) {
  const lo = i > 0 ? S.times[i - 1] + 0.05 : 0;
  const hi = (i + 1 < S.times.length ? S.times[i + 1] : S.endTime) - 0.05;
  S.times[i] = Math.min(Math.max(S.times[i] + delta, lo), hi);
  renderTimeList(); save();
}
function renderTimeList() {
  const list = $("timeList");
  list.innerHTML = "";
  // רשומה לכל הופעה בסדר הביצוע (performance.js) — כתובית שחוזרת מופיעה שוב,
  // עם מספר הכתובית בטקסט ו"חזרה 2"; בלי סדר ביצוע — בדיוק כמו קודם
  const expanded = !!S.timesOrder;
  cueList().forEach((cue, i) => {
    const seg = S.data.segments[cue.i];
    const row = document.createElement("div");
    row.className = "timerow";
    const tag = expanded
      ? `<small class="cueTag">כתובית ${cue.i + 1}${cue.occ > 1 ? ` · חזרה ${cue.occ}` : ""}</small>` : "";
    row.innerHTML =
      `<span class="t">${fmtSrt(S.times[i]).slice(3, 11)}</span>` +
      `<span class="txt bible">${tag}${isUnitsSource() ? escapeHtml(seg.display) : seg.display}</span>` +
      `<button class="small secondary" data-act="play" data-i="${i}">▶</button>` +
      `<button class="small secondary" data-act="minus" data-i="${i}">−0.2</button>` +
      `<button class="small secondary" data-act="plus" data-i="${i}">+0.2</button>`;
    list.appendChild(row);
  });
  list.onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    const i = +b.dataset.i;
    if (b.dataset.act === "play") { player.currentTime = S.times[i]; player.play(); }
    else nudge(i, b.dataset.act === "plus" ? 0.2 : -0.2);
  };
}
