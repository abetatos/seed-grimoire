"""Project-level configuration: `config.toml` at the repo root.

Holds facts that belong to the whole project rather than to one book —
today just the writer's pen name (`[author] name`). Per-book values in
`setup.md` always win over these defaults.

The file is optional: a missing config yields empty defaults instead of
an error, so nothing downstream hard-depends on it. Malformed TOML still
raises loudly (tomllib's own error) rather than being swallowed.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config.toml"


def load(config_path: Path = CONFIG_PATH) -> dict:
    """Parse config.toml; an absent file is an empty config."""
    if not config_path.exists():
        return {}
    return tomllib.loads(config_path.read_text(encoding="utf-8"))


def author_name(config_path: Path = CONFIG_PATH) -> str:
    """The project-wide pen name, or "" if unset."""
    value = load(config_path).get("author", {}).get("name", "")
    return value.strip() if isinstance(value, str) else ""
