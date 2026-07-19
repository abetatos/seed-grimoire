#!/usr/bin/env python3
"""Phase-0 instrument — per-phase token report for a session transcript.

Captures the deterministic baseline the IMPROVEMENT-PLAN needs before any
architecture moves: where the main-thread tokens go, per pipeline phase, and
whether the session breached the two fixed thresholds (main-thread context
ceiling, per-chapter output target).

Usage:
    # newest transcript for this project
    python scripts/token_report.py
    # a specific session (path or id-prefix)
    python scripts/token_report.py --session 4cbc0958
    python scripts/token_report.py path/to/session.jsonl
    # non-zero exit if a threshold is breached (wire into CI / a loop later)
    python scripts/token_report.py --strict

Capture 3-4 chapters this way, then read the tables together — one transcript is
one write-novel session (≈ one chapter). Exit: 0 ok; 1 = threshold breach under
--strict; 2 = no transcript found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.token_report import (  # noqa: E402
    CONTEXT_CEILING, OUTPUT_TARGET, analyze,
)

# Claude Code stores transcripts under ~/.claude/projects/<cwd-with-slashes-as->.
PROJECT_DIR = Path.home() / ".claude" / "projects" / str(REPO_ROOT).replace("/", "-")


def _resolve(session: str | None) -> Path | None:
    """Locate a transcript: explicit path, id-prefix, or newest in the project."""
    if session:
        p = Path(session)
        if p.suffix == ".jsonl" and p.exists():
            return p
        matches = sorted(PROJECT_DIR.glob(f"{session}*.jsonl"))
        return matches[0] if matches else None
    transcripts = list(PROJECT_DIR.glob("*.jsonl"))
    if not transcripts:
        return None
    return max(transcripts, key=lambda p: p.stat().st_mtime)


def _records(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _fmt(n: int) -> str:
    return f"{n:,}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("session", nargs="?", help="transcript path or session-id prefix")
    parser.add_argument("--session", dest="session_opt", help="session-id prefix (alt to positional)")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero if a threshold is breached")
    args = parser.parse_args()

    path = _resolve(args.session or args.session_opt)
    if path is None:
        print(f"ERROR: no transcript found in {PROJECT_DIR}", file=sys.stderr)
        return 2

    report = analyze(_records(path))

    print(f"Token report — {path.name}\n")
    w = max((len(p.phase) for p in report.phases), default=12)
    print(f"  {'phase':<{w}}  {'msgs':>5}  {'output':>10}  {'peak ctx':>10}")
    print(f"  {'-' * w}  {'-' * 5}  {'-' * 10}  {'-' * 10}")
    for p in report.phases:
        print(f"  {p.phase:<{w}}  {p.messages:>5}  {_fmt(p.output_tokens):>10}  {_fmt(p.peak_context):>10}")
    print(f"  {'-' * w}  {'-' * 5}  {'-' * 10}  {'-' * 10}")
    print(f"  {'TOTAL (main)':<{w}}  {sum(p.messages for p in report.phases):>5}  "
          f"{_fmt(report.total_output):>10}  {_fmt(report.peak_context):>10}")
    if report.sidechain_messages:
        print(f"  {'subagent (side)':<{w}}  {report.sidechain_messages:>5}  "
              f"{_fmt(report.sidechain_output):>10}  {'—':>10}")

    print()
    ceil_flag = "OVER" if report.over_ceiling else "ok"
    tgt_flag = "OVER" if report.over_target else "ok"
    print(f"  peak main-thread context : {_fmt(report.peak_context):>10}  "
          f"(ceiling {_fmt(CONTEXT_CEILING)}) [{ceil_flag}]")
    print(f"  total main-thread output : {_fmt(report.total_output):>10}  "
          f"(target  {_fmt(OUTPUT_TARGET)}) [{tgt_flag}]")

    if args.strict and (report.over_ceiling or report.over_target):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
