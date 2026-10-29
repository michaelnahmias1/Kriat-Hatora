// מריץ את segmentsFromSplits / isAudible של js/segments.js (סקריפט דפדפן
// גלובלי) מחוץ לדפדפן, כדי ש-tests/test_segments_js_sync.py ישווה אותם
// לחותך ב-Python. קלט ב-stdin: JSON
//   {"cases": [{"mode": "tefila", "words": [{"t": "...", "verse": 1}], "sizes": [..]}]}
// פלט: לכל מקרה — רשימת {display, verse}.
import { readFileSync } from "node:fs";
import vm from "node:vm";

const src = readFileSync(new URL("../js/segments.js", import.meta.url), "utf8");
const ctx = vm.createContext({});
vm.runInContext(src + "\nlet MODE = 'tanakh';\nfunction alignMode() { return MODE; }", ctx);

const input = JSON.parse(readFileSync(0, "utf8"));
const out = input.cases.map(c => {
  ctx.__case = c;
  return vm.runInContext(
    "MODE = __case.mode; segmentsFromSplits(__case.words, __case.sizes)", ctx);
});
process.stdout.write(JSON.stringify(out));
