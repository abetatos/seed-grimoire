"""Parse setup.md for programmatic field access.

The setup.md format is human-edited Markdown with fixed level-2 sections
(## Identity, ## Magic system, etc.). We don't enforce schema rigidly —
we just extract sections by header for the helpers that need them
(e.g., target word count, language, chapter count).

Lightweight, lenient. If a section is missing, callers get "".
"""

from __future__ import annotations

import re
from pathlib import Path


SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
FIELD_LINE_RE = re.compile(r"^[-*]\s*\*\*(?P<key>[^*]+?):\*\*\s*(?P<val>.+?)\s*$", re.MULTILINE)
# also catch "- Key: value" without bold
LOOSE_FIELD_RE = re.compile(r"^[-*]\s*(?P<key>[^:\n]{1,60}?):\s*(?P<val>.+?)\s*$", re.MULTILINE)


def load(setup_path: Path) -> str:
    if not setup_path.exists():
        return ""
    return setup_path.read_text(encoding="utf-8")


def sections(text: str) -> dict[str, str]:
    """Return {section_title_lower: section_body_text}."""
    out: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = m.group(1).strip().lower()
        out[title] = text[start:end].strip()
    return out


def get_section(text: str, title_substr: str) -> str:
    """Return the body of the first section whose title contains title_substr."""
    secs = sections(text)
    sub = title_substr.lower()
    for k, v in secs.items():
        if sub in k:
            return v
    return ""


def fields(section_body: str) -> dict[str, str]:
    """Extract `**Key:** value` and `- Key: value` lines from a section."""
    out: dict[str, str] = {}
    for m in FIELD_LINE_RE.finditer(section_body):
        key = m.group("key").strip().lower()
        out[key] = m.group("val").strip()
    for m in LOOSE_FIELD_RE.finditer(section_body):
        key = m.group("key").strip().lower()
        if key not in out:
            out[key] = m.group("val").strip()
    return out


def _label_value_re(label_substr: str, value_re: str) -> re.Pattern[str]:
    """Build a regex matching `label: value` only when the label STARTS a line.

    The label may be preceded by a Markdown list bullet and/or bold markers,
    and the separator must be a colon. Anchoring to the line start (and using
    a colon, never a hyphen) prevents a label substring buried mid-line — e.g.
    the "writer" inside "**(writer-only):**" — from being mistaken for the
    field, which would otherwise leak writer-only prose into the value.
    """
    return re.compile(
        r"^[ \t]*(?:[-*+]\s+)?(?:\*\*)?"
        + re.escape(label_substr)
        + r"(?:\*\*)?\s*:\s*(?:\*\*)?\s*"
        + value_re,
        re.IGNORECASE | re.MULTILINE,
    )


def find_int(text: str, label_substr: str) -> int | None:
    """Find the first integer value associated with a label like 'Capítulos:'.

    Searches case-insensitively, label must start a line. Returns None if not found.
    """
    m = _label_value_re(label_substr, r"([0-9]+)").search(text)
    return int(m.group(1)) if m else None


def find_str(text: str, label_substr: str) -> str:
    """Find the value associated with a label (label must start a line)."""
    m = _label_value_re(label_substr, r"(.+)").search(text)
    if not m:
        return ""
    val = m.group(1).strip()
    # Strip trailing bold/italic markers
    val = re.sub(r"\*+\s*$", "", val).rstrip()
    return val


def book_title(text: str) -> str:
    # H1 line
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip().lstrip("Book setup — ").lstrip("Book setup -").strip()
    return ""


def num_chapters(text: str) -> int | None:
    return (
        find_int(text, "Capítulos")
        or find_int(text, "Chapters")
        or find_int(text, "Number of chapters")
    )


def language(text: str) -> str:
    return (
        find_str(text, "Idioma de escritura")
        or find_str(text, "Language")
        or "es"
    )


def words_per_chapter_range(text: str) -> tuple[int, int]:
    """Parse a target range like '8000-12000' or '8000 a 12000'."""
    val = (
        find_str(text, "Palabras por capítulo")
        or find_str(text, "Words per chapter")
        or ""
    )
    m = re.search(r"(\d[\d,\.]*)\s*[-–a]\s*(\d[\d,\.]*)", val)
    if not m:
        # single number → treat as midpoint with ±20%
        single = re.search(r"(\d[\d,\.]*)", val)
        if single:
            n = int(single.group(1).replace(",", "").replace(".", ""))
            return (int(n * 0.85), int(n * 1.15))
        return (8000, 12000)
    lo = int(m.group(1).replace(",", "").replace(".", ""))
    hi = int(m.group(2).replace(",", "").replace(".", ""))
    return (lo, hi)
