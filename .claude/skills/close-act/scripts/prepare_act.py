#!/usr/bin/env python3
"""Prepare the inputs for compressing one act into an act-level summary.

Bundles the chapter summaries that fall inside an act range into a single
file the agent can read and condense, plus writes an empty act-NN.md
skeleton for the agent to fill.

Usage:
    python prepare_act.py --series-slug <slug> --book-number <n> --act <a>
    python prepare_act.py --series-slug <slug> --book-number <n> --act <a> --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths, summary_chapter_numbers
from lib import summaries as sum_mod


ACT_SUMMARY_TEMPLATE = """# Act {act} — summary (chapters {lo}-{hi})

> Target ~1500 words. Read by future chapters as the canonical account of
> this act once the individual chapter summaries fall out of the recent
> window. **Seeds and shadow are NOT compressed** — they remain in
> `plan/seeds.md` and `plan/shadow.md`.

## What this act did for the book
> TODO: 4-6 bullets — the act's function in the larger arc.

## Plot — sequence of events
> TODO: 10-20 short bullets, chronological. Focus on irreversibles
> (decisions made, deaths, alliances, geographic moves). Do not retell
> texture beats.

## Character state changes
> TODO: one block per principal, 2-3 lines on what shifted.

## Magic / world disclosures
> TODO: any new rules, costs, places, vocabulary introduced this act.

## Seeds activity (reference only — see plan/seeds.md for source of truth)
> TODO: list the seed ids that were planted / echoed / paid this act.

## At the end of the act
> TODO: 3-5 lines — where each principal is, what the world believes,
> what threads are live entering the next act.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--act", type=int, required=True)
    parser.add_argument(
        "--chapters-per-act",
        type=int,
        default=sum_mod.DEFAULT_CHAPTERS_PER_ACT,
        help="How many chapters per act (must match writer config).",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    paths.ensure_dirs()

    lo, hi = sum_mod.act_range(args.act, args.chapters_per_act)
    present = [n for n in summary_chapter_numbers(paths) if lo <= n <= hi]
    if not present:
        print(f"ERROR: no chapter summaries in range {lo}-{hi} for act {args.act}.", file=sys.stderr)
        return 2

    # Bundle the per-chapter summaries into a single working file.
    bundle_path = paths.notes_dir / f"_act-{args.act:02d}-bundle.md"
    parts = [f"# Inputs for act {args.act} compression (chapters {lo}-{hi})\n"]
    for n in present:
        body = paths.chapter_summary(n).read_text(encoding="utf-8").strip()
        parts.append(f"\n---\n## Source: ch-{n:02d}.md\n\n{body}\n")
    bundle_path.write_text("\n".join(parts), encoding="utf-8")

    act_path = paths.act_summary(args.act)
    if act_path.exists() and not args.force:
        print(f"act summary already exists: {act_path} (use --force to overwrite)")
    else:
        act_path.write_text(
            ACT_SUMMARY_TEMPLATE.format(act=args.act, lo=lo, hi=hi),
            encoding="utf-8",
        )
        print(f"act skeleton written: {act_path}")

    print()
    print(f"chapters in act {args.act}: {present}")
    print(f"bundle of source summaries: {bundle_path}")
    print(f"act skeleton to fill: {act_path}")
    print()
    print("REMINDER: do NOT compress plan/seeds.md or plan/shadow.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
