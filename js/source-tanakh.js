"use strict";
/* שלב 1 — מקור התנ״ך: ספר/פרק/פסוק, מבנה הספר וטעינת הטקסט */

/* ---------- שלב 1: טעינת הטקסט ---------- */
function readQuery() {
  return {
    book: $("book").value,
    chapter: $("chapter").value,
    verse_start: $("verse_start").value,
    verse_end: $("verse_end").value,
    chapter_end: $("chapter_end").value,
  };
}
async function loadText() {
  const q = readQuery();
  if (!q.chapter) { $("loadMsg").innerHTML = '<p class="error">חסר מספר פרק</p>'; return; }
  $("loadBtn").disabled = true;
  $("loadBtn").textContent = "טוען מ-Sefaria…";
  $("loadMsg").innerHTML = "";
  try {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(q)) if (v) params.set(k, v);
    const res = await fetch("/api/segments?" + params.toString());
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || ("שגיאה " + res.status));
    S.data = data;
    S.times = null; S.endTime = null; S.report = null;
    S.splits = null;
    S.baseSplits = data.segments.map(s => tokensOf(s.display).length);
    renderTextLoaded();
    save();
  } catch (e) {
    $("loadMsg").innerHTML = `<p class="error">הטעינה נכשלה: ${e.message}</p>`;
  } finally {
    $("loadBtn").disabled = false;
    $("loadBtn").textContent = "טען את הטקסט";
  }
}

function renderTextLoaded() {
  const d = S.data;
  $("loadOk").textContent =
    `נטען: ${d.ref} · ${d.n_verses} פסוקים · ${d.segments.length} כתוביות · גרסה: ${d.version}`;
  $("editSplitBtn").hidden = false;
  const list = $("segPreview");
  list.innerHTML = "";
  let lastVerse = null;
  d.segments.forEach((seg, i) => {
    const row = document.createElement("div");
    row.className = "segrow";
    const chip = seg.verse !== lastVerse ? `<span class="vchip">פסוק ${seg.verse}</span>` : "";
    lastVerse = seg.verse;
    row.innerHTML = `<span class="idx">${i + 1}</span>${chip}<span class="txt">${seg.display}</span>`;
    list.appendChild(row);
  });
  $("segPreviewWrap").hidden = false;
  $("done1").hidden = false;
  setLocked("step2", false);
  refreshTimingSteps();
}

/* ---------- מבנה הספר: תפריטי פרק/פסוק באותיות ---------- */
let bookChapters = null;    // מספר הפסוקים בכל פרק בספר הנבחר (מ-Sefaria)
// גיבוי כשאין רשת: מספר הפרקים ידוע, טווח הפסוקים נדיב — הטעינה תאמת מול Sefaria
const FALLBACK_CHAPTERS = {
  "בראשית": 50, "שמות": 40, "ויקרא": 27, "במדבר": 36, "דברים": 34,
  "יהושע": 24, "שופטים": 21, "שמואל א": 31, "שמואל ב": 24,
  "מלכים א": 22, "מלכים ב": 25, "ישעיהו": 66, "ירמיהו": 52, "יחזקאל": 48,
  "הושע": 14, "יואל": 4, "עמוס": 9, "עובדיה": 1, "יונה": 4, "מיכה": 7,
  "נחום": 3, "חבקוק": 3, "צפניה": 3, "חגי": 2, "זכריה": 14, "מלאכי": 3,
  "תהלים": 150, "משלי": 31, "איוב": 42, "שיר השירים": 8, "רות": 4,
  "איכה": 5, "קהלת": 12, "אסתר": 10, "דניאל": 12, "עזרא": 10, "נחמיה": 13,
  "דברי הימים א": 29, "דברי הימים ב": 36,
};

function fillSelect(sel, count, prefer) {
  const want = prefer != null && prefer !== "" ? +prefer : +sel.value;
  sel.innerHTML = "";
  for (let i = 1; i <= count; i++) {
    const o = document.createElement("option");
    o.value = i;
    o.textContent = heNumeral(i);
    sel.appendChild(o);
  }
  sel.value = String(want >= 1 && want <= count ? want : 1);
}
function versesInChapter(ch) {
  if (!bookChapters) return 1;
  return bookChapters[Math.max(1, +ch) - 1] || 1;
}
function populateVerseStart(prefer) { fillSelect($("verse_start"), versesInChapter($("chapter").value), prefer); }
function populateVerseEnd(prefer)   { fillSelect($("verse_end"),   versesInChapter($("chapter_end").value), prefer); }
function enforceOrder() {
  // "עד" לא יכול להקדים את "מ"
  if (bookChapters && +$("chapter_end").value < +$("chapter").value) {
    fillSelect($("chapter_end"), bookChapters.length, $("chapter").value);
    populateVerseEnd($("verse_start").value);
  }
  if (+$("chapter_end").value === +$("chapter").value &&
      +$("verse_end").value < +$("verse_start").value) {
    $("verse_end").value = $("verse_start").value;
  }
}
async function loadStructure(book, prefer) {
  try {
    const res = await fetch("/api/structure?book=" + encodeURIComponent(book));
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || ("שגיאה " + res.status));
    bookChapters = data.chapters;
  } catch (e) {
    bookChapters = Array(FALLBACK_CHAPTERS[book] || 50).fill(90);
  }
  const p = prefer || {};
  fillSelect($("chapter"),     bookChapters.length, p.chapter);
  fillSelect($("chapter_end"), bookChapters.length, p.chapter_end != null && p.chapter_end !== "" ? p.chapter_end : p.chapter);
  populateVerseStart(p.verse_start);
  populateVerseEnd(p.verse_end != null && p.verse_end !== "" ? p.verse_end : p.verse_start);
  enforceOrder();
  save();
}
$("book").addEventListener("change", () =>
  loadStructure($("book").value, { chapter: 1, verse_start: 1, chapter_end: 1, verse_end: 1 }));
$("chapter").addEventListener("change", () => { populateVerseStart(1); enforceOrder(); save(); });
$("chapter_end").addEventListener("change", () => { populateVerseEnd(1); enforceOrder(); save(); });
$("verse_start").addEventListener("change", () => { enforceOrder(); save(); });
$("verse_end").addEventListener("change", save);
