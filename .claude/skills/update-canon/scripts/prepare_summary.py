#!/usr/bin/env python3
"""Prepare the chapter summary skeleton + report what canon updates are due.

Run AFTER the chapter prose is finalized. This script does the deterministic
file work so the agent can focus on summary content:

  1. Reads chapters/NN.md.
  2. Writes summaries/ch-NN.md skeleton (if it doesn't exist).
  3. Lists the seed envelope for chapter N so the agent can update statuses.
  4. Lists the canon files the agent should consider updating.

Usage:
    python prepare_summary.py --series-slug <slug> --book-number <n> --chapter <m>
    python prepare_summary.py --series-slug <slug> --book-number <n> --chapter <m> --force
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib import setup_doc, seeds as seeds_mod, wordcount


SUMMARY_TEMPLATE = """# Chapter {n} — summary

> 400-500 words. Structured. Read by future chapters as the canonical
> account of what happened here. Keep tight; do not retell the prose.

**Word count of chapter:** {actual}
**POV:** > TODO:
**Where / when:** > TODO:

## What happened (visible plot)
> TODO: 4-8 bullet points, in order.

## Texture beats present
> TODO: 1-2 lines naming the dwelling moments (e.g., "the artisans'
> quarter at dawn, the river bath, the bell at sundown").

## Subtext / interior shifts
> TODO: what changed underneath. Decisions delayed, lies protected,
> wounds touched.

## Seeds in play this chapter
{seed_block}

## Anchor quotes (verbatim)
> TODO: 2-3 EXACT lines quoted from the chapter («…»), chosen so a later payoff
> can rhyme with the page after the prose leaves the context window: the
> strongest seed-touch line, the chapter's end-state line, one voice-defining
> line. Copy-paste, never paraphrase — `lint_book.py` verifies these against the
> prose.

## Canon updates required (writer's notes)
> TODO: list any new facts that should be promoted to canon —
> a new place name, a new minor character, a new rule of magic
> observed. Mark each with the target canon file (e.g.,
> "canon/world.md: river Soral, north of Vael").

## Carry forward (next chapter)
> TODO: 1-3 lines on what state characters/world are in at chapter end.
"""


def _render_seed_block(envelope: dict) -> str:
    lines = []
    sections = [
        ("Planted", envelope["plant"]),
        ("Echoed", envelope["echo"]),
        ("Paid off", envelope["payoff"]),
    ]
    any_active = any(items for _, items in sections)
    if not any_active:
        return "(no seeds active in this chapter)"
    for label, items in sections:
        if items:
            lines.append(f"- **{label}:**")
            for s in items:
                lines.append(f"  - `{s.id}` — {s.detail}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    ch_path = paths.chapter_file(args.chapter)
    if not ch_path.exists():
        print(f"ERROR: chapter not written: {ch_path}", file=sys.stderr)
        return 2

    # T12: if the critique recorded a chapter hash, confirm the chapter has not
    # changed since it was audited. A mismatch means the prose was edited after
    # the critique PASS — lock-in must not proceed on an un-audited chapter.
    critique_path = paths.notes_dir / f"critique-ch{args.chapter:02d}.md"
    if critique_path.exists() and not args.force:
        m = re.search(r"\*\*Chapter-hash:\*\*\s*([0-9a-f]{64})",
                      critique_path.read_text(encoding="utf-8"))
        if m:
            current = hashlib.sha256(ch_path.read_bytes()).hexdigest()
            if current != m.group(1):
                print(
                    f"ERROR: chapter {args.chapter} changed since it was critiqued "
                    f"(hash mismatch).\n"
                    f"  critiqued: {m.group(1)}\n  current:   {current}\n"
                    f"Re-run the consistency pass (or re-critique) before locking in. "
                    f"Use --force to override.",
                    file=sys.stderr,
                )
                return 4

    paths.ensure_dirs()

    setup_text = setup_doc.load(paths.setup_md)
    lo, hi = setup_doc.words_per_chapter_range(setup_text)
    actual = wordcount.count_words(ch_path.read_text(encoding="utf-8"))
    rep = wordcount.report(actual, lo, hi)

    seeds_list = seeds_mod.load_seeds(paths.seeds_md)
    envelope = seeds_mod.envelope_for_chapter(seeds_list, args.chapter)
    seed_block = _render_seed_block(envelope)

    summary_path = paths.chapter_summary(args.chapter)
    if summary_path.exists() and not args.force:
        print(f"summary already exists: {summary_path} (use --force to overwrite)")
    else:
        summary_path.write_text(
            SUMMARY_TEMPLATE.format(n=args.chapter, actual=actual, seed_block=seed_block),
            encoding="utf-8",
        )
        print(f"summary skeleton written: {summary_path}")

    # Report next steps for the agent.
    print()
    print(f"chapter: {args.chapter}")
    print(f"  words: {rep.describe()}")
    if rep.is_too_short:
        print(f"  WARNING: chapter is too short. Consider expand-chapter before locking in.")
    print(f"seed envelope for chapter {args.chapter}:")
    for label, items in (("plant", envelope["plant"]), ("echo", envelope["echo"]), ("payoff", envelope["payoff"])):
        for s in items:
            print(f"  - {label}: {s.id} (current status: {s.status})")
    if not (envelope["plant"] or envelope["echo"] or envelope["payoff"]):
        print("  (none scheduled)")

    # Suggest canon files to inspect.
    print()
    print("canon files to review for updates:")
    for name in ("characters", "factions", "magic", "world", "timeline"):
        p = paths.canon_file(name)
        print(f"  - {p} {'(exists)' if p.exists() else '(missing)'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
