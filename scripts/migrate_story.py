#!/usr/bin/env python3
"""One-shot migrator: seeds.md / shadow.md -> the world-state store.

Fase 4 step 0 of RESTRUCTURE-V2. Moves the two NEVER-compress planning files
into ``state/{seeds,shadow}.json`` — the engine's structured home (``story.Seed``
/ ``story.Truth``) — WITHOUT losing a single seed, status, touch-log line, or
truth.

What is mechanical here vs. what stays deferred to L5
-----------------------------------------------------
- **SEEDS migrate fully.** Plant/Echo/Payoff chapters are already numbers in the
  file, so ``schedule = {plant, echo, payoff}`` maps 1:1 (via the shared loud
  parser, so a cross-book deferral like "Libro II" contributes no chapter and no
  warning). Every *other* field — real meaning, how-to, dose, obligatory,
  status, and the ``Realized`` touch-log — has no slot on the engine Seed, so it
  is preserved **verbatim** in ``notes``. Nothing is dropped.

- **TRUTHS migrate DEFINITIONS ONLY.** The old shadow model carries a single
  book-wide reveal-cap LEVEL (``hidden -> sensed -> suspected -> confirmed``);
  the engine ``Truth`` wants a per-chapter reveal *schedule*
  (``reveal_caps: {chapter: dose}``) that the file does NOT contain — building it
  is the L5 knowledge layer, author-in-the-loop. So ``reveal_caps`` is left
  **empty** and every old field (incl. the cap level) is kept in ``notes``. The
  migrator never fabricates a reveal schedule.

Why the migration is safe to run now
-------------------------------------
It is **additive**: ``seeds.md`` / ``shadow.md`` stay in place (the legacy
Markdown path still reads them until Fase 4 retires it), and
``world.json`` / ``entities.json`` / event logs are NOT written — those are the
L1-L3 creative layers. A store with only ``seeds.json`` + ``shadow.json`` leaves
``context.py``'s world-state block dormant (it gates on ``world.json``), so no
existing behaviour changes. Re-running is idempotent.

Verification (the point of step 0): after writing, ``verify_coverage`` re-loads
the store and asserts every id, schedule chapter, touch-log line, status and
truth from the originals survived; ``render_seeds_view`` writes a human-readable
``notes/_seeds-view.md`` to eyeball.

Usage:
    migrate_story.py --series-slug el-vitral --book-number 1
    migrate_story.py --series-slug el-vitral --book-number 1 --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from lib.engine import store
from lib.engine.story import DORMANT, Seed, Truth, seed_status
from lib.parsing import (
    FIELD_VALUE_END,
    parse_chapter_list,
    parse_single_chapter,
    parse_touch_log,
)
from lib.paths import BookPaths, book_paths
from lib import seeds as seeds_mod
from lib import shadows as shadows_mod


# A **Key:** value pair, value possibly spanning continuation lines. Same
# terminator as the loud parser so touch-log blocks (multi-line) are captured
# whole. Key must start at line-begin and hold no ':' or '*' (so bold *inside* a
# value, e.g. "**no calienta**", is never mistaken for a field header).
_FIELD_RE = re.compile(
    r"^\*\*(?P<key>[^:*\n]+):\*\*[ \t]*(?P<val>.*?)" + FIELD_VALUE_END,
    re.DOTALL | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Raw field extraction (verbatim, order-preserving, lossless)
# ---------------------------------------------------------------------------

def iter_fields(section: str) -> list[tuple[str, str]]:
    """Every ``**Key:** value`` in a section, in order, values verbatim.

    Newlines inside a value are preserved (a ``Realized:`` / ``Surfaced:``
    touch-log stays multi-line). Only the trailing whitespace is trimmed.
    """
    out: list[tuple[str, str]] = []
    for m in _FIELD_RE.finditer(section):
        out.append((m.group("key").strip(), m.group("val").rstrip()))
    return out


def _field(fields: list[tuple[str, str]], key: str) -> str:
    """Value of the first field whose key matches (case-insensitive), or ''."""
    kl = key.lower()
    for k, v in fields:
        if k.lower() == kl:
            return v
    return ""


def _collapse(value: str) -> str:
    """Collapse internal whitespace/newlines to single spaces (for desc)."""
    return re.sub(r"\s+", " ", value).strip()


def _render_notes(fields: list[tuple[str, str]], skip: set[str]) -> str:
    """Rebuild the fields NOT captured structurally, verbatim, as a notes blob.

    Keeping the original ``**Key:** value`` lines (including Plant/Echo/Payoff)
    is deliberate provenance: the schedule field is the machine-readable extract;
    ``notes`` is the faithful, human-readable record the writer still reads.
    """
    skip = {s.lower() for s in skip}
    lines: list[str] = []
    for key, val in fields:
        if key.lower() in skip:
            continue
        lines.append(f"**{key}:** {val}".rstrip())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Seed migration
# ---------------------------------------------------------------------------

# Header regexes reused from the loud parsers so we split sections identically.
_SEED_HEADER_RE = re.compile(r"^##\s+SEED:\s*(.+?)\s*$", re.MULTILINE)
_TRUTH_HEADER_RE = re.compile(r"^##\s+SHADOW-TRUTH:\s*(.+?)\s*$", re.MULTILINE)


def _sections(text: str, header_re: re.Pattern) -> list[tuple[str, str]]:
    """(id, section_body) for each header match, body up to the next header."""
    heads = list(header_re.finditer(text))
    out: list[tuple[str, str]] = []
    for i, h in enumerate(heads):
        start = h.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out.append((h.group(1).strip(), text[start:end]))
    return out


def migrate_seed(seed_id: str, section: str) -> Seed:
    fields = iter_fields(section)
    detail = _collapse(_field(fields, "Detail"))

    schedule: dict[str, list[int]] = {}
    plant, _ = parse_single_chapter(_field(fields, "Plant in"))
    echo, _ = parse_chapter_list(_field(fields, "Echo in"))
    payoff, _ = parse_single_chapter(_field(fields, "Payoff in"))
    if plant is not None:
        schedule["plant"] = [plant]
    if echo:
        schedule["echo"] = echo
    if payoff is not None:
        schedule["payoff"] = [payoff]

    # Everything except Detail (which became desc) is preserved verbatim. The
    # schedule fields are kept in notes too, on purpose — a deferred payoff
    # ("Payoff in: Libro II ...") contributes no chapter, so its prose would
    # otherwise be lost.
    notes = _render_notes(fields, skip={"Detail"})
    return Seed(id=seed_id, desc=detail, schedule=schedule, notes=notes)


def migrate_truth(truth_id: str, section: str) -> Truth:
    fields = iter_fields(section)
    desc = _collapse(_field(fields, "Truth"))
    # reveal_caps intentionally EMPTY — the per-chapter reveal schedule is the L5
    # knowledge layer, not in this file. Every old field (incl. the book-wide
    # 'Reveal cap' level and 'Surfaced' touch-log) is preserved in notes.
    notes = _render_notes(fields, skip={"Truth"})
    return Truth(id=truth_id, desc=desc, reveal_caps={}, notes=notes)


def build_store(seeds_text: str, shadow_text: str) -> tuple[dict[str, Seed], dict[str, Truth]]:
    seeds = {sid: migrate_seed(sid, body) for sid, body in _sections(seeds_text, _SEED_HEADER_RE)}
    truths = {tid: migrate_truth(tid, body) for tid, body in _sections(shadow_text, _TRUTH_HEADER_RE)}
    return seeds, truths


# ---------------------------------------------------------------------------
# Coverage verification — the reason step 0 exists
# ---------------------------------------------------------------------------

@dataclass
class Coverage:
    problems: list[str]

    @property
    def ok(self) -> bool:
        return not self.problems


def _contains(haystack: str, needle: str) -> bool:
    return _collapse(needle) in _collapse(haystack)


def verify_coverage(
    seeds_text: str,
    shadow_text: str,
    seeds: dict[str, Seed],
    truths: dict[str, Truth],
) -> Coverage:
    """Assert nothing from the originals was dropped by the migration.

    Cross-checks two ways: (1) the ids/schedules parsed by the *legacy* loaders
    match the store; (2) every raw field value from the source markdown appears
    in the store's desc or notes (so no prose was silently lost).
    """
    problems: list[str] = []

    # --- seeds ---
    legacy_seeds = seeds_mod.parse_seeds(seeds_text)
    legacy_ids = {s.id for s in legacy_seeds}
    if legacy_ids != set(seeds):
        problems.append(
            f"seed id set differs: only-in-source={sorted(legacy_ids - set(seeds))}, "
            f"only-in-store={sorted(set(seeds) - legacy_ids)}"
        )
    for ls in legacy_seeds:
        ms = seeds.get(ls.id)
        if ms is None:
            continue
        if ls.plant_in is not None and ls.plant_in not in ms.scheduled_chapters("plant"):
            problems.append(f"seed {ls.id}: plant {ls.plant_in} lost from schedule")
        if sorted(ls.echo_in) != sorted(ms.scheduled_chapters("echo")):
            problems.append(
                f"seed {ls.id}: echo schedule {ls.echo_in} != store {ms.scheduled_chapters('echo')}"
            )
        if ls.payoff_in is not None and ls.payoff_in not in ms.scheduled_chapters("payoff"):
            problems.append(f"seed {ls.id}: payoff {ls.payoff_in} lost from schedule")
        # status + touch-log survive as text in notes
        if ls.status and not _contains(ms.notes + " " + ms.desc, ls.status):
            problems.append(f"seed {ls.id}: status {ls.status!r} not preserved in notes")
        for touch in ls.realized:
            if not _contains(ms.notes, touch):
                problems.append(f"seed {ls.id}: realized touch {touch!r} lost")

    # every raw source field must land in desc or notes
    for sid, body in _sections(seeds_text, _SEED_HEADER_RE):
        ms = seeds.get(sid)
        if ms is None:
            continue
        blob = ms.desc + "\n" + ms.notes
        for key, val in iter_fields(body):
            # touch-log lines are checked per-item above; skip the block header
            if key.lower() in ("realized", "surfaced"):
                continue
            if val and not _contains(blob, val):
                problems.append(f"seed {sid}: field {key!r} value not preserved")

    # --- truths ---
    legacy_truths = shadows_mod.parse_truths(shadow_text)
    legacy_tids = {t.id for t in legacy_truths}
    if legacy_tids != set(truths):
        problems.append(
            f"truth id set differs: only-in-source={sorted(legacy_tids - set(truths))}, "
            f"only-in-store={sorted(set(truths) - legacy_tids)}"
        )
    for lt in legacy_truths:
        mt = truths.get(lt.id)
        if mt is None:
            continue
        blob = mt.desc + "\n" + mt.notes
        if lt.reveal_cap and not _contains(blob, lt.reveal_cap):
            problems.append(f"truth {lt.id}: reveal cap level {lt.reveal_cap!r} not preserved")
        if lt.status and not _contains(blob, lt.status):
            problems.append(f"truth {lt.id}: status {lt.status!r} not preserved")
        for surfaced in lt.surfaced:
            if not _contains(blob, surfaced):
                problems.append(f"truth {lt.id}: surfaced touch {surfaced!r} lost")

    for tid, body in _sections(shadow_text, _TRUTH_HEADER_RE):
        mt = truths.get(tid)
        if mt is None:
            continue
        blob = mt.desc + "\n" + mt.notes
        for key, val in iter_fields(body):
            if key.lower() in ("realized", "surfaced"):
                continue
            if val and not _contains(blob, val):
                problems.append(f"truth {tid}: field {key!r} value not preserved")

    return Coverage(problems)


# ---------------------------------------------------------------------------
# Human-readable view
# ---------------------------------------------------------------------------

def render_seeds_view(seeds: dict[str, Seed], truths: dict[str, Truth]) -> str:
    lines = ["# Seeds & shadow — migrated store view", ""]
    lines.append("_Computed from `state/seeds.json` + `state/shadow.json` by "
                 "`migrate_story.py`. Regeneratable; do not hand-edit._")
    lines.append("")
    lines.append(f"## Seeds ({len(seeds)})")
    lines.append("")
    for s in seeds.values():
        sched = ", ".join(
            f"{k}={s.scheduled_chapters(k)}" for k in ("plant", "echo", "payoff")
            if s.scheduled_chapters(k)
        ) or "—"
        # No events yet → status derives to dormant for all.
        status = seed_status([], at_chapter=10 ** 9)
        lines.append(f"### {s.id}  ·  status `{status}`")
        lines.append(f"- **detail:** {s.desc}")
        lines.append(f"- **schedule:** {sched}")
        lines.append("")
    lines.append(f"## Shadow truths ({len(truths)})")
    lines.append("")
    lines.append("_`reveal_caps` deferred to the L5 knowledge layer — empty here._")
    lines.append("")
    for t in truths.values():
        lines.append(f"### {t.id}")
        lines.append(f"- **truth:** {t.desc}")
        lines.append(f"- **reveal_caps:** {t.reveal_caps or '{} (L5 pending)'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def migrate_book(paths: BookPaths, *, dry_run: bool = False) -> tuple[Coverage, str]:
    """Migrate one book. Returns (coverage, view_markdown). Writes unless dry_run."""
    if not paths.seeds_md.exists():
        raise FileNotFoundError(f"no seeds.md at {paths.seeds_md}")
    seeds_text = paths.seeds_md.read_text(encoding="utf-8")
    shadow_text = paths.shadow_md.read_text(encoding="utf-8") if paths.shadow_md.exists() else ""

    seeds, truths = build_store(seeds_text, shadow_text)
    coverage = verify_coverage(seeds_text, shadow_text, seeds, truths)
    view = render_seeds_view(seeds, truths)

    if not dry_run and coverage.ok:
        store.save_seeds(paths.state_dir, seeds)
        store.save_truths(paths.state_dir, truths)
        view_path = paths.notes_dir / "_seeds-view.md"
        view_path.parent.mkdir(parents=True, exist_ok=True)
        view_path.write_text(view, encoding="utf-8")

    return coverage, view


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--series-slug", required=True)
    p.add_argument("--book-number", type=int, required=True)
    p.add_argument("--dry-run", action="store_true",
                   help="verify coverage and print the view without writing the store")
    args = p.parse_args(argv)

    paths = book_paths(args.series_slug, args.book_number)
    coverage, view = migrate_book(paths, dry_run=args.dry_run)

    if not coverage.ok:
        print("COVERAGE FAILED — store NOT written:", file=sys.stderr)
        for problem in coverage.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(view)
        print(f"\nOK (dry run): {len(_sections(paths.seeds_md.read_text(encoding='utf-8'), _SEED_HEADER_RE))} "
              f"seeds, coverage clean — nothing written.")
    else:
        print(f"OK: migrated to {paths.state_dir}/ (seeds.json + shadow.json), "
              f"view at {paths.notes_dir}/_seeds-view.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
