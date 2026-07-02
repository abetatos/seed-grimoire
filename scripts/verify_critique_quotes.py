#!/usr/bin/env python3
"""Verify that a chapter critique's quoted lines actually exist in the prose.

The critique format requires every MUST finding to quote the offending line.
Nothing checked that the quote was real, so a hallucinated finding entered the
verdict count (lib.verdict) with the same weight as a true one. This script
extracts the quoted spans from each finding and confirms they appear either in
the chapter or in a source file the finding says the chapter breaks (quoting the
rule you violate is legitimate). An unverifiable quote in a MUST is treated as a
presumptively hallucinated finding.

Usage:
    python scripts/verify_critique_quotes.py \
        --critique-file <path> \
        --series-slug <slug> --book-number <n> --chapter <m> [--strict]

Exit: 0 = every quote verified; 1 = an ERROR (unverifiable MUST quote), or any
finding with --strict. 2 = a required file is missing.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib.parsing import strip_expand_markers
from lib import quotes
from lib.verdict import section_bodies, bullets


# Sources whose lines a critique may legitimately quote (the rule being broken).
def _source_haystacks(paths) -> dict[str, str]:
    hays: dict[str, str] = {}
    candidates = [paths.setup_md, paths.style_md, paths.outline_md,
                  paths.arcs_md, paths.seeds_md, paths.shadow_md,
                  paths.decisions_md]
    for d in (paths.canon_dir, paths.series_canon_dir):
        if d.exists():
            candidates += sorted(d.glob("*.md"))
    if paths.notes_dir.exists():
        candidates += sorted(paths.notes_dir.glob("decisions-ch*.md"))
    for p in candidates:
        if p.exists():
            hays[str(p.relative_to(REPO_ROOT)) if p.is_absolute() else str(p)] = \
                p.read_text(encoding="utf-8")
    return hays


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--critique-file", required=True)
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on WARN findings too, not just ERROR.")
    args = parser.parse_args()

    crit = Path(args.critique_file)
    if not crit.exists():
        print(f"ERROR: critique file not found: {crit}", file=sys.stderr)
        return 2

    paths = book_paths(args.series_slug, args.book_number)
    chapter_file = paths.chapter_file(args.chapter)
    if not chapter_file.exists():
        print(f"ERROR: chapter file not found: {chapter_file}", file=sys.stderr)
        return 2

    # Primary haystack: the same marker-stripped view of the chapter the critic
    # read; secondary: the source files a finding may cite as the broken rule.
    haystacks = {"chapter": strip_expand_markers(chapter_file.read_text(encoding="utf-8"))}
    haystacks.update(_source_haystacks(paths))

    bodies = section_bodies(crit.read_text(encoding="utf-8"))
    errors = 0
    warns = 0
    for section in ("MUST", "SHOULD", "CONSIDER"):
        is_must = section == "MUST"
        for i, bullet in enumerate(bullets(bodies.get(section, "")), start=1):
            # An empty-section placeholder ("(none)" / "(ninguno)") is not a
            # finding — skip it so it does not read as an unquoted MUST.
            if re.fullmatch(r"\(\s*(?:none|ninguno|ninguna|n/?a)\s*\)\.?", bullet.strip(), re.IGNORECASE):
                continue
            spans = quotes.extract_quoted_spans(bullet)
            if not spans:
                if is_must:
                    warns += 1
                    print(f"WARN {crit.name} [{section} #{i}]: finding carries no "
                          f"verifiable quote (MUST findings must quote the line)")
                continue
            findings = quotes.verify_quotes(spans, haystacks)
            for qf in findings:
                if qf.verified:
                    continue
                preview = qf.span if len(qf.span) <= 80 else qf.span[:77] + "…"
                if is_must:
                    errors += 1
                    print(f"ERROR {crit.name} [{section} #{i}]: quote not found in "
                          f"chapter or sources: «{preview}»")
                else:
                    warns += 1
                    print(f"WARN {crit.name} [{section} #{i}]: quote not found in "
                          f"chapter or sources: «{preview}»")

    print(f"\nverify-quotes: {errors} error(s), {warns} warning(s)")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
