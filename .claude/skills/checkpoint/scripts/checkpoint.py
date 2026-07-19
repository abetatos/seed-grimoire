#!/usr/bin/env python3
"""Checkpoint helper — ensures notes files exist and reports current state.

This script does not extract knowledge from the conversation. That's the
agent's job (the `checkpoint` SKILL.md). The script's job is to:

  1. Create any missing notes files with their template.
  2. Print the current state of each (so the agent knows what's already
     captured and what's new).

Usage:
    python checkpoint.py --series-slug <slug> --book-number <n>
    python checkpoint.py --series-slug <slug> --book-number <n> --report
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib import notes_files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--report", action="store_true", help="Print current state of notes files.")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.book_root.exists():
        print(f"ERROR: book directory not found: {paths.book_root}", file=sys.stderr)
        return 2

    created = notes_files.ensure(paths)

    print("Checkpoint files:")
    for key, path in (
        ("voice", paths.voice_md),
        ("style_rules", paths.style_rules_md),
        ("session_handoff", paths.session_handoff_md),
    ):
        status = "(new)" if created.get(key) else "(exists)"
        print(f"  {status} {path}")

    if args.report:
        contents = notes_files.read_all(paths)
        for key, body in contents.items():
            print()
            print(f"=== {key}.md ===")
            print(body.rstrip())

    print()
    print("Next: agent updates these files with new observations.")
    print(f"Date stamp for new entries: {notes_files.today_stamp()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
