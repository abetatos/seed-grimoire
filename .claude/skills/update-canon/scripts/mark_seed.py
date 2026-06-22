#!/usr/bin/env python3
"""Update the status field of one seed in plan/seeds.md.

Usage:
    python mark_seed.py --series-slug <slug> --book-number <n> \\
        --seed-id <id> --status <new_status>

Valid statuses: planned, planted, echoed-1, echoed-2, echoed-3, paid_off
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
    parser.add_argument("--status", required=True)
    args = parser.parse_args()

    if args.status not in VALID_STATUSES:
        print(f"ERROR: invalid status '{args.status}'. Valid: {sorted(VALID_STATUSES)}", file=sys.stderr)
        return 2

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.seeds_md.exists():
        print(f"ERROR: seeds file not found: {paths.seeds_md}", file=sys.stderr)
        return 3

    # Surgical in-place edit of just the **Status:** line — never a lossy
    # parse→regenerate round-trip (seeds.md is a NEVER-compress file).
    text = paths.seeds_md.read_text(encoding="utf-8")
    new_text, found = seeds_mod.update_status_in_text(text, args.seed_id, args.status)
    if not found:
        print(f"ERROR: seed id '{args.seed_id}' not found in {paths.seeds_md}", file=sys.stderr)
        return 3

    if new_text != text:
        paths.seeds_md.write_text(new_text, encoding="utf-8")
    print(f"seed '{args.seed_id}' → {args.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
