"use strict";
/* PWA — רישום ה-Service Worker, חלונית ההגדרות וכפתור ההתקנה */

/* ---------- PWA: התקנה, הגדרות ו-Service Worker ---------- */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}

const settingsOverlay = $("settingsOverlay");
$("settingsBtn").addEventListener("click", () => {
  settingsOverlay.classList.add("open");
  refreshInstallUi();
});
$("settingsClose").addEventListener("click", () => settingsOverlay.classList.remove("open"));
settingsOverlay.addEventListener("click", e => {
  if (e.target === settingsOverlay) settingsOverlay.classList.remove("open");
});

let installPrompt = null;
window.addEventListener("beforeinstallprompt", e => {
  e.preventDefault();
  installPrompt = e;
  refreshInstallUi();
});
function isStandalone() {
  return matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
}
function refreshInstallUi() {
  const btn = $("installBtn"), msg = $("installMsg");
  if (isStandalone()) {
    btn.hidden = true;
    msg.textContent = "האפליקציה מותקנת ופועלת ממסך הבית ✓";
  } else if (installPrompt) {
    btn.hidden = false;
    msg.textContent = "ההתקנה מוסיפה את האפליקציה למסך הבית — נפתחת במסך מלא וזמינה גם בלי רשת.";
  } else if (/iphone|ipad|ipod/i.test(navigator.userAgent)) {
    btn.hidden = true;
    msg.textContent = "התקנה באייפון: בספארי לוחצים על כפתור השיתוף (הריבוע עם החץ) ואז \"הוספה למסך הבית\".";
  } else {
    btn.hidden = true;
    msg.textContent = "ההתקנה תוצע כאן כשהדפדפן יאשר אותה (דרושים Chrome/Edge, וביקור קצר באתר).";
  }
}
$("installBtn").addEventListener("click", async () => {
  if (!installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice.catch(() => {});
  installPrompt = null;
  refreshInstallUi();
});
$("clearDataBtn").addEventListener("click", () => {
  try { localStorage.removeItem(STORE_KEY); } catch (e) {}
  location.reload();
});
