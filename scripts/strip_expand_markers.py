#!/usr/bin/env python3
"""Strip expand-chapter banner lines from chapter prose (in place).

expand-chapter wraps every inserted zone in visible ``▼▼▼ INICIO EXPAND N ▼▼▼``
… ``▲▲▲ FIN EXPAND N ▲▲▲`` banners so the author can tell machine-added prose
from original while drafting (including on Kindle). The SKILL calls this a
temporary standard "stripped in a later cleanup pass" — this IS that pass. It
removes only the banner lines; the prose between them is kept byte-for-byte.

Usage:
    python scripts/strip_expand_markers.py --series-slug S --book-number N --chapter M
    python scripts/strip_expand_markers.py --series-slug S --book-number N --all
    python scripts/strip_expand_markers.py --series-slug S --book-number N --all --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths, chapter_numbers
from lib.parsing import _EXPAND_MARKER_RE, strip_expand_markers


def _process(path: Path, dry_run: bool) -> int:
    """Return the number of banner lines removed from ``path``."""
    text = path.read_text(encoding="utf-8")
    n = len(_EXPAND_MARKER_RE.findall(text))
    if n and not dry_run:
        path.write_text(strip_expand_markers(text), encoding="utf-8")
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chapter", type=int)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report banner lines per chapter without editing.")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    chapters = chapter_numbers(paths) if args.all else [args.chapter]

    total = 0
    for n in chapters:
        p = paths.chapter_file(n)
        if not p.exists():
            print(f"chapter {n}: (missing)")
            continue
        removed = _process(p, args.dry_run)
        total += removed
        verb = "would remove" if args.dry_run else "removed"
        print(f"chapter {n:02d}: {verb} {removed} marker line(s)")

    action = "would strip" if args.dry_run else "stripped"
    print(f"\n{action} {total} marker line(s) across {len(chapters)} chapter(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
