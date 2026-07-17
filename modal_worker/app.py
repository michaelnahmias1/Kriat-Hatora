# -*- coding: utf-8 -*-
"""ה-worker בענן (Modal) — מסלול ה-AI ההיברידי בתוך האפליקציה, בלי Colab.

עטיפה בלבד: הצינור עצמו הוא `src/aligner/hybrid.py::run_hybrid` הקיים,
ללא שום שינוי — אותה משיכת טקסט מ-Sefaria (API), אותו תמלול-עוגנים,
אותו יישור ממושכן ואותו VAD שעובדים היום ב-Colab. רק סביבת הריצה מתחלפת:
GPU T4 לפי-שימוש במקום notebook.

פריסה (חד-פעמית, ראה README):
    pip install modal
    modal setup
    modal secret create kriat-hatora KRIAT_HATORA_TOKEN=<מחרוזת-אקראית>
    modal deploy modal_worker/app.py
ואז מדביקים את ה-URL וה-token בקבועים שבראש index.html.

הפרוטוקול מול הדפדפן (עיבוד אורך דקות — לא מחזיקים בקשה פתוחה מהטלפון):
    POST /submit  (multipart: file + book/chapter/טווח + token) → {"call_id"}
    GET  /status?call_id=…                                      → 202 בזמן ריצה,
                                                                  {"srt","report"} בסיום.
"""

import os
import re
import sys
from pathlib import Path

import modal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from params import parse_params  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent

app = modal.App("kriat-hatora")

# שמות המודלים אינם מובטחים מהזיכרון (כלל PLAN.md) — אותה רשימת מועמדים
# כמו src/aligner/asr.py; בבניית ה-image מורידים את הראשון שמצליח, ובזמן
# ריצה asr.py ממילא יודע ליפול למועמד הבא.
_ASR_CANDIDATES = [
    "ivrit-ai/whisper-large-v3-turbo-ct2",
    "ivrit-ai/whisper-large-v3-ct2",
    "ivrit-ai/faster-whisper-v2-d4",
]

MAX_UPLOAD_MB = 300  # ~5 שעות אודיו ב-m4a — הרבה מעבר לכל קריאה אמיתית


def _download_models():
    """רץ בזמן בניית ה-image: אופה את המודלים בפנים נגד cold-start ארוך."""
    from huggingface_hub import snapshot_download
    for name in _ASR_CANDIDATES:
        try:
            snapshot_download(name)
            print(f"✅ מודל תמלול נאפה ב-image: {name}")
            break
        except Exception as e:
            print(f"⚠️ {name} לא ירד ({type(e).__name__}) — מנסה את הבא")
    import torchaudio
    torchaudio.pipelines.MMS_FA.get_model()  # משקולות המיישר → TORCH_HOME
    print("✅ מודל MMS_FA נאפה ב-image")


# בסיס CUDA עם cuDNN מערכתי — כמו בסביבת Colab שבה הצינור כבר עובד
# (faster-whisper/ctranslate2 צריכים cuDNN זמין ברמת המערכת).
_gpu_image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04",
                              add_python="3.11")
    .apt_install("ffmpeg")
    .pip_install("torch", "torchaudio", "faster-whisper", "silero-vad",
                 "uroman", "requests")
    .env({"HF_HOME": "/models/hf", "TORCH_HOME": "/models/torch"})
    # params חייב להיכנס ל-image *לפני* run_function ועם copy=True: פונקציית
    # ה-build מייבאת מחדש את app.py, וזה מריץ את `from params import parse_params`
    # ברמת המודול — בלי זה הבנייה נופלת ב-ModuleNotFoundError: No module named 'params'.
    .add_local_python_source("params", copy=True)
    .run_function(_download_models)
    .add_local_dir(str(_REPO_ROOT / "src"), remote_path="/root/src")
)

_web_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi[standard]")
    .add_local_python_source("params")
)


@app.function(image=_gpu_image, gpu="T4", timeout=30 * 60)
def process(audio_bytes: bytes, filename: str, params: dict) -> dict:
    """הקלטה + פרמטרים → SRT + דוח איכות, דרך run_hybrid הקיים ללא שינוי."""
    import tempfile

    sys.path.insert(0, "/root/src")
    from aligner.hybrid import run_hybrid

    suffix = Path(filename or "").suffix
    if not re.fullmatch(r"\.[A-Za-z0-9]{1,8}", suffix or ""):
        suffix = ".m4a"  # ffmpeg מזהה את הפורמט האמיתי מהתוכן ממילא

    with tempfile.TemporaryDirectory() as td:
        audio_path = Path(td) / f"recording{suffix}"
        audio_path.write_bytes(audio_bytes)
        out_srt = Path(td) / "out.srt"

        run_hybrid(book=params["book"],
                   chapter=params["chapter"],
                   audio_path=str(audio_path),
                   out_srt_path=str(out_srt),
                   verse_start=params["verse_start"],
                   chapter_end=params["chapter_end"],
                   verse_end=params["verse_end"],
                   max_words=params["max_words"],
                   work_dir=td)

        srt = out_srt.read_text(encoding="utf-8-sig")
        report_path = out_srt.with_suffix(".report.txt")
        report = (report_path.read_text(encoding="utf-8")
                  if report_path.exists() else "")
    return {"srt": srt, "report": report}


@app.function(image=_web_image,
              secrets=[modal.Secret.from_name("kriat-hatora")])
@modal.asgi_app()
def web():
    import secrets as pysecrets

    from fastapi import FastAPI, File, Form, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    # הגישה מוגנת ב-token; CORS פתוח כדי שגם פריסות preview של Vercel יעבדו
    api.add_middleware(CORSMiddleware, allow_origins=["*"],
                       allow_methods=["*"], allow_headers=["*"])

    def _token_ok(token: str) -> bool:
        expected = os.environ.get("KRIAT_HATORA_TOKEN", "")
        return bool(expected) and pysecrets.compare_digest(token or "", expected)

    @api.post("/submit")
    async def submit(file: UploadFile = File(...),
                     token: str = Form(""),
                     book: str = Form(""),
                     chapter: str = Form(""),
                     verse_start: str = Form(""),
                     verse_end: str = Form(""),
                     chapter_end: str = Form(""),
                     max_words: str = Form("")):
        if not _token_ok(token):
            return JSONResponse({"error": "גישה נדחתה — ה-token שגוי או שה-secret "
                                          "‏kriat-hatora לא הוגדר ב-Modal"},
                                status_code=401)
        try:
            params = parse_params({
                "book": book, "chapter": chapter,
                "verse_start": verse_start, "verse_end": verse_end,
                "chapter_end": chapter_end, "max_words": max_words,
            })
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        audio_bytes = await file.read()
        if not audio_bytes:
            return JSONResponse({"error": "קובץ ההקלטה ריק"}, status_code=400)
        if len(audio_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
            return JSONResponse(
                {"error": f"הקובץ גדול מ-{MAX_UPLOAD_MB}MB — פצל את ההקלטה"},
                status_code=413)

        call = process.spawn(audio_bytes, file.filename or "", params)
        return {"call_id": call.object_id}

    @api.get("/status")
    async def status(call_id: str = ""):
        if not call_id:
            return JSONResponse({"error": "חסר call_id"}, status_code=400)
        try:
            call = modal.FunctionCall.from_id(call_id)
        except Exception:
            return JSONResponse({"error": "call_id לא מוכר"}, status_code=404)
        try:
            result = await call.get.aio(timeout=0)
        except TimeoutError:
            return JSONResponse({"status": "running"}, status_code=202)
        except Exception as e:
            return JSONResponse(
                {"error": f"העיבוד נכשל ({type(e).__name__}): {e}"},
                status_code=500)
        return result

    return api
