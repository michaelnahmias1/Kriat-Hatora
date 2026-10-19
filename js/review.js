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
  S.data.segments.forEach((seg, i) => {
    const row = document.createElement("div");
    row.className = "timerow";
    row.innerHTML =
      `<span class="t">${fmtSrt(S.times[i]).slice(3, 11)}</span>` +
      `<span class="txt bible">${isFreeText() ? escapeHtml(seg.display) : seg.display}</span>` +
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
