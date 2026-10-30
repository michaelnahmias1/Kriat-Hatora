# -*- coding: utf-8 -*-
"""בדיקות ל-POST /identify ב-worker (PLAN_TEFILA.md 4.5.1) — בלי modal ובלי fastapi.

modal_worker/app.py נטען עם מודולים מזויפים של modal ו-fastapi: הדקורטורים
רושמים את הפונקציות והנתיבים, ‏spawn נרשם במקום לרוץ בענן. כך נבדקים הניתוב,
ה-token, הוולידציה, ושהנתיבים הקיימים לא השתנו (תאימות לאחור — עיקרון 3).
"""

import asyncio
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# --- modal מזויף ----------------------------------------------------------------

class _Image:
    calls = []

    def __getattr__(self, name):
        def method(*a, **kw):
            _Image.calls.append((name, a, kw))
            return self
        return method


class _Function:
    def __init__(self, fn, kw):
        self.fn, self.kw, self.spawned = fn, kw, []

    def spawn(self, *args):
        self.spawned.append(args)
        return types.SimpleNamespace(object_id=f"fc-{self.fn.__name__}-{len(self.spawned)}")


class _App:
    def __init__(self, name):
        self.functions = {}

    def function(self, **kw):
        def deco(fn):
            f = _Function(fn, kw)
            self.functions[fn.__name__] = f
            return f
        return deco


def _fake_modal():
    m = types.ModuleType("modal")
    m.App = _App
    m.Image = types.SimpleNamespace(from_registry=lambda *a, **k: _Image(),
                                    debian_slim=lambda *a, **k: _Image())
    m.Secret = types.SimpleNamespace(from_name=lambda n: n)
    m.asgi_app = lambda: (lambda fn: fn)
    m.FunctionCall = types.SimpleNamespace(from_id=lambda i: None)
    return m


# --- fastapi מזויף ---------------------------------------------------------------

class _FastAPI:
    def __init__(self, **kw):
        self.routes = {}

    def add_middleware(self, *a, **k):
        pass

    def _route(self, method, path):
        def deco(fn):
            self.routes[(method, path)] = fn
            return fn
        return deco

    def post(self, path):
        return self._route("POST", path)

    def get(self, path):
        return self._route("GET", path)


class _JSONResponse:
    def __init__(self, content, status_code=200):
        self.content, self.status_code = content, status_code


def _fake_fastapi():
    fa = types.ModuleType("fastapi")
    fa.FastAPI = _FastAPI
    fa.File = lambda default=None: None
    fa.Form = lambda default="": default
    fa.UploadFile = object
    mw = types.ModuleType("fastapi.middleware")
    cors = types.ModuleType("fastapi.middleware.cors")
    cors.CORSMiddleware = object
    resp = types.ModuleType("fastapi.responses")
    resp.JSONResponse = _JSONResponse
    return {"fastapi": fa, "fastapi.middleware": mw,
            "fastapi.middleware.cors": cors, "fastapi.responses": resp}


class _Upload:
    def __init__(self, data: bytes, filename="rec.m4a"):
        self.data, self.filename = data, filename

    async def read(self):
        return self.data


def load_app():
    """app.py עם modal/fastapi מזויפים (הם נשארים ב-sys.modules עד הניקוי —
    ‏web() מייבא את fastapi רק כשהוא נקרא)."""
    spec = importlib.util.spec_from_file_location(
        "kh_modal_app", ROOT / "modal_worker" / "app.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    return app


TOKEN = "secret-token"


class TestIdentifyRoute(unittest.TestCase):

    def setUp(self):
        _Image.calls = []
        fakes = mock.patch.dict(sys.modules, {"modal": _fake_modal(), **_fake_fastapi()})
        fakes.start()
        self.addCleanup(fakes.stop)
        self.app = load_app()
        env = mock.patch.dict("os.environ", {"KRIAT_HATORA_TOKEN": TOKEN})
        env.start()
        self.addCleanup(env.stop)
        self.api = self.app.web.fn()
        self.routes = self.api.routes

    def call(self, method, path, **kw):
        return asyncio.run(self.routes[(method, path)](**kw))

    def test_routes_old_and_new(self):
        """הנתיבים הקיימים במקומם, ונוסף רק POST /identify."""
        self.assertEqual(set(self.routes), {("POST", "/submit"), ("GET", "/status"),
                                            ("POST", "/cancel"), ("POST", "/identify")})

    def test_identify_spawns_background_job(self):
        got = self.call("POST", "/identify", file=_Upload(b"audio", "nishmat.m4a"),
                        token=TOKEN, nusach="sefard")
        self.assertEqual(got, {"call_id": "fc-identify_job-1"})
        job = self.app.app.functions["identify_job"]
        self.assertEqual(job.spawned, [(b"audio", "nishmat.m4a",
                                        {"nusach": "sefard", "max_sec": 600})])
        self.assertEqual(self.app.app.functions["process"].spawned, [])

    def test_identify_without_nusach(self):
        self.call("POST", "/identify", file=_Upload(b"a"), token=TOKEN, nusach="")
        args = self.app.app.functions["identify_job"].spawned[0]
        self.assertIsNone(args[2]["nusach"])

    def test_identify_rejects(self):
        r = self.call("POST", "/identify", file=_Upload(b"a"), token="wrong", nusach="")
        self.assertEqual(r.status_code, 401)
        r = self.call("POST", "/identify", file=_Upload(b"a"), token=TOKEN, nusach="<script>")
        self.assertEqual(r.status_code, 400)
        self.assertIn("נוסח", r.content["error"])
        r = self.call("POST", "/identify", file=_Upload(b""), token=TOKEN, nusach="")
        self.assertEqual(r.status_code, 400)
        with mock.patch.object(self.app, "MAX_UPLOAD_MB", 0):
            r = self.call("POST", "/identify", file=_Upload(b"abc"), token=TOKEN, nusach="")
        self.assertEqual(r.status_code, 413)
        self.assertEqual(self.app.app.functions["identify_job"].spawned, [])

    def test_submit_unchanged(self):
        """‏/submit עדיין שולח ל-process (ולא לזיהוי), עם אותם פרמטרים."""
        form = dict(book="בראשית", chapter="1", verse_start="", verse_end="",
                    chapter_end="", max_words="", splits="", push_sub="", source="",
                    units="", title="", performance="", profile="")
        got = self.call("POST", "/submit", file=_Upload(b"x"), token=TOKEN, **form)
        self.assertEqual(got, {"call_id": "fc-process-1"})
        self.assertEqual(self.app.app.functions["identify_job"].spawned, [])

    def test_identify_job_is_gpu_function_with_timeout(self):
        kw = self.app.app.functions["identify_job"].kw
        self.assertEqual(kw["gpu"], "T4")
        self.assertEqual(kw["timeout"], self.app.IDENTIFY_TIMEOUT_SEC)
        self.assertIs(kw["image"], self.app._gpu_image)

    def test_index_baked_where_identify_looks(self):
        """הקובץ שנאפה ב-image נמצא בדיוק במקום ש-identify.py מחפש בקונטיינר:
        src/ ב-/root/src ⇐ האינדקס ב-/root/data/siddur."""
        from siddur import identify as idm
        files = [(a, kw) for name, a, kw in _Image.calls if name == "add_local_file"]
        self.assertEqual(len(files), 1)
        (local, ), kw = files[0][0][:1], files[0][1]
        self.assertTrue(Path(local).exists(), local)
        self.assertEqual(Path(local).resolve(), idm.INDEX_PATH.resolve())
        remote = kw["remote_path"]
        rel = idm.INDEX_PATH.resolve().relative_to(ROOT)
        self.assertEqual(remote, "/root/" + rel.as_posix())
        dirs = [(a, kw) for name, a, kw in _Image.calls if name == "add_local_dir"]
        self.assertTrue(any(kw.get("remote_path") == "/root/src" for _, kw in dirs))

    def test_identify_job_runs_run_identify(self):
        seen = {}

        def fake_run_identify(**kw):
            seen.update(kw)
            seen["bytes"] = Path(kw["audio_path"]).read_bytes()
            return {"kind": "identify", "candidates": []}

        from siddur import identify as idm
        with mock.patch.object(idm, "run_identify", side_effect=fake_run_identify):
            out = self.app.app.functions["identify_job"].fn(
                b"RIFF", "rec.wav", {"nusach": "ashkenaz", "max_sec": 600})
        self.assertEqual(out, {"kind": "identify", "candidates": []})
        self.assertEqual(seen["bytes"], b"RIFF")
        self.assertTrue(seen["audio_path"].endswith("recording.wav"))
        self.assertEqual((seen["nusach"], seen["vad_filter"], seen["max_sec"]),
                         ("ashkenaz", False, 600))

    def test_identify_job_bad_suffix(self):
        seen = {}
        from siddur import identify as idm
        with mock.patch.object(idm, "run_identify",
                               side_effect=lambda **kw: seen.update(kw) or {}):
            self.app.app.functions["identify_job"].fn(b"x", "../../evil.sh;rm", {})
        self.assertTrue(seen["audio_path"].endswith("recording.m4a"))
        self.assertTrue(Path(seen["audio_path"]).parent.as_posix().startswith(
            Path(tempfile.gettempdir()).as_posix()))


class TestIdentifyParams(unittest.TestCase):

    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "modal_params_identify", ROOT / "modal_worker" / "params.py")
        self.params = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.params)

    def test_parse(self):
        p = self.params
        self.assertEqual(p.parse_identify_params({}), {"nusach": None, "max_sec": 600})
        self.assertEqual(p.parse_identify_params({"nusach": " edot-hamizrach "})["nusach"],
                         "edot-hamizrach")
        for bad in ("Sefard", "ספרד", "a" * 41, "x/y", "-a"):
            with self.assertRaises(ValueError):
                p.parse_identify_params({"nusach": bad})

    def test_identify_call_matches_run_identify_signature(self):
        import inspect
        from siddur.identify import run_identify
        kw = self.params.identify_call({"nusach": "sefard", "max_sec": 600}, "/a.m4a", "/w")
        self.assertEqual(kw, {"audio_path": "/a.m4a", "work_dir": "/w", "nusach": "sefard",
                              "vad_filter": False, "max_sec": 600})
        inspect.signature(run_identify).bind(**kw)   # כל המפתחות קיימים בפונקציה


if __name__ == "__main__":
    unittest.main()
