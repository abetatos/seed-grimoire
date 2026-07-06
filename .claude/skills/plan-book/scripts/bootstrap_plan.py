#!/usr/bin/env python3
"""Bootstrap the plan/ and canon/ skeletons for a book.

Reads `setup.md` to learn the chapter count, principal character names,
and faction names, then writes empty-but-structured files the agent will
fill in interactively during the `plan-book` skill.

Does NOT invent content. Where setup.md has not been filled in, the
generated skeletons contain `> TODO:` markers.

Usage:
    python bootstrap_plan.py --series-slug <slug> --book-number <n>
    python bootstrap_plan.py --series-slug <slug> --book-number <n> --force
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths, BookPaths
from lib import setup_doc


# --- header parsing for setup.md sub-sections -----------------------------

PRINCIPAL_HEADER_LONG_RE = re.compile(r"^###\s+(?:Character|Personaje)\s*\d+\s*—\s*(.+?)\s*$", re.MULTILINE)
# Accept the short form too: bare "### Name" inside the principals section.
PRINCIPAL_HEADER_SHORT_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
FACTION_HEADER_RE = re.compile(r"^###\s+(?:Faction|Facción)\s*\d+\s*(?:—\s*(.+?))?\s*$", re.MULTILINE)


def parse_principals(setup_text: str) -> list[str]:
    """Return a list of principal character names from setup.md.

    Accepts both the long-form template header ("### Character 1 — Bruno")
    and the short form ("### Bruno"). Skips placeholder names like
    "(name)" / "(nombre)".
    """
    chars_section = setup_doc.get_section(setup_text, "characters — principals") or \
        setup_doc.get_section(setup_text, "personajes — principales") or \
        setup_doc.get_section(setup_text, "characters")
    names: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        raw = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
        if raw.lower() in ("name", "nombre", "(name)", "(nombre)", ""):
            return
        if raw not in seen:
            names.append(raw)
            seen.add(raw)

    # Long form wins where present
    for m in PRINCIPAL_HEADER_LONG_RE.finditer(chars_section):
        add(m.group(1).strip())
    # Then short form catches "### Bruno"
    for m in PRINCIPAL_HEADER_SHORT_RE.finditer(chars_section):
        raw = m.group(1).strip()
        # Skip ones that already matched the long form pattern
        if re.match(r"^(?:Character|Personaje)\s*\d+", raw, re.IGNORECASE):
            continue
        add(raw)
    return names


def parse_factions(setup_text: str) -> list[str]:
    """Return a list of faction names from setup.md."""
    sec = setup_doc.get_section(setup_text, "castes") or \
        setup_doc.get_section(setup_text, "factions") or \
        setup_doc.get_section(setup_text, "facciones") or \
        setup_doc.get_section(setup_text, "castas")
    names: list[str] = []
    # Look for "### Faction N — name" pattern or just "### name"
    for line in sec.splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if not m:
            continue
        name = m.group(1).strip()
        # Skip generic "Faction 1" placeholders without a real name
        if re.fullmatch(r"(Faction|Facción|Caste|Casta)\s*\d+", name, re.IGNORECASE):
            continue
        # Strip "Faction 1 — RealName" → "RealName"
        m2 = re.match(r"^(?:Faction|Facción|Caste|Casta)\s*\d+\s*—\s*(.+)$", name, re.IGNORECASE)
        if m2:
            name = m2.group(1).strip()
        names.append(name)
    return names


# --- generators -----------------------------------------------------------

def outline_skeleton(num_chapters: int, words_lo: int, words_hi: int) -> str:
    """A per-chapter outline skeleton with three beat types per chapter."""
    head = f"""# Outline — visible timeline

> This file is the **public** timeline: every chapter, what the reader
> witnesses. The hidden truth lives in `shadow.md`. The seeds catalog
> lives in `seeds.md`.
>
> For each chapter, fill **three beat types**:
> - **Plot beats:** what happens in the world (events, dialogue, decisions).
> - **Texture beats:** the grounding moments, each typed with one of the
>   six licensed kinds (world unfolded in use, stage built, cost made
>   visible, deliberation, re-orientation, secondary humanized).
>   Aim for 2-4 of these per chapter at 150-400 words each.
> - **Subtext beats:** what's happening underneath — internal state,
>   things characters don't say, seeds planted obliquely.
>
> Target length per chapter: {words_lo}-{words_hi} words.

"""
    chapters: list[str] = []
    # Act boundaries: roughly 25 / 50 / 75 of num_chapters
    a1_end = max(1, round(num_chapters * 0.28))
    mid = max(a1_end + 1, round(num_chapters * 0.5))
    a2_end = max(mid + 1, round(num_chapters * 0.75))

    def act_label(n: int) -> str:
        if n <= a1_end:
            return f"Act 1 — Inhabitation (ch 1-{a1_end})"
        if n < mid:
            return f"Act 2A — Expansion (ch {a1_end + 1}-{mid - 1})"
        if n == mid:
            return f"Midpoint — Overturning (ch {mid})"
        if n <= a2_end:
            return f"Act 2B — Convergence (ch {mid + 1}-{a2_end})"
        return f"Act 3 — Climax & Resolution (ch {a2_end + 1}-{num_chapters})"

    last_act = ""
    for n in range(1, num_chapters + 1):
        a = act_label(n)
        if a != last_act:
            chapters.append(f"\n# {a}\n")
            last_act = a
        chapters.append(
            f"## Chapter {n}\n"
            f"- **Title:** > TODO:\n"
            f"- **POV:** > TODO:\n"
            f"- **Where / when:** > TODO:\n"
            f"- **Target words:** {words_lo}-{words_hi}\n"
            f"- **Function in the act:** > TODO: (what this chapter does for the larger arc)\n"
            f"\n"
            f"### Plot beats\n"
            f"> TODO: 3-6 short bullets. What happens, in order.\n"
            f"\n"
            f"### Texture beats\n"
            f"> TODO: 2-4 grounding moments (150-400 words each), each typed\n"
            f"> (unfold / stage / cost / deliberation / re-orient / secondary).\n"
            f"> Be specific — name the smell, the labor, the room.\n"
            f"\n"
            f"### Subtext beats\n"
            f"> TODO: what does the character feel but not say? What lie are\n"
            f"> they protecting? What does the reader sense without being told?\n"
            f"\n"
            f"### Transition out\n"
            f"> TODO: how does this chapter end so the next one feels inevitable?\n"
        )
    return head + "\n".join(chapters)


def shadow_skeleton(num_chapters: int) -> str:
    """Hidden timeline. Writer-only. Never compressed."""
    a1_end = max(1, round(num_chapters * 0.28))
    mid = max(a1_end + 1, round(num_chapters * 0.5))
    a2_end = max(mid + 1, round(num_chapters * 0.75))

    acts = [
        ("Act 1", 1, a1_end),
        ("Act 2A", a1_end + 1, mid - 1),
        ("Midpoint", mid, mid),
        ("Act 2B", mid + 1, a2_end),
        ("Act 3", a2_end + 1, num_chapters),
    ]

    head = """# Shadow timeline — writer-only

> **The reader will NEVER see this file.** This is the truth that the
> writer knows and the POV character does not.
>
> Fill in the *actual* causes, the *real* motivations, the secrets being
> hidden by characters from each other and from the reader. Reference
> seed ids from `seeds.md` when relevant.
>
> **NEVER compress or summarize this file.** It is consulted on every
> chapter so the writer plants and pays off honestly.

## Overview

> TODO: In 5-10 sentences, what is REALLY happening behind the surface
> story? Who is lying, to whom, why? What's the secret history that
> only resolves at the climax? What will the reader retroactively
> understand by the last page?

## Master truths

> TODO: facts TRUE in the book's reality but hidden FROM THE READER, revealed
> bit by bit until they stop being shadows. Track only the **reader's** knowledge
> (a *character* learning a truth on the page is tracked by the seed that carries
> it). Do NOT give a truth its own reveal schedule — that duplicates its carrier
> seeds and drifts out of sync. Each truth declares:
>
> - **Revealed-by:** its carrier seed id(s) — the schedule lives there. Use `—`
>   for an exposition-only truth (revealed by dialogue, not a seed).
> - **Reveal cap:** the loudest it may sound in THIS book. A truth that pays off
>   in a later book caps BELOW `confirmed`.
> - **Status:** advanced by `update-canon` over the page, never above the cap.
>
> Reveal ladder = the READER'S interior state, NOT how loudly to write:
> `hidden → sensed → suspected → confirmed`. Never call a level a "hard hint" —
> that makes an LLM state the truth plainly. `suspected` is still subtle: reached
> by accumulation, never by a line that says it.
>
> Aim for MANY truths, not a thin handful: the protagonist's hidden nature, EACH
> antagonist's real agenda, EACH institution's real function, the secret history,
> and EACH major subplot. A ~25-chapter book wants ~12-20 truths, not 5.
>
> Copy this record per truth (semantic slug id; keep the statement verbatim):
>
> ## SHADOW-TRUTH: <slug>
> **Truth:** <the hidden fact, stated plainly here for the writer only>
> **Decoy:** <OPTIONAL — only for a MISREAD: the FALSE belief the reader should
>   actively hold until a carrier payoff inverts it. The carriers then build this
>   wrong belief; the ladder reads misled → convinced → inverted. Omit unless the
>   reader should believe the OPPOSITE of Truth (not merely not-know it). Reserve
>   for a belief carried across chapters — a one-scene red herring is just a seed.>
> **Mystery:** <exact §14b master-mystery name from the grimoire, if this truth carries one>
> **Revealed-by:** <seed-id, seed-id>
> **Reveal cap:** <sensed | suspected | confirmed>
> **Confirm in:** <chapter>   (only for seedless truths; omit otherwise)
> **Status:** hidden
> **Surfaced:**
>
> Every grimoire §14b master mystery introduced in THIS book must have a truth
> tagging it with `**Mystery:**` (critique-plan flags any that don't).
"""
    parts = [head]
    for name, lo, hi in acts:
        if lo > num_chapters:
            continue
        parts.append(
            f"\n## {name} (chapters {lo}-{hi})\n\n"
            f"> TODO: What's REALLY happening in this act behind the visible\n"
            f"> events? Which seeds are planted / echoed / paid in this span?\n"
            f"> What does the antagonist (or fate, or the world) know that the\n"
            f"> protagonist doesn't?\n"
        )
        for n in range(lo, hi + 1):
            parts.append(
                f"\n### Chapter {n}\n"
                f"> TODO: hidden truth for this chapter, if any. What seems to\n"
                f"> be happening vs. what is actually happening. Reference seed ids.\n"
            )
    return "".join(parts)


def seeds_skeleton(book_title: str) -> str:
    return f"""# Seeds — {book_title}

These are the foreshadowing seeds for the whole book. Status progresses as
chapters are written: `planned → planted → echoed-N → paid_off`.

**NEVER compress or summarize this file.** It is consulted on every chapter.

> Each seed has: a stable id, a visible detail, a real meaning, the
> chapter to plant in, chapters to echo in, the chapter to pay off in,
> and instructions for both ends. Use `references/seed-craft.md` for
> craft guidance.

> Add seeds during planning with this structure:

## SEED: example-id
**Detail:** the surface detail the reader will see (e.g., "a fresh scratch on the boy's knuckle")
**Real meaning:** what it actually signifies (writer-only)
**Plant in:** 3
**Echo in:** 9, 14
**Payoff in:** 19
**How to plant:** specific instructions for how to drop this seed without telegraphing
**How to pay off:** how the truth surfaces — what scene, what cost
**Obligatory:** §14 <exact grimoire loaded-gun name>   (only if this seed realizes one; omit otherwise)
**Status:** planned

> Replace the example above with real seeds, or delete it. Aim for 8-15
> seeds per book minimum. Every grimoire §14 loaded gun whose "Siembra en"
> includes this book must have a seed tagged `**Obligatory:**` (critique-plan
> flags any that don't).
"""


def arcs_skeleton(principals: list[str]) -> str:
    head = """# Character arcs

> One section per principal. The arc is the private transformation
> separate from the plot. Read `references/fantasy-beats.md` (Character
> arcs section) for the structure.
>
> Wound → Want → Need → Lie → Decision → Transformation.

"""
    if not principals:
        principals = ["(name)"]
    blocks = []
    for name in principals:
        blocks.append(
            f"## {name}\n"
            f"- **Wound (still active):** > TODO:\n"
            f"- **Want (conscious goal):** > TODO:\n"
            f"- **Need (real healing):** > TODO:\n"
            f"- **Lie they believe:** > TODO:\n"
            f"- **Decision point (which chapter):** > TODO:\n"
            f"- **Transformation type:** positive / negative / tragic — > TODO:\n"
            f"\n"
            f"### Waypoints\n"
            f"- **Act 1 — state at start:** > TODO:\n"
            f"- **First crack (chapter ~):** > TODO:\n"
            f"- **Midpoint shift:** > TODO:\n"
            f"- **All-is-lost low:** > TODO:\n"
            f"- **Decision moment:** > TODO:\n"
            f"- **End-state:** > TODO:\n"
            f"\n"
        )
    return head + "\n".join(blocks)


# --- canon skeletons ------------------------------------------------------

def canon_characters_skeleton(principals: list[str]) -> str:
    head = """# Canon — characters

> Stable, evolving fact sheet. Updated by `update-canon` after each
> chapter. Hold names, physical details, relationships, current
> location, current emotional state, and known secrets.
>
> One section per character. Keep entries tight; this file is read in
> full on every chapter, so don't let it bloat.

"""
    if not principals:
        principals = ["(name)"]
    blocks = []
    for name in principals:
        blocks.append(
            f"## {name}\n"
            f"- **Role:** > TODO:\n"
            f"- **Physical (3 specifics):** > TODO:\n"
            f"- **Voice / vocabulary tics:** > TODO:\n"
            f"- **Current location:** > TODO:\n"
            f"- **Current emotional state:** > TODO:\n"
            f"- **Relationships:** > TODO:\n"
            f"- **Magic relationship:** > TODO:\n"
            f"- **Secrets they hold (writer-only):** > TODO:\n"
            f"- **First appearance:** ch __\n"
            f"\n"
        )
    return head + "\n".join(blocks)


def canon_factions_skeleton(factions: list[str]) -> str:
    head = """# Canon — factions / castes / orders

> Each major power center: name, ideology, leadership, magic relation,
> stance toward principals, current state.

"""
    if not factions:
        factions = ["(faction name)"]
    blocks = []
    for f in factions:
        blocks.append(
            f"## {f}\n"
            f"- **Premise:** > TODO:\n"
            f"- **Hierarchy / leadership:** > TODO:\n"
            f"- **Symbol / ritual:** > TODO:\n"
            f"- **Magic relation:** > TODO:\n"
            f"- **Current conflict:** > TODO:\n"
            f"- **Stance toward each principal:** > TODO:\n"
            f"\n"
        )
    return head + "\n".join(blocks)


def canon_magic_skeleton() -> str:
    return """# Canon — magic system

> Stable rules of the magic. Promoted from setup.md and expanded as the
> writer needs more specifics during chapters. Inviolable.
>
> Use `references/magic-design-checklist.md`.

## Source
> TODO:

## Mechanic (step-by-step access)
> TODO:

## Costs (≥ 2)
> TODO:

## Hard limits (≥ 3, sacred)
> TODO:

## Who can use, who cannot
> TODO:

## Social consequence
> TODO:

## Thematic question forced
> TODO:

## Three escalation tiers
- **Common (visible act 1):** > TODO:
- **Skilled (visible act 2):** > TODO:
- **Apex (visible at climax — cost is permanent):** > TODO:

## Vocabulary / terms
> TODO: glossary of in-world terms for the magic. Lock them now to avoid drift.
"""


def canon_world_skeleton() -> str:
    return """# Canon — world / geography

> Named places with sensory detail and political position. Updated as
> the writer expands a place during chapters.

## Macro geography
> TODO:

## Calendar / time
> TODO:

## Languages / scripts
> TODO:

## Places
> TODO: one block per named place:
>
> ### Place name
> - **Type:** city / village / region / road / structure
> - **Sensory anchor:** the smell, sound, or texture by which the reader
>   will remember it
> - **Function in plot:** why it appears
> - **Who lives there:**
> - **Political stance:**
"""


def canon_timeline_skeleton() -> str:
    return """# Canon — timeline

> Two parts: **historical weight** (events before the book begins that
> echo through the present) and **book chronology** (the verifiable
> sequence of events within the book, updated by `update-canon`).

## Historical weight (pre-book)
> TODO: 3-5 past events. For each: what happened, how long ago, who
> remembers it, what wound it left.

## Book chronology
> TODO: time elapsed per chapter. Updated as the book is written.

- **Ch 1:** day 1
- **Ch 2:** > TODO:
"""


# --- main -----------------------------------------------------------------

def write_if_absent(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--force", action="store_true", help="Overwrite existing plan/canon files")
    args = parser.parse_args()

    paths: BookPaths = book_paths(args.series_slug, args.book_number)

    if not paths.setup_md.exists():
        print(f"ERROR: setup.md not found at {paths.setup_md}. Run book-setup first.")
        return 2

    paths.ensure_dirs()

    setup_text = setup_doc.load(paths.setup_md)
    title = setup_doc.book_title(setup_text) or "(untitled)"
    n_chapters = setup_doc.num_chapters(setup_text) or 25
    words_lo, words_hi = setup_doc.words_per_chapter_range(setup_text)
    principals = parse_principals(setup_text)
    factions = parse_factions(setup_text)

    written: list[Path] = []
    skipped: list[Path] = []

    def do(path: Path, content: str) -> None:
        if write_if_absent(path, content, args.force):
            written.append(path)
        else:
            skipped.append(path)

    do(paths.outline_md, outline_skeleton(n_chapters, words_lo, words_hi))
    do(paths.shadow_md, shadow_skeleton(n_chapters))
    do(paths.seeds_md, seeds_skeleton(title))
    do(paths.arcs_md, arcs_skeleton(principals))

    do(paths.canon_file("characters"), canon_characters_skeleton(principals))
    do(paths.canon_file("factions"), canon_factions_skeleton(factions))
    do(paths.canon_file("magic"), canon_magic_skeleton())
    do(paths.canon_file("world"), canon_world_skeleton())
    do(paths.canon_file("timeline"), canon_timeline_skeleton())

    print(f"Bootstrapped plan for {paths.book_root}")
    print(f"  title: {title}")
    print(f"  chapters: {n_chapters}  words/chapter: {words_lo}-{words_hi}")
    print(f"  principals parsed: {principals or '(none — fill in setup.md first)'}")
    print(f"  factions parsed: {factions or '(none)'}")
    print(f"  written: {len(written)} files")
    for p in written:
        print(f"    + {p}")
    if skipped:
        print(f"  skipped (already exist, use --force to overwrite): {len(skipped)}")
        for p in skipped:
            print(f"    = {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
