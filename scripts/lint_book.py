#!/usr/bin/env python3
"""Deterministic auditor of a book's on-disk state.

Turns a dozen continuity invariants (seed schedule sanity, seed↔shadow
referential integrity, lock-in completeness, book-summary freshness) into exit
codes so the pipeline can gate on a script instead of a careful read.

Usage:
    python scripts/lint_book.py --series-slug <slug> --book-number <n> [--strict]

Exit: 0 = clean or WARN-only; 1 = any ERROR (or any finding with --strict).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib import lint


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on WARN findings too, not just ERROR.")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.book_root.exists():
        print(f"ERROR: book not found: {paths.book_root}", file=sys.stderr)
        return 2

    findings = lint.lint_book(paths)
    for f in findings:
        print(str(f))

    errors = sum(1 for f in findings if f.level == lint.ERROR)
    warns = sum(1 for f in findings if f.level == lint.WARN)
    print(f"\nlint: {errors} error(s), {warns} warning(s)")

    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
