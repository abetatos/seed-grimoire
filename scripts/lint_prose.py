#!/usr/bin/env python3
"""Deterministic prose-tic auditor — moves tic COUNTING off the LLM.

style.md caps six named tics ("no X, sino Y" once/scene, one "como si" per beat,
the explanatory simile, repetition-as-emphasis, anaphora, adverb/gerund density)
and the writer accumulates signature words across chapters that no single
fresh-session view can see. Asking the critic to count these by eye is exactly
the exhaustive-checklist task an LLM does unreliably. This turns them into
counted evidence: a per-chapter tic table + cross-chapter repetition, written to
notes/_prose-report-chNN.md, for critique-chapter to judge (not recount).

Usage:
    python scripts/lint_prose.py --series-slug S --book-number N --chapter M
    python scripts/lint_prose.py --series-slug S --book-number N --all
    python scripts/lint_prose.py --file path/to/chapter.md   # quick simile check

Exit: 0 (evidence, not a gate) unless --strict (1 if any cap exceeded).
2 = book/chapter/file missing or bad arguments.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths, chapter_numbers
from lib import prose_lint


def _read_chapters(paths, upto: int | None) -> dict[int, str]:
    out: dict[int, str] = {}
    for n in chapter_numbers(paths):
        if upto is not None and n > upto:
            continue
        out[n] = paths.chapter_file(n).read_text(encoding="utf-8")
    return out


def _quick_file_audit(path: Path, args) -> int:
    """Ad-hoc simile-density check on an arbitrary file (no config, no report
    file) — kept for quick spot-checks outside a book layout."""
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    scenes, findings = prose_lint.audit_prose(text)
    total = sum(s.count for s in scenes)
    words = sum(s.word_count for s in scenes)
    rate = (1000.0 * total / words) if words else 0.0
    print(f"{path.name}: {len(scenes)} scene(s), {total} similes / {words} words "
          f"({rate:.1f}/1000)")
    for f in findings:
        print(f"  {f}")
    if not findings:
        print("  ok")
    if args.strict and findings:
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--series-slug")
    p.add_argument("--book-number", type=int)
    p.add_argument("--chapter", type=int,
                   help="Full report for this chapter + cross-chapter up to it.")
    p.add_argument("--all", action="store_true",
                   help="Cross-chapter report only (all chapters), to stdout.")
    p.add_argument("--file", type=Path,
                   help="Quick simile-only audit of an arbitrary Markdown file.")
    p.add_argument("--strict", action="store_true",
                   help="Exit 1 when any cap is exceeded (default: never gate).")
    args = p.parse_args()

    if args.file:
        return _quick_file_audit(args.file, args)

    if not (args.series_slug and args.book_number):
        p.error("provide --file, or both --series-slug and --book-number")
    paths = book_paths(args.series_slug, args.book_number)
    if not paths.book_root.exists():
        print(f"ERROR: book not found: {paths.book_root}", file=sys.stderr)
        return 2

    try:
        config = prose_lint.load_config(paths)
    except prose_lint.UnsupportedLanguageError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.all and args.chapter is None:
        print(prose_lint.render_cross_report(_read_chapters(paths, None), config))
        return 0

    if args.chapter is None:
        p.error("pass --chapter M, --all, or --file")

    chap_file = paths.chapter_file(args.chapter)
    if not chap_file.exists():
        print(f"ERROR: chapter not found: {chap_file}", file=sys.stderr)
        return 2

    text = chap_file.read_text(encoding="utf-8")
    chapters = _read_chapters(paths, upto=args.chapter)
    report = prose_lint.render_chapter_report(args.chapter, text, config)
    if len(chapters) > 1:
        report += "\n" + prose_lint.render_cross_report(chapters, config)

    out_path = paths.notes_dir / f"_prose-report-ch{args.chapter:02d}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    over = [t for t in prose_lint.audit_chapter_tics(text, config) if t.over]
    print(f"lint_prose: config={config.source}; wrote {out_path.name}; "
          f"{len(over)} tic(s) over cap"
          + (": " + ", ".join(t.name for t in over) if over else ""))

    if args.strict and prose_lint.any_cap_exceeded(args.chapter, text, config):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
