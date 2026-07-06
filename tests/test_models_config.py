"""Tests for scripts/lib/models_config.py (models.toml → file sync)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.models_config import (
    ModelsConfigError,
    load_config,
    set_dispatch_model,
    set_frontmatter_model,
    sync,
)

AGENT_MD = """---
name: book-critic
tools: Bash, Read
model: opus
---

# book-critic
body mentions model: opus in prose, untouched.
"""

AGENT_MD_NO_MODEL = """---
name: naive-reader
tools: Read, Glob
---

body
"""

SKILL_MD = """---
name: search-corpus
---
Dispatch with `subagent_type: Explore`, `model: haiku` — cheap.
"""


class TestFrontmatter(unittest.TestCase):
    def test_replaces_existing_model_line(self) -> None:
        out = set_frontmatter_model(AGENT_MD, "sonnet", label="x")
        self.assertIn("\nmodel: sonnet\n", out)
        self.assertNotIn("model: opus\n---", out)
        # Prose after the frontmatter is untouched.
        self.assertIn("body mentions model: opus in prose", out)

    def test_inserts_when_missing(self) -> None:
        out = set_frontmatter_model(AGENT_MD_NO_MODEL, "sonnet", label="x")
        head = out.split("\n---", 1)[0]
        self.assertIn("model: sonnet", head)

    def test_idempotent(self) -> None:
        once = set_frontmatter_model(AGENT_MD, "sonnet", label="x")
        twice = set_frontmatter_model(once, "sonnet", label="x")
        self.assertEqual(once, twice)

    def test_no_frontmatter_is_loud(self) -> None:
        with self.assertRaises(ModelsConfigError):
            set_frontmatter_model("# just a doc\n", "opus", label="x")


class TestDispatch(unittest.TestCase):
    def test_replaces_single_token(self) -> None:
        out = set_dispatch_model(SKILL_MD, "sonnet", label="x")
        self.assertIn("`model: sonnet`", out)
        self.assertNotIn("`model: haiku`", out)

    def test_zero_or_many_tokens_is_loud(self) -> None:
        with self.assertRaises(ModelsConfigError):
            set_dispatch_model("no token here", "haiku", label="x")
        with self.assertRaises(ModelsConfigError):
            set_dispatch_model(SKILL_MD + "again `model: opus`", "haiku", label="x")


class TestConfigAndSync(unittest.TestCase):
    def _repo(self) -> Path:
        root = Path(self._tmp.name)
        (root / ".claude" / "agents").mkdir(parents=True)
        (root / ".claude" / "skills" / "search-corpus").mkdir(parents=True)
        (root / ".claude" / "agents" / "book-critic.md").write_text(
            AGENT_MD, encoding="utf-8")
        (root / ".claude" / "skills" / "search-corpus" / "SKILL.md").write_text(
            SKILL_MD, encoding="utf-8")
        return root

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def _write_config(self, root: Path, body: str) -> Path:
        path = root / ".claude" / "models.toml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_invalid_model_value_is_loud(self) -> None:
        root = self._repo()
        cfg = self._write_config(root, '[agents]\nbook-critic = "gpt-5"\n')
        with self.assertRaises(ModelsConfigError):
            load_config(cfg)

    def test_unknown_section_is_loud(self) -> None:
        root = self._repo()
        cfg = self._write_config(root, '[skills]\nfoo = "opus"\n')
        with self.assertRaises(ModelsConfigError):
            load_config(cfg)

    def test_full_model_id_accepted(self) -> None:
        root = self._repo()
        cfg = self._write_config(
            root, '[agents]\nbook-critic = "claude-haiku-4-5-20251001"\n')
        self.assertEqual(
            load_config(cfg)["agents"]["book-critic"],
            "claude-haiku-4-5-20251001")

    def test_sync_applies_and_reaches_fixpoint(self) -> None:
        root = self._repo()
        cfg = self._write_config(
            root,
            '[agents]\nbook-critic = "sonnet"\n'
            '[dispatch]\nsearch-corpus = "sonnet"\n')
        changed = sync(root, cfg)
        self.assertEqual(len(changed), 2)
        self.assertIn(
            "model: sonnet",
            (root / ".claude" / "agents" / "book-critic.md").read_text(encoding="utf-8"))
        # Second run: nothing left to do.
        self.assertEqual(sync(root, cfg), [])

    def test_check_mode_reports_without_writing(self) -> None:
        root = self._repo()
        cfg = self._write_config(root, '[agents]\nbook-critic = "sonnet"\n')
        before = (root / ".claude" / "agents" / "book-critic.md").read_text(
            encoding="utf-8")
        changed = sync(root, cfg, check=True)
        self.assertEqual(len(changed), 1)
        after = (root / ".claude" / "agents" / "book-critic.md").read_text(
            encoding="utf-8")
        self.assertEqual(before, after)

    def test_missing_target_is_loud(self) -> None:
        root = self._repo()
        cfg = self._write_config(root, '[agents]\nghost-agent = "opus"\n')
        with self.assertRaises(ModelsConfigError):
            sync(root, cfg)


if __name__ == "__main__":
    unittest.main()
