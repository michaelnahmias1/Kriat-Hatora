// בדיקת עשן לממשק (index.html) — Playwright + Chromium, בלי רשת חיצונית.
//
//   node tests/smoke/smoke.mjs            # כל התרחישים, דסקטופ + אייפון
//   SMOKE_ONLY=desktop node tests/smoke/smoke.mjs
//
// מגישה את הריפו בשרת סטטי קטן, ומחליפה ב-mock את כל מה שיוצא מהדפדפן:
//   /api/segments, /api/structure — ה-build_payload האמיתי מ-api/ עם Sefaria מזויף
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
  closeSplitEditor nudge renderTimeList buildSrt srtName srtFile isStandalone refreshInstallUi`.split(/\s+/);
const GLOBAL_BINDINGS = `$ STORE_KEY AI_ENDPOINT AI_TOKEN VAPID_PUBLIC_KEY S HE_LETTER_RE NIQQUD_RE MAQAF
  bookChapters FALLBACK_CHAPTERS player audioReady audioFileObj audioDurationSec lastObjectUrl
  MAX_UPLOAD_MB MAX_DECODE_MB CLOUD_POLL_MS CLOUD_JOB_LIMIT_MS cloudAbort cloudTimerInt
  CLOUD_BTN_LABEL wakeLock E settingsOverlay installPrompt`.split(/\s+/);

/* ---------- הקשר דפדפן עם כל ה-mocks ---------- */
async function newSession(browser, base, profile, { serviceWorkers = "block" } = {}) {
  const ctxOpts = profile === "mobile"
    ? (({ defaultBrowserType, ...d }) => d)(devices["iPhone 13"])
    : { viewport: { width: 1280, height: 860 } };
  const context = await browser.newContext({ ...ctxOpts, locale: "he-IL", serviceWorkers });
  const cloud = { submits: [], statusCalls: [], cancels: [], statusQueue: [], external: [], api: [] };
  const origin = new URL(base).origin;
  const cors = { "Access-Control-Allow-Origin": "*" };
  await context.route("**/*", async route => {
    const req = route.request();
    const url = new URL(req.url());
    if (url.origin === origin) {
      if (url.pathname.startsWith("/api/")) {
        const kind = url.pathname.slice(5);
        const params = Object.fromEntries(url.searchParams);
        cloud.api.push({ kind, params });
        const { status, body } = mockApi(kind, params);
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
