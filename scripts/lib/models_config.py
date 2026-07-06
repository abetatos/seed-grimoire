"""Model-assignment config: parse `.claude/models.toml` and rewrite targets.

Two kinds of target, both mutated surgically (never a parse→dump round-trip):

- ``[agents]``   → the ``model:`` line inside the YAML frontmatter of
  ``.claude/agents/<name>.md`` (replaced if present, inserted before the
  closing ``---`` if not).
- ``[dispatch]`` → the single inline ``` `model: <x>` ``` token inside
  ``.claude/skills/<name>/SKILL.md`` (the model handed to a built-in
  subagent at dispatch time).

Loud by design: an unknown model value, a missing file, a frontmatter without
delimiters, or a dispatch token appearing zero or multiple times all raise
``ModelsConfigError`` instead of guessing.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

MODEL_ALIASES = {"opus", "sonnet", "haiku", "inherit"}

_FRONTMATTER_MODEL_RE = re.compile(r"^model:[ \t]*\S+[ \t]*$", re.MULTILINE)
_DISPATCH_MODEL_RE = re.compile(r"`model:\s*([A-Za-z0-9._-]+)`")


class ModelsConfigError(Exception):
    """Any unrecoverable problem with the config or a target file."""


def _validate_model(name: str, model: str) -> None:
    if model in MODEL_ALIASES or model.startswith("claude-"):
        return
    raise ModelsConfigError(
        f"{name}: invalid model {model!r} — use one of "
        f"{sorted(MODEL_ALIASES)} or a full 'claude-*' model id"
    )


def load_config(config_path: Path) -> dict[str, dict[str, str]]:
    """Parse models.toml into {'agents': {...}, 'dispatch': {...}}, validated."""
    if not config_path.exists():
        raise ModelsConfigError(f"config not found: {config_path}")
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    unknown = set(data) - {"agents", "dispatch"}
    if unknown:
        raise ModelsConfigError(
            f"unknown section(s) in {config_path.name}: {sorted(unknown)}"
        )

    config: dict[str, dict[str, str]] = {"agents": {}, "dispatch": {}}
    for section in ("agents", "dispatch"):
        for name, model in data.get(section, {}).items():
            if not isinstance(model, str):
                raise ModelsConfigError(
                    f"[{section}] {name}: expected a string, got {type(model).__name__}"
                )
            _validate_model(f"[{section}] {name}", model)
            config[section][name] = model
    return config


def set_frontmatter_model(text: str, model: str, *, label: str) -> str:
    """Replace (or insert) the ``model:`` line of a ``---``-delimited frontmatter."""
    if not text.startswith("---\n"):
        raise ModelsConfigError(f"{label}: no frontmatter block at top of file")
    close = text.find("\n---", 4)
    if close == -1:
        raise ModelsConfigError(f"{label}: frontmatter never closes")

    head, tail = text[: close + 1], text[close + 1 :]
    new_line = f"model: {model}"
    if _FRONTMATTER_MODEL_RE.search(head):
        head = _FRONTMATTER_MODEL_RE.sub(new_line, head, count=1)
    else:
        head = head + new_line + "\n"
    return head + tail


def set_dispatch_model(text: str, model: str, *, label: str) -> str:
    """Replace the single inline `` `model: <x>` `` dispatch token."""
    hits = _DISPATCH_MODEL_RE.findall(text)
    if len(hits) != 1:
        raise ModelsConfigError(
            f"{label}: expected exactly one `model: <x>` dispatch token, found {len(hits)}"
        )
    return _DISPATCH_MODEL_RE.sub(f"`model: {model}`", text, count=1)


def sync(repo_root: Path, config_path: Path, *, check: bool = False) -> list[str]:
    """Apply (or with ``check=True`` just diff) the config against the repo.

    Returns the list of out-of-sync targets, formatted ``path: old -> new``.
    In apply mode those files have been rewritten by the time it returns.
    """
    config = load_config(config_path)
    changed: list[str] = []

    targets: list[tuple[Path, str, str]] = []  # (path, kind, model)
    for name, model in config["agents"].items():
        targets.append((repo_root / ".claude" / "agents" / f"{name}.md", "agents", model))
    for name, model in config["dispatch"].items():
        targets.append(
            (repo_root / ".claude" / "skills" / name / "SKILL.md", "dispatch", model)
        )

    for path, kind, model in targets:
        if not path.exists():
            raise ModelsConfigError(f"target not found: {path}")
        label = str(path.relative_to(repo_root))
        old = path.read_text(encoding="utf-8")
        if kind == "agents":
            new = set_frontmatter_model(old, model, label=label)
        else:
            new = set_dispatch_model(old, model, label=label)
        if new != old:
            changed.append(f"{label}: -> {model}")
            if not check:
                path.write_text(new, encoding="utf-8")
    return changed
