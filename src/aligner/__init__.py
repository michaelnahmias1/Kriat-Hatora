# -*- coding: utf-8 -*-
"""צינור העיבוד: טקסט → חיתוך → יישור → SRT. ראה pipeline.py."""

from .pipeline import build_ref, build_srt, run, verses_to_segments

__all__ = ["build_ref", "build_srt", "run", "verses_to_segments"]
