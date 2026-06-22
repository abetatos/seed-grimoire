#!/usr/bin/env python3
"""Update one seed in plan/seeds.md: its status and/or its Realized touch-log.

Usage:
    python mark_seed.py --series-slug <slug> --book-number <n> \\
        --seed-id <id> --status <new_status> \\
        [--realized "chN: the image AS WRITTEN this chapter"]

Valid statuses: planned, planted, echoed-1, echoed-2, echoed-3, paid_off

``--realized`` appends one line to the seed's Realized log (the touch-log of how
the seed actually landed on the page) — record it every time you plant or echo a
seed, so a far-later payoff rhymes with the prose, not the plan. Both edits are
surgical: only the matched seed's lines change.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib import seeds as seeds_mod

VALID_STATUSES = {"planned", "planted", "echoed-1", "echoed-2", "echoed-3", "echoed-4", "paid_off"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--seed-id", required=True)
    parser.add_argument("--status", required=False)
    parser.add_argument("--realized", required=False,
                        help='append one Realized touch-log line, e.g. "ch3: ..."')
    args = parser.parse_args()

    if not args.status and not args.realized:
        print("ERROR: pass --status and/or --realized (nothing to do).", file=sys.stderr)
        return 2
    if args.status and args.status not in VALID_STATUSES:
        print(f"ERROR: invalid status '{args.status}'. Valid: {sorted(VALID_STATUSES)}", file=sys.stderr)
        return 2

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.seeds_md.exists():
        print(f"ERROR: seeds file not found: {paths.seeds_md}", file=sys.stderr)
        return 3

    # Surgical in-place edits — never a lossy parse→regenerate round-trip
    # (seeds.md is a NEVER-compress file).
    text = paths.seeds_md.read_text(encoding="utf-8")
    done = []
    if args.realized:
        text, found = seeds_mod.append_realized_in_text(text, args.seed_id, args.realized)
        if not found:
            print(f"ERROR: seed id '{args.seed_id}' not found in {paths.seeds_md}", file=sys.stderr)
            return 3
        done.append(f"realized += \"{args.realized}\"")
    if args.status:
        text, found = seeds_mod.update_status_in_text(text, args.seed_id, args.status)
        if not found:
            print(f"ERROR: seed id '{args.seed_id}' not found in {paths.seeds_md}", file=sys.stderr)
            return 3
        done.append(f"status → {args.status}")

    paths.seeds_md.write_text(text, encoding="utf-8")
    print(f"seed '{args.seed_id}': " + "; ".join(done))
    return 0


if __name__ == "__main__":
    sys.exit(main())
