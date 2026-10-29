# -*- coding: utf-8 -*-
"""קטלוג הסידור — טעינה, ניווט, חיפוש ו-ref לעלה (PLAN_TEFILA.md 4.2.1).

ספריה סטנדרטית בלבד: רץ בתוך פונקציית Vercel (‏api/siddur.py, משימה 4.2.2).
הקטלוג עצמו — ‏data/siddur/catalog.json — נבנה ע״י tools/build_siddur_catalog.py
ונשמר בגיט. הוא מכיל רק את העץ, הכותרות וה-ref/הגרסה של כל עלה; הטקסט נמשך
בזמן ריצה מ-Sefaria (עלה אחרי עלה — לעולם לא טווח בין עלים).

מבנה העץ: נוסח ← סוג יום ← תפילה ← (קבוצות, באשכנז) ← קטע (עלה). תפילה יכולה
להיות עלה בעצמה (למשל "קבלת שבת" בעדות המזרח). כל צומת: ‏key (ייחודי בין
אחיו), ‏title (אנגלית, מ-Sefaria), ‏heTitle. עלה: ‏ref (ref מלא של Sefaria),
‏v (מזהה הגרסה שנבחרה, מתוך versions של הנוסח; ‏None ⇐ unavailable=True),
‏alt (גרסאות נוספות שנבדקו ויש בהן טקסט), ‏first (המילים הראשונות של הטקסט
הנאמר בגרסה שנבחרה — לחיפוש לפי "מילים ראשונות"), ‏depth (רק כשעומק הטקסט ≠ 1).

נתיב = מפתחות מופרדים ב-"/" מהשורש, למשל
"ashkenaz/weekday/shacharit/pesukei-dezimra/ashrei".

שימוש:
    from siddur.catalog import load_catalog
    cat = load_catalog()
    cat.children("edot-hamizrach/shabbat")
    cat.source("edot-hamizrach/weekday/weekday-shacharit/ashrei")
    cat.search("אשרי", nusach="sefard")
    cat.find("שמונה עשרה", nusach="sefard", popular=..., aliases=load_aliases())
"""

import json
import re
import unicodedata
from pathlib import Path

CATALOG_PATH = (Path(__file__).resolve().parent.parent.parent
                / "data" / "siddur" / "catalog.json")
ALIASES_PATH = CATALOG_PATH.parent / "aliases.json"

_MARKS_RE = re.compile(r"[֑-ׇ]")
_GERESH_RE = re.compile(r"[׳’‘`´]")
_NON_WORD_RE = re.compile(r"[^0-9a-zא-ת']+")


def normalize(text: str) -> str:
    """נרמול לחיפוש: בלי ניקוד וטעמים, מקף ← רווח, גרש אחיד ('), אותיות
    לטיניות קטנות, כל השאר ← רווח. ‏"בָּרוּךְ־שֶׁאָמַר" ⇐ "ברוך שאמר"."""
    s = unicodedata.normalize("NFC", text or "")
    s = s.replace("־", " ")
    s = _MARKS_RE.sub("", s)
    s = _GERESH_RE.sub("'", s)
    s = s.replace("״", '"').lower()
    s = _NON_WORD_RE.sub(" ", s)
    # גרש שאינו צמוד לאות (מרכאות בודדות וכד׳) — רעש
    words = [w.strip("'") if not re.search(r"[א-ת]'$", w) else w
             for w in s.split()]
    return " ".join(w for w in words if w)


_GERSHAYIM_IN_WORD_RE = re.compile(r'(?<=[א-ת])["״](?=[א-ת])')
_FINALS = str.maketrans("ךםןףץ", "כמנפצ")
_PREFIX = "[ובלכמשה]{0,3}"
# שם ה׳ בכל צורותיו (גם עם תחילית: "לה'", "ליהוה") ⇐ "ה"
_DIVINE_RE = re.compile(rf"^({_PREFIX})(?:יהוה|יי|ה')$")
# "אלקינו"/"אלוקים" ⇐ "אלהינו"/"אלהים" (ו/י נבלעים ממילא ב-skeleton)
_ELOKIM_RE = re.compile(rf"^({_PREFIX})אלו?ק")


def fold(text: str) -> str:
    """נרמול להשוואה בחיפוש — חזק מ-normalize: גם בלי גרשיים בתוך מילה
    ‏(‏"ק״ש" ⇐ "קש", ‏'בהמ"ז' ⇐ "בהמז"), שם ה׳ אחיד ("ה'", "יי", "יהוה" ⇐
    "ה"), "אלקינו" ⇐ "אלהינו", בלי גרש, ואותיות סופיות ⇐ רגילות. משמש גם
    לשאילתה וגם לכותרות, כך שכל צורה מוצאת כל צורה."""
    s = unicodedata.normalize("NFC", text or "")
    s = s.replace("־", " ")
    s = _MARKS_RE.sub("", s)
    s = _GERSHAYIM_IN_WORD_RE.sub("", s)
    s = _GERESH_RE.sub("'", s).lower()
    s = _NON_WORD_RE.sub(" ", s)
    out = []
    for w in s.split():
        m = _DIVINE_RE.match(w)
        if m:
            w = m.group(1) + "ה"
        else:
            w = _ELOKIM_RE.sub(lambda mm: mm.group(1) + "אלה", w)
        w = w.replace("'", "").translate(_FINALS)
        if w:
            out.append(w)
    return " ".join(out)


def skeleton(folded: str) -> str:
    """כתיב חסר: בלי ו/י אחרי האות הראשונה של כל מילה ("כאלוהינו" ⇐ "כאלהנו",
    ‏"שוכן" ⇐ "שכנ"). רק לסבילות לכתיב — לא לדירוג רגיל."""
    return " ".join(w[0] + re.sub("[וי]", "", w[1:]) for w in folded.split())


def _title_tier(title: str, q: str, mid: bool = False, whole: bool = False):
    """דרגת ההתאמה של כותרת מקופלת לשאילתה מקופלת: 0 זהה, 1 תחילית, 2 מילה
    בכותרת שמתחילה בשאילתה, 3 תת-מחרוזת באמצע מילה (רק כש-mid, ורק לשאילתה
    של מילה אחת); אחרת None.
    ‏whole — רק מילים שלמות (לשמות נרדפים: "שמע" לא מוצא "שמעון")."""
    if not title or not q:
        return None
    if title == q:
        return 0
    end = " " if whole else ""
    if (title + " ").startswith(q + end):
        return 1
    if (" " + q + end) in (" " + title + " "):
        return 2
    if mid and " " not in q and q in title:
        return 3
    return None


def _rank_key(tier: int, via: int) -> tuple:
    """סדר התוצאות: כותרת זהה (ישירה ← דרך שם נרדף ← "בתוך"); אחריה תחילית
    או מילה בכותרת באותו סדר; אחר-כך התאמות חלשות (תת-מחרוזת, מילים
    ראשונות); ובסוף סבילות לכתיב."""
    return (0 if tier == 0 else 1 if tier <= 2 else 2 if tier <= 4 else 3, via, tier)


def _best(tiers):
    vals = [t for t in tiers if t is not None]
    return min(vals) if vals else None


def _first_words_match(first: str, q: str, whole: bool = False) -> bool:
    """המילים הראשונות (מקופלות) מתחילות במילים של השאילתה — המילה
    האחרונה גם כתחילית (חוץ מ-whole)."""
    qw, fw = q.split(), (first or "").split()
    if not qw or len(fw) < len(qw):
        return False
    n = len(qw)
    if whole:
        return fw[:n] == qw
    return fw[:n - 1] == qw[:-1] and fw[n - 1].startswith(qw[-1])


def _within_one(a: str, b: str) -> bool:
    """מרחק עריכה ≤ 1 (החלפה, השמטה או הוספה של תו אחד)."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    if la == lb:
        return a[i + 1:] == b[i + 1:]
    return a[i:] == b[i + 1:]


def _fuzzy_match(title: str, q: str) -> bool:
    """סבילות לכתיב: כתיב מלא/חסר (ו/י), או שגיאת אות אחת בשאילתה של 4
    אותיות ומעלה — מול הכותרת כולה או מול תחילתה."""
    if _title_tier(skeleton(title), skeleton(q)) is not None:
        return True
    if len(q) >= 4:
        return _within_one(q, title) or any(
            _within_one(q, title[:n]) for n in (len(q) - 1, len(q), len(q) + 1)
            if 0 < n <= len(title))
    return False


class Aliases:
    """שמות נרדפים (data/siddur/aliases.json): ‏groups = [{names, inside?}]."""

    def __init__(self, data: dict = None):
        self.groups = []
        for g in (data or {}).get("groups", []):
            names = [(fold(n), n) for n in g.get("names", []) if fold(n)]
            inside = [(fold(n), n) for n in g.get("inside", []) if fold(n)]
            if names:
                self.groups.append((names, inside))

    @classmethod
    def load(cls, path=None) -> "Aliases":
        p = Path(path) if path else ALIASES_PATH
        return cls(json.loads(p.read_text(encoding="utf-8")))

    def expand(self, q: str) -> list:
        """שאילתה מקופלת ⇐ [(צורה, דרך, שם לתצוגה)]: השאילתה עצמה (דרך 0),
        שמות נרדפים (1) ו"בתוך" (2). קבוצה נבחרת כשהשאילתה זהה לאחד השמות
        או תחילית שלו (מ-3 תווים). לא לפי skeleton: "קדיש" ו"קידוש" זהים בו."""
        out, seen = [(q, 0, None)], {q}
        for names, inside in self.groups:
            if not any(n == q or (len(q) >= 3 and n.startswith(q))
                       for n, _ in names):
                continue
            display = names[0][1]
            for n, _ in names:
                if n not in seen:
                    seen.add(n)
                    out.append((n, 1, display))
            for n, _ in inside:
                if n not in seen:
                    seen.add(n)
                    out.append((n, 2, display))
        return out


_ALIASES = None


def load_aliases(path=None) -> Aliases:
    """השמות הנרדפים שבגיט (נטענים פעם אחת לכל תהליך), או קובץ אחר."""
    global _ALIASES
    if path is not None:
        return Aliases.load(path)
    if _ALIASES is None:
        _ALIASES = Aliases.load()
    return _ALIASES


def split_path(path) -> list:
    """"a/b/c" / ["a","b","c"] / "" / None ⇐ רשימת מפתחות."""
    if path is None:
        return []
    if isinstance(path, (list, tuple)):
        return [p for p in path if p]
    return [p for p in str(path).strip("/").split("/") if p]


def is_leaf(node: dict) -> bool:
    return "children" not in node


class Catalog:
    """עטיפה טהורה סביב ה-dict של catalog.json (בלי רשת, בלי מצב גלובלי)."""

    def __init__(self, data: dict):
        self.data = data
        self.nusachim = data.get("nusachim", [])
        self._flat = None  # [(path, node, he_breadcrumb)] לפי סדר הקטלוג
        self._sflat = None  # אותו דבר + כותרות ומילים ראשונות מקופלות (fold)

    @classmethod
    def load(cls, path=None) -> "Catalog":
        p = Path(path) if path else CATALOG_PATH
        return cls(json.loads(p.read_text(encoding="utf-8")))

    # --- ניווט -----------------------------------------------------------

    def node(self, path):
        """הצומת בנתיב, או None. נתיב ריק ⇐ None (השורש אינו צומת)."""
        keys = split_path(path)
        if not keys:
            return None
        level, node = self.nusachim, None
        for k in keys:
            node = next((c for c in level if c.get("key") == k), None)
            if node is None:
                return None
            level = node.get("children")
            if level is None:
                level = []
        return node

    def nusach_of(self, path):
        keys = split_path(path)
        return self.node(keys[:1]) if keys else None

    def children(self, path=""):
        """רשימת הילדים של צומת (שורש ⇐ הנוסחים), כסיכומים קצרים.
        ‏None אם הנתיב לא קיים או שהוא עלה."""
        keys = split_path(path)
        if keys:
            node = self.node(keys)
            if node is None or is_leaf(node):
                return None
            level = node["children"]
        else:
            level = self.nusachim
        return [self._summary(keys + [c["key"]], c) for c in level]

    def leaf(self, path):
        """העלה בנתיב, או None אם הנתיב לא קיים או שאינו עלה."""
        node = self.node(path)
        return node if node is not None and is_leaf(node) else None

    def source(self, path):
        """מאיפה מושכים את הטקסט של עלה: {ref, version, version_id, license,
        index, depth, nusach}. ‏None אם העלה מסומן unavailable.
        ‏KeyError אם הנתיב לא קיים או שאינו עלה."""
        keys = split_path(path)
        leaf = self.leaf(keys)
        if leaf is None:
            raise KeyError("/".join(keys))
        if leaf.get("unavailable") or not leaf.get("v"):
            return None
        nus = self.nusach_of(keys)
        ver = nus["versions"][leaf["v"]]
        return {
            "ref": leaf["ref"],
            "version": ver["title"],
            "version_id": leaf["v"],
            "license": ver.get("license", ""),
            "index": nus.get("index", ""),
            "depth": leaf.get("depth", 1),
            "nusach": nus["key"],
        }

    def leaves(self, path=""):
        """כל העלים מתחת לנתיב (כולל הוא עצמו אם הוא עלה), לפי הסדר:
        רשימת (נתיב, עלה)."""
        prefix = "/".join(split_path(path))
        return [(p, n) for p, n, _ in self._index()
                if is_leaf(n) and (not prefix or p == prefix
                                   or p.startswith(prefix + "/"))]

    def breadcrumb(self, path) -> list:
        """הכותרות העבריות מהנוסח ועד הצומת עצמו."""
        keys = split_path(path)
        out, level = [], self.nusachim
        for k in keys:
            node = next((c for c in level if c.get("key") == k), None)
            if node is None:
                return []
            out.append(node.get("heTitle", ""))
            level = node.get("children") or []
        return out

    # --- חיפוש ------------------------------------------------------------
    # מימוש יחיד: search_titles/search_first_words/search (הפשוטים) ו-find
    # (מה ש-/api/siddur?q= מחזיר: קיצורים, שמות נרדפים, סבילות לכתיב)
    # משתמשים באותן פונקציות התאמה — fold, ‏_title_tier, ‏_first_words_match.

    def search_titles(self, query, nusach=None, limit=50) -> list:
        """צמתים (בכל רמה) שהכותרת העברית או האנגלית שלהם מכילה את השאילתה.
        דירוג: התאמה מלאה ← תחילית ← תת-מחרוזת; בתוך דרגה — סדר הקטלוג."""
        q = fold(query)
        if not q:
            return []
        ranked = []
        for order, (path, node, crumbs, titles, _) in enumerate(self._search_index()):
            if nusach and not path.startswith(nusach + "/"):
                continue
            best = _best(_title_tier(t, q, mid=True) for t in titles)
            if best is not None:
                ranked.append((best, order, self._result(path, node, crumbs,
                                                         "title")))
        ranked.sort(key=lambda x: (x[0], x[1]))
        return [r for _, _, r in ranked[:limit]]

    def search_first_words(self, query, nusach=None, limit=50) -> list:
        """עלים שהטקסט שלהם מתחיל במילים של השאילתה (המילה האחרונה — גם
        כתחילית: "אשרי יושבי ב" מוצא את אשרי)."""
        q = fold(query)
        if not q:
            return []
        out = []
        for path, node, crumbs, _, first in self._search_index():
            if nusach and not path.startswith(nusach + "/"):
                continue
            if _first_words_match(first, q):
                out.append(self._result(path, node, crumbs, "first"))
                if len(out) >= limit:
                    break
        return out

    def search(self, query, nusach=None, limit=50) -> list:
        """חיפוש משולב: קודם התאמות כותרת, אחר-כך מילים ראשונות (בלי כפילויות)."""
        res = self.search_titles(query, nusach, limit)
        seen = {r["path"] for r in res}
        for r in self.search_first_words(query, nusach, limit):
            if len(res) >= limit:
                break
            if r["path"] not in seen:
                res.append(r)
                seen.add(r["path"])
        return res

    def shortcut_item(self, entry: dict):
        """רשומה של popular.json ⇐ קיצור לתצוגה: {label, path, title,
        breadcrumb, available[, from, to]}. ‏None אם הנתיב כבר אינו עלה."""
        leaf = self.leaf(entry.get("path"))
        if leaf is None:
            return None
        item = {"label": entry["label"], "path": entry["path"],
                "title": leaf.get("heTitle", ""),
                "breadcrumb": self.breadcrumb(entry["path"]),
                "available": not leaf.get("unavailable") and bool(leaf.get("v"))}
        for k in ("from", "to"):
            if entry.get(k):
                item[k] = entry[k]
        return item

    def find(self, query, nusach=None, all_nusachim=False, popular=None,
             aliases=None, limit=30, shortcut_limit=12) -> dict:
        """החיפוש של הממשק: ⇐ {"shortcuts": [...], "results": [...],
        "truncated": bool}.

        ‏shortcuts — קיצורים (popular.json) שהתווית שלהם (או המילים הראשונות
        של הטווח) מתאימה; ‏results — צמתים בקטלוג (כותרת / מילים ראשונות).
        שמות נרדפים (aliases.json) מרחיבים את השאילתה: "שמונה עשרה" מוצא
        "עמידה", ‏"קדיש אבלים" את "קדיש יתום". דירוג: התאמה מלאה ← תחילית ←
        מילה בכותרת שמתחילה בשאילתה ← תת-מחרוזת ← מילים ראשונות; התאמה דרך
        שם נרדף אחרי התאמה ישירה באותה דרגה. כתיב מלא/חסר (ו/י) ושגיאת אות
        אחת — רק כשאין שום התאמה אחרת.

        ‏nusach — הנוסח הנוכחי; ‏all_nusachim — גם שאר הנוסחים, הנוכחי קודם.
        בלי nusach ⇐ כל הנוסחים (בסדר הקטלוג)."""
        q = fold(query)
        empty = {"shortcuts": [], "results": [], "truncated": False}
        if not q:
            return empty
        order = [n["key"] for n in self.nusachim]
        if nusach and not all_nusachim:
            scope = [nusach]
        else:
            scope = ([nusach] if nusach else []) + [k for k in order if k != nusach]
        rank = {k: i for i, k in enumerate(scope)}
        variants = (aliases or Aliases()).expand(q)

        def better(best, tier, via):
            if best is None or _rank_key(tier, via) < _rank_key(*best):
                return (tier, via)
            return best

        def score(texts, first, prefix_of_query=False):
            """⇐ (דרגה, דרך) הטובים ביותר, או None. דרך: 0 ישירה, 1 שם נרדף,
            2 "בתוך"."""
            best = None
            for v, via, _ in variants:
                for t in texts:
                    tier = _title_tier(t, v, mid=via == 0, whole=via > 0)
                    if tier is None and prefix_of_query and via == 0 and \
                            t and v.startswith(t + " "):
                        tier = 2  # "נשמת כל חי" ⇐ הקיצור "נשמת"
                    if tier is not None:
                        best = better(best, tier, via)
                if via < 2 and _first_words_match(first, v, whole=via > 0):
                    best = better(best, 4, via)
            return best

        def fuzzy(texts, first):
            for t in texts:
                if _fuzzy_match(t, q):
                    return (5, 0)
            if first and _first_words_match(skeleton(first), skeleton(q)):
                return (5, 0)
            return None

        def hint_for(via, texts):
            if via != 2:
                return None
            name = next((d for v, w, d in variants
                         if w == 2 and any(_title_tier(t, v, whole=True) is not None
                                           for t in texts)), None)
            return f"«{name}» נאמר בתוך התפילה הזו" if name else None

        # קיצורים
        sc_cands = []
        for k in scope:
            for i, entry in enumerate((popular or {}).get("nusachim", {}).get(k, [])):
                label = fold(entry.get("label", ""))
                sc_cands.append((k, i, entry, [label], fold(entry.get("first", ""))))
        # צמתים
        node_cands = []
        for i, (path, node, crumbs, titles, first) in enumerate(self._search_index()):
            k = path.split("/", 1)[0]
            if k in rank:
                node_cands.append((k, i, (path, node, crumbs), titles, first))

        def run(cands, scorer, **kw):
            out = []
            for k, i, obj, texts, first in cands:
                s = scorer(texts, first, **kw)
                if s is not None:
                    out.append(((rank[k],) + _rank_key(*s) + (i,), k, obj, s, texts))
            return out

        sc_hits = run(sc_cands, score, prefix_of_query=True)
        node_hits = run(node_cands, score)
        if not sc_hits and not node_hits:  # סבילות לכתיב — רק כשאין כלום
            sc_hits = run(sc_cands, fuzzy)
            node_hits = run(node_cands, fuzzy)
        sc_hits.sort(key=lambda h: h[0])
        node_hits.sort(key=lambda h: h[0])

        shortcuts, whole = [], set()
        for _, k, entry, (tier, via), texts in sc_hits:
            item = self.shortcut_item(entry)
            if item is None or not item["available"]:
                continue
            item["nusach"] = k
            item["match"] = "fuzzy" if tier == 5 else "first" if tier == 4 else "label"
            if via:
                item["via"] = "alias"
            shortcuts.append(item)
            if "from" not in item:
                whole.add(item["path"])
            if len(shortcuts) >= shortcut_limit:
                break
        results = []
        for _, k, (path, node, crumbs), (tier, via), texts in node_hits:
            if path in whole:  # הקיצור כבר מוצג — אותו עלה שלם
                continue
            r = self._result(path, node, crumbs,
                             "fuzzy" if tier == 5 else "first" if tier == 4 else "title")
            r["nusach"] = k
            if via:
                r["via"] = "inside" if via == 2 else "alias"
            hint = hint_for(via, texts)
            if hint:
                r["hint"] = hint
            results.append(r)
        return {"shortcuts": shortcuts, "results": results[:limit],
                "truncated": len(results) > limit}

    # --- פנימי -------------------------------------------------------------

    def _search_index(self):
        """[(נתיב, צומת, פירורים, [כותרות מקופלות], מילים ראשונות מקופלות)]
        — כל הצמתים חוץ מהנוסחים עצמם, לפי סדר הקטלוג."""
        if self._sflat is None:
            self._sflat = [
                (p, n, c,
                 [t for t in (fold(n.get("heTitle", "")), fold(n.get("title", ""))) if t],
                 fold(n.get("first", "")) if is_leaf(n) else "")
                for p, n, c in self._index() if "/" in p]
        return self._sflat

    def _index(self):
        if self._flat is None:
            flat = []

            def visit(nodes, keys, crumbs):
                for n in nodes:
                    p = keys + [n["key"]]
                    c = crumbs + [n.get("heTitle", "")]
                    flat.append(("/".join(p), n, c))
                    if not is_leaf(n):
                        visit(n["children"], p, c)
            visit(self.nusachim, [], [])
            self._flat = flat
        return self._flat

    @staticmethod
    def _summary(keys, node) -> dict:
        out = {"key": node["key"], "path": "/".join(keys),
               "title": node.get("title", ""),
               "heTitle": node.get("heTitle", ""), "leaf": is_leaf(node)}
        if is_leaf(node):
            out["available"] = not node.get("unavailable") and bool(node.get("v"))
            if node.get("first"):
                out["first"] = node["first"]
        else:
            out["count"] = len(node["children"])
        return out

    def _result(self, path, node, crumbs, match) -> dict:
        r = self._summary(path.split("/"), node)
        r["breadcrumb"] = list(crumbs)
        r["match"] = match
        return r


_DEFAULT = None


def load_catalog(path=None) -> Catalog:
    """הקטלוג המחויב בגיט (נטען פעם אחת לכל תהליך), או קובץ אחר לפי path."""
    global _DEFAULT
    if path is not None:
        return Catalog.load(path)
    if _DEFAULT is None:
        _DEFAULT = Catalog.load()
    return _DEFAULT
