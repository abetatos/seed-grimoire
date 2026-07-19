"""Tests for the front-matter model in lib.paths — courtesy pages that
precede chapter 1 in the compiled EPUB, and the chapter-0 exclusion."""

import tempfile
import unittest
from pathlib import Path

from lib import paths as P
from tests._fixtures import make_book


class FrontMatter(unittest.TestCase):
    def _book(self, d: Path) -> P.BookPaths:
        return make_book(d, chapters_written=3)

    def test_empty_when_no_dir(self):
        with tempfile.TemporaryDirectory() as d:
            bp = self._book(Path(d))
            # ensure_dirs creates front-matter/, but it is empty
            self.assertEqual(P.front_matter_files(bp), [])

    def test_files_sorted_by_name(self):
        with tempfile.TemporaryDirectory() as d:
            bp = self._book(Path(d))
            (bp.front_matter_dir / "02-epigraph.md").write_text("x", encoding="utf-8")
            (bp.front_matter_dir / "01-dedication.md").write_text("y", encoding="utf-8")
            (bp.front_matter_dir / "notes.txt").write_text("z", encoding="utf-8")
            names = [p.name for p in P.front_matter_files(bp)]
            self.assertEqual(names, ["01-dedication.md", "02-epigraph.md"])

    def test_is_dedication_matches_both_languages_and_prefix(self):
        self.assertTrue(P.is_dedication(Path("dedication.md")))
        self.assertTrue(P.is_dedication(Path("dedicatoria.md")))
        self.assertTrue(P.is_dedication(Path("01-dedication.md")))
        self.assertTrue(P.is_dedication(Path("03-Dedicatoria.md")))
        self.assertFalse(P.is_dedication(Path("epigraph.md")))
        self.assertFalse(P.is_dedication(Path("02-epigraph.md")))

    def test_chapter_zero_is_not_a_chapter(self):
        with tempfile.TemporaryDirectory() as d:
            bp = self._book(Path(d))
            (bp.chapters_dir / "00.md").write_text("legacy dedication", encoding="utf-8")
            self.assertEqual(P.chapter_numbers(bp), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
