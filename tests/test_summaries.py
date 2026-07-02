"""Tests for lib.summaries — scene extraction + window arithmetic."""

import tempfile
import unittest
from pathlib import Path

from lib import summaries as SM
from lib.paths import BookPaths


def _para(word: str, n: int) -> str:
    return " ".join([word] * n)


class ExtractLastScene(unittest.TestCase):
    def test_asterisk_break(self):
        text = "# Cap 1\n\n" + _para("a", 200) + "\n\n* * *\n\n" + _para("b", 200)
        out = SM.extract_last_scene(text)
        self.assertTrue(out.startswith("b"))
        self.assertNotIn("a a", out)

    def test_three_hyphen_break(self):
        # the T5 fix: `---` must be recognized as a scene break
        text = "# Cap 1\n\n" + _para("a", 200) + "\n\n---\n\n" + _para("b", 200)
        out = SM.extract_last_scene(text)
        self.assertTrue(out.startswith("b"))
        self.assertNotIn("a a", out)

    def test_no_break_word_tail(self):
        text = "# Cap 1\n\n" + "\n\n".join(_para(str(i), 300) for i in range(6))
        out = SM.extract_last_scene(text, target_words=900)
        # ~900-word tail, snapped to paragraph boundary
        self.assertGreaterEqual(len(out.split()), 900)
        self.assertLess(len(out.split()), 1500)

    def test_expand_markers_stripped(self):
        text = (
            "# Cap 1\n\n" + _para("a", 200) + "\n\n* * *\n\n"
            "▼▼▼ INICIO EXPAND 1 (prosa AÑADIDA) ▼▼▼\n\n"
            + _para("b", 200) + "\n\n▲▲▲ FIN EXPAND 1 ▲▲▲\n"
        )
        out = SM.extract_last_scene(text)
        self.assertNotIn("EXPAND", out)
        self.assertNotIn("▼", out)

    def test_short_tail_after_break_falls_back(self):
        # tail after break < 150 words → fall back to word tail (keeps earlier prose)
        text = "# Cap 1\n\n" + _para("a", 400) + "\n\n* * *\n\n" + _para("b", 10)
        out = SM.extract_last_scene(text, target_words=200)
        self.assertIn("a", out)


class PlanContext(unittest.TestCase):
    def _book(self, tmp: Path, n_summaries: int) -> BookPaths:
        series = tmp / "output" / "s"
        book = series / "book-01"
        (book / "summaries").mkdir(parents=True)
        for i in range(1, n_summaries + 1):
            (book / "summaries" / f"ch-{i:02d}.md").write_text(f"summary {i}", encoding="utf-8")
        return BookPaths(series_root=series, book_root=book)

    def test_chapter_2_seam_only(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self._book(Path(d), 1)
            plan = SM.plan_context(paths, 2)
            self.assertEqual(plan.full_text_chapters, [1])  # ch1 in seam
            self.assertEqual(plan.detail_chapters, [])

    def test_window_boundary_ch8(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self._book(Path(d), 7)  # chapters 1..7 written
            plan = SM.plan_context(paths, 8)
            # ch7 → seam; ch1..6 → detail (RECENT_DETAIL_WINDOW=6); no act summary
            self.assertEqual(plan.full_text_chapters, [7])
            self.assertEqual(plan.detail_chapters, [1, 2, 3, 4, 5, 6])


if __name__ == "__main__":
    unittest.main()
