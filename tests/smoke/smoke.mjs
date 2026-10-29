// בדיקת עשן לממשק (index.html) — Playwright + Chromium, בלי רשת חיצונית.
//
//   node tests/smoke/smoke.mjs            # כל התרחישים, דסקטופ + אייפון
//   SMOKE_ONLY=desktop node tests/smoke/smoke.mjs
//
// מגישה את הריפו בשרת סטטי קטן, ומחליפה ב-mock את כל מה שיוצא מהדפדפן:
//   /api/segments, /api/structure — ה-build_payload האמיתי מ-api/ עם Sefaria מזויף
//   /api/text_segments (POST)     — api/text_segments.py האמיתי
//                                    (tests/smoke/mock_api.py)
//   ה-worker בענן (*.modal.run)    — submit / status / cancel מזויפים
//   כל host חיצוני אחר (גופנים)    — תשובה ריקה; שום בקשה לא יוצאת לרשת
// נכתבה לפני פיצול index.html (שלב 0.5 ב-PLAN_TEFILA.md) ורצה זהה לפניו
// ואחריו — ההוכחה שאין שינוי התנהגות.

import { createRequire } from "node:module";
import { execFileSync, execSync } from "node:child_process";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const MOCK_API = path.join(ROOT, "tests", "smoke", "mock_api.py");

/* Playwright מותקן גלובלית (בלי package.json בריפו) */
function loadPlaywright() {
  const req = createRequire(import.meta.url);
  try { return req("playwright"); } catch (e) { /* נופלים לגלובלי */ }
  const globalRoot = execSync("npm root -g").toString().trim();
  return req(path.join(globalRoot, "playwright"));
}
const { chromium, devices } = loadPlaywright();

/* ---------- שרת סטטי ---------- */
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json", ".webmanifest": "application/manifest+json",
  ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon",
};
function startServer() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
    if (p === "/") p = "/index.html";
    const file = path.normalize(path.join(ROOT, p));
    if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404, { "Content-Type": "text/plain" }); res.end("not found"); return;
    }
    res.writeHead(200, {
      "Content-Type": TYPES[path.extname(file)] || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(r => server.listen(0, "127.0.0.1", () => r(server)));
}

/* ---------- mock ל-/api ---------- */
const apiCache = new Map();
function mockApi(kind, params) {
  const key = kind + JSON.stringify(params);
  if (!apiCache.has(key)) {
    const out = execFileSync("python3", [MOCK_API, kind, JSON.stringify(params)], { cwd: ROOT });
    apiCache.set(key, JSON.parse(out.toString("utf-8")));
  }
  return apiCache.get(key);
}

/* ---------- עזרים ---------- */
const results = [];
/* SMOKE_DUMP=<תיקייה>: אחרי כל שלב נשמר ה-DOM (בלי תגי script) וה-localStorage
   של הדף הפעיל — להשוואת diff בין שתי גרסאות של הממשק */
const DUMP_DIR = process.env.SMOKE_DUMP || "";
let dumpPage = null;
async function dumpState(name) {
  if (!DUMP_DIR || !dumpPage || dumpPage.isClosed()) return;
  const snap = await dumpPage.evaluate(() => {
    const body = document.body.cloneNode(true);
    body.querySelectorAll("script").forEach(s => s.remove());
    return body.outerHTML + "\n----- localStorage -----\n" + (localStorage.getItem("kriat-hatora-v1") || "");
  }).catch(e => "dump failed: " + e.message);
  fs.mkdirSync(DUMP_DIR, { recursive: true });
  fs.writeFileSync(path.join(DUMP_DIR, String(results.length).padStart(2, "0") + ".html"), name + "\n" + snap);
}
async function step(name, fn) {
  const t0 = Date.now();
  try {
    await fn();
    results.push({ name, ok: true });
    await dumpState(name);
    console.log(`  ✓ ${name} (${Date.now() - t0}ms)`);
  } catch (e) {
    results.push({ name, ok: false, e });
    console.log(`  ✗ ${name}\n    ${String(e && e.stack || e).split("\n").map(s => s.trim()).filter(Boolean).slice(0, 40).join(" ")}`);
  }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(fn, what, timeout = 10000) {
  const t0 = Date.now();
  let last;
  while (Date.now() - t0 < timeout) {
    try { last = await fn(); if (last) return last; } catch (e) { last = e; }
    await sleep(50);
  }
  throw new Error(`timeout: ${what} (last=${last && last.message || JSON.stringify(last)})`);
}

/* WAV מונו 16kHz של שנייה אחת (שקט) */
function wavSilence(seconds = 1, rate = 16000) {
  const n = Math.round(seconds * rate);
  const b = Buffer.alloc(44 + n * 2);
  b.write("RIFF", 0); b.writeUInt32LE(36 + n * 2, 4); b.write("WAVE", 8);
  b.write("fmt ", 12); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(rate, 24); b.writeUInt32LE(rate * 2, 28); b.writeUInt16LE(2, 32);
  b.writeUInt16LE(16, 34); b.write("data", 36); b.writeUInt32LE(n * 2, 40);
  return b;
}
const fmtSrt = t => {
  const ms = Math.max(0, Math.round(t * 1000));
  const p = (n, w) => String(n).padStart(w, "0");
  return `${p(Math.floor(ms / 3600000), 2)}:${p(Math.floor(ms % 3600000 / 60000), 2)}:` +
         `${p(Math.floor(ms % 60000 / 1000), 2)},${p(ms % 1000, 3)}`;
};
function srtFor(segments, times, endTime) {
  return segments.map((s, i) =>
    `${i + 1}\n${fmtSrt(times[i])} --> ${fmtSrt(i + 1 < times.length ? times[i + 1] : endTime)}\n${s.display}\n`)
    .join("\n");
}
/* פירוק גס של multipart — מספיק כדי לראות אילו שדות נשלחו */
function parseMultipart(buf) {
  const text = buf.toString("latin1");
  const fields = {}, files = {};
  const re = /name="([^"]+)"(?:; filename="([^"]*)")?[^\r]*\r\n(?:[^\r]+\r\n)*\r\n([\s\S]*?)\r\n--/g;
  let m;
  while ((m = re.exec(text))) {
    if (m[2] !== undefined) files[m[1]] = { filename: Buffer.from(m[2], "latin1").toString("utf-8"), size: m[3].length };
    else fields[m[1]] = Buffer.from(m[3], "latin1").toString("utf-8");
  }
  return { fields, files };
}

/* כל הפונקציות והקבועים ברמה העליונה של הסקריפט — הפיצול חייב לשמור את כולם */
const GLOBAL_FUNCTIONS = `heNumeral fmtClock fmtSrt setLocked escapeHtml save readQuery loadText tokensOf
  isAudible flatWords segmentsFromSplits currentSplits applySplits renderTextLoaded fillSelect
  versesInChapter populateVerseStart populateVerseEnd enforceOrder loadStructure fmtSize showFileChip
  probeDuration refreshTimingSteps encodeWav16 decodeAudio downsampleTo16k extractAudioForUpload
  parseReport renderReport applySrtTimes setStayNotice cloudBusy estimateCloudSeconds startCloudTimer
  stopCloudTimer setProcLabel cloudSleep holdWakeLock releaseWakeLock b64urlToBytes
  ensurePushSubscription uploadToCloud announceCloudProcessing pollCloudJob trackCloudJob
  resumeCloudJob runCloudTiming editGroupOf editRender editMove editSplitAt editMerge openSplitEditor
  closeSplitEditor nudge renderTimeList buildSrt srtName srtFile isStandalone refreshInstallUi
  dataSource isFreeText isUnitsSource alignMode unitLabel sourceTitle setSourceTab titleSrtName
  siddurSaved siddurRestore siddurActivate selectLeaf loadSiddurLeaf copySiddurToText`.split(/\s+/);
const GLOBAL_BINDINGS = `$ STORE_KEY AI_ENDPOINT AI_TOKEN VAPID_PUBLIC_KEY S HE_LETTER_RE NIQQUD_RE MAQAF
  bookChapters FALLBACK_CHAPTERS player audioReady audioFileObj audioDurationSec lastObjectUrl
  MAX_UPLOAD_MB MAX_DECODE_MB CLOUD_POLL_MS CLOUD_JOB_LIMIT_MS MAX_UNITS_BYTES cloudAbort cloudTimerInt
  CLOUD_BTN_LABEL wakeLock E settingsOverlay installPrompt`.split(/\s+/);

/* ---------- הקשר דפדפן עם כל ה-mocks ---------- */
async function newSession(browser, base, profile, { serviceWorkers = "block" } = {}) {
  const ctxOpts = profile === "mobile"
    ? (({ defaultBrowserType, ...d }) => d)(devices["iPhone 13"])
    : { viewport: { width: 1280, height: 860 } };
  const context = await browser.newContext({ ...ctxOpts, locale: "he-IL", serviceWorkers });
  const cloud = { submits: [], statusCalls: [], cancels: [], statusQueue: [], external: [], api: [], override: null };
  const origin = new URL(base).origin;
  const cors = { "Access-Control-Allow-Origin": "*" };
  await context.route("**/*", async route => {
    const req = route.request();
    const url = new URL(req.url());
    if (url.origin === origin) {
      if (url.pathname.startsWith("/api/")) {
        const kind = url.pathname.slice(5);
        // ‏POST (‏/api/text_segments) — גוף ה-JSON הוא הפרמטרים
        const params = req.method() === "POST"
          ? JSON.parse(req.postData() || "{}") : Object.fromEntries(url.searchParams);
        cloud.api.push({ kind, params });
        // תשובה סינתטית לבדיקה מסוימת (למשל 413/504 של הסידור) — אחרת ה-API האמיתי
        const { status, body } = (cloud.override && cloud.override(kind, params)) || mockApi(kind, params);
        return route.fulfill({ status, contentType: "application/json; charset=utf-8", body: JSON.stringify(body) });
      }
      return route.continue();
    }
    if (url.hostname.endsWith(".modal.run")) {
      if (req.method() === "OPTIONS") return route.fulfill({ status: 204, headers: { ...cors, "Access-Control-Allow-Headers": "*" } });
      if (url.pathname === "/submit") {
        cloud.submits.push(parseMultipart(req.postDataBuffer() || Buffer.alloc(0)));
        return route.fulfill({ status: 200, headers: cors, contentType: "application/json", body: JSON.stringify({ call_id: "fc-test-1" }) });
      }
      if (url.pathname === "/status") {
        cloud.statusCalls.push(url.searchParams.get("call_id"));
        const next = cloud.statusQueue.length > 1 ? cloud.statusQueue.shift() : cloud.statusQueue[0];
        const r = typeof next === "function" ? next() : next;
        if (!r) return route.fulfill({ status: 202, headers: cors, contentType: "application/json", body: '{"status":"running"}' });
        return route.fulfill({ status: r.status || 200, headers: cors, contentType: "application/json", body: JSON.stringify(r.body) });
      }
      if (url.pathname === "/cancel") {
        cloud.cancels.push(parseMultipart(req.postDataBuffer() || Buffer.alloc(0)));
        return route.fulfill({ status: 200, headers: cors, contentType: "application/json", body: '{"ok":true}' });
      }
      return route.fulfill({ status: 404, headers: cors, body: "" });
    }
    // כל host חיצוני אחר (Google Fonts וכד') — לא יוצאים לרשת
    cloud.external.push(url.host);
    const ct = url.host === "fonts.googleapis.com" ? "text/css" : "application/octet-stream";
    return route.fulfill({ status: 200, contentType: ct, body: "" });
  });
  const page = await context.newPage();
  const errors = [];
  page.on("console", m => { if (m.type() === "error") errors.push("console: " + m.text()); });
  page.on("pageerror", e => errors.push("pageerror: " + e.message));
  dumpPage = page;
  return { context, page, cloud, errors };
}

async function gotoReady(page, base) {
  await page.goto(base + "/");
  // השחזור טוען את מבנה הספר ברקע — מחכים שתפריט הפרקים יתמלא
  await page.waitForFunction(() => document.getElementById("chapter").options.length > 0);
}
const txt = (page, sel) => page.locator(sel).first().innerText();
const isHidden = (page, id) => page.evaluate(id => document.getElementById(id).hidden, id);
const isLocked = (page, id) => page.evaluate(id => document.getElementById(id).classList.contains("locked"), id);
const val = (page, id) => page.evaluate(id => document.getElementById(id).value, id);
const lsState = page => page.evaluate(() => JSON.parse(localStorage.getItem("kriat-hatora-v1")));
const assertNoErrors = errors => assert.deepEqual(errors, [], "console errors:\n" + errors.join("\n"));

/* =================== התרחישים =================== */

async function flowMain(browser, base, profile) {
  const { context, page, cloud, errors } = await newSession(browser, base, profile);
  const seg = mockApi("segments", { book: "שמות", chapter: "2", verse_start: "3", verse_end: "5", chapter_end: "2" }).body;

  await step(`[${profile}] טעינה: תפריטים, שלבים נעולים, כל הגלובליים קיימים`, async () => {
    await gotoReady(page, base);
    assert.equal(await page.title(), "קריאת התורה — כתוביות מסונכרנות");
    const groups = await page.$$eval("#book optgroup", g => g.map(x => [x.label, x.querySelectorAll("option").length]));
    assert.deepEqual(groups, [["תורה", 5], ["נביאים", 21], ["כתובים", 13]]);
    assert.equal(await val(page, "book"), "בראשית");
    assert.equal(await page.$$eval("#chapter option", o => o.length), 50);
    assert.equal(await page.$$eval("#verse_start option", o => o.length), 31);
    assert.equal(await page.$eval("#chapter option[value='15']", o => o.textContent), "ט״ו");
    assert.equal(await page.$eval("#chapter option[value='1']", o => o.textContent), "א׳");
    assert.equal(await isHidden(page, "startCloud"), false, "כפתור הסנכרון גלוי כש-AI_ENDPOINT מוגדר");
    for (const id of ["step2", "step3", "stepReport", "step4", "step5"]) assert.ok(await isLocked(page, id), id + " locked");
    assert.equal(await isHidden(page, "segPreviewWrap"), true);
    assert.equal(await isHidden(page, "editSplitBtn"), true);
    const missingFns = await page.evaluate(names => names.filter(n => { try { return typeof eval(n) !== "function"; } catch (e) { return true; } }), GLOBAL_FUNCTIONS);
    assert.deepEqual(missingFns, [], "missing functions");
    const missingVars = await page.evaluate(names => names.filter(n => { try { eval(n); return false; } catch (e) { return true; } }), GLOBAL_BINDINGS);
    assert.deepEqual(missingVars, [], "missing bindings");
    assert.equal(await page.evaluate(() => CLOUD_BTN_LABEL), "✨ סנכרון אוטומטי של הכתוביות");
    assert.deepEqual(cloud.api, [{ kind: "structure", params: { book: "בראשית" } }]);
    // הסגנון נטען (צבע הרקע מ-:root) והעמוד לא גולל לרוחב בטלפון
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    assert.ok(["rgb(246, 244, 239)", "rgb(20, 24, 29)"].includes(bg), "body bg " + bg);
    assert.equal(await page.evaluate(() => getComputedStyle(document.getElementById("step2")).opacity), "0.45");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "no horizontal scroll");
  });

  await step(`[${profile}] בחירת ספר/פרק/טווח + סדר "מ"/"עד"`, async () => {
    await page.selectOption("#book", "שמות");
    await page.waitForFunction(() => document.getElementById("chapter").options.length === 40);
    assert.deepEqual(cloud.api.at(-1), { kind: "structure", params: { book: "שמות" } });
    await page.selectOption("#chapter", "2");
    assert.equal(await page.$$eval("#verse_start option", o => o.length), 25);
    assert.equal(await val(page, "chapter_end"), "2", "עד לא מקדים את מ");
    await page.selectOption("#verse_start", "3");
    assert.equal(await val(page, "verse_end"), "3");
    await page.selectOption("#verse_end", "5");
    const st = await lsState(page);
    assert.deepEqual(st.query, { book: "שמות", chapter: "2", verse_start: "3", verse_end: "5", chapter_end: "2" });
  });

  await step(`[${profile}] טעינת הטקסט מציגה את המקטעים`, async () => {
    await page.click("#loadBtn");
    await page.waitForFunction(() => !document.getElementById("segPreviewWrap").hidden);
    assert.deepEqual(cloud.api.at(-1), { kind: "segments", params: { book: "שמות", chapter: "2", verse_start: "3", verse_end: "5", chapter_end: "2" } });
    assert.equal(await page.$$eval("#segPreview .segrow", r => r.length), seg.segments.length);
    assert.equal(await txt(page, "#loadOk"),
      `נטען: Exodus 2:3-5 · 3 פסוקים · ${seg.segments.length} כתוביות · גרסה: Miqra according to the Masorah`);
    const rows = await page.$$eval("#segPreview .segrow", r => r.map(x => x.textContent));
    assert.equal(rows[0], "1פסוק 3" + seg.segments[0].display);
    assert.equal(rows[1], "2" + seg.segments[1].display);
    assert.equal(await isHidden(page, "done1"), false);
    assert.equal(await isHidden(page, "editSplitBtn"), false);
    assert.equal(await isLocked(page, "step2"), false);
    assert.equal(await isLocked(page, "step3"), true, "שלב 3 נעול בלי קובץ");
    assert.equal(await page.$eval("#loadBtn", b => b.textContent), "טען את הטקסט");
    const st = await lsState(page);
    assert.equal(st.data.segments.length, seg.segments.length);
    assert.deepEqual(st.baseSplits, seg.segments.map(s => s.display.split(" ").filter(Boolean).length));
    assert.equal(st.splits, null);
  });

  const base0 = seg.segments.map(s => s.display.split(" ").filter(Boolean).length);
  let expectedSplits;
  await step(`[${profile}] עורך החלוקה: בחירה, פיצול, איחוד, העברה, גרירה, שמירה`, async () => {
    assert.deepEqual(base0, [3, 4, 4, 3, 3, 2, 4, 1]);
    await page.click("#editSplitBtn");
    await page.waitForFunction(() => document.getElementById("editOverlay").classList.contains("open"));
    const groups = () => page.$$eval("#editList .egroup", g => g.map(x => x.querySelectorAll(".w").length));
    assert.deepEqual(await groups(), base0);
    assert.equal(await txt(page, "#editCount"), `8 כתוביות · ${base0.reduce((a, b) => a + b)} מילים`);
    assert.equal(await page.$eval("#editList .egroup .vch", e => e.textContent), "פסוק ג׳");
    for (const id of ["editUp", "editDown", "editSplit"]) assert.ok(await page.$eval("#" + id, b => b.disabled));
    // הקשה על המילה השנייה ← פיצול
    await page.click('#editList .w[data-i="1"]');
    assert.ok(await page.$eval('#editList .w[data-i="1"]', w => w.classList.contains("sel")));
    assert.equal(await page.$eval("#editSplit", b => b.disabled), false);
    assert.equal(await page.$eval("#editUp", b => b.disabled), true, "קבוצה ראשונה — אין למעלה");
    await page.click("#editSplit");
    assert.deepEqual(await groups(), [1, 2, 4, 4, 3, 3, 2, 4, 1]);
    // איחוד חזרה
    await page.click('#editList [data-mrg="1"]');
    assert.deepEqual(await groups(), base0);
    // הקשה על המילה השלישית ← לכתובית שמתחת
    await page.click('#editList .w[data-i="2"]');
    await page.click("#editDown");
    assert.deepEqual(await groups(), [2, 5, 4, 3, 3, 2, 4, 1]);
    // המילה נשארת בחירה אחרי ההעברה; הקשה נוספת מבטלת את הבחירה
    assert.equal(await page.$$eval("#editList .w.sel", w => w.map(x => x.dataset.i).join()), "2");
    await page.click('#editList .w[data-i="2"]');
    assert.equal(await page.$$eval("#editList .w.sel", w => w.length), 0);
    assert.equal(await page.$eval("#editDown", b => b.disabled), true);
    // גרירה (לחיצה ארוכה) של המילה הראשונה בקבוצה 3 אל קבוצה 2
    const w7 = await page.locator('#editList .w[data-i="7"]').boundingBox();
    const g1 = await page.locator('#editList .egroup[data-g="1"] .gi').boundingBox();
    await page.mouse.move(w7.x + w7.width / 2, w7.y + w7.height / 2);
    await page.mouse.down();
    await sleep(350);
    await page.waitForSelector("#dragGhost");
    await page.mouse.move(g1.x + g1.width / 2, g1.y + g1.height / 2, { steps: 6 });
    assert.ok(await page.$eval('#editList .egroup[data-g="1"]', g => g.classList.contains("target")));
    await page.mouse.up();
    assert.equal(await page.$("#dragGhost"), null);
    expectedSplits = [2, 6, 3, 3, 3, 2, 4, 1];
    assert.deepEqual(await groups(), expectedSplits);
    await page.click("#editSave");
    assert.equal(await page.evaluate(() => document.getElementById("editOverlay").classList.contains("open")), false);
    assert.equal(await txt(page, "#loadMsg"), "החלוקה עודכנה ✓");
    assert.equal(await page.$$eval("#segPreview .segrow", r => r.length), 8);
    const st = await lsState(page);
    assert.deepEqual(st.splits, expectedSplits);
    assert.deepEqual(st.baseSplits, base0);
    // איפוס בעורך ואז ביטול — לא משנה כלום
    await page.click("#editSplitBtn");
    await page.click("#editReset");
    assert.deepEqual(await groups(), base0);
    await page.click("#editCancel");
    assert.deepEqual((await lsState(page)).splits, expectedSplits);
    assert.equal(await page.$$eval("#segPreview .segrow", r => r.length), 8);
  });

  await step(`[${profile}] בחירת קובץ הקלטה פותחת את שלב 3`, async () => {
    await page.setInputFiles("#audioFile", { name: "aliyah.wav", mimeType: "audio/wav", buffer: wavSilence(1) });
    await page.waitForFunction(() => !document.getElementById("done2").hidden);
    assert.equal(await isLocked(page, "step3"), false);
    assert.equal(await isHidden(page, "audioInfo"), false);
    await until(async () => (await txt(page, "#audioInfo .meta")).includes("0:01"), "משך ההקלטה בצ'יפ");
    assert.equal(await txt(page, "#audioInfo .nm"), "aliyah.wav");
    assert.equal(await isHidden(page, "player"), false);
    assert.equal((await lsState(page)).audioName, "aliyah.wav");
  });

  const times = [0.5, 1.0, 2.25, 3.5, 4.75, 6.0, 7.1, 8.4], endTime = 9.6;
  const report = [
    "דוח איכות הסנכרון", "=".repeat(40),
    "מקטעים: 8 | ביטחון חציוני: 0.81 | לבדיקה ידנית: 1", "",
    "מקטעים בביטחון נמוך (<0.5) — מומלץ לגרור ידנית:",
    "  [00:03] פסוק 4 | ביטחון 0.22 | וְחֹ֖שֶׁךְ עַל־פְּנֵ֣י תְה֑וֹם",
    "        סיבה: ציון יישור נמוך",
  ].join("\n");
  await step(`[${profile}] סנכרון בענן (mock): העלאה, מעקב, זמנים ודוח`, async () => {
    const segsNow = await page.evaluate(() => S.data.segments);
    cloud.statusQueue.push(null, { body: { srt: "﻿" + srtFor(segsNow, times, endTime), report } });
    await page.click("#startCloud");
    await until(() => cloud.submits.length === 1, "submit");
    const { fields, files } = cloud.submits[0];
    assert.equal(fields.token, await page.evaluate(() => AI_TOKEN));
    assert.equal(fields.book, "שמות");
    assert.equal(fields.chapter, "2");
    assert.equal(fields.verse_start, "3");
    assert.equal(fields.verse_end, "5");
    assert.equal(fields.chapter_end, "2");
    assert.equal(fields.splits, JSON.stringify(expectedSplits));
    assert.equal(fields.push_sub, undefined, "אין VAPID — אין push_sub");
    assert.equal(files.file.filename, "aliyah.wav");
    // אחרי ההעלאה: העבודה שמורה, האזהרה ירוקה
    await until(async () => (await lsState(page)).cloudJob, "cloudJob נשמר");
    const job = (await lsState(page)).cloudJob;
    assert.equal(job.id, "fc-test-1");
    assert.ok(job.t0 >= job.ts && job.est >= 60);
    assert.equal(await page.$eval("#stayNotice", e => e.className), "notice ok");
    assert.equal(await page.$eval("#startCloud", b => b.textContent), "⏳ מעבד בענן…");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    assert.ok(cloud.statusCalls.length >= 2 && cloud.statusCalls.every(c => c === "fc-test-1"));
    assert.equal(await page.$eval("#startCloud", b => b.textContent), "✨ סנכרון אוטומטי של הכתוביות");
    assert.equal(await isHidden(page, "stayNotice"), true);
    for (const id of ["stepReport", "step4", "step5"]) assert.equal(await isLocked(page, id), false, id);
    assert.equal(await isHidden(page, "done3"), false);
    assert.equal(await isHidden(page, "doneR"), false);
    assert.equal(await isHidden(page, "noAudioHint"), true);
    const tiles = await page.$$eval(".repTile .v", v => v.map(x => x.textContent));
    assert.deepEqual(tiles, ["8", "81%", "1"]);
    assert.equal(await page.$$eval(".repItem", r => r.length), 1);
    assert.equal(await page.$eval(".repItem .badge", b => b.textContent), "פסוק 4");
    assert.equal(await page.$eval(".repItem button.time", b => b.dataset.t), "3");
    assert.equal(await page.$$eval("#timeList .timerow", r => r.length), 8);
    assert.equal(await page.$eval("#timeList .timerow .t", t => t.textContent), "00:00,50");
    const st = await lsState(page);
    assert.equal(st.cloudJob, null);
    assert.deepEqual(st.times, times);
    assert.equal(st.endTime, endTime);
    assert.equal(st.report, report);
    // פס ההתקדמות מתמלא ונעלם (אחרי 600ms) — כך גם תמונות ה-DOM יציבות
    await page.waitForFunction(() => document.getElementById("cloudProgress").hidden);
    assert.equal(await page.$eval("#procBar", b => b.style.width), "0px");
  });

  await step(`[${profile}] כוונון ±0.2`, async () => {
    await page.click('#timeList button[data-act="plus"][data-i="1"]');
    assert.equal(await page.$$eval("#timeList .timerow .t", t => t[1].textContent), "00:01,20");
    await page.click('#timeList button[data-act="minus"][data-i="2"]');
    assert.equal(await page.$$eval("#timeList .timerow .t", t => t[2].textContent), "00:02,05");
    // תקרה: לא עובר את המקטע הבא פחות 0.05
    for (let k = 0; k < 10; k++) await page.click('#timeList button[data-act="plus"][data-i="7"]');
    assert.ok(Math.abs((await lsState(page)).times[7] - 9.55) < 1e-9);
    times[1] = 1.2; times[2] = 2.05; times[7] = 9.55;
  });

  await step(`[${profile}] ייצוא SRT: הורדה עם שם ותוכן נכונים`, async () => {
    // ה-<a> לא מחובר ל-DOM, ולכן Chromium בבדיקה מדווח שם "download" —
    // את שם הקובץ שהאפליקציה מבקשת קוראים ישירות מה-anchor
    await page.evaluate(() => {
      const orig = HTMLAnchorElement.prototype.click;
      HTMLAnchorElement.prototype.click = function () { window.__lastDownload = this.download; return orig.call(this); };
    });
    const [dl] = await Promise.all([page.waitForEvent("download"), page.click("#dlBtn")]);
    assert.equal(await page.evaluate(() => window.__lastDownload), "שמות_2_3-5.srt");
    assert.ok(["שמות_2_3-5.srt", "download"].includes(dl.suggestedFilename()), dl.suggestedFilename());
    const content = fs.readFileSync(await dl.path(), "utf-8");
    const segsNow = await page.evaluate(() => S.data.segments);
    const expected = "﻿" + segsNow.map((s, i) => {
      const st = times[i];
      let en = i + 1 < segsNow.length ? times[i + 1] : endTime + 0.25;
      en = Math.max(en, st + 0.3);
      return `${i + 1}\n${fmtSrt(st)} --> ${fmtSrt(en)}\n${s.display}\n`;
    }).join("\n");
    assert.equal(content, expected);
    assert.equal(await page.evaluate(() => buildSrt()), expected);
    assert.equal(await txt(page, "#exportMsg"), "ירד הקובץ שמות_2_3-5.srt ✓");
  });

  await step(`[${profile}] buildSrt מזמנים מוזרקים (כולל מינימום 0.3 שנ')`, async () => {
    const out = await page.evaluate(() => {
      const keep = [S.times, S.endTime];
      S.times = [0, 0.1, 0.2, 1, 2, 3, 4, 3661.5];
      S.endTime = 3662;
      const r = buildSrt();
      [S.times, S.endTime] = keep;
      return r;
    });
    const lines = out.split("\n");
    assert.equal(lines[0], "﻿1");
    assert.equal(lines[1], "00:00:00,000 --> 00:00:00,300");
    assert.equal(lines[5], "00:00:00,100 --> 00:00:00,400");
    assert.equal(lines[29], "01:01:01,500 --> 01:01:02,250");
    assert.equal(lines.length, 32);
    assert.equal(await page.evaluate(() => srtName()), "שמות_2_3-5.srt");
  });

  await step(`[${profile}] שחזור מ-localStorage אחרי טעינה מחדש`, async () => {
    await page.reload();
    await page.waitForFunction(() => document.getElementById("chapter").options.length === 40);
    assert.equal(await val(page, "book"), "שמות");
    assert.equal(await val(page, "chapter"), "2");
    assert.equal(await val(page, "verse_start"), "3");
    assert.equal(await val(page, "chapter_end"), "2");
    assert.equal(await val(page, "verse_end"), "5");
    assert.equal(await page.$$eval("#segPreview .segrow", r => r.length), 8);
    assert.equal(await isHidden(page, "editSplitBtn"), false);
    assert.equal(await isLocked(page, "step2"), false);
    assert.equal(await isLocked(page, "step3"), true, "אין קובץ ואין עבודה");
    for (const id of ["stepReport", "step4", "step5"]) assert.equal(await isLocked(page, id), false, id);
    assert.equal(await isHidden(page, "noAudioHint"), false);
    assert.equal(await txt(page, "#audioInfo .nm"), "aliyah.wav");
    assert.equal(await txt(page, "#audioInfo .meta"), "בחר את הקובץ שוב");
    assert.equal(await page.$$eval("#timeList .timerow .t", t => t[1].textContent), "00:01,20");
    assert.deepEqual(await page.$$eval(".repTile .v", v => v.map(x => x.textContent)), ["8", "81%", "1"]);
    assert.deepEqual(await page.evaluate(() => S.splits), expectedSplits);
    assert.equal(await page.evaluate(() => buildSrt()).then(s => s.length) > 0, true);
    assert.equal(await page.evaluate(() => S.cloudJob), null);
  });

  await step(`[${profile}] הגדרות: חלונית, הודעת התקנה, ניקוי נתונים`, async () => {
    await page.click("#settingsBtn");
    assert.ok(await page.evaluate(() => document.getElementById("settingsOverlay").classList.contains("open")));
    const msg = await txt(page, "#installMsg");
    if (profile === "mobile") assert.ok(msg.startsWith("התקנה באייפון"), msg);
    else assert.ok(msg.startsWith("ההתקנה תוצע כאן"), msg);
    assert.equal(await isHidden(page, "installBtn"), true);
    await page.click("#settingsClose");
    assert.equal(await page.evaluate(() => document.getElementById("settingsOverlay").classList.contains("open")), false);
    await page.click("#settingsBtn");
    await page.mouse.click(5, 5);  // הקשה על הרקע סוגרת
    assert.equal(await page.evaluate(() => document.getElementById("settingsOverlay").classList.contains("open")), false);
    await page.click("#settingsBtn");
    await Promise.all([page.waitForEvent("load"), page.click("#clearDataBtn")]);
    await page.waitForFunction(() => document.getElementById("chapter").options.length === 50);
    assert.equal(await val(page, "book"), "בראשית");
    assert.equal(await isHidden(page, "segPreviewWrap"), true);
    const st = await lsState(page);
    assert.equal(st.data, null);
    assert.deepEqual(st.query, { book: "בראשית", chapter: "1", verse_start: "1", verse_end: "1", chapter_end: "1" });
  });

  await step(`[${profile}] אין שגיאות קונסול ואין יציאה לרשת חיצונית`, async () => {
    assertNoErrors(errors);
    assert.ok(cloud.external.every(h => /^fonts\.(googleapis|gstatic)\.com$/.test(h)), cloud.external.join(","));
  });
  await context.close();
}

/* עבודה שרצה ברקע וחזרה לאפליקציה (אחרי סגירה מלאה — אין קובץ אודיו) */
async function flowResume(browser, base, profile) {
  const { context, page, cloud, errors } = await newSession(browser, base, profile);
  const q = { book: "שמות", chapter: "2", verse_start: "3", verse_end: "5", chapter_end: "2" };
  const data = mockApi("segments", q).body;
  const seed = (job) => page.evaluate(([q, data, job]) => localStorage.setItem("kriat-hatora-v1", JSON.stringify({
    query: q, data, times: null, endTime: null, audioName: "aliyah.m4a", report: null,
    cloudJob: job, splits: null, baseSplits: data.segments.map(s => s.display.split(" ").filter(Boolean).length),
  })), [q, data, job]);
  const times = data.segments.map((_, i) => i * 1.5);

  await step(`[${profile}] חזרה לעבודה ברקע: הטיימר ממשיך, התוצאה נמשכת`, async () => {
    await gotoReady(page, base);
    const now = await page.evaluate(() => Date.now());
    await seed({ id: "fc-bg-7", t0: now - 60000, ts: now - 95000, est: 300, push: false });
    cloud.statusQueue.push(null, { body: { srt: srtFor(data.segments, times, 20), report: "" } });
    await page.reload();
    await page.waitForFunction(() => !document.getElementById("cloudProgress").hidden);
    assert.equal(await isLocked(page, "step3"), false, "שלב 3 פתוח בזמן מעקב גם בלי קובץ");
    assert.ok((await txt(page, "#procTime")).startsWith("1:3"), await txt(page, "#procTime"));
    assert.ok((await txt(page, "#procTime")).endsWith("/ ~5:00"));
    assert.equal(await txt(page, "#procLabel"), "מסנכרן…");
    assert.equal(await page.$eval("#stayNotice", e => e.className), "notice ok");
    assert.equal((await lsState(page)).cloudJob.id, "fc-bg-7");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    assert.deepEqual([...new Set(cloud.statusCalls)], ["fc-bg-7"]);
    assert.equal(await txt(page, "#audioInfo .meta"), "בחר את הקובץ שוב כדי להאזין");
    assert.equal(await isLocked(page, "step3"), true);
    for (const id of ["stepReport", "step4", "step5"]) assert.equal(await isLocked(page, id), false, id);
    assert.equal(await page.$eval("#reportView", v => v.textContent.trim().startsWith("הדוח נוצר בסיום")), true);
    const st = await lsState(page);
    assert.equal(st.cloudJob, null);
    assert.deepEqual(st.times, times);
  });

  await step(`[${profile}] ביטול עבודה ששוחזרה: ‏/cancel נשלח והמעקב נעצר`, async () => {
    const now = await page.evaluate(() => Date.now());
    await seed({ id: "fc-bg-8", t0: now - 1000, ts: now - 2000, est: 120, push: false });
    cloud.statusQueue.length = 0; cloud.statusQueue.push(null);
    await page.reload();
    await page.waitForFunction(() => !document.getElementById("cloudProgress").hidden);
    await page.click("#cancelCloud");
    await until(() => cloud.cancels.length === 1, "cancel");
    assert.equal(cloud.cancels[0].fields.call_id, "fc-bg-8");
    assert.equal(cloud.cancels[0].fields.token, await page.evaluate(() => AI_TOKEN));
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent === "הסנכרון בוטל.");
    await page.waitForFunction(() => document.getElementById("cloudProgress").hidden);
    assert.equal((await lsState(page)).cloudJob, null);
    // בזמן עבודה פעילה אי אפשר לפתוח את עורך החלוקה
    await seed({ id: "fc-bg-9", t0: now, ts: now, est: 120, push: false });
    await page.reload();
    await page.waitForFunction(() => !document.getElementById("cloudProgress").hidden);
    await page.click("#editSplitBtn");
    assert.equal(await page.evaluate(() => document.getElementById("editOverlay").classList.contains("open")), false);
    assert.ok((await txt(page, "#loadMsg")).startsWith("אי אפשר לשנות את החלוקה"));
    await page.click("#cancelCloud");
    await until(() => cloud.cancels.length === 2, "cancel 2");
  });

  await step(`[${profile}] (resume) אין שגיאות קונסול`, async () => assertNoErrors(errors));
  await context.close();
}

/* תיקון האייפון (eb28576): קובץ שהדפדפן לא מצליח לקרוא ממנו מטא-דאטה */
async function flowUnreadableVideo(browser, base, profile) {
  const { context, page, cloud, errors } = await newSession(browser, base, profile);
  await step(`[${profile}] וידאו בלי מטא-דאטה: מתקבל מיד, ומועלה כמו שהוא`, async () => {
    await gotoReady(page, base);
    await page.click("#loadBtn");
    await page.waitForFunction(() => !document.getElementById("segPreviewWrap").hidden);
    assert.deepEqual(cloud.api.at(-1).params, { book: "בראשית", chapter: "1", verse_start: "1", verse_end: "1", chapter_end: "1" });
    await page.setInputFiles("#audioFile", { name: "clip.mov", mimeType: "video/quicktime", buffer: Buffer.from("not really a movie".repeat(64)) });
    // מיד, בלי לחכות ל-loadedmetadata
    assert.equal(await isHidden(page, "done2"), false);
    assert.equal(await isLocked(page, "step3"), false);
    assert.equal(await txt(page, "#audioInfo .nm"), "clip.mov");
    await until(async () => (await txt(page, "#audioInfo .meta")).endsWith("ללא נגן"), "ללא נגן", 12000);
    assert.equal(await isHidden(page, "player"), true);
    const n = await page.evaluate(() => S.data.segments.length);
    cloud.statusQueue.push({ body: { srt: srtFor(Array(n).fill({ display: "x" }), [...Array(n).keys()], n), report: "" } });
    await page.click("#startCloud");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    assert.equal(cloud.submits[0].files.file.filename, "clip.mov", "ההמרה נכשלה — הקובץ המקורי עולה");
    assert.equal(cloud.submits[0].fields.splits, undefined, "בלי עריכה — אין splits");
    assert.equal(await isHidden(page, "noAudioHint"), true);
  });
  await step(`[${profile}] (video) אין שגיאות קונסול`, async () => assertNoErrors(errors));
  await context.close();
}

/* ה-Service Worker מתקין את כל מעטפת האפליקציה, כולל כל קובץ JS/CSS מקומי */
async function flowServiceWorker(browser, base) {
  const { context, page, errors } = await newSession(browser, base, "desktop", { serviceWorkers: "allow" });
  await step("[sw] כל קובצי המעטפת נשמרים ב-cache, וכל JS/CSS מקומי נמצא ב-SHELL", async () => {
    const sw = fs.readFileSync(path.join(ROOT, "sw.js"), "utf-8");
    const shell = JSON.parse(sw.match(/const SHELL = (\[[\s\S]*?\]);/)[1].replace(/,\s*\]/, "]"));
    const cacheName = sw.match(/const CACHE = "([^"]+)"/)[1];
    const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf-8");
    const local = [...html.matchAll(/<(?:script[^>]*\ssrc|link[^>]*rel="stylesheet"[^>]*\shref)="([^"]+)"/g)]
      .map(m => m[1]).filter(u => !/^https?:/.test(u));
    for (const u of local) assert.ok(shell.includes(u.startsWith("/") ? u : "/" + u), `${u} חסר ב-SHELL`);
    await gotoReady(page, base);
    await page.evaluate(() => navigator.serviceWorker.ready);
    const cached = await until(() => page.evaluate(async name => {
      const keys = await caches.keys();
      if (!keys.includes(name)) return null;
      const c = await caches.open(name);
      return (await c.keys()).map(r => new URL(r.url).pathname);
    }, cacheName), "cache " + cacheName);
    for (const u of shell) assert.ok(cached.includes(u), `${u} לא נשמר ב-cache`);
    // כל קובצי ה-SHELL נגישים מהשרת
    for (const u of shell) {
      const st = await page.evaluate(u => fetch(u, { cache: "no-store" }).then(r => r.status), u);
      assert.equal(st, 200, u);
    }
  });
  await step("[sw] אין שגיאות קונסול", async () => assertNoErrors(errors));
  await context.close();
}

/* =================== טקסט חופשי (PLAN_TEFILA.md 4.1.6) =================== */
// שורה מנוקדת עם פיסוק; שורה בלי ניקוד בכלל (במצב תפילה — נקראת!); שורה עם
// שם ה׳ (יְיָ) ופיסוק שמוצמד ברווח קשיח (U+00A0); שורה ריקה ושורה בלי עברית
const NBSP = " ";
const FREE_TEXT = [
  "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ, עוֹד יְהַלְלוּךָ סֶּלָה.",
  "ברוך אתה יי אלהינו מלך העולם",
  `בָּרוּךְ אַתָּה יְיָ${NBSP}: אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם`,
  "",
  "— 3 —",
].join("\n");
const tabState = page => page.evaluate(() => {
  const st = {
    sel: [...document.querySelectorAll(".srcTabs [data-src]")].filter(b => b.getAttribute("aria-selected") === "true").map(b => b.dataset.src),
    tanakh: !document.getElementById("srcTanakh").hidden,
    text: !document.getElementById("srcText").hidden,
  };
  if (!document.getElementById("srcSiddur").hidden) st.siddur = true;  // רק כשהיא פתוחה
  return st;
});

async function flowFreeText(browser, base, profile) {
  const { context, page, cloud, errors } = await newSession(browser, base, profile);
  const api = mockApi("text_segments", { text: FREE_TEXT, mode: "tefila" });
  const ts = api.body;
  const toks = d => d.split(" ").filter(Boolean);
  const base0 = ts.segments.map(s => toks(s.display).length);

  await step(`[${profile}] לשוניות המקור: תנ״ך ⇄ טקסט חופשי`, async () => {
    await gotoReady(page, base);
    assert.deepEqual(await tabState(page), { sel: ["tanakh"], tanakh: true, text: false });
    assert.deepEqual(await page.$$eval(".srcTabs [data-src]:not([hidden])", b => b.map(x => x.textContent)), ["תנ״ך", "תפילה", "טקסט חופשי"]);
    await page.click('.srcTabs [data-src="text"]');
    assert.deepEqual(await tabState(page), { sel: ["text"], tanakh: false, text: true });
    assert.equal((await lsState(page)).source, "text");
    await page.click('.srcTabs [data-src="tanakh"]');
    assert.deepEqual(await tabState(page), { sel: ["tanakh"], tanakh: true, text: false });
    assert.equal((await lsState(page)).source, "tanakh");
    await page.click('.srcTabs [data-src="text"]');
    assert.deepEqual(cloud.api, [{ kind: "structure", params: { book: "בראשית" } }], "מעבר לשונית לא קורא ל-API");
    // בלי גלילה לרוחב בטלפון גם בלשונית הטקסט; גופן ≥16px — בלי זום באייפון
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "no horizontal scroll");
    assert.ok(await page.evaluate(() => parseFloat(getComputedStyle(document.getElementById("freeText")).fontSize) >= 16));
    assert.ok(await page.evaluate(() => parseFloat(getComputedStyle(document.getElementById("textTitle")).fontSize) >= 16));
  });

  await step(`[${profile}] טקסט חופשי: שגיאות בעברית (ריק, בלי עברית)`, async () => {
    await page.click("#textLoadBtn");
    assert.equal(await txt(page, "#loadMsg"), "הדביקו את הטקסט בתיבה");
    assert.equal(cloud.api.length, 1, "טקסט ריק לא נשלח");
    await page.fill("#freeText", "hello world 123");
    await page.click("#textLoadBtn");
    await until(async () => (await txt(page, "#loadMsg")).startsWith("הטעינה נכשלה"), "שגיאת API");
    assert.equal(await txt(page, "#loadMsg"), "הטעינה נכשלה: לא נמצאו אותיות עבריות בטקסט");
    // ה-400 המכוון מופיע בקונסול כ-"Failed to load resource" — צפוי, פעם אחת
    const i400 = errors.findIndex(e => e.includes("status of 400"));
    assert.ok(i400 >= 0, "ה-API החזיר 400");
    errors.splice(i400, 1);
    assert.deepEqual(cloud.api.at(-1), { kind: "text_segments", params: { text: "hello world 123", mode: "tefila" } });
    assert.equal(await isHidden(page, "segPreviewWrap"), true);
    assert.equal(await isLocked(page, "step2"), true);
    assert.equal(await page.$eval("#textLoadBtn", b => b.textContent), "טען את הטקסט");
  });

  await step(`[${profile}] טקסט חופשי: טעינה דרך api/text_segments.py, תוויות "שורה", הנחיה בלי טעמים`, async () => {
    assert.equal(api.status, 200);
    assert.equal(ts.n_units, 3);
    assert.deepEqual(base0, [3, 3, 3, 3, 3, 3]);
    await page.fill("#freeText", FREE_TEXT);
    await page.fill("#textTitle", "אשרי");
    await page.click("#textLoadBtn");
    await page.waitForFunction(() => !document.getElementById("segPreviewWrap").hidden);
    assert.deepEqual(cloud.api.at(-1), { kind: "text_segments", params: { text: FREE_TEXT, mode: "tefila" } });
    assert.equal(await txt(page, "#loadMsg"), "");
    assert.equal(await txt(page, "#loadOk"), "נטען: אשרי · 3 שורות · 6 כתוביות");
    const rows = await page.$$eval("#segPreview .segrow", r => r.map(x => x.textContent));
    assert.equal(rows.length, 6);
    assert.equal(rows[0], "1שורה 1" + ts.segments[0].display);
    assert.equal(rows[1], "2" + ts.segments[1].display);
    assert.equal(rows[2], "3שורה 2ברוך אתה יי");
    assert.equal(rows[4], `5שורה 3בָּרוּךְ אַתָּה יְיָ${NBSP}:`, "הרווח הקשיח נשמר בתצוגה");
    assert.equal(await page.$$eval("#segPreview .vchip", c => c.some(x => x.textContent.includes("פסוק"))), false);
    const hint = await txt(page, "#segHint");
    assert.ok(!hint.includes("טעמי המקרא") && hint.includes("סימני הפיסוק"), hint);
    assert.equal(await isHidden(page, "editSplitBtn"), false);
    assert.equal(await isLocked(page, "step2"), false);
    // סנכרון הספירה מול השרת: מצב tefila, מילה לא מנוקדת נשמעת, U+00A0 לא מפצל
    const js = await page.evaluate(() => ({
      mode: alignMode(), free: isFreeText(),
      audible: ["ברוך", "יי", "יְיָ", "—", "אבג־", "3"].map(isAudible),
      tokens: S.data.segments.map(s => tokensOf(s.display).length),
      again: segmentsFromSplits(flatWords(), S.baseSplits).map(s => s.display),
      lone: segmentsFromSplits(flatWords(), [3, 3, 1, 2, 3, 3, 3]).length,
    }));
    assert.equal(js.mode, "tefila");
    assert.equal(js.free, true);
    assert.deepEqual(js.audible, [true, true, true, false, true, false]);
    assert.deepEqual(js.tokens, base0);
    assert.deepEqual(js.again, ts.segments.map(s => s.display));
    assert.equal(js.lone, 7, "כתובית של מילה לא מנוקדת לבדה לא מתמזגת (כמו בשרת במצב tefila)");
    const st = await lsState(page);
    assert.equal(st.source, "text");
    assert.equal(st.data.source, "text");
    assert.deepEqual(st.data.units, ts.units);
    assert.deepEqual(st.freeText, { text: FREE_TEXT, title: "אשרי" });
    assert.deepEqual(st.baseSplits, base0);
    assert.equal(st.splits, null);
    assert.deepEqual(st.query, { book: "בראשית", chapter: "1", verse_start: "1", verse_end: "1", chapter_end: "1" }, "שדות התנ״ך לא נגעו");
  });

  const splits = [3, 3, 1, 2, 3, 3, 3];
  await step(`[${profile}] טקסט חופשי: עורך החלוקה (תוויות שורה, פיצול מילה לא מנוקדת)`, async () => {
    await page.click("#editSplitBtn");
    await page.waitForFunction(() => document.getElementById("editOverlay").classList.contains("open"));
    const groups = () => page.$$eval("#editList .egroup", g => g.map(x => x.querySelectorAll(".w").length));
    assert.deepEqual(await groups(), base0);
    assert.deepEqual(await page.$$eval("#editList .vch", v => v.map(x => x.textContent)), ["שורה 1", "שורה 2", "שורה 3"]);
    assert.equal(await txt(page, "#editReset"), "🔄 חזרה לחלוקה האוטומטית");
    assert.equal(await txt(page, "#editCount"), "6 כתוביות · 18 מילים");
    assert.equal(await page.$eval('#editList .w[data-i="12"]', w => w.textContent), "בָּרוּךְ");
    assert.equal(await page.$eval('#editList .w[data-i="14"]', w => w.textContent), `יְיָ${NBSP}:`);
    await page.click('#editList .w[data-i="7"]');
    await page.click("#editSplit");
    assert.deepEqual(await groups(), splits);
    await page.click("#editSave");
    assert.equal(await txt(page, "#loadMsg"), "החלוקה עודכנה ✓");
    assert.equal(await page.$$eval("#segPreview .segrow", r => r.length), 7, "‏\"ברוך\" לבד נשאר כתובית");
    assert.equal(await txt(page, "#loadOk"), "נטען: אשרי · 3 שורות · 7 כתוביות");
    assert.deepEqual(await page.$$eval("#segPreview .vchip", c => c.map(x => x.textContent)), ["שורה 1", "שורה 2", "שורה 3"]);
    const st = await lsState(page);
    assert.deepEqual(st.splits, splits);
    assert.deepEqual(st.data.units, ts.units, "היחידות נשמרות גם אחרי עריכה");
  });

  const report = [
    "דוח איכות הסנכרון", "=".repeat(40),
    "מקטעים: 7 | ביטחון חציוני: 0.74 | לבדיקה ידנית: 1", "",
    "מקטעים בביטחון נמוך (<0.5) — מומלץ לגרור ידנית:",
    "  [00:02] שורה 2 | ביטחון 0.31 | ברוך",
    "        סיבה: ציון יישור נמוך",
  ].join("\n");
  const times = [0.4, 1.3, 2.2, 2.9, 4.0, 5.1, 6.3], endTime = 7.5;
  await step(`[${profile}] טקסט חופשי: סנכרון בענן — source=text, units, title, splits`, async () => {
    await page.setInputFiles("#audioFile", { name: "ashrei.wav", mimeType: "audio/wav", buffer: wavSilence(1) });
    await page.waitForFunction(() => !document.getElementById("done2").hidden);
    assert.equal(await isLocked(page, "step3"), false);
    const segsNow = await page.evaluate(() => S.data.segments);
    cloud.statusQueue.push(null, { body: { srt: srtFor(segsNow, times, endTime), report } });
    await page.click("#startCloud");
    await until(() => cloud.submits.length === 1, "submit");
    const { fields, files } = cloud.submits[0];
    assert.deepEqual(Object.keys(fields).sort(), ["max_words", "source", "splits", "title", "token", "units"]);
    assert.equal(fields.source, "text");
    assert.equal(fields.units, JSON.stringify(ts.units), "בדיוק היחידות שה-API החזיר");
    assert.deepEqual(JSON.parse(fields.units), ts.units);
    assert.equal(fields.title, "אשרי");
    assert.equal(fields.max_words, "4");
    assert.equal(fields.token, await page.evaluate(() => AI_TOKEN));
    const sent = JSON.parse(fields.splits);
    assert.deepEqual(sent, splits);
    assert.equal(sent.reduce((a, b) => a + b), ts.segments.reduce((a, s) => a + toks(s.display).length, 0), "סכום ה-splits = מספר המילים");
    assert.equal(files.file.filename, "ashrei.wav");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    for (const id of ["stepReport", "step4", "step5"]) assert.equal(await isLocked(page, id), false, id);
    assert.deepEqual(await page.$$eval(".repTile .v", v => v.map(x => x.textContent)), ["7", "74%", "1"]);
    assert.equal(await page.$eval(".repItem .badge", b => b.textContent), "שורה 2");
    assert.equal(await page.$eval(".repItem button.time", b => b.dataset.t), "2");
    assert.equal(await page.$$eval("#timeList .timerow", r => r.length), 7);
    assert.equal(await page.$$eval("#timeList .timerow .txt", t => t[5].textContent), `בָּרוּךְ אַתָּה יְיָ${NBSP}:`);
    const st = await lsState(page);
    assert.deepEqual(st.times, times);
    assert.equal(st.cloudJob, null);
    await page.waitForFunction(() => document.getElementById("cloudProgress").hidden);
  });

  await step(`[${profile}] טקסט חופשי: יחידות מעבר למגבלת ה-worker — שגיאה בלי העלאה`, async () => {
    const nSubmits = cloud.submits.length;
    await page.evaluate(() => {
      window.__units = S.data.units;
      S.data.units = [{ text: "א".repeat(MAX_UNITS_BYTES / 2), kind: "line" }];
    });
    await page.click("#startCloud");
    assert.equal(await txt(page, "#timingMsg"), "הטקסט ארוך מדי לסנכרון (עד 200KB) — פצלו את הטקסט לכמה חלקים.");
    assert.equal(cloud.submits.length, nSubmits, "לא הועלה דבר");
    assert.equal(await page.$eval("#cloudProgress", e => e.hidden), true);
    await page.evaluate(() => { S.data.units = window.__units; delete window.__units; });
  });

  await step(`[${profile}] טקסט חופשי: כוונון וייצוא SRT בשם הכותרת`, async () => {
    await page.click('#timeList button[data-act="plus"][data-i="2"]');
    assert.equal(await page.$$eval("#timeList .timerow .t", t => t[2].textContent), "00:02,40");
    times[2] = 2.4;
    await page.evaluate(() => {
      const orig = HTMLAnchorElement.prototype.click;
      HTMLAnchorElement.prototype.click = function () { window.__lastDownload = this.download; return orig.call(this); };
    });
    const [dl] = await Promise.all([page.waitForEvent("download"), page.click("#dlBtn")]);
    assert.equal(await page.evaluate(() => window.__lastDownload), "אשרי.srt");
    const content = fs.readFileSync(await dl.path(), "utf-8");
    const segsNow = await page.evaluate(() => S.data.segments);
    const expected = "﻿" + segsNow.map((s, i) => {
      const a = times[i];
      let b = i + 1 < segsNow.length ? times[i + 1] : endTime + 0.25;
      b = Math.max(b, a + 0.3);
      return `${i + 1}\n${fmtSrt(a)} --> ${fmtSrt(b)}\n${s.display}\n`;
    }).join("\n");
    assert.equal(content, expected);
    assert.ok(content.includes(`יְיָ${NBSP}:`));
    assert.equal(await txt(page, "#exportMsg"), "ירד הקובץ אשרי.srt ✓");
    // שם הקובץ: ניקוד ותווים אסורים יורדים; בלי כותרת — שם ברירת מחדל
    await page.fill("#textTitle", "אַשְׁרֵי / שַׁחֲרִית: חול");
    assert.equal(await page.evaluate(() => srtName()), "אשרי_שחרית_חול.srt");
    await page.fill("#textTitle", "  ");
    assert.equal(await page.evaluate(() => srtName()), "טקסט_חופשי.srt");
    await page.fill("#textTitle", "אשרי");
    await until(async () => (await lsState(page)).freeText.title === "אשרי", "השמירה המושהית של הכותרת");
  });

  await step(`[${profile}] טקסט חופשי: חזרה לעבודה ברקע אחרי סגירה (שחזור + משיכת התוצאה)`, async () => {
    const now = await page.evaluate(() => Date.now());
    await page.evaluate(job => {
      const st = JSON.parse(localStorage.getItem("kriat-hatora-v1"));
      Object.assign(st, { times: null, endTime: null, report: null, cloudJob: job });
      localStorage.setItem("kriat-hatora-v1", JSON.stringify(st));
    }, { id: "fc-text-2", t0: now - 30000, ts: now - 50000, est: 200, push: false });
    const times2 = [0, 1, 2, 3, 4, 5, 6];
    const segsNow = await page.evaluate(() => S.data.segments);
    cloud.statusQueue.length = 0;
    cloud.statusQueue.push(null, { body: { srt: srtFor(segsNow, times2, 8), report: "" } });
    const nApi = cloud.api.length;
    await page.reload();
    await page.waitForFunction(() => !document.getElementById("cloudProgress").hidden);
    assert.deepEqual(await tabState(page), { sel: ["text"], tanakh: false, text: true });
    assert.equal(await val(page, "freeText"), FREE_TEXT);
    assert.equal(await val(page, "textTitle"), "אשרי");
    assert.equal(await page.$$eval("#segPreview .segrow", r => r.length), 7);
    assert.equal(await txt(page, "#loadOk"), "נטען: אשרי · 3 שורות · 7 כתוביות");
    assert.equal(await page.evaluate(() => alignMode()), "tefila");
    assert.equal(await isLocked(page, "step3"), false);
    assert.equal(await page.$eval("#stayNotice", e => e.className), "notice ok");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    assert.deepEqual([...new Set(cloud.statusCalls.slice(-2))], ["fc-text-2"]);
    assert.ok(cloud.api.slice(nApi).every(c => c.kind === "structure"), "השחזור לא טוען את הטקסט מחדש");
    const st = await lsState(page);
    assert.deepEqual(st.times, times2);
    assert.equal(st.cloudJob, null);
    assert.equal(st.source, "text");
    assert.equal(await page.evaluate(() => srtName()), "אשרי.srt");
  });

  await step(`[${profile}] מעבר לתנ״ך: הטקסט החופשי נשאר עד שנטען קטע חדש, ואז הכול תנ״ך`, async () => {
    await page.click('.srcTabs [data-src="tanakh"]');
    assert.deepEqual(await tabState(page), { sel: ["tanakh"], tanakh: true, text: false });
    // הטקסט שנטען לא נמחק במעבר לשונית — הזמנים והייצוא עדיין שלו
    assert.equal(await page.$$eval("#segPreview .segrow", r => r.length), 7);
    assert.equal(await page.evaluate(() => [isFreeText(), srtName()].join()), "true,אשרי.srt");
    await page.click("#loadBtn");
    await page.waitForFunction(() => document.getElementById("loadOk").textContent.startsWith("נטען: Genesis"));
    assert.equal(await page.evaluate(() => [isFreeText(), alignMode(), srtName()].join()), "false,tanakh,בראשית_1_1-1.srt");
    assert.equal(await page.$eval("#segPreview .vchip", c => c.textContent), "פסוק 1");
    assert.ok((await txt(page, "#segHint")).includes("טעמי המקרא"));
    assert.equal(await page.evaluate(() => isAudible("ברוך")), false, "בתנ״ך מילה לא מנוקדת היא כתיב");
    // והטופס של הטקסט החופשי שמור
    await page.click('.srcTabs [data-src="text"]');
    assert.equal(await val(page, "freeText"), FREE_TEXT);
    const st = await lsState(page);
    assert.equal(st.source, "text");
    assert.equal(st.data.source, undefined);
  });

  await step(`[${profile}] (טקסט חופשי) אין שגיאות קונסול ואין יציאה לרשת`, async () => {
    assertNoErrors(errors);
    assert.ok(cloud.external.every(h => /^fonts\.(googleapis|gstatic)\.com$/.test(h)), cloud.external.join(","));
  });
  await context.close();
}

/* מצב שמור בפורמט הישן (לפני source) עם עבודה פעילה בענן — חייב להמשיך כתנ״ך */
async function flowOldState(browser, base, profile) {
  const { context, page, cloud, errors } = await newSession(browser, base, profile);
  const q = { book: "שמות", chapter: "2", verse_start: "3", verse_end: "5", chapter_end: "2" };
  const data = mockApi("segments", q).body;
  await step(`[${profile}] שחזור מצב ישן בלי source: לשונית תנ״ך, העבודה בענן נמשכת`, async () => {
    await gotoReady(page, base);
    const now = await page.evaluate(() => Date.now());
    const old = {
      query: q, data, times: null, endTime: null, audioName: "old.m4a", report: null,
      cloudJob: { id: "fc-old-1", t0: now - 5000, ts: now - 9000, est: 240, push: false },
      splits: null, baseSplits: data.segments.map(s => s.display.split(" ").filter(Boolean).length),
    };
    await page.evaluate(st => localStorage.setItem("kriat-hatora-v1", JSON.stringify(st)), old);
    const times = data.segments.map((_, i) => i * 1.25);
    cloud.statusQueue.push(null, { body: { srt: srtFor(data.segments, times, 15), report: "" } });
    await page.reload();
    await page.waitForFunction(() => document.getElementById("chapter").options.length === 40);
    assert.deepEqual(await tabState(page), { sel: ["tanakh"], tanakh: true, text: false });
    assert.equal(await val(page, "freeText"), "");
    assert.equal(await val(page, "book"), "שמות");
    assert.equal(await page.evaluate(() => [S.source, dataSource(), alignMode(), isFreeText()].join()), "tanakh,tanakh,tanakh,false");
    assert.equal(await page.$eval("#segPreview .vchip", c => c.textContent), "פסוק 3");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    assert.deepEqual([...new Set(cloud.statusCalls)], ["fc-old-1"]);
    assert.equal(await page.evaluate(() => srtName()), "שמות_2_3-5.srt");
    const st = await lsState(page);
    assert.deepEqual(st.times, times);
    assert.equal(st.source, "tanakh");
    assert.deepEqual(st.query, q);
    assert.deepEqual(st.freeText, { text: "", title: "" });
  });
  await step(`[${profile}] (מצב ישן) אין שגיאות קונסול`, async () => assertNoErrors(errors));
  await context.close();
}

/* =================== ספריית התפילות (PLAN_TEFILA.md 4.2.4) =================== */
// ‏/api/siddur — api/siddur.py האמיתי עם תשובות Sefaria אמיתיות שהוקלטו
// (tests/fixtures/siddur; mock_api.py). צילומי מסך: SMOKE_SHOTS=<תיקייה>
const SHOTS_DIR = process.env.SMOKE_SHOTS || "";
async function shot(page, profile, name) {
  if (!SHOTS_DIR || profile !== "mobile") return;
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.evaluate(() => scrollTo(0, 0));   // הכותרת הדביקה — במקומה בצילום של כל הדף
  await page.screenshot({ path: path.join(SHOTS_DIR, name + ".png"), fullPage: true });
}
const SEFARD_KS = "sefard/shabbat/kabbalat-shabbat";
const SEFARD_ASHREI = "sefard/weekday/weekday-shacharit/ashrei";      // ‏versions ריק ⇐ 502
const EDOT_ASHREI = "edot-hamizrach/weekday/weekday-shacharit/ashrei"; // מוקלט (Shaliehsaboo)
const DAAT_ASHER = "ashkenaz/general/berachot/asher-yatzar-etchem-badin";  // לא מנוקד ⇐ 422
const UNAVAILABLE = "ashkenaz/weekday/shacharit/torah-reading/reading-from-sefer/prayers-for-welfare-of-the-people";
const siddurCalls = (cloud, pred = () => true) => cloud.api.filter(c => c.kind === "siddur" && pred(c.params));
const leafCalls = (cloud, p) => siddurCalls(cloud, q => q.path === p);
const visible = (page, id) => page.evaluate(id => !document.getElementById(id).hidden, id);
const checkedParas = page => page.$$eval("#sdParas input:checked", c => c.map(x => +x.dataset.n));
const range = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => a + i);

async function flowSiddur(browser, base, profile) {
  const { context, page, cloud, errors } = await newSession(browser, base, profile);
  const root = mockApi("siddur", {}).body;
  const pop = mockApi("siddur", { popular: "1", nusach: "sefard" }).body;
  const sefard = mockApi("siddur", { path: "sefard" }).body;
  const LD = mockApi("siddur", { path: SEFARD_KS, from: "17", to: "38" }).body;
  const LD37 = mockApi("siddur", { path: SEFARD_KS, from: "17", to: "37" }).body;
  const toks = d => d.split(" ").filter(Boolean);
  const instrCount = d => d.units.filter(u => u.kind === "instruction").length;

  await step(`[${profile}] תפילה: הלשונית נפתחת, הנוסחים מה-API (רק אחרי פתיחה)`, async () => {
    await gotoReady(page, base);
    assert.equal(siddurCalls(cloud).length, 0, "בלי בקשות לסידור לפני פתיחת הלשונית");
    await page.click('.srcTabs [data-src="siddur"]');
    assert.deepEqual(await tabState(page), { sel: ["siddur"], tanakh: false, text: false, siddur: true });
    await page.waitForFunction(() => document.getElementById("sdNusach").options.length === 4);
    assert.deepEqual(siddurCalls(cloud).map(c => c.params), [{}]);
    assert.deepEqual(await page.$$eval("#sdNusach option", o => o.map(x => [x.value, x.textContent])),
      [["", "בחרו נוסח…"], ...root.children.map(c => [c.key, c.title])]);
    assert.equal(await visible(page, "sdBrowse"), false);
    assert.equal(await visible(page, "sdLeaf"), false);
    assert.equal((await lsState(page)).source, "siddur");
    for (const id of ["sdNusach", "sdSearch", "sdFrom", "sdTo"])
      assert.ok(await page.evaluate(id => parseFloat(getComputedStyle(document.getElementById(id)).fontSize) >= 16, id), id + " ≥16px");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "no horizontal scroll");
    // החיפוש — הדבר הראשון בלשונית, גלוי עוד לפני בחירת נוסח, גדול
    assert.equal(await page.evaluate(() => document.querySelector("#srcSiddur > :first-child").contains(document.getElementById("sdSearch"))), true);
    assert.equal(await page.isVisible("#sdSearch"), true);
    assert.equal(await page.getAttribute("#sdSearch", "placeholder"), "חיפוש: אשרי, קדיש, נשמת…");
    assert.ok(await page.evaluate(() => document.getElementById("sdSearch").getBoundingClientRect().height >= 48), "תיבת חיפוש גדולה");
    assert.equal(await visible(page, "sdAllWrap"), false, "בלי נוסח — ממילא בכל הנוסחים");
    await shot(page, profile, "siddur-1-tab");
  });

  await step(`[${profile}] תפילה: בחירת נוסח ⇐ קטעים נפוצים + העץ, הנוסח נזכר`, async () => {
    await page.selectOption("#sdNusach", "sefard");
    await page.waitForFunction(n => document.querySelectorAll("#sdPopular .sdPop").length === n, pop.items.length);
    await page.waitForFunction(n => document.querySelectorAll("#sdList .sdItem").length === n, sefard.children.length);
    assert.deepEqual(await page.$$eval("#sdPopular .sdPop", b => b.map(x => x.textContent)), pop.items.map(i => i.label));
    assert.ok(pop.items.length >= 10 && !pop.draft, "הרשימה אושרה (8.16)");
    assert.ok(["נשמת", "שוכן עד", "ישתבח"].every(l => pop.items.some(i => i.label === l)));
    assert.equal(await visible(page, "sdPopularNote"), true);
    assert.ok(!(await txt(page, "#sdPopularNote")).includes("ממתינה לאישור"));
    // סדר הלשונית: חיפוש ← נוסח ← קיצורים
    const top = id => page.evaluate(id => document.getElementById(id).getBoundingClientRect().top, id);
    assert.ok(await top("sdSearch") < await top("sdNusach") && await top("sdNusach") < await top("sdPopular"));
    assert.equal(await visible(page, "sdAllWrap"), true);
    assert.deepEqual(await page.$$eval("#sdCrumbs button", b => b.map(x => x.textContent)), ["ספרד"]);
    assert.deepEqual(await page.$$eval("#sdList .sdItem .tt", t => t.map(x => x.firstChild.textContent)), sefard.children.map(c => c.title));
    const calls = siddurCalls(cloud).map(c => c.params);
    assert.ok(calls.some(p => p.popular === "1" && p.nusach === "sefard"));
    assert.ok(calls.some(p => p.path === "sefard" && Object.keys(p).length === 1));
    assert.deepEqual((await lsState(page)).siddur, { nusach: "sefard", path: "sefard", leaf: null });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "no horizontal scroll");
    await shot(page, profile, "siddur-2-nusach-shortcuts");
    await shot(page, profile, "search-1-top");
  });

  await step(`[${profile}] תפילה: ניווט בעץ (תיקייה, מיקום, חזרה)`, async () => {
    await page.click('#sdList .sdItem[data-path="sefard/shabbat"]');
    await page.waitForFunction(() => document.querySelectorAll("#sdCrumbs button").length === 2);
    assert.deepEqual(await page.$$eval("#sdCrumbs button", b => b.map(x => [x.textContent, x.disabled])), [["ספרד", false], ["שבת", true]]);
    const shabbat = mockApi("siddur", { path: "sefard/shabbat" }).body;
    assert.equal(await page.$$eval("#sdList .sdItem", i => i.length), shabbat.children.length);
    const ks = page.locator(`#sdList .sdItem[data-path="${SEFARD_KS}"]`);
    assert.ok((await ks.getAttribute("class")).includes("leaf"));
    assert.equal(await ks.locator("small").innerText(), shabbat.children.find(c => c.path === SEFARD_KS).first_words);
    assert.equal((await lsState(page)).siddur.path, "sefard/shabbat");
    await shot(page, profile, "siddur-3-tree");
    await page.click("#sdCrumbs button:not([disabled])");
    await page.waitForFunction(() => document.querySelectorAll("#sdCrumbs button").length === 1);
    assert.equal(await page.$$eval("#sdList .sdItem", i => i.length), sefard.children.length);
  });

  await step(`[${profile}] תפילה: חיפוש עם השהיה — בקשה אחת, קיצורים ואחריהם קטעים, ניקוי חוזר לעץ`, async () => {
    const before = siddurCalls(cloud, p => "q" in p).length;
    await page.locator("#sdSearch").pressSequentially("אשרי", { delay: 40 });
    await page.waitForSelector(`#sdResults .sdItem.leaf[data-path="${SEFARD_ASHREI}"]`);
    const qs = siddurCalls(cloud, p => "q" in p).slice(before).map(c => c.params);
    assert.deepEqual(qs, [{ q: "אשרי", nusach: "sefard" }], "השהיה: בקשת חיפוש אחת להקלדה");
    const res = mockApi("siddur", { q: "אשרי", nusach: "sefard" }).body;
    assert.ok(res.shortcuts.length >= 1 && res.results.length >= 1);
    // קיצורים קודם (כוכב), ואחריהם הקטעים מהסידור
    assert.deepEqual(await page.$$eval("#sdResults .sdResHead", h => h.map(x => x.textContent)), ["קיצורים", "בסידור"]);
    const rows = await page.$$eval("#sdResults .sdItem", i => i.map(x => [x.classList.contains("sc"), x.dataset.path]));
    assert.deepEqual(rows, [...res.shortcuts.map(s => [true, s.path]), ...res.results.map(r => [false, r.path])]);
    assert.equal(await page.$eval("#sdResults .sdItem.sc .tt", t => t.firstChild.textContent), "אשרי");
    const hit = res.results.find(r => r.path === SEFARD_ASHREI);
    assert.equal(await page.locator(`#sdResults .sdItem.leaf[data-path="${SEFARD_ASHREI}"] small`).innerText(), hit.breadcrumb.slice(1, -1).join(" › "));
    // בזמן חיפוש — רק התוצאות; הנוסח, הקיצורים והעץ מוסתרים
    assert.equal(await visible(page, "sdMain"), false);
    assert.equal(await page.isVisible("#sdSearchClear"), true);
    const nApi = cloud.api.length;
    await page.click("#sdSearchClear");
    await page.waitForFunction(() => document.getElementById("sdResults").hidden);
    assert.equal(await val(page, "sdSearch"), "");
    assert.equal(await visible(page, "sdMain"), true);
    assert.equal(await visible(page, "sdCrumbs"), true);
    assert.equal(await page.$$eval("#sdList .sdItem", i => i.length), sefard.children.length);
    assert.equal(cloud.api.length, nApi, "חזרה לעץ בלי בקשה נוספת");
  });

  await step(`[${profile}] תפילה: קטע לא זמין מוצג באפור ולא לחיץ (אשכנז)`, async () => {
    await page.selectOption("#sdNusach", "ashkenaz");
    await page.waitForFunction(() => document.querySelectorAll("#sdPopular .sdPop").length > 0 &&
      document.querySelector("#sdCrumbs button") && document.querySelector("#sdCrumbs button").textContent === "אשכנז");
    const parent = UNAVAILABLE.split("/").slice(0, -1).join("/");
    await page.evaluate(p => browseTo(p), parent);
    await page.waitForSelector(`#sdList .sdItem[data-path="${UNAVAILABLE}"]`);
    const na = page.locator(`#sdList .sdItem[data-path="${UNAVAILABLE}"]`);
    assert.ok((await na.getAttribute("class")).includes("na"));
    assert.equal(await na.isDisabled(), true);
    assert.equal(await na.locator("small").innerText(), "לא זמין ב-Sefaria במהדורה שנבחרה");
    assert.ok(parseFloat(await na.evaluate(e => getComputedStyle(e).opacity)) < 0.6);
    await page.selectOption("#sdNusach", "sefard");
    await page.waitForFunction(n => document.querySelectorAll("#sdPopular .sdPop").length === n, pop.items.length);
  });

  await step(`[${profile}] תפילה: קיצור "לכה דודי" ⇐ פסקאות 17–38 מתוך 43 מסומנות`, async () => {
    await page.click('#sdPopular .sdPop:text-is("לכה דודי")');
    await page.waitForFunction(() => document.querySelectorAll("#sdParas .sdPara").length === 43);
    assert.deepEqual(leafCalls(cloud, SEFARD_KS).map(c => c.params), [{ path: SEFARD_KS, from: "17", to: "38" }]);
    assert.equal(await visible(page, "sdBrowse"), false);
    assert.equal(await visible(page, "sdLeaf"), true);
    assert.equal(await txt(page, "#sdLeafTitle"), "לכה דודי");
    const meta = (await txt(page, "#sdLeafMeta")).replace(/[\u2068\u2069]/g, "");
    assert.ok(meta.startsWith("מתוך «קבלת שבת» · ספרד › שבת") && meta.includes("מהדורה: Torat Emet 357"), meta);
    assert.deepEqual(await checkedParas(page), range(17, 38));
    assert.equal(await val(page, "sdFrom"), "17");
    assert.equal(await val(page, "sdTo"), "38");
    // פסקאות ההוראה באפור
    const instr = LD.paragraphs.filter(p => p.kind === "instruction" || p.kind === "empty").map(p => p.n);
    assert.ok(instr.length > 0);
    assert.deepEqual(await page.$$eval("#sdParas .sdPara.instr input", c => c.map(x => +x.dataset.n)), instr);
    assert.equal(await page.$eval("#sdParas .sdPara:nth-child(17) .pt", e => e.textContent), LD.paragraphs[16].first_words + "…");
    const st = (await lsState(page)).siddur;
    assert.deepEqual([st.leaf.path, st.leaf.label, st.leaf.from, st.leaf.to, st.leaf.total, st.leaf.paragraphs.length],
      [SEFARD_KS, "לכה דודי", 17, 38, 43, 43]);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "no horizontal scroll");
  });

  await step(`[${profile}] תפילה: בחירת טווח — סימון, ביטול בקצה ובאמצע, "מפסקה/עד"`, async () => {
    const tap = n => page.click(`#sdParas input[data-n="${n}"]`);
    await tap(38); assert.deepEqual(await checkedParas(page), range(17, 37), "ביטול בקצה מקצר");
    await tap(40); assert.deepEqual(await checkedParas(page), range(17, 40), "סימון בחוץ מרחיב");
    await tap(30); assert.deepEqual(await checkedParas(page), range(17, 29), "ביטול באמצע — נגמר לפניה");
    await tap(17); assert.deepEqual(await checkedParas(page), range(18, 29));
    await page.selectOption("#sdFrom", "20");
    assert.deepEqual(await checkedParas(page), range(20, 29));
    await page.selectOption("#sdTo", "5");   // "עד" לפני "מ" ⇐ "מ" עובר איתו
    assert.deepEqual(await checkedParas(page), [5]);
    await page.selectOption("#sdFrom", "17");  // "מ" אחרי "עד" ⇐ "עד" עובר איתו
    assert.deepEqual(await checkedParas(page), [17]);
    await page.selectOption("#sdTo", "37");
    assert.deepEqual(await checkedParas(page), range(17, 37));
    const st = (await lsState(page)).siddur.leaf;
    assert.deepEqual([st.from, st.to], [17, 37]);
    // טווח שונה מהקיצור ⇐ בקשה חדשה, והכותרת היא שם הקטע + הטווח
    await page.click("#sdLoadBtn");
    await page.waitForFunction(() => !document.getElementById("segPreviewWrap").hidden);
    assert.deepEqual(leafCalls(cloud, SEFARD_KS).at(-1).params, { path: SEFARD_KS, from: "17", to: "37" });
    assert.equal(await page.$$eval("#segPreview .segrow:not(.instr)", r => r.length), LD37.segments.length);
    assert.ok((await txt(page, "#loadOk")).startsWith("נטען: קבלת שבת (פסקאות 17–37) · פסקאות 17–37 מתוך 43"));
    assert.equal(await page.evaluate(() => srtName()), "קבלת_שבת_(פסקאות_17–37).srt");
    // חזרה לטווח של הקיצור
    await tap(38);
    assert.deepEqual(await checkedParas(page), range(17, 38));
  });

  await step(`[${profile}] תפילה: "טען" ⇐ כמו טקסט חופשי — תוויות, הוראות באפור ולא נספרות`, async () => {
    const n0 = leafCalls(cloud, SEFARD_KS).length;
    await page.click("#sdLoadBtn");
    await page.waitForFunction(n => document.querySelectorAll("#segPreview .segrow:not(.instr)").length === n, LD.segments.length);
    assert.equal(leafCalls(cloud, SEFARD_KS).length, n0 + 1);
    assert.equal(await txt(page, "#loadOk"), `נטען: לכה דודי · פסקאות 17–38 מתוך 43 · ${LD.segments.length} כתוביות · גרסה: Torat Emet 357`);
    assert.equal(await page.$$eval("#segPreview .segrow.instr", r => r.length), instrCount(LD));
    assert.ok(instrCount(LD) > 0);
    // שורת הוראה: בלי מספר כתובית, הטקסט כמו ביחידה
    const instrUnit = LD.units.find(u => u.kind === "instruction");
    assert.ok(await page.$$eval("#segPreview .segrow.instr", (r, t) => r.some(x => x.querySelector(".idx").textContent === "" && x.querySelector(".txt").textContent === t), instrUnit.text));
    const rows = await page.$$eval("#segPreview .segrow:not(.instr)", r => r.map(x => x.querySelector(".txt").textContent));
    assert.deepEqual(rows, LD.segments.map(s => s.display));
    assert.deepEqual(await page.$$eval("#segPreview .segrow:not(.instr) .idx", r => r.map(x => +x.textContent)), range(1, LD.segments.length));
    assert.equal(await page.$eval("#segPreview .vchip", c => c.textContent), "קבלת שבת · 17");
    assert.ok((await txt(page, "#segHint")).includes("הוראות"));
    assert.equal(await isLocked(page, "step2"), false);
    const js = await page.evaluate(() => ({
      src: dataSource(), mode: alignMode(), units: isUnitsSource(), free: isFreeText(),
      audible: isAudible("ברוך"),
      again: segmentsFromSplits(flatWords(), S.baseSplits).map(s => s.display),
    }));
    assert.deepEqual([js.src, js.mode, js.units, js.free, js.audible], ["siddur", "tefila", true, false, true]);
    assert.deepEqual(js.again, LD.segments.map(s => s.display));
    const st = await lsState(page);
    assert.equal(st.source, "siddur");
    assert.equal(st.data.source, "siddur");
    assert.equal(st.data.label, "לכה דודי");
    assert.deepEqual(st.data.units, LD.units);
    assert.deepEqual(st.baseSplits, LD.segments.map(s => toks(s.display).length));
    assert.equal(st.splits, null);
    assert.equal(await page.evaluate(() => srtName()), "לכה_דודי.srt");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "no horizontal scroll");
    await page.locator("#segPreviewWrap").scrollIntoViewIfNeeded();
    await shot(page, profile, "siddur-4-loaded");
  });

  let splits;
  await step(`[${profile}] תפילה: עורך החלוקה (תוויות הסידור, פיצול)`, async () => {
    await page.click("#editSplitBtn");
    await page.waitForFunction(() => document.getElementById("editOverlay").classList.contains("open"));
    const base0 = LD.segments.map(s => toks(s.display).length);
    const groups = () => page.$$eval("#editList .egroup", g => g.map(x => x.querySelectorAll(".w").length));
    assert.deepEqual(await groups(), base0);
    assert.equal(await page.$eval("#editList .vch", v => v.textContent), "קבלת שבת · 17");
    assert.equal(await txt(page, "#editReset"), "🔄 חזרה לחלוקה האוטומטית");
    await page.click('#editList .w[data-i="1"]');
    await page.click("#editSplit");
    splits = [1, base0[0] - 1, ...base0.slice(1)];
    assert.deepEqual(await groups(), splits);
    await page.click("#editSave");
    assert.equal(await txt(page, "#loadMsg"), "החלוקה עודכנה ✓");
    assert.equal(await page.$$eval("#segPreview .segrow:not(.instr)", r => r.length), LD.segments.length + 1);
    assert.equal(await page.$$eval("#segPreview .segrow.instr", r => r.length), instrCount(LD), "ההוראות נשארות אחרי עריכה");
    assert.deepEqual((await lsState(page)).splits, splits);
  });

  await step(`[${profile}] תפילה: סנכרון בענן — source=siddur, units כמו ה-API, title, splits`, async () => {
    await page.setInputFiles("#audioFile", { name: "lecha.wav", mimeType: "audio/wav", buffer: wavSilence(1) });
    await page.waitForFunction(() => !document.getElementById("done2").hidden);
    const segsNow = await page.evaluate(() => S.data.segments);
    const times = segsNow.map((_, i) => i * 0.75);
    cloud.statusQueue.push(null, { body: { srt: srtFor(segsNow, times, segsNow.length), report: "" } });
    await page.click("#startCloud");
    await until(() => cloud.submits.length === 1, "submit");
    const { fields, files } = cloud.submits[0];
    assert.deepEqual(Object.keys(fields).sort(), ["max_words", "source", "splits", "title", "token", "units"]);
    assert.equal(fields.source, "siddur");
    assert.equal(fields.units, JSON.stringify(LD.units), "בדיוק היחידות שה-API החזיר, כולל הוראות");
    assert.ok(JSON.parse(fields.units).some(u => u.kind === "instruction"));
    assert.equal(fields.title, "לכה דודי");
    assert.equal(fields.max_words, "4");
    assert.deepEqual(JSON.parse(fields.splits), splits);
    assert.equal(files.file.filename, "lecha.wav");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    assert.equal(await page.$$eval("#timeList .timerow", r => r.length), segsNow.length);
    assert.deepEqual((await lsState(page)).times, times);
    await page.waitForFunction(() => document.getElementById("cloudProgress").hidden);
  });

  await step(`[${profile}] תפילה: חזרה אחרי סגירה — הבחירה, הקטע והעבודה בענן משוחזרים`, async () => {
    const now = await page.evaluate(() => Date.now());
    await page.evaluate(job => {
      const st = JSON.parse(localStorage.getItem("kriat-hatora-v1"));
      Object.assign(st, { times: null, endTime: null, report: null, cloudJob: job });
      localStorage.setItem("kriat-hatora-v1", JSON.stringify(st));
    }, { id: "fc-siddur-2", t0: now - 20000, ts: now - 40000, est: 200, push: false });
    const segsNow = await page.evaluate(() => S.data.segments);
    cloud.statusQueue.length = 0;
    cloud.statusQueue.push(null, { body: { srt: srtFor(segsNow, segsNow.map((_, i) => i), segsNow.length + 1), report: "" } });
    const nApi = cloud.api.length;
    await page.reload();
    await page.waitForFunction(() => !document.getElementById("cloudProgress").hidden);
    assert.deepEqual(await tabState(page), { sel: ["siddur"], tanakh: false, text: false, siddur: true });
    await page.waitForFunction(() => document.getElementById("sdNusach").value === "sefard");
    assert.equal(await visible(page, "sdLeaf"), true);
    assert.equal(await visible(page, "sdBrowse"), false);
    assert.equal(await txt(page, "#sdLeafTitle"), "לכה דודי");
    assert.equal(await page.$$eval("#sdParas .sdPara", r => r.length), 43);
    assert.deepEqual(await checkedParas(page), range(17, 38));
    assert.equal(await page.$$eval("#segPreview .segrow:not(.instr)", r => r.length), LD.segments.length + 1);
    assert.equal(await page.$$eval("#segPreview .segrow.instr", r => r.length), instrCount(LD));
    assert.equal(await page.evaluate(() => [alignMode(), srtName()].join()), "tefila,לכה_דודי.srt");
    await page.waitForFunction(() => document.getElementById("timingMsg").textContent.includes("הסנכרון הושלם"), null, { timeout: 15000 });
    assert.ok(cloud.statusCalls.includes("fc-siddur-2"));
    const after = cloud.api.slice(nApi);
    assert.ok(!after.some(c => c.kind === "siddur" && c.params.path === SEFARD_KS), "הקטע לא נטען מחדש");
    assert.equal((await lsState(page)).cloudJob, null);
  });

  await step(`[${profile}] תפילה: "העתק לטקסט חופשי" — רק הטקסט הנאמר, לעריכה`, async () => {
    const nApi = cloud.api.length;
    await page.click("#sdCopyBtn");
    await page.waitForFunction(() => !document.getElementById("srcText").hidden);
    assert.deepEqual(await tabState(page), { sel: ["text"], tanakh: false, text: true });
    const spoken = LD.units.filter(u => u.kind !== "instruction").map(u => u.text.trim()).join("\n");
    assert.equal(await val(page, "freeText"), spoken);
    assert.equal(await val(page, "textTitle"), "לכה דודי");
    assert.ok((await txt(page, "#loadMsg")).startsWith("הקטע הועתק לטקסט חופשי ✓"));
    assert.equal(cloud.api.length, nApi, "הקטע שנטען — בלי בקשה");
    const st = await lsState(page);
    assert.equal(st.source, "text");
    assert.deepEqual(st.freeText, { text: spoken, title: "לכה דודי" });
    // הטקסט שהועתק נטען כטקסט חופשי
    await page.click("#textLoadBtn");
    await page.waitForFunction(() => /^נטען: לכה דודי · \d+ שורות/.test(document.getElementById("loadOk").textContent));
    assert.equal(await page.evaluate(() => dataSource()), "text");
    assert.equal(await page.$$eval("#segPreview .segrow.instr", r => r.length), 0);
    assert.equal(await page.evaluate(() => srtName()), "לכה_דודי.srt");
  });

  await step(`[${profile}] תפילה: שגיאות בעברית — 422 (העתקה), 502, 413 (טווח), 504`, async () => {
    await page.click('.srcTabs [data-src="siddur"]');
    assert.equal(await visible(page, "sdLeaf"), true);
    // 422 — עלה בלי ניקוד: הודעה + העתקה לטקסט חופשי של כל הטקסט
    await page.evaluate(p => selectLeaf({ path: p, title: "אשר יצר" }), DAAT_ASHER);
    await until(async () => (await txt(page, "#loadMsg")).includes("אינו מנוקד"), "422");
    const m422 = await txt(page, "#loadMsg");
    assert.ok(m422.startsWith("טעינת הקטע נכשלה: ") && m422.includes('אפשר ללחוץ על "העתק לטקסט חופשי"'), m422);
    const e422 = mockApi("siddur", { path: DAAT_ASHER }).body;
    assert.equal(e422.unvocalized, true);
    page.once("dialog", d => d.accept());   // בתיבת הטקסט החופשי כבר יש טקסט
    const nApi = cloud.api.length;
    await page.click("#sdCopyBtn");
    await page.waitForFunction(() => !document.getElementById("srcText").hidden);
    assert.equal(await val(page, "freeText"), e422.units.map(u => u.text.trim()).join("\n"));
    assert.equal(await val(page, "textTitle"), "אשר יצר");
    assert.equal(cloud.api.length, nApi, "גוף ה-422 שמור — בלי בקשה");
    await page.click('.srcTabs [data-src="siddur"]');
    // 502 — ‏versions ריק (תשובה אמיתית)
    await page.evaluate(p => selectLeaf({ path: p, title: "אשרי" }), SEFARD_ASHREI);
    await until(async () => (await txt(page, "#loadMsg")).includes("versions ריק"), "502");
    assert.ok((await txt(page, "#loadMsg")).endsWith("נסו שוב בעוד רגע."));
    // 413 — סינתטי, עם paragraphs כמו ב-API: מציעים טווח
    cloud.override = (kind, p) => kind === "siddur" && p.path === SEFARD_KS && !p.from ? {
      status: 413, body: { error: "הקטע ארוך מדי לסנכרון אחד (43 פסקאות) — עד 10. בחרו טווח פסקאות (from/to)", paragraphs: LD.paragraphs } } : null;
    await page.evaluate(p => selectLeaf({ path: p, title: "קבלת שבת" }), SEFARD_KS);
    await until(async () => (await txt(page, "#loadMsg")).includes("ארוך מדי"), "413");
    const m413 = await txt(page, "#loadMsg");
    assert.ok(!m413.includes("from/to") && m413.includes("סמנו טווח פסקאות קצר יותר"), m413);
    assert.equal(await page.$$eval("#sdParas .sdPara", r => r.length), 43, "הפסקאות מוצגות לבחירת טווח");
    assert.deepEqual(await checkedParas(page), range(1, 43));
    // 504 — Sefaria לא ענתה; אחר-כך טווח קצר נטען כרגיל
    cloud.override = (kind, p) => kind === "siddur" && p.path === SEFARD_KS && p.to === "38" && p.from === "20" ? {
      status: 504, body: { error: "Sefaria לא ענתה בזמן (20 שניות) — נסו שוב בעוד רגע" } } : null;
    await page.selectOption("#sdFrom", "20"); await page.selectOption("#sdTo", "38");
    await page.click("#sdLoadBtn");
    await until(async () => (await txt(page, "#loadMsg")).includes("לא ענתה בזמן"), "504");
    cloud.override = null;
    await page.click("#sdLoadBtn");
    await page.waitForFunction(() => document.getElementById("loadOk").textContent.startsWith("נטען: קבלת שבת (פסקאות 20–38)"));
    assert.equal(await txt(page, "#loadMsg"), "");
    // השגיאות המכוונות מופיעות בקונסול כ-"Failed to load resource" — צפוי
    const expected = errors.filter(e => /status of (413|422|502|504)/.test(e));
    assert.equal(expected.length, 4, errors.join("\n"));
    for (const e of expected) errors.splice(errors.indexOf(e), 1);
  });

  await step(`[${profile}] תפילה: שם נרדף ("שיר הכבוד", "תהלה לדוד") ⇐ הקיצור; בכל הנוסחים; הקשה טוענת`, async () => {
    // "שיר הכבוד" ⇐ הקיצור "אנעים זמירות" (הכותרת בספרד שונה)
    await page.fill("#sdSearch", "שיר הכבוד");
    await page.waitForFunction(() => (document.querySelector("#sdResults .sdItem.sc .tt") || {}).firstChild?.textContent === "אנעים זמירות");
    const kavod = mockApi("siddur", { q: "שיר הכבוד", nusach: "sefard" }).body;
    assert.equal(kavod.shortcuts[0].label, "אנעים זמירות");
    assert.equal(await page.$eval("#sdResults .sdItem.sc .tt", t => t.firstChild.textContent), "אנעים זמירות");
    assert.ok((await page.$eval("#sdResults .sdItem.sc small", s => s.textContent)).includes("מתוך «מוסף של שבת»"));
    await shot(page, profile, "search-2-alias");
    // "תהלה לדוד" בכל הנוסחים: הנוכחי (ספרד) קודם, עם שם הנוסח בכל שורה
    await page.fill("#sdSearch", "תהלה לדוד");
    await page.check("#sdAll");
    await page.waitForFunction(() => [...document.querySelectorAll("#sdResults .sdItem.sc small")].some(s => s.textContent.startsWith("עדות המזרח")));
    const q = siddurCalls(cloud, p => p.q === "תהלה לדוד").at(-1).params;
    assert.deepEqual(q, { q: "תהלה לדוד", nusach: "sefard", all: "1" });
    const all = mockApi("siddur", q).body;
    assert.deepEqual(all.shortcuts.map(s => [s.nusach, s.label]).slice(0, 3),
      [["sefard", "אשרי"], ["edot-hamizrach", "אשרי"], ["ashkenaz", "אשרי"]]);
    await shot(page, profile, "search-3-all-nusachim");
    // הקשה על הקיצור של עדות המזרח ⇐ עוברים לנוסח שלו, והקטע נטען עם הטווח
    const edot = all.shortcuts.find(s => s.nusach === "edot-hamizrach");
    assert.equal(edot.path, EDOT_ASHREI);
    await page.locator("#sdResults .sdItem.sc").nth(all.shortcuts.indexOf(edot)).click();
    await page.waitForFunction(n => document.querySelectorAll("#sdParas .sdPara").length === n, 6);
    assert.equal(await val(page, "sdSearch"), "");
    assert.equal(await visible(page, "sdResults"), false);
    assert.equal(await val(page, "sdNusach"), "edot-hamizrach");
    assert.equal(await txt(page, "#sdLeafTitle"), "אשרי");
    assert.deepEqual(await checkedParas(page), range(edot.from, edot.to));
    assert.deepEqual(leafCalls(cloud, EDOT_ASHREI).at(-1).params, { path: EDOT_ASHREI, from: String(edot.from), to: String(edot.to) });
    await page.click("#sdLoadBtn");
    await page.waitForFunction(() => document.getElementById("loadOk").textContent.startsWith("נטען: אשרי"));
    assert.equal(await page.evaluate(() => dataSource()), "siddur");
    const st = (await lsState(page)).siddur;
    assert.equal(st.nusach, "edot-hamizrach");
    assert.equal(st.leaf.path, EDOT_ASHREI);
    await page.uncheck("#sdAll");
    // סבילות לכתיב: "ישתבך" ⇐ ישתבח
    await page.fill("#sdSearch", "ישתבך");
    await page.waitForFunction(() => [...document.querySelectorAll("#sdResults .sdItem.sc .tt")].some(t => t.firstChild.textContent === "ישתבח"));
    // ניקוי ⇐ הקטע שנבחר עדיין שם
    await page.click("#sdSearchClear");
    assert.equal(await visible(page, "sdLeaf"), true);
    assert.equal(await txt(page, "#sdLeafTitle"), "אשרי");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "no horizontal scroll");
  });

  await step(`[${profile}] תפילה: מצב שמור ישן (טקסט חופשי, בלי siddur) משוחזר כמו קודם`, async () => {
    const ts = mockApi("text_segments", { text: "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ", mode: "tefila" }).body;
    await page.evaluate(([data]) => localStorage.setItem("kriat-hatora-v1", JSON.stringify({
      query: { book: "בראשית", chapter: "1", verse_start: "1", verse_end: "1", chapter_end: "1" },
      data: Object.assign(data, { source: "text" }), times: null, endTime: null, audioName: null, report: null,
      cloudJob: null, splits: null, baseSplits: data.segments.map(s => s.display.split(" ").filter(Boolean).length),
      source: "text", freeText: { text: "אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ", title: "אשרי" },
    })), [ts]);
    const nApi = cloud.api.length;
    await page.reload();
    await page.waitForFunction(() => !document.getElementById("segPreviewWrap").hidden);
    assert.deepEqual(await tabState(page), { sel: ["text"], tanakh: false, text: true });
    assert.equal(await txt(page, "#loadOk"), `נטען: אשרי · 1 שורות · ${ts.segments.length} כתוביות`);
    assert.equal(siddurCalls({ api: cloud.api.slice(nApi) }).length, 0, "הסידור לא נטען בלי פתיחת הלשונית");
    assert.deepEqual((await lsState(page)).siddur, { nusach: "", path: "", leaf: null });
    await page.click('.srcTabs [data-src="siddur"]');
    await page.waitForFunction(() => document.getElementById("sdNusach").options.length === 4);
    assert.equal(await val(page, "sdNusach"), "");
    assert.equal(await visible(page, "sdBrowse"), false);
    assert.equal(await visible(page, "sdLeaf"), false);
    assert.equal(await page.evaluate(() => dataSource()), "text", "הטקסט שנטען לא נמחק במעבר לשונית");
  });

  await step(`[${profile}] (תפילה) אין שגיאות קונסול ואין יציאה לרשת`, async () => {
    assertNoErrors(errors);
    assert.ok(cloud.external.every(h => /^fonts\.(googleapis|gstatic)\.com$/.test(h)), cloud.external.join(","));
  });
  await context.close();
}

/* =================== הרצה =================== */
const server = await startServer();
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch();
const only = process.env.SMOKE_ONLY;
try {
  for (const profile of ["desktop", "mobile"]) {
    if (only && only !== profile) continue;
    console.log(`\n== ${profile} ==`);
    await flowMain(browser, base, profile);
    await flowResume(browser, base, profile);
    await flowUnreadableVideo(browser, base, profile);
    await flowFreeText(browser, base, profile);
    await flowSiddur(browser, base, profile);
    await flowOldState(browser, base, profile);
  }
  if (!only || only === "sw") {
    console.log("\n== service worker ==");
    await flowServiceWorker(browser, base);
  }
} finally {
  await browser.close();
  server.close();
}
const failed = results.filter(r => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);
