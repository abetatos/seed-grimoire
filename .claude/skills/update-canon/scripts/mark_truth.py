#!/usr/bin/env python3
"""Update one shadow truth in plan/shadow.md: its reveal status and/or Surfaced log.

Usage:
    python mark_truth.py --series-slug <slug> --book-number <n> \\
        --truth-id <id> --status <new_status> \\
        [--surfaced "chN [sensed]: how the reader was brought, AS WRITTEN"]

Reveal ladder (the READER'S interior state, never how loudly to write):
    hidden → sensed → suspected → confirmed

The new status is REFUSED if it exceeds the truth's ``Reveal cap`` — the loudest
the truth may get in this book (truths that pay off in a later book cap below
``confirmed``). ``--surfaced`` appends one line to the touch-log of how the
reveal actually landed on the page. Both edits are surgical: only the matched
truth's lines change (shadow.md is a NEVER-compress, hand-authored file).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib import shadows as shadows_mod


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--truth-id", required=True)
    parser.add_argument("--status", required=False,
                        help=f"one of {shadows_mod.REVEAL_LEVELS}")
    parser.add_argument("--surfaced", required=False,
                        help='append one Surfaced line, e.g. "ch8 [sensed]: ..."')
    args = parser.parse_args()

    if not args.status and not args.surfaced:
        print("ERROR: pass --status and/or --surfaced (nothing to do).", file=sys.stderr)
        return 2
    if args.status and args.status not in shadows_mod.REVEAL_LEVELS:
        print(f"ERROR: invalid status '{args.status}'. Valid: {shadows_mod.REVEAL_LEVELS}",
              file=sys.stderr)
        return 2

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.shadow_md.exists():
        print(f"ERROR: shadow file not found: {paths.shadow_md}", file=sys.stderr)
        return 3

    text = paths.shadow_md.read_text(encoding="utf-8")

    # Cap guardrail: refuse to push a truth past the loudest it may sound here.
    if args.status:
        truth = next((t for t in shadows_mod.parse_truths(text) if t.id == args.truth_id), None)
        if truth is None:
            print(f"ERROR: truth id '{args.truth_id}' not found in {paths.shadow_md}",
                  file=sys.stderr)
            return 3
        idx = shadows_mod._level_index
        if idx(args.status) > idx(truth.reveal_cap):
            print(
                f"ERROR: '{args.status}' exceeds reveal cap '{truth.reveal_cap}' for "
                f"truth '{args.truth_id}'. This truth must not get louder than its cap "
                f"in this book (it pays off later). Cap it, or change Reveal cap in shadow.md "
                f"on purpose.",
                file=sys.stderr,
            )
            return 2

    done = []
    if args.surfaced:
        text, found = shadows_mod.append_surfaced_in_text(text, args.truth_id, args.surfaced)
        if not found:
            print(f"ERROR: truth id '{args.truth_id}' not found in {paths.shadow_md}",
                  file=sys.stderr)
            return 3
        done.append(f"surfaced += \"{args.surfaced}\"")
    if args.status:
        text, found = shadows_mod.update_truth_status_in_text(text, args.truth_id, args.status)
        if not found:
            print(f"ERROR: truth id '{args.truth_id}' not found in {paths.shadow_md}",
                  file=sys.stderr)
            return 3
        done.append(f"status → {args.status}")

    paths.shadow_md.write_text(text, encoding="utf-8")
    print(f"truth '{args.truth_id}': " + "; ".join(done))
    return 0


if __name__ == "__main__":
    sys.exit(main())
