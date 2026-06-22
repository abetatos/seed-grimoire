#!/usr/bin/env python3
"""Assemble the writer's context for a single chapter and write it to disk.

The agent reads the resulting file before writing the chapter. The file is
deterministic, so re-running the script regenerates an identical bundle.

Output:
    output/<series>/book-NN/notes/_context-ch<NN>.md

Usage:
    python build_context.py --series-slug <slug> --book-number <n> --chapter <m>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.context import build_context
from lib.paths import book_paths
from lib import setup_doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument(
        "--phase",
        choices=("write", "plan", "critique"),
        default="write",
        help="Tailor the bundle to the reader. 'plan' and 'critique' drop the "
        "heavy recent-chapters-in-full block (and 'plan' also the style guide / "
        "craft checklist); 'write' is the full bundle. Default: write.",
    )
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)

    if not paths.setup_md.exists():
        print(f"ERROR: setup.md not found at {paths.setup_md}", file=sys.stderr)
        return 2
    if not paths.outline_md.exists():
        print(f"ERROR: plan/outline.md not found. Run plan-book first.", file=sys.stderr)
        return 2

    paths.ensure_dirs()
    bundle = build_context(paths, args.chapter, phase=args.phase)

    out_path = paths.notes_dir / f"_context-ch{args.chapter:02d}.md"
    out_path.write_text(bundle, encoding="utf-8")

    # Print a short summary for the agent.
    setup_text = setup_doc.load(paths.setup_md)
    lo, hi = setup_doc.words_per_chapter_range(setup_text)
    lang = setup_doc.language(setup_text)

    word_count = len(bundle.split())
    print(f"Context written: {out_path}")
    print(f"  language: {lang}")
    print(f"  target words for chapter {args.chapter}: {lo}-{hi}")
    print(f"  context size: {word_count} words (~{word_count * 4 // 3} tokens approx)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
