"use strict";
/* שלב 6 — ייצוא SRT: בנייה, הורדה ושיתוף */

/* ---------- שלב 5: ייצוא SRT ---------- */
function buildSrt() {
  const segs = S.data.segments, n = segs.length, lines = [];
  for (let i = 0; i < n; i++) {
    const start = S.times[i];
    let end = i + 1 < n ? S.times[i + 1] : S.endTime + 0.25;
    end = Math.max(end, start + 0.3);
    lines.push(String(i + 1), `${fmtSrt(start)} --> ${fmtSrt(end)}`, segs[i].display, "");
  }
  return "\uFEFF" + lines.join("\n");  // BOM — כמו utf-8-sig בצינור ה-Colab
}
function srtName() {
  const q = readQuery();
  let name = `${q.book}_${q.chapter}`;
  if (q.verse_start) name += `_${q.verse_start}`;
  if (q.chapter_end && +q.chapter_end !== +q.chapter) name += `-${q.chapter_end}_${q.verse_end || 1}`;
  else if (q.verse_end) name += `-${q.verse_end}`;
  return name + ".srt";
}
function srtFile() {
  return new File([buildSrt()], srtName(), { type: "application/x-subrip" });
}
$("dlBtn").addEventListener("click", () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(srtFile());
  a.download = srtName();
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 30000);
  $("exportMsg").innerHTML = `<p class="okline">ירד הקובץ ${srtName()} ✓</p>`;
});
if (navigator.canShare && navigator.canShare({ files: [new File([""], "a.srt")] })) {
  $("shareBtn").hidden = false;
  $("shareBtn").addEventListener("click", () =>
    navigator.share({ files: [srtFile()], title: srtName() }).catch(() => {}));
}
