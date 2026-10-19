"use strict";
/* שלב 1 — מקור "טקסט חופשי" ולשוניות המקור (PLAN_TEFILA.md 4.1.6) */

/* ---------- מקור הטקסט ----------
   שני מושגים נפרדים במכוון:
   - S.source — הלשונית הפעילה (איזה טופס מוצג). נשמר ב-localStorage.
   - dataSource() — המקור של הטקסט שכבר נטען (S.data.source). ממנו נגזרים
     מצב היישור, מה נשלח לענן ושם הקובץ. מעבר לשונית לא מוחק טקסט שנטען
     ולא נוגע בעבודה שרצה בענן.
   מצב שמור ישן (לפני ההרחבה) אין בו source בכלל ⇒ תנ״ך, כמו תמיד. */
function dataSource() {
  return (S.data && S.data.source) || "tanakh";
}
function isFreeText() { return dataSource() === "text"; }
/* מצב היישור של הטקסט שנטען — חייב להתאים ל-mode בשרת (text ⇒ tefila),
   אחרת ספירת המילים הנשמעות בדפדפן ובענן תתפצל (ראה isAudible) */
function alignMode() { return dataSource() === "tanakh" ? "tanakh" : "tefila"; }

/* התווית של יחידה לפי verse (מ-1) — "שורה N" מה-API, לא "פסוק" */
function unitLabel(verse) {
  const u = S.data && S.data.units && S.data.units[verse - 1];
  return (u && u.label) || `שורה ${verse}`;
}

/* ---------- לשוניות ---------- */
function setSourceTab(src) {
  S.source = src === "text" ? "text" : "tanakh";
  document.querySelectorAll(".srcTabs [data-src]").forEach(b =>
    b.setAttribute("aria-selected", String(b.dataset.src === S.source)));
  $("srcTanakh").hidden = S.source !== "tanakh";
  $("srcText").hidden = S.source !== "text";
}
document.querySelectorAll(".srcTabs [data-src]").forEach(b =>
  b.addEventListener("click", () => {
    if (b.dataset.src === S.source) return;
    setSourceTab(b.dataset.src);
    $("loadMsg").innerHTML = "";
    save();
  }));

/* ---------- טקסט חופשי: טעינה ---------- */
function readFreeText() {
  return { text: $("freeText").value, title: $("textTitle").value.trim() };
}
async function loadFreeText() {
  const { text } = readFreeText();
  if (!text.trim()) {
    $("loadMsg").innerHTML = '<p class="error">הדביקו את הטקסט בתיבה</p>';
    return;
  }
  $("textLoadBtn").disabled = true;
  $("textLoadBtn").textContent = "חותך את הטקסט…";
  $("loadMsg").innerHTML = "";
  try {
    let res, data;
    try {
      res = await fetch("/api/text_segments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, mode: "tefila" }),
      });
    } catch (e) {
      throw new Error("אין חיבור לשרת — בדקו את החיבור ונסו שוב");
    }
    try { data = await res.json(); }
    catch (e) { data = {}; }
    if (!res.ok) throw new Error(data.error || ("שגיאה " + res.status));
    data.source = "text";   // מכאן — מצב יישור, שליחה לענן ושם הקובץ
    S.data = data;
    S.times = null; S.endTime = null; S.report = null;
    S.splits = null;
    S.baseSplits = data.segments.map(s => tokensOf(s.display).length);
    renderTextLoaded();
    save();
  } catch (e) {
    $("loadMsg").innerHTML = `<p class="error">הטעינה נכשלה: ${escapeHtml(e.message)}</p>`;
  } finally {
    $("textLoadBtn").disabled = false;
    $("textLoadBtn").textContent = "טען את הטקסט";
  }
}
$("textLoadBtn").addEventListener("click", loadFreeText);

/* הטקסט והכותרת נשמרים תוך כדי הקלדה — לא נעלמים כשהאפליקציה נסגרת */
let freeTextSaveTimer = null;
function saveSoon() {
  clearTimeout(freeTextSaveTimer);
  freeTextSaveTimer = setTimeout(save, 400);
}
$("freeText").addEventListener("input", saveSoon);
$("textTitle").addEventListener("input", saveSoon);

/* ---------- שם קובץ הכתוביות ---------- */
/* מהכותרת (בלי ניקוד וטעמים, בלי תווים שאסורים בשם קובץ); בלי כותרת —
   "טקסט_חופשי" */
function freeTextSrtName() {
  let name = readFreeText().title
    .replace(/[֑-ׇ]/g, "")
    .replace(/[\\/:*?"<>|\u0000-\u001F]/g, "")
    .replace(/\s+/g, "_")
    .replace(/^[._]+|[._]+$/g, "")
    .slice(0, 60);
  return (name || "טקסט_חופשי") + ".srt";
}
