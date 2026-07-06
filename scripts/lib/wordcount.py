"""Prose word counting — density denominators ONLY.

Deliberately NO target validation: generated chapter length is never measured
back to the model (a visible count vs. target breeds compensation — padding
this chapter or "write more generously" leaking into the next). The word range
in setup.md is a planning-time objective for outline sizing; nothing in the
pipeline checks prose against it. `count_words` exists solely so
lib.prose_lint can normalize tic counts per 1000 words."""

from __future__ import annotations

import re

from .parsing import strip_expand_markers

_WORD_RE = re.compile(r"\b[\w'’-]+\b", re.UNICODE)


def prose_text(text: str) -> str:
    """Reduce a chapter to prose only: strip expand-chapter banner lines, fenced
    code blocks and Markdown headers. One helper so word counting and the prose
    auditor (lib.prose_lint) strip the same scaffolding instead of each
    re-deriving it."""
    text = strip_expand_markers(text)
    # Remove fenced code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove headers but keep their text on subsequent line
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    return text


def count_words(text: str) -> int:
    """Count words in prose only (the EXPAND scaffolding otherwise inflates it by
    ~10 words per inserted zone)."""
    return len(_WORD_RE.findall(prose_text(text)))
