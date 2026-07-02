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
from lib.parsing import strip_expand_markers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument(
        "--phase",
        choices=("write", "plan", "critique", "expand"),
        default="write",
        help="Tailor the bundle to the reader. 'plan' and 'critique' drop the "
        "heavy recent-chapters-in-full block (and 'plan' also the style guide / "
        "craft checklist); 'expand' additionally drops series/shadow/plan/"
        "story/seam (a texture pass needs none of them); 'write' is the full "
        "bundle. Default: write.",
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

    # For critique: also emit a marker-stripped copy of the chapter, so the
    # critic never sees the expand-chapter scaffolding (which used to draw a
    # false "scaffolding left in the body" MUST that bounced clean chapters).
    clean_path = None
    chapter_hash = None
    if args.phase == "critique":
        ch_file = paths.chapter_file(args.chapter)
        if ch_file.exists():
            clean_path = paths.notes_dir / f"_chapter-clean-ch{args.chapter:02d}.md"
            clean_path.write_text(
                strip_expand_markers(ch_file.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
            # Hash the ORIGINAL chapter so the critique can record it and
            # update-canon can later confirm nothing changed since (T12).
            import hashlib
            chapter_hash = hashlib.sha256(ch_file.read_bytes()).hexdigest()

    # Print a short summary for the agent.
    setup_text = setup_doc.load(paths.setup_md)
    lo, hi = setup_doc.words_per_chapter_range(setup_text)
    lang = setup_doc.language(setup_text)

    word_count = len(bundle.split())
    print(f"Context written: {out_path}")
    print(f"  language: {lang}")
    print(f"  target words for chapter {args.chapter}: {lo}-{hi}")
    print(f"  context size: {word_count} words (~{word_count * 4 // 3} tokens approx)")
    if clean_path is not None:
        print(f"  marker-stripped chapter for the critic: {clean_path}")
    if chapter_hash is not None:
        print(f"  Chapter-hash (sha256): {chapter_hash}")
        print(f"    → record this in critique-ch{args.chapter:02d}.md as "
              f"'**Chapter-hash:** {chapter_hash}' so update-canon can verify.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
