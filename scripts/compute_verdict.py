#!/usr/bin/env python3
"""Compute a critique verdict (PASS/REVISE/REJECT) from a findings file.

The critic writes the MUST/SHOULD/CONSIDER findings WITHOUT a verdict line, then
runs this script and writes the returned verdict into the file's **Verdict:**
field. Deriving the verdict by counting — instead of by the critic's judgment at
the step that triggers actions — is what keeps severity honest.

Usage:
    python scripts/compute_verdict.py --critique-file <path> --target chapter|plan|grimoire

Prints e.g. `VERDICT: REVISE (MUST=1 SHOULD=2 CONSIDER=0)` and exits 0. Exits 2
if the file is missing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.verdict import compute_verdict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--critique-file", required=True)
    parser.add_argument("--target", choices=("chapter", "plan", "grimoire"),
                        default="chapter")
    args = parser.parse_args()

    p = Path(args.critique_file)
    if not p.exists():
        print(f"ERROR: critique file not found: {p}", file=sys.stderr)
        return 2

    v = compute_verdict(p.read_text(encoding="utf-8"), args.target)
    print(v.line())
    if v.reject_tags:
        print(f"  reject-tier findings: {', '.join(v.reject_tags)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
