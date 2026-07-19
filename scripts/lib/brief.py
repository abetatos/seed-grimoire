"""The per-chapter brief — plan-chapter's single hand-off to the writer.

Movement 2 of IMPROVEMENT-PLAN collapses three per-chapter / rolling note files
into one fixed-shape file, ``notes/brief-chNN.md``:

    ## Decisiones                        — closed creative forks (was decisions-chNN.md)
    ## Estado que no se puede contradecir — the checkable state sheet (was continuity-chNN.md)
    ## Arrastre                          — carry threads for THIS chapter, hard-close
                                           (replaces the per-chapter role of open-questions.md)

The three sections live in ONE file but load at DIFFERENT bundle positions:
``## Decisiones`` at the top as binding law, the state sheet late (next to the
beat sheet, where continuity errors are born), ``## Arrastre`` only in the
plan / critique phases. Placement is the whole reason for the merge, so
``context.py`` splits the file back into sections by header via ``split_brief``.

The brief is **mandatory and committed** — the "optional file that is always
written" smell named in the plan is a mandatory file in disguise. Sections are
always present; an empty ``## Arrastre`` reads ``- (ninguno)`` and is dropped
from the bundle like any other placeholder.
"""

from __future__ import annotations

import re

# Canonical section titles (exact header text in the file, Spanish per project
# convention). context.py and plan-chapter both key off these constants.
SEC_DECISIONS = "Decisiones"
SEC_STATE = "Estado que no se puede contradecir"
SEC_ARRASTRE = "Arrastre"

# Placeholder markers for an empty carry buffer — treated as "no content" so an
# empty Arrastre never dilutes the bundle. Matched case-insensitively.
ARRASTRE_EMPTY = ("(ninguno)", "(none")

_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def split_brief(text: str) -> dict[str, str]:
    """Split a brief into ``{section-title: body}`` with bodies stripped.

    Keys are the exact ``## `` header texts. Robust to extra sections and to a
    missing file (empty text → empty dict).
    """
    out: dict[str, str] = {}
    matches = list(_HEADER_RE.finditer(text or ""))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[title] = text[start:end].strip()
    return out


def section(sections: dict[str, str], title: str) -> str:
    """The body of one section (``""`` if absent), from a ``split_brief`` dict."""
    return sections.get(title, "").strip()


def template(n: int) -> str:
    """The idempotent scaffold plan-chapter fills. Same shape every chapter."""
    return f"""# Brief — chapter {n:02d}

> plan-chapter's single hand-off to write-chapter. **Mandatory, committed.**
> Three fixed sections, always present. `context.py` splits them to their bundle
> positions (Decisiones at the top as binding law; the state sheet and Arrastre
> late). An empty Arrastre reads `- (ninguno)`.

## {SEC_DECISIONS}

<closed creative forks from the gate — BINDING. write-chapter honors these and a
plan regeneration cannot silently overwrite them.>

## {SEC_STATE}

<the checkable state sheet: who is on stage and in what state, what the POV knows
/ does not know yet, objects in play, the seed-calendar slice — facts the prose
must not contradict.>

## {SEC_ARRASTRE}

- (ninguno)
"""
