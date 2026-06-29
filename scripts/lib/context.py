"""Context assembly for write-chapter.

Produces a single Markdown document that Claude reads to write chapter N.
All file IO is deterministic; the LLM never has to guess where to look.

Layered structure (in order):

    0. PRECEDENCE        — which sources win when two conflict
    1. SETUP             — setup.md (the book's identity)
    1b. DECISIONS        — notes/decisions.md (binding authored choices) +
                           notes/decisions-chNN.md (this chapter's gate)
    2. SERIES STATE      — series-state.md + previous book summaries
    3. CANON             — every file under canon/ (both series and book)
    4. PLAN              — neighbor beats (prev + next, for continuity) + arcs.
                           The CURRENT chapter's beat is section 9, not here,
                           and future chapters stay out to avoid plot leakage.
    5. SHADOW            — shadow.md slice for chapter N (overview + act + ch)
    6. SEED ENVELOPE     — exact seeds to plant/echo/payoff in N
    7. STORY SO FAR      — hierarchical summaries (acts + recent ch summaries)
    8. CONTINUITY SEAM   — chapter N-1's summary + its final scene verbatim
    9. CHAPTER BEAT      — the specific instruction for chapter N
   10. STYLE GUIDE       — this book's own style.md (copied from the master)
   11. REFERENCES        — a compact craft checklist (the full reference files
                           live in references/ and are read on demand)
"""

from __future__ import annotations

import re
from pathlib import Path

from . import seeds as seeds_mod
from . import shadows as shadows_mod
from . import summaries as sum_mod
from .paths import BookPaths, find_books


REFERENCES_DIR = Path("references")


# When two sections below conflict, resolve in this order (earlier wins).
# This is the single source of truth for precedence — do not re-litigate it
# per chapter.
PRECEDENCE = """\
When two sections below conflict, the earlier one in this list wins:

1. **Decisions** (book-level + this chapter's gate) — authored choices.
2. **Setup** — the book's identity.
3. **Canon** — established facts.
4. **Shadow** — the hidden truth (governs what the POV may NOT know yet).
5. **Seed envelope** — what to plant/echo/pay this chapter.
6. **Plan** (beats + arcs).
7. **Style guide / Voice notes** — how it reads.

If a beat seems to require breaking a higher rule, STOP and surface it to
the author instead of choosing silently."""


# Distilled craft rules. The full reference files (references/*.md) are read
# on demand; this checklist is what must be in-context for every chapter so we
# do not re-inline ~300 lines of static docs into each bundle.
CRAFT_CHECKLIST = """\
**Prose anti-patterns — never write these** (full list:
`references/prose-antipatterns.md`):
- No "delve", "tapestry of", "ethereal whispers", chosen-one rhetoric.
- No Y-and-Z triplet lists that flatten specifics into mush.
- No exposition dumps; worldbuilding arrives through use, not explanation.
- No chapter-ending self-talk that states the theme aloud.

**Dwelling — inhabit before advancing** (full file:
`references/dwelling-techniques.md`):
- 2-4 texture dwellings of 300-500 words; land one concrete non-visual
  sensation (temperature, sound, weight, taste, smell) per scene.
- One specific over three vague; no summary prose ("days passed").

**Seeds — plant/echo/pay with discipline** (full file:
`references/seed-craft.md`):
- Plant inside a scene already underway, never as a flagged object.
- Echo in a different sensory register; pay off without explaining.
- Protect reveal timing: do not spend a later-due payoff early."""


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


def _voice_stable_only(text: str) -> str:
    """Feed the writer the consolidated voice rules, not the rolling per-chapter
    observations (those are working material for close-act). For a POV that has a
    ``### Stable rules`` block, keep ONLY that block; for a POV not yet
    consolidated (current act in progress), keep its running observations so
    nothing is lost mid-act. ``## Recurring patterns`` is always kept in full.
    Nothing is deleted from voice.md on disk — this only trims what is loaded
    into context."""
    if not text:
        return ""
    h2 = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", text))
    if not h2:
        return text.strip()
    blocks: list[str] = []
    for i, m in enumerate(h2):
        title = m.group(1).strip()
        section = text[m.start(): h2[i + 1].start() if i + 1 < len(h2) else len(text)]
        low = title.lower()
        if low.startswith("pov"):
            stable = re.search(r"(?ms)^###\s+Stable rules.*?(?=^##\s|\Z)", section)
            if stable:
                blocks.append(f"## {title}\n\n{stable.group(0).strip()}")
            else:
                blocks.append(section.strip())  # not consolidated yet → keep obs
        elif "pattern" in low or "patrones" in low:
            blocks.append(section.strip())
        # else: drop the file intro / misc working sections
    return "\n\n".join(b for b in blocks if b).strip()


# Capitalized tokens that are roles / colors / connectors, not a person's name —
# so a character is kept on their DISTINCTIVE name, not on a stray "Maestro" or
# "Academia" that happens to appear in the chapter.
_CHAR_STOPWORDS = {
    "don", "doña", "el", "la", "los", "las", "de", "del", "un", "una",
    "maestro", "maestra", "profesor", "profesora", "guardia", "inquisidor",
    "inquisidora", "secundario", "secundarios", "padre", "madre", "hermano",
    "hermana", "señor", "señora", "rojo", "roja", "azul", "verde", "amarillo",
    "magenta", "morado", "ciano", "blanco", "negro", "marrón", "marron",
    "academia", "iglesia", "orden",
}


def _scope_characters_md(text: str, haystack: str) -> tuple[str, list[str]]:
    """Scope the long tail of the character roster to the chapter.

    Principals (top-level ``##`` sections) are kept in full. Inside the
    ``## Secundarios`` section, a ``###`` minor-character entry is kept only when
    one of its names appears in this chapter's relevance haystack (beat sheet,
    decisions, shadow slice, arcs, prev-chapter summary). Bias is to INCLUDE: an
    entry with no extractable proper name is kept. Returns (scoped_text,
    dropped_names) so the caller can tell the writer what was set aside."""
    if not text:
        return text, []
    hay = haystack.lower()
    h2 = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", text))
    if not h2:
        return text, []

    dropped: list[str] = []
    out = [text[: h2[0].start()].rstrip()]  # file heading / preamble
    for i, m in enumerate(h2):
        title = m.group(1).strip()
        section = text[m.start(): h2[i + 1].start() if i + 1 < len(h2) else len(text)]
        if not re.match(r"(?i)secundari|minor|secondary", title):
            out.append(section.rstrip())          # principal → keep whole
            continue
        # Secundarios: keep header/preamble, filter ### children by relevance.
        h3 = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", section))
        out.append(section[: h3[0].start()].rstrip() if h3 else section.rstrip())
        for j, hm in enumerate(h3):
            htitle = hm.group(1).strip()
            child = section[hm.start(): h3[j + 1].start() if j + 1 < len(h3) else len(section)]
            head_clean = re.sub(r'[#*"]', " ", htitle)
            # Distinctive proper-name tokens (drop role/color/connector words).
            names = [w for w in re.findall(r"[A-ZÁÉÍÓÚÑ][\wáéíóúñ]{2,}", head_clean)
                     if w.lower() not in _CHAR_STOPWORDS]
            # Distinctive lowercase aliases only from QUOTED nicknames ("el dorado").
            for alias in re.findall(r'"([^"]*)"', htitle):
                names += [w for w in re.findall(r"[a-záéíóúñ]{4,}", alias)
                          if w not in _CHAR_STOPWORDS]
            if not names or any(n.lower() in hay for n in names):
                out.append(child.rstrip())
            else:
                dropped.append(names[0])
    return "\n\n".join(b for b in out if b).strip() + "\n", dropped


# Setup sections whose content lives (richer) in a canon file once the book is
# under way. Each maps to the canon stem that supersedes it. Only these are ever
# dropped from the setup block — identity, premise, theme, plot, POV, pacing,
# prose constraints and open decisions are NOT in canon and always stay.
_SETUP_CANON_DUP = [
    ("magic system", "magic"),
    ("castes", "factions"),
    ("factions", "factions"),
    ("geography", "world"),
    ("characters — principals", "characters"),
    ("characters — secondary", "characters"),
]


def _canon_has_content(canon_dir: Path, stem: str, min_words: int = 120) -> bool:
    """True when canon/<stem>.md holds real promoted content (not just the
    bootstrap skeleton). Guards the setup filter: if canon is still empty (early
    in a new book), the setup section is kept."""
    p = canon_dir / f"{stem}.md"
    if not p.exists():
        return False
    body = re.sub(r"(?m)^#.*$|^>.*$", "", p.read_text(encoding="utf-8"))
    return len(body.split()) >= min_words


def _filter_setup(setup_text: str, canon_dir: Path) -> tuple[str, list[str]]:
    """Drop the setup sections now superseded by canon, but only when that canon
    file actually has content. Everything canon does NOT hold stays. Returns
    (filtered_text, dropped_titles)."""
    if not setup_text:
        return setup_text, []
    h2 = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", setup_text))
    if not h2:
        return setup_text, []
    dropped: list[str] = []
    out = [setup_text[: h2[0].start()].rstrip()]
    for i, m in enumerate(h2):
        title = m.group(1).strip()
        section = setup_text[m.start(): h2[i + 1].start() if i + 1 < len(h2) else len(setup_text)]
        low = title.lower()
        stem = next((st for sub, st in _SETUP_CANON_DUP if sub in low), None)
        if stem and _canon_has_content(canon_dir, stem):
            dropped.append(title)
        else:
            out.append(section.rstrip())
    return "\n\n".join(b for b in out if b).strip() + "\n", dropped


def _neighbor_beats(outline_text: str, chapter: int) -> str:
    """Prev + next chapter beats only, for continuity.

    The current chapter's beat is rendered separately (section 9). Future
    chapters beyond N+1 are deliberately withheld to avoid leaking plot the
    writer should not yet know.
    """
    parts: list[str] = []
    prev_beat = _extract_chapter_beat(outline_text, chapter - 1) if chapter > 1 else ""
    if prev_beat:
        parts.append(f"### Previous chapter ({chapter - 1}) — for continuity only\n\n{prev_beat}")
    next_beat = _extract_chapter_beat(outline_text, chapter + 1)
    if next_beat:
        parts.append(f"### Next chapter ({chapter + 1}) — where you must hand off TO\n\n{next_beat}")
    return "\n\n".join(parts)


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


def build_context(paths: BookPaths, chapter: int, phase: str = "write") -> str:
    """Assemble the Markdown context document for chapter N.

    ``phase`` tailors the bundle to who is reading it, so the heavy blocks are
    only paid for where they earn their tokens:

        write    — the full bundle (the only phase that drafts prose).
        plan     — for plan-chapter's decision gate. Drops the recent chapters
                   in full, the style guide and the craft checklist (it decides
                   forks, it does not write); the prior chapters arrive as
                   summaries instead.
        critique — for critique-chapter. Drops the recent chapters in full (the
                   critic reads the target chapter directly from chapters/), but
                   keeps style + craft because it checks them.
    """

    full_text = phase == "write"
    want_style = phase in ("write", "critique")
    want_craft = phase in ("write", "critique")

    blocks: list[str] = []

    # 0. Precedence — resolve conflicts deterministically instead of per chapter.
    blocks.append(_section("Precedence (read first — how to resolve conflicts)", PRECEDENCE))

    # 1. Setup
    setup_text_filtered, setup_dropped = _filter_setup(_read(paths.setup_md), paths.canon_dir)
    if setup_dropped:
        setup_text_filtered += (
            "\n> Sections folded into canon (loaded in the Canon block below, not "
            f"repeated here): {', '.join(setup_dropped)}.\n"
        )
    blocks.append(_section("Setup (the book's identity — never violate)", setup_text_filtered))

    # 1b. Locked decisions — binding law that survives any plan regeneration.
    # Book-level decisions.md (authored choices that must never be silently
    # overwritten) plus this chapter's gate decisions from plan-chapter, if any.
    decisions_parts: list[str] = []
    decisions_text = _read(paths.decisions_md).strip()
    if decisions_text and "no decisions" not in decisions_text.lower():
        decisions_parts.append(f"## Locked decisions (book-level — BINDING, never contradict)\n\n{decisions_text}\n")
    chapter_decisions = _read(paths.chapter_decisions_md(chapter)).strip()
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

    # 3. Canon (series + book). Read outline + shadow here (reused below) so we
    # can build a relevance haystack: the systems/processes canon (magic, world,
    # factions, timeline) and the principals are ALWAYS loaded in full — only the
    # long tail of the secondary-character roster is scoped to this chapter, and
    # only ever dropped when no signal names them (bias to include).
    outline_text = _read(paths.outline_md)
    shadow_text = shadows_mod.load_shadow(paths.shadow_md)
    # Chapter-focused signals only — who is actually in play THIS chapter. We do
    # NOT use arcs.md or the full shadow render here: those name the whole cast
    # and would keep everyone (no scoping). Bias is still to include — these are
    # the beat sheet, this chapter's gate decisions, the shadow CHAPTER slice,
    # and the previous chapter's summary (recently-active characters).
    relevance_haystack = "\n".join([
        _extract_chapter_beat(outline_text, chapter),
        _neighbor_beats(outline_text, chapter),
        chapter_decisions,
        decisions_text,
        shadows_mod.chapter_section(shadow_text, chapter) if shadow_text else "",
        sum_mod.load_chapter_summary(paths, chapter - 1) if chapter > 1 else "",
    ])
    canon_parts: list[str] = []
    scoped_out: list[str] = []
    for p in _list_canon_files(paths.series_canon_dir):
        canon_parts.append(f"## Series canon — {p.stem}\n\n{p.read_text(encoding='utf-8').strip()}\n")
    for p in _list_canon_files(paths.canon_dir):
        body = p.read_text(encoding="utf-8").strip()
        if p.stem == "characters":
            body, dropped = _scope_characters_md(body, relevance_haystack)
            scoped_out.extend(dropped)
            body = body.strip()
        canon_parts.append(f"## Book canon — {p.stem}\n\n{body}\n")
    if scoped_out:
        canon_parts.append(
            "## Book canon — scoped out this chapter\n\n"
            f"Minor characters not in play this chapter were omitted to save context: "
            f"{', '.join(sorted(set(scoped_out)))}. Pull any with `search-corpus` if needed.\n"
        )
    if canon_parts:
        blocks.append(_section("Canon (established facts — must never contradict)", "\n".join(canon_parts)))

    # 4. Plan: neighbor beats (prev + next, for continuity) + arcs.
    # The full outline is NOT inlined — only the adjacent beats — so the writer
    # gets continuity without the future plot of chapters N+2.. leaking in.
    plan_parts = []
    neighbors = _neighbor_beats(outline_text, chapter)  # outline_text read in block 3
    if neighbors:
        plan_parts.append(f"## Neighbor beats (context for the seam)\n\n{neighbors}\n")
    arcs = _read(paths.arcs_md)
    if arcs:
        plan_parts.append(f"## Character arcs\n\n{arcs.strip()}\n")
    if plan_parts:
        blocks.append(_section("Plan", "\n".join(plan_parts)))

    # 5. Shadow timeline slice for this chapter (shadow_text read in block 3)
    if shadow_text:
        blocks.append(_section("Shadow timeline (writer-only)", shadows_mod.render_shadow_for_chapter(shadow_text, chapter)))

    # 6. Seed envelope. If shadow.md declares any misread (a decoy truth), join
    # its false-reading guidance onto the carrier seeds active THIS chapter, so
    # the deceit instruction rides chapter-scoped on the seed instead of sitting
    # in the persistent shadow panel. Built here to keep seeds.py unaware of
    # shadows.py.
    seeds_list = seeds_mod.load_seeds(paths.seeds_md)
    envelope = seeds_mod.envelope_for_chapter(seeds_list, chapter)
    decoy_by_seed: dict = {}
    if shadow_text:
        payoff_ids = {s.id for s in envelope["payoff"]}
        active_ids = payoff_ids | {s.id for s in envelope["plant"]} | {s.id for s in envelope["echo"]}
        for t in shadows_mod.parse_truths(shadow_text):
            if not t.is_decoy():
                continue
            for sid in t.revealed_by:
                if sid in active_ids:
                    decoy_by_seed[sid] = {
                        "id": t.id, "decoy": t.decoy, "truth": t.truth,
                        "is_payoff": sid in payoff_ids,
                    }
    blocks.append(_section("Seed envelope (this chapter's seeds)", seeds_mod.render_envelope(envelope, chapter, decoy_by_seed)))

    # 7. Story so far (hierarchical summaries)
    plan = sum_mod.plan_context(paths, chapter)
    if full_text:
        story_plan = plan
    else:
        # No full-text block this phase, so the chapters that would have been
        # inlined in full (typically N-1) appear here as summaries instead —
        # otherwise they'd vanish from the bundle entirely.
        story_plan = sum_mod.SummaryPlan(
            full_text_chapters=[],
            detail_chapters=sorted(set(plan.detail_chapters) | set(plan.full_text_chapters)),
            act_summaries=plan.act_summaries,
        )
    blocks.append(_section("Story so far", sum_mod.render_summaries(paths, story_plan)))

    # 8. Continuity seam (write phase only). Instead of inlining the whole
    #    previous chapter (~9k words), carry its structured summary (end-state +
    #    carry-forward) plus only its final scene verbatim. Plan and critique
    #    rely on the summaries above instead.
    if full_text:
        blocks.append(_section("Continuity seam (previous chapter)", sum_mod.render_seam(paths, plan.full_text_chapters)))

    # 9. The beat for THIS chapter
    chapter_beat = _extract_chapter_beat(outline_text, chapter)
    if not chapter_beat:
        chapter_beat = f"(No outline section found for chapter {chapter}. The writer must lean on plan + shadow + setup.)"
    blocks.append(_section(f"Chapter {chapter} — beat sheet (your instruction)", chapter_beat))

    # 10. Style guide: this book's own style.md (self-contained; copied from
    # references/style.md at book creation). Falls back to the master template
    # only if the book somehow has no style.md yet.
    style_text = _read(paths.style_md).strip() or _read(REFERENCES_DIR / "style.md").strip()
    if style_text and want_style:
        blocks.append(_section("Style guide (this book — apply throughout)", style_text))

    # 10b. Conversation-memory notes: stable voice rules, author-declared
    # style rules, and open questions. Persisted by update-canon /
    # close-act so a fresh session writes a consistent voice without
    # needing chat memory.
    # Load only the consolidated voice (stable rules + recurring patterns), not
    # the rolling per-chapter observations — those are working material for
    # close-act and balloon the bundle. voice.md on disk keeps everything.
    voice_text = _voice_stable_only(_read(paths.voice_md)).strip()
    style_rules_text = _read(paths.style_rules_md).strip()
    open_questions_text = _read(paths.open_questions_md).strip()
    notes_parts: list[str] = []
    if voice_text and "no observations yet" not in voice_text.lower():
        notes_parts.append(f"## Voice rules (consolidated — apply when writing each POV)\n\n{voice_text}\n")
    if style_rules_text and "no rules declared yet" not in style_rules_text.lower():
        notes_parts.append(f"## Style rules (author-declared)\n\n{style_rules_text}\n")
    if open_questions_text and "no pendientes" not in open_questions_text.lower() and "(none yet)" not in open_questions_text.lower():
        notes_parts.append(f"## Open questions (pendientes)\n\n{open_questions_text}\n")
    if notes_parts:
        blocks.append(_section("Conversation memory (persisted via checkpoint)", "\n".join(notes_parts)))

    # 11. Craft checklist (distilled). The full reference files live in
    # references/ and the writer reads them on demand — we do not re-inline
    # ~300 lines of static docs into every chapter bundle. Skipped in the plan
    # phase (the decision gate writes no prose).
    if want_craft:
        blocks.append(_section("Craft checklist (apply throughout)", CRAFT_CHECKLIST))

    return "\n".join(b for b in blocks if b)
