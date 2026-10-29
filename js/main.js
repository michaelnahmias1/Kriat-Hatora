"use strict";
/* אתחול — נטען אחרון: שחזור המצב מ-localStorage וחיבור כפתור הטעינה */

/* ---------- שחזור מ-localStorage ---------- */
(function restore() {
  let st = null;
  try { st = JSON.parse(localStorage.getItem(STORE_KEY)); } catch (e) {}
  // הטקסט החופשי והלשונית — לפני כל save(); מצב ישן בלי source ⇒ תנ״ך
  const ft = (st && st.freeText) || {};
  $("freeText").value = ft.text || "";
  $("textTitle").value = ft.title || "";
  siddurRestore(st && st.siddur);   // הבחירה בסידור — לפני הלשונית (שעשויה לפתוח אותה)
  setSourceTab((st && st.source) || "tanakh");
  const q = (st && st.query) || {};
  if (q.book) $("book").value = q.book;
  // טוען את מבנה הספר וממלא את התפריטים באותיות (עם הערכים השמורים אם יש)
  loadStructure($("book").value, {
    chapter: q.chapter, verse_start: q.verse_start,
    chapter_end: q.chapter_end, verse_end: q.verse_end,
  });
  if (!st) return;
  if (st.data) {
    S.data = st.data; S.times = st.times; S.endTime = st.endTime; S.audioName = st.audioName;
    S.report = st.report || null;
    S.splits = st.splits || null;
    S.baseSplits = st.baseSplits || null;
    renderTextLoaded();
    if (st.audioName) showFileChip(st.audioName, "בחר את הקובץ שוב");
  }
  // עבודת ענן שנשארה מהביקור הקודם — ממשיכים לעקוב / מושכים את התוצאה
  S.cloudJob = st.cloudJob || null;
  if (S.cloudJob) resumeCloudJob();
})();
$("loadBtn").addEventListener("click", loadText);
