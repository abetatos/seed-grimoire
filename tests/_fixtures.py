"""Build a minimal-but-valid book on disk for context/lint tests."""

from __future__ import annotations

from pathlib import Path

from lib.paths import BookPaths


SETUP = """# Book setup — Fixture

## Identity
- **Idioma de escritura:** es
- **Capítulos:** 7
- **Palabras por capítulo:** 8000-12000

## Premise
Un mundo donde el color se drena.

## POV
Close third, past.
"""

OUTLINE = """# Outline — Fixture

## Capítulo 1 — Apertura
- Beat: se presenta a Bruno en el taller.

## Capítulo 2 — Vuelta de tuerca
- Beat: aparece el tutor.

## Capítulo 3 — El pozo
- Beat: Bruno ve el pozo.
"""

SEEDS = """# Seeds — Fixture

## SEED: el-pozo
**Detail:** un pozo que pide
**Real meaning:** el sumidero
**Plant in:** 1
**Echo in:** 2
**Payoff in:** 3
**How to plant:** de pasada
**How to pay off:** sin explicar
**Status:** planned

## SEED: cross-book
**Detail:** el padre
**Plant in:** 1
**Payoff in:** Libro II
**Status:** planned
"""

SHADOW = """# Shadow — Fixture

## Overview
La verdad oculta del mundo.

## Master truths

## SHADOW-TRUTH: t-pozo
**Truth:** el pozo drena a la gente
**Revealed-by:** el-pozo
**Reveal cap:** suspected
**Status:** hidden

## Acto 1 (capítulos 1-7)
Verdad operativa del acto.

### Capítulo 1
- Bruno no sabe nada aún.
"""

ARCS = """# Arcs — Fixture

## Bruno
- Waypoint ch1: inocente.
"""

CHARACTERS = """# Characters — Fixture

## Bruno (principal)
Trece años, aprendiz.

## Secundarios

### Ío, la vecina «la callada»
Aparece de refilón.

### Mauro, el verdugo
Un secundario que no sale este capítulo.
"""


def make_book(root: Path, *, chapters_written: int = 0) -> BookPaths:
    series = root / "output" / "fixture"
    book = series / "book-01"
    paths = BookPaths(series_root=series, book_root=book)
    paths.ensure_dirs()
    paths.setup_md.write_text(SETUP, encoding="utf-8")
    paths.outline_md.write_text(OUTLINE, encoding="utf-8")
    paths.seeds_md.write_text(SEEDS, encoding="utf-8")
    paths.shadow_md.write_text(SHADOW, encoding="utf-8")
    paths.arcs_md.write_text(ARCS, encoding="utf-8")
    paths.canon_file("characters").write_text(CHARACTERS, encoding="utf-8")
    for name in ("factions", "magic", "world", "timeline"):
        paths.canon_file(name).write_text(f"# {name}\n\ncontenido.\n", encoding="utf-8")
    for i in range(1, chapters_written + 1):
        paths.chapter_file(i).write_text(f"# Capítulo {i}\n\nprosa.\n", encoding="utf-8")
        paths.chapter_summary(i).write_text(f"# Chapter {i} — summary\n\nresumen.\n", encoding="utf-8")
    return paths
