# -*- coding: utf-8 -*-
"""חיתוך טקסט למקטעי כתוביות: פסוקי תנ״ך לפי טעמי המקרא (PLAN.md), וטקסט
לא-מוטעם — תפילה, פיוט, טקסט חופשי — לפי פיסוק (prose.py, PLAN_TEFILA.md)."""

from .chunker import (
    build_segment,
    clean_sefaria_text,
    is_ketiv,
    letters_only,
    rank_table_for,
    regroup_words,
    segments_for_pipeline,
    split_unit,
    to_alignment_words,
    tokenize,
    verse_to_segments,
    word_accents,
    word_rank,
)
from .prose import prose_lines, prose_segments, prose_tokens, split_prose
from . import books
from . import taamim

__all__ = [
    "books",
    "build_segment",
    "clean_sefaria_text",
    "is_ketiv",
    "letters_only",
    "prose_lines",
    "prose_segments",
    "prose_tokens",
    "rank_table_for",
    "regroup_words",
    "segments_for_pipeline",
    "split_prose",
    "split_unit",
    "taamim",
    "to_alignment_words",
    "tokenize",
    "verse_to_segments",
    "word_accents",
    "word_rank",
]
