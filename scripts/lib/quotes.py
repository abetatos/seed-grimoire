"""Verify that quotes in a critique actually appear in the prose they cite.

A critique finding is only trustworthy if its quoted line exists. The pipeline
counts MUST/SHOULD/CONSIDER bullets to compute a verdict (lib.verdict), so a
finding built on a hallucinated quote carries the same weight as a real one.
This module extracts the quoted spans from a bullet and checks them against a
haystack (the chapter, or a source file the critique says the chapter breaks),
so a fabricated quote can be caught deterministically instead of trusted.

It is also reused to verify the anchor quotes an update-canon summary records
(lib.lint), so a summary's "verbatim" line is really verbatim.

The matching is intentionally lenient about surface form (curly vs straight
quotes, accents kept but whitespace/dashes normalised) and strict about
content: an ellipsis (``…`` / ``...`` / ``[…]``) inside a span splits it into
fragments that must all appear IN ORDER, so "he entered … and left" cannot be
satisfied by two unrelated lines.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


# Quote pairs we recognise, per the critique format (angle «», straight "",
# curly “”, curly single ‘’). Straight single quotes are deliberately NOT a
# pair — an apostrophe would open a phantom span.
_QUOTE_PAIRS = (
    ("«", "»"),   # « »
    ("“", "”"),   # “ ”
    ("‘", "’"),   # ‘ ’
    ('"', '"'),             # " "
)

# Split a span on any ellipsis form so elided quotes match fragment-by-fragment.
_ELLIPSIS_RE = re.compile(r"\[\s*(?:\.{3}|…)\s*\]|…|\.{3}")

_WORD_RE = re.compile(r"\w+", re.UNICODE)

# Characters normalised away so surface punctuation does not defeat a match.
_DASHES = "‐‑‒–—―−"  # ‐‑‒–—―−
_QUOTE_CHARS = "«»“”‘’‚„\"'`"


@dataclass
class QuoteFinding:
    span: str
    verified: bool
    where: str | None       # which haystack key matched, or None


def _strip_emphasis(text: str) -> str:
    """Drop markdown emphasis so ``*"line"*`` yields the bare quote."""
    return re.sub(r"[*_`]", "", text)


def extract_quoted_spans(bullet: str, min_words: int = 4) -> list[str]:
    """Quoted spans in a critique bullet with at least ``min_words`` words.

    The floor keeps short ``file:line`` labels and one- or two-word tags out of
    scope — those are references, not verbatim evidence.
    """
    text = _strip_emphasis(bullet)
    spans: list[str] = []
    for open_q, close_q in _QUOTE_PAIRS:
        if open_q == close_q:
            # Symmetric delimiter: pair them left-to-right, non-greedy.
            pattern = re.compile(re.escape(open_q) + r"([^" + re.escape(open_q) + r"]+)" + re.escape(close_q))
        else:
            pattern = re.compile(re.escape(open_q) + r"([^" + re.escape(close_q) + r"]+)" + re.escape(close_q))
        for m in pattern.finditer(text):
            inner = m.group(1).strip()
            if len(_WORD_RE.findall(inner)) >= min_words:
                spans.append(inner)
    return spans


def normalize(text: str) -> str:
    """Canonical form for matching: NFKC, casefold, unified quotes/dashes,
    collapsed whitespace. Accents are preserved (they are meaning in Spanish)."""
    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()
    text = text.translate({ord(c): " " for c in _DASHES})
    text = text.translate({ord(c): " " for c in _QUOTE_CHARS})
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def verify_span(span: str, haystack_norm: str) -> bool:
    """True when ``span`` (already-raw) is found in the normalised haystack.

    An ellipsis in the span splits it into fragments that must each appear, in
    order, so an elided quote cannot be satisfied out of sequence.
    """
    fragments = [normalize(f) for f in _ELLIPSIS_RE.split(span)]
    fragments = [f for f in fragments if f]
    if not fragments:
        return False
    pos = 0
    for frag in fragments:
        idx = haystack_norm.find(frag, pos)
        if idx < 0:
            return False
        pos = idx + len(frag)
    return True


def verify_quotes(spans: list[str], haystacks: dict[str, str]) -> list[QuoteFinding]:
    """Check each span against every haystack; first match wins and is named.

    ``haystacks`` maps a label (e.g. ``"chapter"``, ``"canon/magic.md"``) to raw
    text; each is normalised once here.
    """
    norm = {key: normalize(text) for key, text in haystacks.items()}
    findings: list[QuoteFinding] = []
    for span in spans:
        where = next((key for key, hay in norm.items() if verify_span(span, hay)), None)
        findings.append(QuoteFinding(span=span, verified=where is not None, where=where))
    return findings
