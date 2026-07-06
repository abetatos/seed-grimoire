"""Tests for lib.project_config — the optional root config.toml."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lib import project_config


class TestProjectConfig(unittest.TestCase):
    def _write(self, text: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(
            "w", suffix=".toml", delete=False, encoding="utf-8"
        )
        self.addCleanup(Path(tmp.name).unlink)
        tmp.write(text)
        tmp.close()
        return Path(tmp.name)

    def test_author_name_read(self) -> None:
        path = self._write('[author]\nname = "Alejandro Garsía"\n')
        self.assertEqual(project_config.author_name(path), "Alejandro Garsía")

    def test_missing_file_is_empty_config(self) -> None:
        missing = Path(tempfile.gettempdir()) / "no-such-config-xyz.toml"
        self.assertEqual(project_config.load(missing), {})
        self.assertEqual(project_config.author_name(missing), "")

    def test_unset_author_is_empty_string(self) -> None:
        path = self._write("[other]\nkey = 1\n")
        self.assertEqual(project_config.author_name(path), "")

    def test_non_string_author_is_empty_string(self) -> None:
        path = self._write("[author]\nname = 3\n")
        self.assertEqual(project_config.author_name(path), "")

    def test_whitespace_is_stripped(self) -> None:
        path = self._write('[author]\nname = "  Alejandro Garsía  "\n')
        self.assertEqual(project_config.author_name(path), "Alejandro Garsía")

    def test_repo_config_declares_the_pen_name(self) -> None:
        # The checked-in config.toml is the project's real default.
        self.assertTrue(project_config.CONFIG_PATH.exists())
        self.assertEqual(project_config.author_name(), "Alejandro Garsía")


if __name__ == "__main__":
    unittest.main()
