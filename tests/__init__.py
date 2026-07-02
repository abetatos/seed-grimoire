"""Test suite for The Seed Grimoire deterministic core.

Run: `uv run python -m unittest discover tests` from the repo root.

Importing this package puts scripts/ on sys.path so tests can `import lib.*`
the same way the CLI entry-points do.
"""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
