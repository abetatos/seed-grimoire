"""Path resolution for series/book/chapter files on disk.

Layout:
    output/
        <series-slug>/
            series.md                  # cross-book identity (trilogy/saga)
            series-state.md            # rolling state shared across books
            canon/                     # cross-book canon (world, magic shared)
                world.md
                magic.md
            book-NN/
                setup.md
                style.md               # per-book style guide (copied from references/style.md)
                assets/                # static assets for export
                    cover.jpg          # book cover (jpg/jpeg/png) — fixed location
                canon/                 # book-specific canon
                    characters.md
                    factions.md
                    magic.md           # book-specific extensions
                    world.md           # book-specific locations
                    timeline.md
                plan/
                    outline.md
                    shadow.md
                    seeds.md
                    arcs.md
                chapters/
                    NN.md
                summaries/
                    ch-NN.md
                    act-NN.md
                    book-summary.md
                notes/
                    decisions.md
                    drops.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


OUTPUT_ROOT = Path("output")


@dataclass(frozen=True)
class BookPaths:
    """All file paths for a single book within a series."""

    series_root: Path
    book_root: Path

    @property
    def series_md(self) -> Path:
        return self.series_root / "series.md"

    @property
    def series_state(self) -> Path:
        return self.series_root / "series-state.md"

    @property
    def grimoire_md(self) -> Path:
        return self.series_root / "grimoire.md"

    @property
    def series_canon_dir(self) -> Path:
        return self.series_root / "canon"

    @property
    def setup_md(self) -> Path:
        return self.book_root / "setup.md"

    @property
    def style_md(self) -> Path:
        """This book's self-contained style guide (copied from the master
        template references/style.md at book creation)."""
        return self.book_root / "style.md"

    @property
    def assets_dir(self) -> Path:
        return self.book_root / "assets"

    # Cover lives at a fixed location: assets/cover.{jpg,jpeg,png}.
    COVER_NAMES = ("cover.jpg", "cover.jpeg", "cover.png")

    def cover_path(self) -> Path | None:
        """The book cover image if present, else None.

        Canonical location is `assets/cover.{jpg,jpeg,png}`, checked in
        that priority order so there is exactly one place to drop it.
        """
        for name in self.COVER_NAMES:
            p = self.assets_dir / name
            if p.exists():
                return p
        return None

    @property
    def canon_dir(self) -> Path:
        return self.book_root / "canon"

    def canon_file(self, name: str) -> Path:
        return self.canon_dir / f"{name}.md"

    @property
    def plan_dir(self) -> Path:
        return self.book_root / "plan"

    @property
    def outline_md(self) -> Path:
        return self.plan_dir / "outline.md"

    @property
    def shadow_md(self) -> Path:
        return self.plan_dir / "shadow.md"

    @property
    def seeds_md(self) -> Path:
        return self.plan_dir / "seeds.md"

    @property
    def arcs_md(self) -> Path:
        return self.plan_dir / "arcs.md"

    @property
    def front_matter_dir(self) -> Path:
        """Courtesy pages that precede chapter 1 in the compiled EPUB —
        dedication, epigraph, etc. Ordered `NN-name.md`; kept OUT of the
        chapters/ pipeline (never a chapter, never linted as prose). Only
        read by build_epub.py. See front_matter_files()."""
        return self.book_root / "front-matter"

    @property
    def chapters_dir(self) -> Path:
        return self.book_root / "chapters"

    def chapter_file(self, n: int) -> Path:
        return self.chapters_dir / f"{n:02d}.md"

    @property
    def summaries_dir(self) -> Path:
        return self.book_root / "summaries"

    def chapter_summary(self, n: int) -> Path:
        return self.summaries_dir / f"ch-{n:02d}.md"

    def act_summary(self, n: int) -> Path:
        return self.summaries_dir / f"act-{n:02d}.md"

    @property
    def book_summary(self) -> Path:
        return self.summaries_dir / "book-summary.md"

    @property
    def notes_dir(self) -> Path:
        return self.book_root / "notes"

    @property
    def decisions_md(self) -> Path:
        return self.notes_dir / "decisions.md"

    def chapter_brief_md(self, n: int) -> Path:
        """This chapter's brief from plan-chapter — the single mandatory,
        committed hand-off to write-chapter. One file, three fixed sections
        (Decisiones / Estado que no se puede contradecir / Arrastre); context.py
        splits them to their bundle positions. Supersedes the split
        decisions-chNN.md + continuity-chNN.md + the per-chapter role of
        open-questions.md (IMPROVEMENT-PLAN Movement 2)."""
        return self.notes_dir / f"brief-ch{n:02d}.md"

    @property
    def drops_md(self) -> Path:
        return self.notes_dir / "drops.md"

    # --- conversation-memory files (checkpoint / handoff) ---------------

    @property
    def voice_md(self) -> Path:
        """Rolling voice / POV observations. Updated each update-canon."""
        return self.notes_dir / "voice.md"

    @property
    def style_rules_md(self) -> Path:
        """Style rules the author has expressed explicitly in chat."""
        return self.notes_dir / "style-rules.md"

    @property
    def prose_lint_toml(self) -> Path:
        """Per-book config for lint_prose.py: tic caps + reserved lexicon.
        Committed; parsed read-only with stdlib tomllib."""
        return self.notes_dir / "prose-lint.toml"

    @property
    def voice_exemplars_md(self) -> Path:
        """Author-blessed prose passages the writer imitates. Curated at
        close-act; committed (authored content, like decisions.md)."""
        return self.notes_dir / "voice-exemplars.md"

    @property
    def voice_spine_md(self) -> Path:
        """This BOOK's half of the voice spine (3-4 bullets: sensory premise,
        POV vocabulary, the one licensed signature move). Written at
        book-setup from the author's voice contract; committed. The house
        half lives in code (context.VOICE_SPINE_*)."""
        return self.notes_dir / "voice-spine.md"

    @property
    def session_handoff_md(self) -> Path:
        """Overwritten at each close-act. Read first thing by resume-act."""
        return self.notes_dir / "session-handoff.md"

    # --- world-state engine store (RESTRUCTURE-V2) ----------------------
    # Structured JSON state, mutated only by scripts (world_tool.py); the LLM
    # reads computed views, never these files. Protected like seeds.md/shadow.md.

    @property
    def state_dir(self) -> Path:
        return self.book_root / "state"

    @property
    def world_json(self) -> Path:
        return self.state_dir / "world.json"

    @property
    def entities_json(self) -> Path:
        return self.state_dir / "entities.json"

    @property
    def seeds_json(self) -> Path:
        return self.state_dir / "seeds.json"

    @property
    def shadow_json(self) -> Path:
        return self.state_dir / "shadow.json"

    @property
    def events_dir(self) -> Path:
        return self.state_dir / "events"

    def chapter_events_jsonl(self, n: int) -> Path:
        return self.events_dir / f"ch-{n:02d}.jsonl"

    def ensure_dirs(self) -> None:
        """Create all directories needed for a book."""
        for d in (
            self.series_root,
            self.series_canon_dir,
            self.book_root,
            self.assets_dir,
            self.canon_dir,
            self.plan_dir,
            self.front_matter_dir,
            self.chapters_dir,
            self.summaries_dir,
            self.notes_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


def book_paths(series_slug: str, book_number: int) -> BookPaths:
    """Build a BookPaths for series_slug/book-NN."""
    series_root = OUTPUT_ROOT / series_slug
    book_root = series_root / f"book-{book_number:02d}"
    return BookPaths(series_root=series_root, book_root=book_root)


def find_series_slugs() -> list[str]:
    """List all existing series in output/."""
    if not OUTPUT_ROOT.exists():
        return []
    return sorted(p.name for p in OUTPUT_ROOT.iterdir() if p.is_dir())


def find_books(series_slug: str) -> list[int]:
    """List all book numbers under a series."""
    series_root = OUTPUT_ROOT / series_slug
    if not series_root.exists():
        return []
    nums = []
    for p in series_root.iterdir():
        m = re.match(r"^book-(\d+)$", p.name)
        if m and p.is_dir():
            nums.append(int(m.group(1)))
    return sorted(nums)


def chapter_numbers(paths: BookPaths) -> list[int]:
    """All chapter numbers written so far, sorted.

    Chapter 0 is not a chapter — legacy books used `chapters/00.md` as a
    dedication before front-matter/ existed, so it is filtered out here to
    keep it from being compiled or linted as prose."""
    if not paths.chapters_dir.exists():
        return []
    nums = []
    for p in paths.chapters_dir.iterdir():
        m = re.match(r"^(\d+)\.md$", p.name)
        if m and int(m.group(1)) >= 1:
            nums.append(int(m.group(1)))
    return sorted(nums)


# A front-matter file is "the dedication" (the page that replaces the
# author byline on the title page) when its stem, after an optional
# `NN-` ordering prefix, is dedication/dedicatoria.
_DEDICATION_STEM = re.compile(r"^(?:\d+-)?dedicat(?:ion|oria)$", re.IGNORECASE)


def front_matter_files(paths: BookPaths) -> list[Path]:
    """Courtesy pages preceding chapter 1, ordered by filename.

    Any `front-matter/*.md`; prefix them `NN-` to control order
    (e.g. `01-dedication.md`, `02-epigraph.md`)."""
    d = paths.front_matter_dir
    if not d.exists():
        return []
    return sorted(p for p in d.iterdir() if p.suffix == ".md" and p.is_file())


def is_dedication(path: Path) -> bool:
    """True if this front-matter file is the dedication (see _DEDICATION_STEM)."""
    return bool(_DEDICATION_STEM.match(path.stem))


def summary_chapter_numbers(paths: BookPaths) -> list[int]:
    """Chapter summary numbers present on disk."""
    if not paths.summaries_dir.exists():
        return []
    nums = []
    for p in paths.summaries_dir.iterdir():
        m = re.match(r"^ch-(\d+)\.md$", p.name)
        if m:
            nums.append(int(m.group(1)))
    return sorted(nums)


def act_numbers(paths: BookPaths) -> list[int]:
    """Act summary numbers present on disk."""
    if not paths.summaries_dir.exists():
        return []
    nums = []
    for p in paths.summaries_dir.iterdir():
        m = re.match(r"^act-(\d+)\.md$", p.name)
        if m:
            nums.append(int(m.group(1)))
    return sorted(nums)
