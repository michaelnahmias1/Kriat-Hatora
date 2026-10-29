"use strict";
/* מבנה הביצוע — חזרות, פזמון ודילוגים (PLAN_TEFILA.md 4.3.1; החוזה ב-3.2)

   מעל החלוקה לכתוביות המשתמש מסמן "בתים" — קבוצות של כתוביות רצופות (ההצעה
   הראשונה: בית לכל שורה/פסקה, או לפי השורות הריקות בטקסט החופשי) — ולכל בית
   או כתובית: "חזור ×N" ו"דלג"; ובית אחד כ"פזמון", שנוסף אחרי כל בית. מכאן
   נגזר performance: רשימת אינדקסי הכתוביות (מ-0, ב-S.data.segments) לפי סדר
   הביצוע בפועל. חזרה = אינדקס שמופיע שוב; דילוג = אינדקס שחסר; סדר הטקסט
   (0..n-1) = אין performance = ההתנהגות של היום.

   המודל נשמר במונחי מילים ולא במונחי מספרי כתוביות: כל בית מזוהה בהיסט
   המילה הראשונה שלו ברצף המילים, וכל כתובית ב"היסט+אורך". רצף המילים לא
   משתנה בעריכת החלוקה, ולכן אחרי עריכה המבנה מותאם לחלוקה החדשה
   (perfAfterSplits) ולא נמחק.

   S.perf = null | { v: 1, sig, after, starts: [w…], blocks: [{rep, skip, refrain}…],
                     subs: {"w+n": {rep, skip}} }
   S.timesOrder — הסדר שאליו שייכים S.times (מה שנשלח לענן); null = סדר הטקסט. */

const PERF_MAX_REP = 9;
// ‏MAX_PERFORMANCE ב-modal_worker/params.py (בדיקה ב-tests שומרת על הסנכרון)
const PERF_MAX_LEN = 20000;
const PERF_DEF_SUB = Object.freeze({ rep: 1, skip: false });
const perfDefBlock = () => ({ rep: 1, skip: false, refrain: false });

/* העורך זמין רק לתפילה ולטקסט חופשי — לא לתנ״ך */
function perfAvailable() { return !!(S.data && S.data.segments && isUnitsSource()); }

/* ---------- גאומטריה: מיקום כל כתובית ברצף המילים ---------- */
function perfGeom() {
  const segs = S.data.segments;
  const lens = segs.map(s => tokensOf(s.display).length);
  const off = [];
  let w = 0;
  for (const n of lens) { off.push(w); w += n; }
  return { segs, lens, off, total: w, key: i => off[i] + "+" + lens[i] };
}
/* הכתובית שמכילה את המילה w */
function perfSubAt(g, w) {
  let lo = 0, hi = g.off.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (g.off[mid] <= w) lo = mid; else hi = mid - 1;
  }
  return lo;
}
/* חתימת רצף המילים — מבנה ששמור לטקסט אחר לא יוחל עליו */
function perfTextSig() {
  const s = S.data.segments.map(seg => tokensOf(seg.display).join(" ")).join(" ");
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h * 33) ^ s.charCodeAt(i)) >>> 0;
  return s.length + ":" + h.toString(36);
}

/* ---------- ההצעה הראשונה לבתים ---------- */
/* טקסט חופשי עם שורות ריקות בין הבתים: מספר הבית של כל יחידה. רק כשהשורות
   בתיבה תואמות בדיוק את היחידות שנטענו (אחרת — null, ובית לכל שורה). שורה
   בלי אות עברית (כמו "***") נחשבת מפריד, כמו שורה ריקה. */
function freeTextParagraphs() {
  if (!isFreeText() || !S.data.units) return null;
  const units = S.data.units;
  const out = [];
  let para = 0, gap = false;
  for (const raw of readFreeText().text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || !HE_LETTER_RE.test(line)) { if (out.length) gap = true; continue; }
    if (out.length >= units.length || units[out.length].text !== line) return null;
    if (gap) { para++; gap = false; }
    out.push(para);
  }
  return out.length === units.length && para > 0 ? out : null;
}
function perfDefault(g) {
  const paras = freeTextParagraphs();
  const starts = [], blocks = [];
  let prev = null;
  g.segs.forEach((s, i) => {
    // תווית היחידה ("שורה 3", ‏"קבלת שבת · 37") — פסקה מעורבת בסידור היא בית אחד
    const grp = paras ? "p" + paras[s.verse - 1] : "u" + unitLabel(s.verse);
    if (grp !== prev) { starts.push(g.off[i]); blocks.push(perfDefBlock()); prev = grp; }
  });
  return { v: 1, sig: perfTextSig(), after: false, starts, blocks, subs: {} };
}

/* ---------- התאמה לחלוקה הנוכחית ---------- */
/* גבול בית שנפל באמצע כתובית עובר לתחילתה; שני בתים שהתמזגו — נשאר הראשון;
   הגדרות של כתובית שכבר לא קיימת נמחקות (dropped = כמה מהן היו פעילות) */
function perfNormalize(p, g) {
  const starts = [], blocks = [];
  let changed = false, dropped = 0;
  (p.starts || []).forEach((w, b) => {
    const sw = g.off[perfSubAt(g, Math.max(0, Math.min(+w || 0, g.total - 1)))];
    if (sw !== w) changed = true;
    if (starts.length && starts[starts.length - 1] >= sw) { changed = true; return; }
    starts.push(sw);
    const bl = (p.blocks || [])[b] || {};
    blocks.push({ rep: perfClampRep(bl.rep), skip: !!bl.skip, refrain: !!bl.refrain });
  });
  if (!starts.length || starts[0] !== 0) { starts.unshift(0); blocks.unshift(perfDefBlock()); changed = true; }
  const valid = new Set(g.segs.map((_, i) => g.key(i)));
  const subs = {};
  for (const [k, a] of Object.entries(p.subs || {})) {
    const rep = perfClampRep(a && a.rep), skip = !!(a && a.skip);
    if (rep === 1 && !skip) continue;
    if (valid.has(k)) subs[k] = { rep, skip };
    else { dropped++; changed = true; }
  }
  return { p: { v: 1, sig: perfTextSig(), after: !!p.after, starts, blocks, subs }, changed, dropped };
}
function perfClampRep(n) {
  n = Math.round(+n || 1);
  return Math.min(PERF_MAX_REP, Math.max(1, n));
}

/* ---------- גזירת סדר הביצוע ---------- */
function perfBlocks(p, g) {
  const from = p.starts.map(w => perfSubAt(g, w));
  return from.map((f, b) => Object.assign({ b, from: f, to: b + 1 < from.length ? from[b + 1] : g.segs.length }, p.blocks[b]));
}
/* הכלל: הבתים לפי סדר הטקסט, כל אחד ×rep (בית שמדלגים עליו — לא נשמע במקומו).
   "הוסף את הפזמון אחרי כל בית": אחרי כל בית שאינו פזמון נשמע הפזמון — אלא אם
   הבית הבא שנשמע כבר הוא פזמון (כמו בסידור, שבו הפזמון כתוב אחרי כל בית).
   חזרות ודילוגים של כתובית חלים בכל מקום שהיא נשמעת, גם בפזמון שנוסף. */
function perfOrder(p, g) {
  const blocks = perfBlocks(p, g);
  const sub = i => p.subs[g.key(i)] || PERF_DEF_SUB;
  const order = [], inserted = [];
  const emit = (bl, ins) => {
    for (let r = 0; r < bl.rep; r++)
      for (let i = bl.from; i < bl.to; i++) {
        const a = sub(i);
        if (a.skip) continue;
        for (let k = 0; k < a.rep && order.length <= PERF_MAX_LEN; k++) { order.push(i); inserted.push(ins); }
      }
  };
  const refrain = blocks.find(bl => bl.refrain);
  blocks.forEach((bl, k) => {
    if (!bl.skip) emit(bl, false);
    if (bl.skip || !p.after || !refrain || bl.refrain) return;
    const next = blocks.slice(k + 1).find(x => !x.skip);
    if (!next || !next.refrain) emit(refrain, true);
  });
  return { order, inserted, blocks };
}
const perfIsLinear = (order, n) => order.length === n && order.every((x, i) => x === i);
function perfIsDefault(p, g) {
  const d = perfDefault(g);
  const strip = m => JSON.stringify([m.starts, m.blocks, m.subs, m.blocks.some(b => b.refrain) && !!m.after]);
  return strip(p) === strip(d);
}
/* בעיה שמונעת שמירה/שליחה — או "" */
function perfProblem(order) {
  if (!order.length) return "אי אפשר לדלג על כל הכתוביות — חייבת להישאר לפחות אחת.";
  if (order.length > PERF_MAX_LEN) return `ארוך מדי: יותר מ-${PERF_MAX_LEN.toLocaleString("he-IL")} כתוביות בהקלטה. הפחיתו חזרות.`;
  return "";
}

/* סדר הביצוע של הטקסט שנטען — או null כשהוא סדר הטקסט (אין מה לשלוח) */
function performanceOrder() {
  if (!perfAvailable() || !S.perf) return null;
  const g = perfGeom();
  const { order } = perfOrder(S.perf, g);
  if (perfIsLinear(order, g.segs.length) || perfProblem(order)) return null;
  return order;
}
/* מה שנשלח ל-worker: רק כשהסנכרון של חזרות פעיל (config.js) */
function sentPerformance() { return PERFORMANCE_ENABLED ? performanceOrder() : null; }

/* ---------- הכתוביות בתוצאה (שלבים 4–6) ----------
   כשהעבודה נשלחה עם סדר ביצוע, ה-SRT חוזר עם רשומה לכל הופעה — S.times
   מקביל ל-S.timesOrder, וכתובית שחוזרת מופיעה שוב ברשימה ובקובץ. */
function cueOrder() {
  return S.timesOrder || S.data.segments.map((_, i) => i);
}
function cueList() {
  const seen = {};
  return cueOrder().map(i => ({ i, occ: (seen[i] = (seen[i] || 0) + 1) }));
}
function cueCount() { return S.timesOrder ? S.timesOrder.length : S.data.segments.length; }
function validTimesOrder(order, n) {
  return Array.isArray(order) && order.length > 0 &&
    order.every(i => Number.isInteger(i) && i >= 0 && i < n);
}

/* ---------- אחרי עריכת החלוקה / שחזור ---------- */
/* נקרא מ-applySplits: מתאים את המבנה לחלוקה החדשה. מחזיר הודעה למשתמש */
function perfAfterSplits() {
  if (!S.perf) return "";
  const g = perfGeom();
  const r = perfNormalize(S.perf, g);
  S.perf = perfIsDefault(r.p, g) ? null : r.p;
  return r.dropped
    ? "מבנה הביצוע הותאם לחלוקה החדשה, וחזרות או דילוגים של כתוביות שהשתנו בוטלו — כדאי לבדוק אותו שוב."
    : "מבנה הביצוע הותאם לחלוקה החדשה — כדאי לבדוק אותו שוב.";
}
/* בשחזור מ-localStorage: מבנה של טקסט אחר (או פגום) — נזרק בשקט */
function perfRestore(saved, timesOrder) {
  S.perf = null;
  S.timesOrder = null;
  if (!S.data || !S.data.segments) return;
  if (saved && typeof saved === "object" && perfAvailable() && saved.sig === perfTextSig()) {
    try {
      const g = perfGeom();
      const p = perfNormalize(saved, g).p;
      S.perf = perfIsDefault(p, g) ? null : p;
    } catch (e) { S.perf = null; }
  }
  if (timesOrder && validTimesOrder(timesOrder, S.data.segments.length)) S.timesOrder = timesOrder;
}

/* ---------- השורה בכרטיס הטקסט שנטען ---------- */
function perfSummary(order) {
  const n = S.data.segments.length;
  const uniq = new Set(order).size;
  const parts = [];
  const p = S.perf;
  if (p && p.after && p.blocks.some(b => b.refrain)) parts.push("פזמון אחרי כל בית");
  if (p && (p.blocks.some(b => b.rep > 1) || Object.values(p.subs).some(a => a.rep > 1))) parts.push("חזרות");
  if (uniq < n) parts.push(`דילוג על ${n - uniq} כתוביות`);
  return parts.join(", ") || "סדר מותאם";
}
function renderPerfStatus() {
  const on = perfAvailable();
  $("perfRow").hidden = !on;
  if (!on) return;
  const order = performanceOrder();
  let t = order
    ? `סדר הביצוע: ${order.length} כתוביות בהקלטה (בטקסט ${S.data.segments.length}) — ${perfSummary(order)}.`
    : "סדר הביצוע: לפי הטקסט, בלי חזרות.";
  if (order && !PERFORMANCE_ENABLED)
    t += "\n⏳ בקרוב: הסנכרון של חזרות. בינתיים הסנכרון ייעשה לפי סדר הטקסט.";
  $("perfStatus").textContent = t;
  $("perfStatus").classList.toggle("on", !!order);
}

/* ---------- העורך ---------- */
const PE = { p: null, g: null, sel: null, tab: "edit" };
const perfClone = p => JSON.parse(JSON.stringify(p));

function openPerfEditor() {
  if (!perfAvailable()) return;
  if (S.cloudJob) {   // הסנכרון שרץ עכשיו נשלח עם הסדר הקודם
    $("loadMsg").innerHTML =
      '<p class="hint">אי אפשר לשנות את מבנה הביצוע בזמן שהסנכרון רץ — בטלו אותו תחילה.</p>';
    return;
  }
  PE.g = perfGeom();
  PE.p = S.perf ? perfNormalize(perfClone(S.perf), PE.g).p : perfDefault(PE.g);
  PE.sel = null;
  PE.tab = "edit";
  $("perfSoon").hidden = PERFORMANCE_ENABLED;
  perfRender();
  $("perfBody").scrollTop = 0;
  $("perfOverlay").classList.add("open");
}
function closePerfEditor() { $("perfOverlay").classList.remove("open"); }

function perfStepper(act, id, n, what) {
  return `<span class="stepper" role="group" aria-label="${what}">` +
    `<button type="button" data-act="${act}-" data-id="${id}" aria-label="פחות"${n <= 1 ? " disabled" : ""}>−</button>` +
    `<b>חזור <bdi dir="ltr">×${n}</bdi></b>` +
    `<button type="button" data-act="${act}+" data-id="${id}" aria-label="עוד"${n >= PERF_MAX_REP ? " disabled" : ""}>+</button></span>`;
}
function perfRender() {
  const { p, g } = PE;
  const res = perfOrder(p, g);
  const hasRefrain = res.blocks.some(b => b.refrain);
  $("perfAfterWrap").hidden = !hasRefrain;
  $("perfAfter").checked = !!p.after;
  $("perfTabEdit").setAttribute("aria-selected", String(PE.tab === "edit"));
  $("perfTabPreview").setAttribute("aria-selected", String(PE.tab === "preview"));
  $("perfTabPreview").textContent = `התוצאה (${res.order.length})`;
  $("perfList").hidden = PE.tab !== "edit";
  $("perfPreview").hidden = PE.tab !== "preview";
  if (PE.tab === "edit") perfRenderEdit(res); else perfRenderPreview(res);
  const problem = perfProblem(res.order);
  const linear = perfIsLinear(res.order, g.segs.length);
  $("perfCount").innerHTML =
    `<span>${g.segs.length} כתוביות בטקסט ← <b>${res.order.length}</b> בהקלטה</span>` +
    (problem ? `<span class="error">${escapeHtml(problem)}</span>`
      : linear ? '<span class="lin">כמו סדר הטקסט</span>' : "");
  $("perfSave").disabled = !!problem;
}
function perfRenderEdit(res) {
  const { p, g } = PE;
  let html = "", stanza = 0;
  for (const bl of res.blocks) {
    const name = bl.refrain ? "🎵 פזמון" : `בית ${++stanza}`;
    html += `<div class="pblock${bl.refrain ? " refrain" : ""}${bl.skip ? " skip" : ""}" data-b="${bl.b}">` +
      `<div class="phead"><span class="pname">${name}</span>` +
      `<span class="plabel">${escapeHtml(unitLabel(g.segs[bl.from].verse))}</span>` +
      (bl.skip ? '<span class="ptag">מדלגים</span>' : "") +
      (bl.b > 0 ? `<button type="button" class="pmrg" data-act="merge" data-id="${bl.b}">🔗 חיבור לבית שמעל</button>` : "") +
      "</div>";
    for (let i = bl.from; i < bl.to; i++) {
      const a = p.subs[g.key(i)] || PERF_DEF_SUB;
      const sel = PE.sel === i;
      html += `<div class="pline${sel ? " sel" : ""}${a.skip ? " skip" : ""}" data-i="${i}">` +
        `<span class="gi">${i + 1}</span><span class="txt bible">${escapeHtml(g.segs[i].display)}</span>` +
        (a.rep > 1 ? `<span class="ptag" dir="ltr">×${a.rep}</span>` : "") +
        (a.skip ? '<span class="ptag">מדלגים</span>' : "") + "</div>";
      if (sel)
        html += `<div class="lact" data-i="${i}">` +
          perfStepper("srep", i, a.rep, "חזרות על השורה") +
          `<button type="button" class="tog${a.skip ? " on" : ""}" data-act="sskip" data-id="${i}" aria-pressed="${a.skip}">⏭ דלג על השורה</button>` +
          `<button type="button" class="tog" data-act="split" data-id="${i}"${i === bl.from ? " disabled" : ""}>✂ בית חדש מכאן</button>` +
          "</div>";
    }
    html += '<div class="bctl">' + perfStepper("brep", bl.b, bl.rep, "חזרות על הבית") +
      `<button type="button" class="tog${bl.refrain ? " on" : ""}" data-act="refrain" data-id="${bl.b}" aria-pressed="${bl.refrain}">🎵 פזמון</button>` +
      `<button type="button" class="tog${bl.skip ? " on" : ""}" data-act="bskip" data-id="${bl.b}" aria-pressed="${bl.skip}">⏭ דלג</button>` +
      "</div></div>";
  }
  $("perfList").innerHTML = html;
}
function perfRenderPreview(res) {
  const { g } = PE;
  const seen = {};
  const skipped = g.segs.length - new Set(res.order).size;
  let html = '<p class="hint pnote">כך ייראו הכתוביות בסרטון, לפי הסדר. המספר האפור הוא מספר הכתובית בטקסט.' +
    (skipped ? ` ${skipped} כתוביות לא מופיעות (דילוג).` : "") + "</p>";
  res.order.forEach((i, k) => {
    const occ = seen[i] = (seen[i] || 0) + 1;
    const ins = res.inserted[k];
    html += `<div class="prow${ins ? " ins" : ""}${occ > 1 ? " rep" : ""}">` +
      `<span class="pi">${k + 1}</span><span class="pb">כתובית ${i + 1}</span>` +
      `<span class="txt bible">${escapeHtml(g.segs[i].display)}</span>` +
      (ins ? '<span class="ptag gold">פזמון</span>' : "") +
      (occ > 1 ? `<span class="ptag">חזרה ${occ}</span>` : "") + "</div>";
  });
  $("perfPreview").innerHTML = html;
}

/* ---------- פעולות העורך ---------- */
/* טקסט הבית בלי ניקוד ופיסוק — כך מזהים את אותו פזמון שכתוב שוב בטקסט */
function perfBlockText(bl) {
  return PE.g.segs.slice(bl.from, bl.to).map(s => s.display).join(" ").replace(/[^א-ת]/g, "");
}
function perfSetSub(i, fn) {
  const k = PE.g.key(i);
  const a = Object.assign({}, PE.p.subs[k] || PERF_DEF_SUB);
  fn(a);
  if (a.rep === 1 && !a.skip) delete PE.p.subs[k]; else PE.p.subs[k] = a;
}
function perfAct(act, id) {
  const { p, g } = PE;
  const blocks = perfBlocks(p, g);
  switch (act) {
    case "brep+": case "brep-":
      p.blocks[id].rep = perfClampRep(p.blocks[id].rep + (act === "brep+" ? 1 : -1)); break;
    case "bskip": p.blocks[id].skip = !p.blocks[id].skip; break;
    case "refrain": {
      // פזמון אחד: כל הבתים עם אותו טקסט מסומנים יחד; פזמון אחר שסומן קודם — מתבטל
      const on = !p.blocks[id].refrain;
      const txt = perfBlockText(blocks[id]);
      blocks.forEach(bl => {
        p.blocks[bl.b].refrain = on && (bl.b === id || (!!txt && perfBlockText(bl) === txt));
      });
      if (on && !blocks.some(bl => bl.refrain)) p.after = true;   // פעם ראשונה — "אחרי כל בית" דלוק
      break;
    }
    case "merge":
      if (id > 0) { p.starts.splice(id, 1); p.blocks.splice(id, 1); }
      PE.sel = null; break;
    case "split": {
      const bl = blocks.find(b => id > b.from && id < b.to);
      if (bl) { p.starts.splice(bl.b + 1, 0, g.off[id]); p.blocks.splice(bl.b + 1, 0, perfDefBlock()); }
      break;
    }
    case "srep+": case "srep-":
      perfSetSub(id, a => { a.rep = perfClampRep(a.rep + (act === "srep+" ? 1 : -1)); }); break;
    case "sskip": perfSetSub(id, a => { a.skip = !a.skip; }); break;
    default: return;
  }
  perfRender();
}
$("perfBtn").addEventListener("click", openPerfEditor);
$("perfCancel").addEventListener("click", closePerfEditor);
$("perfTabEdit").addEventListener("click", () => { PE.tab = "edit"; perfRender(); });
$("perfTabPreview").addEventListener("click", () => { PE.tab = "preview"; perfRender(); $("perfBody").scrollTop = 0; });
$("perfAfter").addEventListener("change", () => { PE.p.after = $("perfAfter").checked; perfRender(); });
$("perfReset").addEventListener("click", () => {
  PE.p = perfDefault(PE.g);
  PE.sel = null;
  perfRender();
});
$("perfList").addEventListener("click", e => {
  const b = e.target.closest("button[data-act]");
  if (b) { if (!b.disabled) perfAct(b.dataset.act, +b.dataset.id); return; }
  const line = e.target.closest(".pline");
  if (!line) return;
  const i = +line.dataset.i;
  PE.sel = PE.sel === i ? null : i;   // הקשה = בחירה/ביטול בחירה
  perfRender();
});
$("perfSave").addEventListener("click", () => {
  const { p, g } = PE;
  if (perfProblem(perfOrder(p, g).order)) return;
  S.perf = perfIsDefault(p, g) ? null : p;
  closePerfEditor();
  // הזמנים שייכים לסדר שנשלח — אם מה שיישלח עכשיו שונה, הם כבר לא תקפים
  let msg = performanceOrder() ? "מבנה הביצוע נשמר ✓" : "סדר הביצוע: לפי הטקסט ✓";
  if (S.times && JSON.stringify(sentPerformance()) !== JSON.stringify(S.timesOrder)) {
    S.times = null; S.endTime = null; S.report = null; S.timesOrder = null;
    msg += " — הזמנים אופסו, יש להריץ את הסנכרון מחדש";
    refreshTimingSteps();
  }
  $("loadMsg").innerHTML = `<p class="okline">${msg}</p>`;
  renderPerfStatus();
  save();
});
