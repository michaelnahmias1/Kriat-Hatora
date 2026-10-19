"use strict";
/* עורך חלוקת הכתוביות (כולל הגרירה במגע) */

/* ---------- עורך חלוקת המילים ----------
   העריכה עובדת על רצף המילים ועל גדלי הקבוצות בלבד — סדר המילים לעולם
   לא משתנה, ולכן כל חלוקה שנוצרת כאן תקפה גם בעיבוד בענן. */
const E = { words: [], sizes: [], sel: null };  // sel — אינדקס גלובלי של המילה הנבחרת
const EDIT_RESET_LABEL = $("editReset").textContent;

function editGroupOf(wordIdx) {
  let acc = 0;
  for (let g = 0; g < E.sizes.length; g++) {
    if (wordIdx < acc + E.sizes[g]) return { g, start: acc };
    acc += E.sizes[g];
  }
  return { g: E.sizes.length - 1, start: acc - E.sizes[E.sizes.length - 1] };
}
function editRender() {
  const list = $("editList");
  list.innerHTML = "";
  let wi = 0, lastVerse = null;
  E.sizes.forEach((n, g) => {
    const row = document.createElement("div");
    row.className = "egroup";
    row.dataset.g = g;
    const verse = E.words[wi] ? E.words[wi].verse : "";
    let html = `<span class="gi">${g + 1}</span>`;
    if (verse !== lastVerse)
      html += isFreeText() ? `<span class="vch">${escapeHtml(unitLabel(verse))}</span>`
                           : `<span class="vch">פסוק ${heNumeral(verse)}</span>`;
    lastVerse = verse;
    if (g > 0) html += `<button class="mrg" data-mrg="${g}" title="איחוד עם הכתובית שמעל">🔗 איחוד</button>`;
    for (let k = 0; k < n; k++, wi++)
      html += `<span class="w${E.sel === wi ? " sel" : ""}" data-i="${wi}">${escapeHtml(E.words[wi].t)}</span>`;
    row.innerHTML = html;
    list.appendChild(row);
  });
  $("editCount").textContent = `${E.sizes.length} כתוביות · ${E.words.length} מילים`;
  const has = E.sel != null;
  const { g, start } = has ? editGroupOf(E.sel) : {};
  $("editUp").disabled = !has || g === 0;
  $("editDown").disabled = !has || g === E.sizes.length - 1;
  $("editSplit").disabled = !has || E.sel === start;
}
/* העברת המילה הנבחרת (עם כל מה שביניה לבין הגבול) לקבוצה השכנה */
function editMove(dir) {
  if (E.sel == null) return;
  const { g, start } = editGroupOf(E.sel);
  const end = start + E.sizes[g] - 1;
  if (dir < 0) {
    if (g === 0) return;
    const move = E.sel - start + 1;
    E.sizes[g - 1] += move; E.sizes[g] -= move;
  } else {
    if (g === E.sizes.length - 1) return;
    const move = end - E.sel + 1;
    E.sizes[g + 1] += move; E.sizes[g] -= move;
  }
  E.sizes = E.sizes.filter(n => n > 0);
  editRender();
}
function editSplitAt(wordIdx) {
  const { g, start } = editGroupOf(wordIdx);
  const off = wordIdx - start;
  if (off <= 0) return;
  E.sizes.splice(g, 1, off, E.sizes[g] - off);
  editRender();
}
function editMerge(g) {
  if (g < 1) return;
  E.sizes[g - 1] += E.sizes[g];
  E.sizes.splice(g, 1);
  editRender();
}
function openSplitEditor() {
  if (!S.data) return;
  if (S.cloudJob) {   // הסנכרון שרץ עכשיו יחזיר את החלוקה הישנה
    $("loadMsg").innerHTML =
      '<p class="hint">אי אפשר לשנות את החלוקה בזמן שהסנכרון רץ — בטלו אותו תחילה.</p>';
    return;
  }
  E.words = flatWords();
  E.sizes = currentSplits();
  E.sel = null;
  // בטקסט חופשי אין טעמים — האיפוס חוזר לחלוקה האוטומטית לפי הפיסוק
  $("editReset").textContent = isFreeText() ? "🔄 חזרה לחלוקה האוטומטית" : EDIT_RESET_LABEL;
  editRender();
  $("editOverlay").classList.add("open");
}
function closeSplitEditor() { $("editOverlay").classList.remove("open"); }
$("editSplitBtn").addEventListener("click", openSplitEditor);
$("editCancel").addEventListener("click", closeSplitEditor);
$("editUp").addEventListener("click", () => editMove(-1));
$("editDown").addEventListener("click", () => editMove(1));
$("editSplit").addEventListener("click", () => { if (E.sel != null) editSplitAt(E.sel); });
$("editReset").addEventListener("click", () => {
  E.sizes = (S.baseSplits || currentSplits()).slice();
  E.sel = null;
  editRender();
});
$("editSave").addEventListener("click", () => {
  const changed = JSON.stringify(E.sizes) !== JSON.stringify(currentSplits());
  closeSplitEditor();
  if (!changed) return;
  const hadTimes = !!S.times;
  applySplits(E.sizes);
  $("loadMsg").innerHTML =
    '<p class="okline">החלוקה עודכנה ✓' +
    (hadTimes ? " — הזמנים אופסו, יש להריץ את הסנכרון מחדש" : "") + "</p>";
});

/* בחירה בהקשה + גרירה במגע (Pointer Events — עובד גם באייפון) */
(function editorGestures() {
  const list = $("editList");
  let press = null, ghost = null, targetRow = null;

  const clearTarget = () => {
    if (targetRow) targetRow.classList.remove("target");
    targetRow = null;
  };
  const stopScroll = e => { if (ghost) e.preventDefault(); };
  document.addEventListener("touchmove", stopScroll, { passive: false });

  function beginDrag() {
    if (!press) return;
    press.dragging = true;
    press.el.classList.add("lift");
    ghost = document.createElement("div");
    ghost.id = "dragGhost";
    ghost.textContent = press.el.textContent;
    ghost.className = "bible";
    document.body.appendChild(ghost);
    moveGhost(press.x, press.y);
  }
  function moveGhost(x, y) {
    if (!ghost) return;
    ghost.style.left = x + "px";
    ghost.style.top = y + "px";
    ghost.style.display = "none";
    const under = document.elementFromPoint(x, y);
    ghost.style.display = "";
    const row = under && under.closest ? under.closest(".egroup") : null;
    clearTarget();
    if (row) {
      const g = +row.dataset.g;
      if (Math.abs(g - press.g) === 1) { targetRow = row; row.classList.add("target"); }
    }
  }
  function endDrag(apply) {
    if (ghost) { ghost.remove(); ghost = null; }
    if (press && press.el) press.el.classList.remove("lift");
    if (apply && targetRow) {
      E.sel = press.i;
      editMove(+targetRow.dataset.g - press.g);
    }
    clearTarget();
    press = null;
  }

  list.addEventListener("pointerdown", e => {
    const chip = e.target.closest(".w");
    if (!chip) return;
    const i = +chip.dataset.i;
    press = { i, g: editGroupOf(i).g, el: chip, x: e.clientX, y: e.clientY,
              x0: e.clientX, y0: e.clientY, dragging: false };
    press.timer = setTimeout(beginDrag, 220);
    // תפיסת המצביע — כך גם תזוזה/שחרור מחוץ לרשימה מגיעים לכאן
    try { list.setPointerCapture(e.pointerId); } catch (err) {}
  });
  list.addEventListener("pointermove", e => {
    if (!press) return;
    press.x = e.clientX; press.y = e.clientY;
    if (press.dragging) { moveGhost(e.clientX, e.clientY); return; }
    // תזוזה גדולה לפני שהלחיצה "נתפסה" = גלילה, לא גרירה
    if (Math.abs(e.clientX - press.x0) > 10 || Math.abs(e.clientY - press.y0) > 10) {
      clearTimeout(press.timer);
      press = null;
    }
  });
  const finish = e => {
    if (!press) return;
    clearTimeout(press.timer);
    if (press.dragging) { endDrag(e.type === "pointerup"); return; }
    const i = press.i;
    press = null;
    E.sel = E.sel === i ? null : i;   // הקשה = בחירה/ביטול בחירה
    editRender();
  };
  list.addEventListener("pointerup", finish);
  list.addEventListener("pointercancel", finish);

  list.addEventListener("click", e => {
    const m = e.target.closest("[data-mrg]");
    if (m) { E.sel = null; editMerge(+m.dataset.mrg); }
  });
})();
