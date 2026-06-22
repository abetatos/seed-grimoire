"""Helpers for the conversation-memory notes files.

These files persist the ephemeral state of a writing session to disk so
that the next session (after /clear or /compact) can pick up without
loss:

    notes/voice.md           — rolling voice / POV observations
    notes/style-rules.md     — author-declared style rules
    notes/open-questions.md  — open threads, surfaced on next session
    notes/session-handoff.md — overwritten at each close-act

Each file has an idempotent template that's only written if the file
does not exist; existing files are never overwritten by ensure().
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .paths import BookPaths


VOICE_TEMPLATE = """# Voice notes (rolling)

> Cumulative observations about how each POV sounds in prose. Updated
> by `update-canon` after each chapter. Consolidated by `close-act` at
> the end of each act.
>
> The author can edit this file freely. The agent reads it before each
> chapter and writes voice that respects what's here.

## POV: (add a section per POV character as you write)

- (no observations yet)

## Recurring patterns to watch / avoid across the book

- (no observations yet)
"""


STYLE_RULES_TEMPLATE = """# Style rules — capture buffer

> Rolling buffer for prose rules the author states in chat. The agent
> appends here; `close-act` folds these into the book's `style.md` (the
> single source of truth) and clears this file. Prescriptive until folded.
> Process rules (word count, expand) live in the skills, not here.
>
> Format: `- (YYYY-MM-DD, ch N) rule text`

## Unfolded

- (no rules declared yet)
"""


OPEN_QUESTIONS_TEMPLATE = """# Open questions (rolling)

> Threads discussed in chat that did NOT get resolved. Surface these at
> the start of the next session. The agent appends as discussions happen
> and marks items resolved (strike-through) when they close.

## Pendientes

- (none yet)

## Resueltos (archivo)

- (none yet)
"""


SESSION_HANDOFF_TEMPLATE = """# Session handoff

> Overwritten at each `close-act`. Read first thing by `resume-act`.
> Captures what the next session needs to continue without loss of
> context.

## Estado al cierre

- Capítulo escrito hasta: (—)
- Acto cerrado: (—)
- Próximo: (—)

## Voz consolidada

- (no consolidations yet)

## Hilos abiertos para la sesión siguiente

- (none yet)

## Decisiones de esta sesión

- (none yet)

## Notas para resume-act

- (none yet)
"""


TEMPLATES = {
    "voice": VOICE_TEMPLATE,
    "style_rules": STYLE_RULES_TEMPLATE,
    "open_questions": OPEN_QUESTIONS_TEMPLATE,
    "session_handoff": SESSION_HANDOFF_TEMPLATE,
}


def _paths_for(paths: BookPaths) -> dict[str, Path]:
    return {
        "voice": paths.voice_md,
        "style_rules": paths.style_rules_md,
        "open_questions": paths.open_questions_md,
        "session_handoff": paths.session_handoff_md,
    }


def ensure(paths: BookPaths) -> dict[str, bool]:
    """Create any missing notes files with their template.

    Returns a dict {key: created} indicating which files were newly
    created in this call. Existing files are never overwritten.
    """
    paths.notes_dir.mkdir(parents=True, exist_ok=True)
    created: dict[str, bool] = {}
    file_map = _paths_for(paths)
    for key, p in file_map.items():
        if p.exists():
            created[key] = False
        else:
            p.write_text(TEMPLATES[key], encoding="utf-8")
            created[key] = True
    return created


def read_all(paths: BookPaths) -> dict[str, str]:
    """Read the current content of all notes files (empty string if absent)."""
    out: dict[str, str] = {}
    for key, p in _paths_for(paths).items():
        out[key] = p.read_text(encoding="utf-8") if p.exists() else ""
    return out


def today_stamp() -> str:
    """ISO date for entries that want a date marker."""
    return date.today().isoformat()
