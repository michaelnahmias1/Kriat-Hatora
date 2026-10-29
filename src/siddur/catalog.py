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
"""

import json
import re
import unicodedata
from pathlib import Path

CATALOG_PATH = (Path(__file__).resolve().parent.parent.parent
                / "data" / "siddur" / "catalog.json")

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

    def search_titles(self, query, nusach=None, limit=50) -> list:
        """צמתים (בכל רמה) שהכותרת העברית או האנגלית שלהם מכילה את השאילתה.
        דירוג: התאמה מלאה ← תחילית ← תת-מחרוזת; בתוך דרגה — סדר הקטלוג."""
        q = normalize(query)
        if not q:
            return []
        ranked = []
        for order, (path, node, crumbs) in enumerate(self._index()):
            if nusach and not path.startswith(nusach + "/"):
                continue
            if path.count("/") < 1:  # הנוסח עצמו אינו תוצאה
                continue
            best = None
            for t in (node.get("heTitle", ""), node.get("title", "")):
                nt = normalize(t)
                if not nt:
                    continue
                if nt == q:
                    r = 0
                elif nt.startswith(q):
                    r = 1
                elif q in nt:
                    r = 2
                else:
                    continue
                best = r if best is None else min(best, r)
            if best is not None:
                ranked.append((best, order, self._result(path, node, crumbs,
                                                         "title")))
        ranked.sort(key=lambda x: (x[0], x[1]))
        return [r for _, _, r in ranked[:limit]]

    def search_first_words(self, query, nusach=None, limit=50) -> list:
        """עלים שהטקסט שלהם מתחיל במילים של השאילתה (המילה האחרונה — גם
        כתחילית: "אשרי יושבי ב" מוצא את אשרי)."""
        qw = normalize(query).split()
        if not qw:
            return []
        out = []
        for path, node, crumbs in self._index():
            if not is_leaf(node) or not node.get("first"):
                continue
            if nusach and not path.startswith(nusach + "/"):
                continue
            fw = normalize(node["first"]).split()
            if len(fw) < len(qw):
                continue
            if fw[:len(qw) - 1] == qw[:-1] and fw[len(qw) - 1].startswith(qw[-1]):
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

    # --- פנימי -------------------------------------------------------------

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
