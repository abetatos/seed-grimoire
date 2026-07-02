"""Shared parsing helpers for the never-compress files (seeds.md, shadow.md).

These were duplicated, near-identically, in ``seeds.py`` and ``shadows.py``.
A bug fixed in one copy silently survived in the other (the bare-digit payoff
gotcha, en-dash handling, bullet markers). They live here now so there is one
place to fix.

Parsing philosophy: **loud, not silent.** The old copies did
``tok.strip("ch ")`` + ``tok.isdigit()`` and dropped anything malformed with no
trace, so a mistyped ``Echo in: 12a`` silently removed the seed from that
chapter's envelope. Here, malformed tokens are collected as *warnings* the
caller can surface (``lint_book.py`` turns them into errors) while parsing still
succeeds — context assembly must never crash mid-write.
"""

from __future__ import annotations

import re


# A wrapped field value (**Key:** value, possibly spanning continuation lines)
# ends at the next bold field key, an H2 heading, a horizontal rule (`---`), a
# blockquote line (seeds.md uses `> ## ...` dividers between seed groups), or
# EOF. Without the rule/blockquote terminators the LAST field before a divider
# (typically **Status:**) silently swallows the divider text — which is how a
# status parsed as "planned --- > ## Hebra emocional…" slipped in. Requires the
# consuming regex to use re.DOTALL | re.MULTILINE.
FIELD_VALUE_END = (
    r"(?=\n\*\*[^*\n]+?:\*\*"   # next bold field key
    r"|\n##\s"                  # next H2 heading (e.g. ## SEED:)
    r"|\n[ \t]*-{3,}[ \t]*$"    # horizontal rule ---
    r"|\n[ \t]*>"               # blockquote divider
    r"|\Z)"
)


# A schedule field ("Plant in:", "Echo in:", "Payoff in:", "Confirm in:") may
# hold: a bare int, a comma list, a chapter token ("ch 12" / "cap 12" /
# "capítulo 12" / "chapter 12"), or a this-book chapter followed by a
# parenthetical / arrow annotation ("22 (el clímax lo pone...) → eco"). It may
# also be a CROSS-BOOK deferral ("Libro II", "Libros II-III", "Book III"),
# which must contribute NO chapter to this book's schedule and raise NO warning.
_EMPTY_TOKENS = {"—", "-", "–", "none", "null", "n/a", ""}
_CROSS_BOOK_RE = re.compile(r"\b(?:libros?|books?)\b", re.IGNORECASE)
# Everything from the first annotation delimiter onward is commentary, not
# schedule. Cutting here first means a comma *inside* a parenthetical
# ("(...Bruno, sobre Mauro)") never gets mistaken for a list separator.
_ANNOTATION_CUT_RE = re.compile(r"[(→—;]")  # '(', '→', '—', ';'
# Optional chapter-word prefix on a single token: ch / cap / capítulo / chapter.
_CH_PREFIX_RE = re.compile(r"(?i)^(?:cap[íi]tulos?|caps?|chapters?|chs?|ch)\.?\s*")


def parse_chapter_list(raw: str) -> tuple[list[int], list[str]]:
    """Parse a schedule field into (chapter_numbers, warnings).

    - Empty / dash / none → ([], []).
    - Cross-book deferral (contains "libro"/"book") → ([], []) — not this book.
    - Trailing annotation after '(', '→', '—' or ';' is dropped, no warning.
    - Each remaining token is an int, optionally prefixed by a chapter word.
    - Any token that is neither empty nor an int is returned as a warning
      string; parsing continues (never raises).
    """
    warnings: list[str] = []
    if raw is None:
        return [], warnings
    value = raw.strip()
    if value.lower() in _EMPTY_TOKENS:
        return [], warnings
    if _CROSS_BOOK_RE.search(value):
        return [], warnings

    head = _ANNOTATION_CUT_RE.split(value, maxsplit=1)[0]
    nums: list[int] = []
    for tok in re.split(r"[,\s]+", head.strip()):
        if not tok:
            continue
        stripped = _CH_PREFIX_RE.sub("", tok).strip()
        if not stripped:
            continue  # a bare "ch"/"cap" prefix word from "ch 12"
        if stripped.isdigit():
            nums.append(int(stripped))
        else:
            warnings.append(
                f"unparseable chapter token {tok!r} in field value {value!r}"
            )
    return nums, warnings


def parse_single_chapter(raw: str) -> tuple[int | None, list[str]]:
    """First chapter of a schedule field, plus warnings. Extra numbers on a
    single-chapter field (Plant/Payoff) are kept as warnings so a typo like
    ``Plant in: 3 4`` is surfaced rather than silently taking 3."""
    nums, warnings = parse_chapter_list(raw)
    if len(nums) > 1:
        warnings.append(
            f"expected a single chapter but found {nums} in {raw.strip()!r}"
        )
    return (nums[0] if nums else None), warnings


def parse_id_list(raw: str) -> list[str]:
    """Comma/space separated ids (e.g. Revealed-by seed ids), backtick-stripped."""
    if not raw or raw.strip().lower() in _EMPTY_TOKENS:
        return []
    out: list[str] = []
    for tok in re.split(r"[,\s]+", raw):
        tok = tok.strip().strip("`").strip()
        if tok:
            out.append(tok)
    return out


def parse_touch_log(body: str) -> list[str]:
    """Strip list markers from a Realized:/Surfaced: block body, one item per
    line, order preserved. Accepts ``-``, ``*`` and ``+`` bullets."""
    items: list[str] = []
    for line in body.splitlines():
        line = re.sub(r"^[ \t]*[-*+][ \t]*", "", line.strip())
        if line:
            items.append(line)
    return items


# expand-chapter wraps inserted prose in visible banner lines. Stripping them
# (keeping the prose between) is needed in three places — the continuity seam,
# the critic's clean copy, and word counting — so the regex lives here.
_EXPAND_MARKER_RE = re.compile(
    r"^.*(?:INICIO EXPAND|FIN EXPAND|▼▼▼|▲▲▲).*$\n?",
    re.MULTILINE,
)


def strip_expand_markers(text: str) -> str:
    """Remove expand-chapter banner lines, keeping the prose between them."""
    return _EXPAND_MARKER_RE.sub("", text)
