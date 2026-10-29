"use strict";
/* שלב 1 — מקור "תפילה": ספריית הסידור (PLAN_TEFILA.md 4.2.4)

   חיפוש (תיבה גדולה בראש הלשונית: קיצורים ואחריהם קטעים, שמות נרדפים —
   ‏/api/siddur?q=) / נוסח (נזכר) ← קטעים נפוצים / ניווט בעץ ← קטע (עלה) ←
   טווח פסקאות ← "טען את הקטע". מכאן הכול כמו בטקסט חופשי: S.data הוא תשובת
   ‏/api/siddur?path=… (‏units + segments, ‏mode=tefila) עם source="siddur",
   ולענן נשלחות היחידות עצמן — כולל יחידות ההוראה, שה-worker מדלג עליהן בדיוק
   כמו ה-API (‏units_to_segments).

   העץ והטקסט נטענים מה-API (‏api/siddur.py) — לא משוכפלים לדף (6.4), ורק
   כשהלשונית "תפילה" נפתחת. כל טקסט שמגיע מה-API מוצג כטקסט (textContent /
   escapeHtml), לעולם לא כ-HTML. */

const SD = {
  nusachim: null,   // [{key, title}] — מה-API, פעם אחת
  nusach: "",       // הנוסח שנבחר (נשמר)
  path: "",         // התיקייה שמוצגת בעץ — נתיב מלא (נשמר)
  leaf: null,       // הקטע שנבחר (נשמר): {path, title, label, base, from, to, total, paragraphs, meta}
  payload: null,    // תשובת ה-API לקטע ולטווח שנטענו לאחרונה (בזיכרון בלבד)
  popular: {},      // נוסח ⇐ תשובת ?popular=1
  browseData: null, // הילדים של התיקייה שמוצגת — לחזרה מקטע בלי בקשה נוספת
  started: false,
  req: 0,           // מונה בקשות העץ — תשובה ישנה לא דורסת חדשה
  searchReq: 0,     // אותו דבר לבקשות החיפוש
  leafReq: 0,       // ולבקשות הקטע
};
const SD_SEARCH_DELAY_MS = 350;
const SD_SEARCH_MIN = 2;

/* ---------- שמירה ושחזור ---------- */
function siddurSaved() {
  const l = SD.leaf;
  return {
    nusach: SD.nusach, path: SD.path,
    leaf: l && { path: l.path, title: l.title, label: l.label, base: l.base,
                 from: l.from, to: l.to, total: l.total, paragraphs: l.paragraphs, meta: l.meta },
  };
}
/* נקרא מ-main.js לפני setSourceTab. מצב ישן בלי siddur — פשוט אין בחירה */
function siddurRestore(saved) {
  if (!saved || typeof saved !== "object") return;
  SD.nusach = typeof saved.nusach === "string" ? saved.nusach : "";
  SD.path = typeof saved.path === "string" && saved.path ? saved.path : SD.nusach;
  const l = saved.leaf;
  if (l && typeof l.path === "string" && l.path) {
    SD.leaf = {
      path: l.path, title: l.title || "", label: l.label || "", base: l.base || null,
      from: +l.from || null, to: +l.to || null, total: +l.total || 0,
      paragraphs: Array.isArray(l.paragraphs) ? l.paragraphs : [], meta: l.meta || "",
    };
  }
}

/* ---------- גישה ל-API ---------- */
class SiddurError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data || {};
  }
}
const SIDDUR_STATUS = {
  400: "הבקשה לא תקינה", 404: "הקטע לא נמצא בסידור", 413: "הקטע ארוך מדי לסנכרון אחד",
  422: "הקטע אינו מנוקד", 500: "תקלה בשרת", 502: "תקלה בקבלת הטקסט מ-Sefaria",
  504: "Sefaria לא ענתה בזמן",
};
function siddurErrorText(status, data) {
  // ההודעות של ה-API בעברית; "from/to" הם שמות פרמטרים — לא למשתמש
  let msg = String(data.error || "").replace(/\s*\(from\/to\)/g, "").replace(/\s*— from\/to/g, "");
  if (!msg) msg = `${SIDDUR_STATUS[status] || "שגיאה"} (${status})`;
  const tip = status === 413 || (status === 400 && data.paragraphs)
    ? "סמנו טווח פסקאות קצר יותר ברשימה ולחצו שוב על \"טען את הקטע\"."
    : status === 422 ? "אפשר ללחוץ על \"העתק לטקסט חופשי\" ולסנכרן משם."
    : status >= 500 ? "נסו שוב בעוד רגע." : "";
  return tip ? msg + "\n" + tip : msg;
}
async function siddurApi(params) {
  let res;
  try {
    res = await fetch("/api/siddur?" + new URLSearchParams(params).toString());
  } catch (e) {
    throw new SiddurError("אין חיבור לשרת — בדקו את החיבור ונסו שוב", 0);
  }
  let data = {};
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) throw new SiddurError(siddurErrorText(res.status, data || {}), res.status, data);
  return data;
}
function siddurMsg(html) { $("loadMsg").innerHTML = html; }
function siddurError(prefix, e) {
  siddurMsg(`<p class="error">${escapeHtml(prefix + (e && e.message || String(e)))}</p>`);
}

/* ---------- הפעלה (בפתיחה הראשונה של הלשונית) ---------- */
async function siddurActivate() {
  renderSiddurPanels();
  if (SD.leaf) renderLeaf();
  if (SD.started) return;
  SD.started = true;
  try {
    const root = await siddurApi({});
    SD.nusachim = (root.children || []).map(c => ({ key: c.key, title: c.title }));
  } catch (e) {
    SD.started = false;   // ננסה שוב בפתיחה הבאה / בכפתור
    siddurMsg(`<p class="error">${escapeHtml("טעינת רשימת הנוסחים נכשלה: " + e.message)}</p>` +
      '<button type="button" class="small secondary" id="sdRetry">נסו שוב</button>');
    $("sdRetry").addEventListener("click", () => { siddurMsg(""); siddurActivate(); });
    return;
  }
  fillNusachSelect();
  if (!SD.nusach) return;
  loadPopular();
  if (!SD.leaf) browseTo(SD.path || SD.nusach);
}
function fillNusachSelect() {
  const sel = $("sdNusach");
  sel.innerHTML = "";
  const ph = document.createElement("option");
  ph.value = ""; ph.textContent = "בחרו נוסח…"; ph.disabled = true;
  sel.appendChild(ph);
  for (const n of SD.nusachim || []) {
    const o = document.createElement("option");
    o.value = n.key; o.textContent = n.title;
    sel.appendChild(o);
  }
  if (SD.nusach && !(SD.nusachim || []).some(n => n.key === SD.nusach)) {
    SD.nusach = ""; SD.path = ""; SD.leaf = null;   // נוסח שכבר לא קיים בקטלוג
  }
  sel.value = SD.nusach;
  renderSiddurPanels();
}
/* בזמן חיפוש — רק התוצאות (מתחת לתיבה); הנוסח, הקיצורים, העץ והקטע שנבחר
   מוסתרים ולא נמחקים, וחוזרים כשהחיפוש מתנקה */
function renderSiddurPanels() {
  const searching = searchActive();
  $("sdResults").hidden = !searching;
  $("sdMain").hidden = searching;
  $("sdBrowse").hidden = !SD.nusach || !!SD.leaf;
  $("sdLeaf").hidden = !SD.leaf;
  $("sdAllWrap").hidden = !SD.nusach;
  $("sdSearchClear").hidden = !$("sdSearch").value;
}
$("sdNusach").addEventListener("change", () => {
  SD.nusach = $("sdNusach").value;
  SD.path = SD.nusach;
  SD.leaf = null; SD.payload = null; SD.browseData = null;
  siddurMsg("");
  renderSiddurPanels();
  save();
  loadPopular();
  browseTo(SD.nusach);
});
/* תוצאת חיפוש מנוסח אחר ("חיפוש בכל הנוסחים") ⇐ עוברים לנוסח שלה */
function useNusach(key) {
  if (!key || key === SD.nusach) return;
  SD.nusach = key;
  $("sdNusach").value = key;
  SD.browseData = null;
  loadPopular();
}

/* ---------- קטעים נפוצים (data/siddur/popular.json דרך ה-API) ---------- */
async function loadPopular() {
  const nusach = SD.nusach;
  $("sdPopularWrap").hidden = true;
  if (!SD.popular[nusach]) {
    try { SD.popular[nusach] = await siddurApi({ popular: 1, nusach }); }
    catch (e) { return; }   // הקיצורים הם נוחות — העץ והחיפוש עובדים גם בלעדיהם
  }
  if (nusach !== SD.nusach) return;
  const pop = SD.popular[nusach];
  const items = (pop.items || []).filter(it => it.available);
  const box = $("sdPopular");
  box.innerHTML = "";
  items.forEach(it => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "sdPop";
    b.textContent = it.label;
    b.title = (it.breadcrumb || []).slice(1).join(" › ");
    b.addEventListener("click", () => selectLeaf({
      path: it.path, title: it.title, label: it.label, from: it.from, to: it.to }));
    box.appendChild(b);
  });
  $("sdPopularNote").hidden = false;
  $("sdPopularNote").textContent = (pop.draft ? "רשימה ראשונית — ממתינה לאישור. " : "") +
    "חסר קטע? חפשו אותו בתיבה למעלה או דפדפו בסידור למטה.";
  $("sdPopularWrap").hidden = !items.length;
}

/* ---------- ניווט בעץ ---------- */
async function browseTo(path) {
  SD.path = path;
  save();
  const id = ++SD.req;
  $("sdList").innerHTML = '<p class="hint sdPad">טוען…</p>';
  let data;
  try { data = await siddurApi({ path }); }
  catch (e) {
    if (id === SD.req) $("sdList").innerHTML = `<p class="error sdPad">${escapeHtml(e.message)}</p>`;
    return;
  }
  if (id !== SD.req) return;
  SD.browseData = data;
  renderBrowse();
}
function renderBrowse() {
  const data = SD.browseData;
  if (!data) return;
  const nav = $("sdCrumbs");
  nav.hidden = false;
  nav.innerHTML = "";
  (data.breadcrumb || []).forEach((c, i, all) => {
    if (i) {
      const sep = document.createElement("span");
      sep.className = "sep"; sep.textContent = "‹";
      nav.appendChild(sep);
    }
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = c.title;
    if (i === all.length - 1) { b.disabled = true; b.setAttribute("aria-current", "page"); }
    else b.addEventListener("click", () => browseTo(c.path));
    nav.appendChild(b);
  });
  const list = $("sdList");
  list.innerHTML = "";
  const items = data.children || [];
  if (!items.length) list.innerHTML = '<p class="hint sdPad">לא נמצאו קטעים.</p>';
  for (const it of items) {
    list.appendChild(sdRow(it, {
      sub: it.is_leaf ? (it.first_words || "") : `${it.count} פריטים`,
      onClick: () => {
        if (!it.is_leaf) { browseTo(it.path); return; }
        SD.path = it.path.split("/").slice(0, -1).join("/");
        selectLeaf({ path: it.path, title: it.title });
      },
    }));
  }
}
/* שורה ברשימה (עץ או חיפוש): תיקייה ⇐ נכנסים; קטע ⇐ נבחר; קטע לא זמין —
   באפור ולא לחיץ; קיצור — כוכב */
function sdRow(it, { sub, onClick, shortcut }) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "sdItem " + (shortcut ? "sc" : it.is_leaf ? "leaf" : "folder") + (it.available ? "" : " na");
  b.dataset.path = it.path;
  b.disabled = !it.available;
  const ic = document.createElement("span");
  ic.className = "ic"; ic.setAttribute("aria-hidden", "true");
  ic.textContent = shortcut ? "⭐" : it.is_leaf ? "📄" : "📁";
  const tt = document.createElement("span");
  tt.className = "tt";
  tt.textContent = shortcut ? it.label : (it.title || it.title_en || it.key);
  const small = document.createElement("small");
  small.className = it.is_leaf && !shortcut ? "bible" : "";
  small.textContent = it.available ? sub : "לא זמין ב-Sefaria במהדורה שנבחרה";
  if (small.textContent) tt.appendChild(small);
  const go = document.createElement("span");
  go.className = "go"; go.setAttribute("aria-hidden", "true"); go.textContent = "‹";
  b.append(ic, tt, go);
  b.addEventListener("click", onClick);
  return b;
}

/* ---------- חיפוש (‏debounce): קיצורים, ואחריהם קטעים מהסידור ----------
   ההתאמה כולה בשרת (src/siddur/catalog.py — ‏Catalog.find): ניקוד, אותיות
   סופיות, גרשיים, שם ה׳, שמות נרדפים (data/siddur/aliases.json) וכתיב מלא/חסר.
   ברירת המחדל — הנוסח שנבחר; "חיפוש בכל הנוסחים" — כולם, הנבחר קודם. */
let sdSearchTimer = null;
function searchActive() { return $("sdSearch").value.trim().length >= SD_SEARCH_MIN; }
function clearSearch() {
  clearTimeout(sdSearchTimer);
  SD.searchReq++;   // תוצאה של חיפוש קודם לא תגיע אחרי הניקוי
  $("sdSearch").value = "";
  $("sdResults").innerHTML = "";
  renderSiddurPanels();
}
$("sdSearch").addEventListener("input", () => {
  clearTimeout(sdSearchTimer);
  if (!searchActive()) {
    SD.searchReq++;
    $("sdResults").innerHTML = "";   // לא להציג תוצאות ישנות כשהחיפוש יתחדש
  } else {
    if (!$("sdResults").hasChildNodes()) $("sdResults").innerHTML = '<p class="hint sdPad">מחפש…</p>';
    sdSearchTimer = setTimeout(runSearch, SD_SEARCH_DELAY_MS);
  }
  renderSiddurPanels();
});
$("sdSearch").addEventListener("keydown", e => {
  if (e.key !== "Enter") return;
  e.preventDefault();
  clearTimeout(sdSearchTimer);
  if (searchActive()) { $("sdSearch").blur(); runSearch(); }   // בטלפון — המקלדת יורדת
});
$("sdSearchClear").addEventListener("click", () => { clearSearch(); $("sdSearch").focus(); });
$("sdAll").addEventListener("change", () => { if (searchActive()) runSearch(); });

async function runSearch() {
  const q = $("sdSearch").value.trim();
  const id = ++SD.searchReq;
  const box = $("sdResults");
  box.innerHTML = '<p class="hint sdPad">מחפש…</p>';
  const params = { q };
  if (SD.nusach) {
    params.nusach = SD.nusach;
    if ($("sdAll").checked) params.all = 1;
  }
  let data;
  try { data = await siddurApi(params); }
  catch (e) {
    if (id === SD.searchReq) box.innerHTML = `<p class="error sdPad">${escapeHtml(e.message)}</p>`;
    return;
  }
  if (id !== SD.searchReq) return;
  renderResults(data);
}
function nusachTitle(key) {
  return ((SD.nusachim || []).find(n => n.key === key) || {}).title || "";
}
function renderResults(data) {
  const box = $("sdResults");
  box.innerHTML = "";
  const shortcuts = data.shortcuts || [], results = data.results || [];
  const many = !!data.all;   // כמה נוסחים ⇐ שם הנוסח בכל שורה
  if (!shortcuts.length && !results.length) {
    const p = document.createElement("p");
    p.className = "hint sdPad";
    p.textContent = `לא נמצא «${data.q}». נסו שם אחר או את המילים הראשונות של הקטע` +
      (SD.nusach && !many ? ', או סמנו "חיפוש בכל הנוסחים".' : ".");
    box.appendChild(p);
    return;
  }
  const section = (title, rows) => {
    const h = document.createElement("div");
    h.className = "range-title sdResHead";
    h.textContent = title;
    const list = document.createElement("div");
    list.className = "sdList";
    rows.forEach(r => list.appendChild(r));
    box.append(h, list);
  };
  if (shortcuts.length) section("קיצורים", shortcuts.map(it => sdRow(it, {
    shortcut: true,
    sub: [many && nusachTitle(it.nusach), it.title !== it.label && `מתוך «${it.title}»`,
          (it.breadcrumb || []).slice(1, -1).join(" › ")].filter(Boolean).join(" · "),
    onClick: () => openFromSearch(it),
  })));
  if (results.length) section("בסידור", results.map(it => sdRow(it, {
    sub: [it.hint, (it.breadcrumb || []).slice(many ? 0 : 1, -1).join(" › ")]
      .filter(Boolean).join(" · "),
    onClick: () => openFromSearch(it),
  })));
  if (data.truncated) {
    const p = document.createElement("p");
    p.className = "hint sdPad";
    p.textContent = `מוצגות ${data.limit} התוצאות הראשונות — הוסיפו מילה כדי לדייק.`;
    box.appendChild(p);
  }
}
/* הקשה על תוצאה: החיפוש מתנקה, ועוברים לקיצור / לקטע / לתיקייה (ולנוסח שלו) */
function openFromSearch(it) {
  clearSearch();
  useNusach(it.nusach);
  if (!it.label && !it.is_leaf) {
    SD.leaf = null; SD.payload = null;
    siddurMsg("");
    renderSiddurPanels();
    browseTo(it.path);
    return;
  }
  SD.path = it.path.split("/").slice(0, -1).join("/");
  selectLeaf({ path: it.path, title: it.title, label: it.label, from: it.from, to: it.to });
}

/* ---------- קטע: טעינה, בחירת טווח ---------- */
function selectLeaf(sel) {
  SD.leaf = {
    path: sel.path, title: sel.title || "", label: sel.label || "",
    base: sel.from ? { from: +sel.from, to: +(sel.to || sel.from) } : null,
    from: sel.from ? +sel.from : null, to: sel.from ? +(sel.to || sel.from) : null,
    total: 0, paragraphs: [], meta: "",
  };
  SD.payload = null;
  siddurMsg("");
  renderSiddurPanels();
  renderLeaf();
  save();
  fetchLeafRange();
  $("sdLeaf").scrollIntoView({ block: "nearest" });
}
$("sdBack").addEventListener("click", () => {
  SD.leaf = null; SD.payload = null;
  siddurMsg("");
  renderSiddurPanels();
  save();
  if (SD.browseData && SD.browseData.path === SD.path) renderBrowse();
  else browseTo(SD.path || SD.nusach);
});

function leafRangeParams() {
  const l = SD.leaf, p = { path: l.path };
  if (l.from && l.to && !(l.from === 1 && l.to === l.total)) { p.from = l.from; p.to = l.to; }
  return p;
}
/* תשובה שמורה שמתאימה לקטע ולטווח הנוכחיים. withErrors — גם גוף שגיאה
   שיש בו יחידות (422 — לא מנוקד; 400 — רק הוראות), להעתקה לטקסט חופשי */
function currentPayload(withErrors) {
  const p = SD.payload, l = SD.leaf;
  if (!p || !l || p.path !== l.path) return null;
  if (p.error && !withErrors) return null;
  return p.range && p.range.from === l.from && p.range.to === l.to ? p : null;
}
async function fetchLeafRange() {
  const l = SD.leaf;
  if (!l) return null;
  const params = leafRangeParams();
  const id = ++SD.leafReq;
  $("sdLoadBtn").disabled = true; $("sdCopyBtn").disabled = true;
  $("sdLoadBtn").textContent = "טוען מ-Sefaria…";
  try {
    const data = await siddurApi(params);
    if (id !== SD.leafReq || l !== SD.leaf) return null;
    l.title = data.title || l.title;
    l.total = data.range.total;
    l.from = data.range.from; l.to = data.range.to;
    l.paragraphs = data.paragraphs || [];
    l.meta = leafMeta(data);
    SD.payload = data;
    renderLeaf(); save();
    return data;
  } catch (e) {
    if (id !== SD.leafReq || l !== SD.leaf) return null;
    const d = e.data || {};
    if (Array.isArray(d.paragraphs) && d.paragraphs.length) {
      l.paragraphs = d.paragraphs;
      l.total = d.paragraphs.length;
      if (!l.from || l.to > l.total) { l.from = 1; l.to = l.total; }
    }
    if (Array.isArray(d.units))   // 422/400 — הטקסט עצמו זמין להעתקה
      SD.payload = { error: e.status, path: l.path, units: d.units,
                     range: { from: l.from, to: l.to, total: l.total } };
    renderLeaf(); save();
    siddurError("טעינת הקטע נכשלה: ", e);
    return null;
  } finally {
    if (id === SD.leafReq) {
      $("sdLoadBtn").disabled = false; $("sdCopyBtn").disabled = false;
      $("sdLoadBtn").textContent = "טען את הקטע";
    }
  }
}
function leafMeta(data) {
  const crumbs = (data.breadcrumb || []).slice(0, -1).map(c => c.title).join(" › ");
  const ver = String(data.version || "").trim();
  // שמות המהדורה והרישיון באנגלית — מבודדים (FSI…PDI), שלא יתערבבו בעברית סביבם
  const iso = t => "\u2068" + t + "\u2069";
  return [crumbs, ver && `מהדורה: ${iso(ver)}`,
          data.license && data.license !== "unknown" && `רישיון: ${iso(data.license)}`]
    .filter(Boolean).join(" · ");
}
function renderLeaf() {
  const l = SD.leaf;
  if (!l) return;
  $("sdLeafTitle").textContent = l.label || l.title || "…";
  const fromTitle = l.label && l.title && l.label !== l.title ? `מתוך «${l.title}»` : "";
  $("sdLeafMeta").textContent = [fromTitle, l.meta].filter(Boolean).join(" · ") ||
    (l.total ? "" : "טוען את הקטע…");
  const many = l.total > 1 && l.paragraphs.length === l.total;
  $("sdRange").hidden = !many;
  if (!many) return;
  for (const id of ["sdFrom", "sdTo"]) {
    const sel = $(id);
    sel.innerHTML = "";
    l.paragraphs.forEach(p => {
      const o = document.createElement("option");
      o.value = p.n;
      o.textContent = `${p.n} · ${p.first_words || "—"}`;
      sel.appendChild(o);
    });
  }
  const box = $("sdParas");
  box.innerHTML = "";
  l.paragraphs.forEach(p => {
    const row = document.createElement("label");
    row.className = "sdPara" + (p.kind === "instruction" || p.kind === "empty" ? " instr" : "");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.dataset.n = p.n;
    const pn = document.createElement("span");
    pn.className = "pn"; pn.textContent = p.n;
    const pt = document.createElement("span");
    pt.className = "pt bible"; pt.textContent = (p.first_words || "—") + "…";
    row.append(cb, pn, pt);
    box.appendChild(row);
  });
  updateRangeUi();
}
function updateRangeUi() {
  const l = SD.leaf;
  $("sdFrom").value = String(l.from);
  $("sdTo").value = String(l.to);
  $("sdParas").querySelectorAll("input[data-n]").forEach(cb => {
    const n = +cb.dataset.n, on = n >= l.from && n <= l.to;
    cb.checked = on;
    cb.parentElement.classList.toggle("on", on);
  });
}
function setRange(from, to) {
  const l = SD.leaf;
  from = Math.max(1, Math.min(from, l.total));
  to = Math.max(1, Math.min(to, l.total));
  if (from > to) [from, to] = [to, from];
  l.from = from; l.to = to;
  updateRangeUi();
  save();
}
/* "מפסקה" אחרי "עד" (או להפך) — הקצה השני עובר איתה: פסקה אחת */
$("sdFrom").addEventListener("change", () => {
  const f = +$("sdFrom").value;
  setRange(f, Math.max(f, SD.leaf.to));
});
$("sdTo").addEventListener("change", () => {
  const t = +$("sdTo").value;
  setRange(Math.min(t, SD.leaf.from), t);
});
/* סימון פסקה מחוץ לטווח ⇐ מרחיב אליה; ביטול בקצה ⇐ מקצר; ביטול באמצע ⇐
   הטווח נגמר לפניה. הטווח תמיד רציף (‏from/to של ה-API) */
$("sdParas").addEventListener("change", e => {
  const cb = e.target.closest("input[data-n]");
  if (!cb) return;
  const n = +cb.dataset.n, l = SD.leaf;
  if (n < l.from) setRange(n, l.to);
  else if (n > l.to) setRange(l.from, n);
  else if (l.from === l.to) updateRangeUi();   // לפחות פסקה אחת
  else if (n === l.from) setRange(n + 1, l.to);
  else setRange(l.from, n - 1);
});

/* הכותרת של מה שנטען: הקיצור ("לכה דודי") כשהטווח שלו, שם הקטע כשהוא שלם,
   ואחרת שם הקטע + הטווח */
function siddurLabel() {
  const l = SD.leaf;
  if (!l) return "";
  const base = l.base || { from: 1, to: l.total };
  if (l.from === base.from && l.to === base.to) return l.label || l.title;
  if (l.from === 1 && l.to === l.total) return l.title;
  return `${l.title} (פסקאות ${l.from}–${l.to})`;
}

async function loadSiddurLeaf() {
  if (!SD.leaf) return;
  siddurMsg("");
  const data = currentPayload(false) || await fetchLeafRange();
  if (!data || data.error) return;
  // עותק — עריכת החלוקה מחליפה את S.data.segments, והתשובה השמורה נשארת נקייה
  const d = JSON.parse(JSON.stringify(data));
  d.source = "siddur";   // מכאן — מצב יישור, שליחה לענן ושם הקובץ
  d.label = siddurLabel();
  S.data = d;
  S.times = null; S.endTime = null; S.report = null;
  S.perf = null; S.timesOrder = null;   // מבנה הביצוע שייך לטקסט הקודם
  S.splits = null;
  S.baseSplits = d.segments.map(s => tokensOf(s.display).length);
  renderTextLoaded();
  save();
}
$("sdLoadBtn").addEventListener("click", loadSiddurLeaf);

/* ---------- "העתק לטקסט חופשי" ----------
   הטקסט הנאמר בלבד (בלי הוראות), יחידה בשורה — כדי לתקן את הנוסח של בית
   הכנסת ולסנכרן מלשונית הטקסט החופשי. קטע בלי ניקוד (422) — כל הטקסט. */
function copyUnitsToFreeText(units, title) {
  const spoken = units.filter(u => u.kind !== "instruction");
  const text = (spoken.length ? spoken : units).map(u => String(u.text).trim())
    .filter(Boolean).join("\n");
  const cur = $("freeText").value;
  if (cur.trim() && cur !== text &&
      !confirm("בתיבת הטקסט החופשי כבר יש טקסט. להחליף אותו בקטע מהסידור?")) return false;
  $("freeText").value = text;
  $("textTitle").value = title;
  setSourceTab("text");
  save();
  siddurMsg('<p class="okline">הקטע הועתק לטקסט חופשי ✓ — אפשר לתקן בו את הנוסח, ואז ללחוץ "טען את הטקסט".</p>');
  return true;
}
async function copySiddurToText() {
  const l = SD.leaf;
  if (!l) return;
  const title = siddurLabel();
  let units = null;
  // הקטע שכבר נטען (גם אחרי טעינה מחדש של הדף — בלי בקשה נוספת)
  if (dataSource() === "siddur" && S.data.path === l.path && S.data.range &&
      S.data.range.from === l.from && S.data.range.to === l.to) units = S.data.units;
  if (!units) {
    const p = currentPayload(true);
    if (p) units = p.units;
  }
  if (!units) {
    siddurMsg("");
    await fetchLeafRange();
    const p = currentPayload(true);
    if (p) units = p.units;
  }
  if (units && units.length) copyUnitsToFreeText(units, title);
}
$("sdCopyBtn").addEventListener("click", copySiddurToText);
