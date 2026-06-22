"""Context assembly for write-chapter.

Produces a single Markdown document that Claude reads to write chapter N.
All file IO is deterministic; the LLM never has to guess where to look.

Layered structure (in order):

    1. SETUP             — setup.md (the book's identity)
    1b. DECISIONS        — notes/decisions.md (binding authored choices) +
                           notes/_decisions-chNN.md (this chapter's gate)
    2. SERIES STATE      — series-state.md + previous book summaries
    3. CANON             — every file under canon/ (both series and book)
    4. PLAN              — outline.md, arcs.md
    5. SHADOW            — shadow.md slice for chapter N (overview + act + ch)
    6. SEED ENVELOPE     — exact seeds to plant/echo/payoff in N
    7. STORY SO FAR      — hierarchical summaries (acts + recent ch summaries)
    8. RECENT CHAPTERS   — last N-1 and N-2 in full
    9. CHAPTER BEAT      — the specific instruction for chapter N
   10. STYLE GUIDE       — this book's own style.md (copied from the master)
   11. REFERENCES        — dwelling techniques + anti-patterns (always)
"""

from __future__ import annotations

import re
from pathlib import Path

from . import seeds as seeds_mod
from . import shadows as shadows_mod
from . import summaries as sum_mod
from .paths import BookPaths, find_books


REFERENCES_DIR = Path("references")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _section(title: str, body: str) -> str:
    body = body.rstrip()
    if not body:
        return ""
    return f"# {title}\n\n{body}\n"




def _list_canon_files(canon_dir: Path) -> list[Path]:
    if not canon_dir.exists():
        return []
    return sorted(p for p in canon_dir.iterdir() if p.suffix == ".md")


def _extract_chapter_beat(outline_text: str, chapter: int) -> str:
    """Find the ## Chapter N section in outline.md."""
    if not outline_text:
        return ""
    pattern = re.compile(
        rf"^##\s+(?:Chapter|Cap|Capítulo)\s+{chapter}\b",
        re.IGNORECASE | re.MULTILINE,
    )
    m = pattern.search(outline_text)
    if not m:
        return ""
    start = m.start()
    # End at the next ## chapter or part header
    next_pat = re.compile(r"^##\s+", re.MULTILINE)
    nxt = next_pat.search(outline_text, m.end())
    end = nxt.start() if nxt else len(outline_text)
    return outline_text[start:end].strip()


def _previous_books_context(paths: BookPaths) -> str:
    """For trilogy: read each prior book's book-summary.md."""
    parts: list[str] = []
    series_slug = paths.series_root.name
    current_num = int(paths.book_root.name.split("-")[-1])
    for n in find_books(series_slug):
        if n >= current_num:
            continue
        prev_root = paths.series_root / f"book-{n:02d}"
        prev_summary = prev_root / "summaries" / "book-summary.md"
        if prev_summary.exists():
            parts.append(f"## Book {n} — summary\n\n{prev_summary.read_text(encoding='utf-8').strip()}\n")
    return "\n".join(parts)


def build_context(paths: BookPaths, chapter: int) -> str:
    """Assemble the full Markdown context document for writing chapter N."""

    blocks: list[str] = []

    # 1. Setup
    blocks.append(_section("Setup (the book's identity — never violate)", _read(paths.setup_md)))

    # 1b. Locked decisions — binding law that survives any plan regeneration.
    # Book-level decisions.md (authored choices that must never be silently
    # overwritten) plus this chapter's gate decisions from plan-chapter, if any.
    decisions_parts: list[str] = []
    decisions_text = _read(paths.decisions_md).strip()
    if decisions_text and "no decisions" not in decisions_text.lower():
        decisions_parts.append(f"## Locked decisions (book-level — BINDING, never contradict)\n\n{decisions_text}\n")
    chapter_decisions = _read(paths.notes_dir / f"_decisions-ch{chapter:02d}.md").strip()
    if chapter_decisions:
        decisions_parts.append(f"## Decisions for this chapter (from plan-chapter — BINDING)\n\n{chapter_decisions}\n")
    if decisions_parts:
        blocks.append(_section("Decisions (authored choices — override anything below that conflicts)", "\n".join(decisions_parts)))

    # 2. Series state + previous books
    series_block_parts = []
    series_md = _read(paths.series_md)
    if series_md:
        series_block_parts.append(f"## Series identity\n\n{series_md}\n")
    series_state = _read(paths.series_state)
    if series_state:
        series_block_parts.append(f"## Series state (cross-book)\n\n{series_state}\n")
    prev_books = _previous_books_context(paths)
    if prev_books:
        series_block_parts.append(prev_books)
    if series_block_parts:
        blocks.append(_section("Series context", "\n".join(series_block_parts)))

    # 3. Canon (series + book)
    canon_parts: list[str] = []
    for p in _list_canon_files(paths.series_canon_dir):
        canon_parts.append(f"## Series canon — {p.stem}\n\n{p.read_text(encoding='utf-8').strip()}\n")
    for p in _list_canon_files(paths.canon_dir):
        canon_parts.append(f"## Book canon — {p.stem}\n\n{p.read_text(encoding='utf-8').strip()}\n")
    if canon_parts:
        blocks.append(_section("Canon (established facts — must never contradict)", "\n".join(canon_parts)))

    # 4. Plan: outline + arcs
    plan_parts = []
    outline_text = _read(paths.outline_md)
    if outline_text:
        plan_parts.append(f"## Outline\n\n{outline_text.strip()}\n")
    arcs = _read(paths.arcs_md)
    if arcs:
        plan_parts.append(f"## Character arcs\n\n{arcs.strip()}\n")
    if plan_parts:
        blocks.append(_section("Plan", "\n".join(plan_parts)))

    # 5. Shadow timeline slice for this chapter
    shadow_text = shadows_mod.load_shadow(paths.shadow_md)
    if shadow_text:
        blocks.append(_section("Shadow timeline (writer-only)", shadows_mod.render_shadow_for_chapter(shadow_text, chapter)))

    # 6. Seed envelope
    seeds_list = seeds_mod.load_seeds(paths.seeds_md)
    envelope = seeds_mod.envelope_for_chapter(seeds_list, chapter)
    blocks.append(_section("Seed envelope (this chapter's seeds)", seeds_mod.render_envelope(envelope, chapter)))

    # 7. Story so far (hierarchical summaries)
    plan = sum_mod.plan_context(paths, chapter)
    blocks.append(_section("Story so far", sum_mod.render_summaries(paths, plan)))

    # 8. Recent chapters in full
    blocks.append(_section("Recent chapters", sum_mod.render_full_text(paths, plan.full_text_chapters)))

    # 9. The beat for THIS chapter
    chapter_beat = _extract_chapter_beat(outline_text, chapter)
    if not chapter_beat:
        chapter_beat = f"(No outline section found for chapter {chapter}. The writer must lean on plan + shadow + setup.)"
    blocks.append(_section(f"Chapter {chapter} — beat sheet (your instruction)", chapter_beat))

    # 10. Style guide: this book's own style.md (self-contained; copied from
    # references/style.md at book creation). Falls back to the master template
    # only if the book somehow has no style.md yet.
    style_text = _read(paths.style_md).strip() or _read(REFERENCES_DIR / "style.md").strip()
    if style_text:
        blocks.append(_section("Style guide (this book — apply throughout)", style_text))

    # 10b. Conversation-memory notes: stable voice rules, author-declared
    # style rules, and open questions. Persisted by update-canon /
    # close-act so a fresh session writes a consistent voice without
    # needing chat memory.
    voice_text = _read(paths.voice_md).strip()
    style_rules_text = _read(paths.style_rules_md).strip()
    open_questions_text = _read(paths.open_questions_md).strip()
    notes_parts: list[str] = []
    if voice_text and "no observations yet" not in voice_text.lower():
        notes_parts.append(f"## Voice notes (rolling — apply when writing each POV)\n\n{voice_text}\n")
    if style_rules_text and "no rules declared yet" not in style_rules_text.lower():
        notes_parts.append(f"## Style rules (author-declared)\n\n{style_rules_text}\n")
    if open_questions_text and "no pendientes" not in open_questions_text.lower() and "(none yet)" not in open_questions_text.lower():
        notes_parts.append(f"## Open questions (pendientes)\n\n{open_questions_text}\n")
    if notes_parts:
        blocks.append(_section("Conversation memory (persisted via checkpoint)", "\n".join(notes_parts)))

    # 11. References (anti-patterns + dwelling)
    ref_parts = []
    for name in ("prose-antipatterns.md", "dwelling-techniques.md", "seed-craft.md"):
        ref_path = REFERENCES_DIR / name
        if ref_path.exists():
            ref_parts.append(f"## {name}\n\n{ref_path.read_text(encoding='utf-8').strip()}\n")
    if ref_parts:
        blocks.append(_section("Craft references (apply throughout)", "\n".join(ref_parts)))

    return "\n".join(b for b in blocks if b)
