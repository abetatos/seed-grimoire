#!/usr/bin/env python3
"""Sync `.claude/models.toml` into agent frontmatter + skill dispatch lines.

The TOML is the project-level source of truth for which model each subagent
(and dispatched search) runs on; this script copies it into the files Claude
Code actually reads (`.claude/agents/*.md` frontmatter, search-corpus's
dispatch token).

Usage:
    uv run python scripts/sync_models.py           # apply
    uv run python scripts/sync_models.py --check   # verify only

Exit: 0 = in sync (or applied); 1 = --check found drift; 2 = config error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.models_config import ModelsConfigError, sync

CONFIG_PATH = REPO_ROOT / ".claude" / "models.toml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Report drift without writing; exit 1 if any.")
    args = parser.parse_args()

    try:
        changed = sync(REPO_ROOT, CONFIG_PATH, check=args.check)
    except ModelsConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not changed:
        print("models: all targets in sync with .claude/models.toml")
        return 0

    verb = "OUT OF SYNC" if args.check else "updated"
    for line in changed:
        print(f"models {verb}: {line}")
    return 1 if args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
