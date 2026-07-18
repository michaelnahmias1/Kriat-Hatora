/* Service Worker — הופך את האתר ל-PWA שאפשר להתקין.
   מעטפת האפליקציה נשמרת ב-cache; ‏/api/ והענן תמיד מהרשת.
   בנוסף: קליטת התראות Web Push מה-worker בענן — מוצגות גם כשהאפליקציה
   סגורה (באייפון: רק כשהיא מותקנת למסך הבית, iOS 16.4+). */
"use strict";

const CACHE = "kriat-hatora-v1";
const SHELL = [
  "/",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/icons/icon-maskable-512.png",
  "/icons/apple-touch-icon.png",
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // רק GET מאותו origin; ה-API (Sefaria דרך /api/segments) תמיד טרי מהרשת
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/api/")) return;

  // network-first: עדכונים מגיעים מיד, וה-cache משמש כשאין רשת
  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() =>
        caches.match(e.request).then(hit => hit ||
          (e.request.mode === "navigate" ? caches.match("/") : Promise.reject(new Error("offline")))))
  );
});

/* ---------- התראות מהעיבוד בענן ---------- */

self.addEventListener("push", e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) {}
  const ok = d.ok !== false;
  const ref = d.ref ? `${d.ref} — ` : "";
  e.waitUntil(self.registration.showNotification(
    ok ? "התזמון בענן הושלם ✓" : "העיבוד בענן נכשל",
    {
      body: ok ? ref + "היכנס לאפליקציה — הזמנים והדוח מחכים בשלב הבדיקה"
               : ref + "היכנס לאפליקציה לפרטים, ונסה שוב",
      icon: "/icons/icon-192.png",
      badge: "/icons/icon-192.png",
      dir: "rtl",
      lang: "he",
      tag: "kriat-hatora-cloud",   // התראה חדשה מחליפה ישנה, לא נערמות
    }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  // אם האפליקציה כבר פתוחה — מתמקדים בה (הסקירה שם כבר רצה); אחרת פותחים
  e.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
      for (const c of list) if ("focus" in c) return c.focus();
      return self.clients.openWindow("/");
    }));
});
