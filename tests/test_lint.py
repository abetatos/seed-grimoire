"""Tests for lib.lint — one fixture per check."""

import tempfile
import unittest
from pathlib import Path

from lib import lint
from tests._fixtures import make_book


def _levels(findings, where_substr):
    return [f.level for f in findings if where_substr in f.where]


class LintChecks(unittest.TestCase):
    def test_clean_fixture_has_no_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=0)
            findings = lint.lint_book(paths)
            self.assertFalse(lint.has_errors(findings), [str(f) for f in findings])

    def test_payoff_before_plant_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d))
            seeds = paths.seeds_md.read_text(encoding="utf-8")
            # el-pozo: plant 1, payoff 3 → make payoff precede plant
            seeds = seeds.replace("**Plant in:** 1\n**Echo in:** 2\n**Payoff in:** 3",
                                  "**Plant in:** 5\n**Echo in:** 2\n**Payoff in:** 3")
            paths.seeds_md.write_text(seeds, encoding="utf-8")
            findings = lint.lint_book(paths)
            self.assertIn(lint.ERROR, _levels(findings, "el-pozo"))

    def test_out_of_range_chapter_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d))  # book has 7 chapters
            seeds = paths.seeds_md.read_text(encoding="utf-8")
            seeds = seeds.replace("**Payoff in:** 3", "**Payoff in:** 99")
            paths.seeds_md.write_text(seeds, encoding="utf-8")
            findings = lint.lint_book(paths)
            msgs = [f.message for f in findings if "el-pozo" in f.where]
            self.assertTrue(any("out of book range" in m for m in msgs), msgs)

    def test_dangling_revealed_by_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d))
            shadow = paths.shadow_md.read_text(encoding="utf-8")
            shadow = shadow.replace("**Revealed-by:** el-pozo",
                                    "**Revealed-by:** no-existe")
            paths.shadow_md.write_text(shadow, encoding="utf-8")
            findings = lint.lint_book(paths)
            self.assertIn(lint.ERROR, _levels(findings, "t-pozo"))

    def test_malformed_token_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d))
            seeds = paths.seeds_md.read_text(encoding="utf-8")
            seeds = seeds.replace("**Echo in:** 2\n**Payoff in:** 3",
                                  "**Echo in:** 2, 3x\n**Payoff in:** 3")
            paths.seeds_md.write_text(seeds, encoding="utf-8")
            findings = lint.lint_book(paths)
            msgs = [f.message for f in findings if "el-pozo" in f.where]
            self.assertTrue(any("unparsed schedule token" in m for m in msgs), msgs)

    def test_missing_summary_for_locked_chapter_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            # chapters 1,2,3 written; delete ch-01 summary → ch1 < highest(3), so error
            paths.chapter_summary(1).unlink()
            findings = lint.lint_book(paths)
            self.assertIn(lint.ERROR, _levels(findings, "ch-01"))

    def test_todo_summary_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            paths.chapter_summary(1).write_text("# Chapter 1\n\n> TODO: fill", encoding="utf-8")
            findings = lint.lint_book(paths)
            self.assertIn(lint.ERROR, _levels(findings, "ch-01"))

    def test_missing_continuity_contract_warns(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            # No continuity-ch01.md → WARN for a locked chapter (ch1 < highest).
            findings = lint.lint_book(paths)
            self.assertIn(lint.WARN, _levels(findings, "continuity-ch01"))

    def test_present_continuity_contract_no_warn(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            paths.chapter_continuity_md(1).write_text("# Continuity — 1\n", encoding="utf-8")
            findings = lint.lint_book(paths)
            self.assertNotIn("continuity-ch01", [f.where for f in findings])

    def test_verbatim_anchor_quote_passes(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            paths.chapter_file(1).write_text(
                "# Capítulo 1\n\nBruno midió a la gente por las manos y calló.\n",
                encoding="utf-8")
            paths.chapter_summary(1).write_text(
                "# Chapter 1 — summary\n\n## Anchor quotes (verbatim)\n"
                "- «Bruno midió a la gente por las manos y calló»\n", encoding="utf-8")
            findings = lint.lint_book(paths)
            self.assertNotIn(lint.ERROR, _levels(findings, "ch-01"))

    def test_paraphrased_anchor_quote_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            paths.chapter_file(1).write_text(
                "# Capítulo 1\n\nBruno midió a la gente por las manos y calló.\n",
                encoding="utf-8")
            paths.chapter_summary(1).write_text(
                "# Chapter 1 — summary\n\n## Anchor quotes (verbatim)\n"
                "- «Bruno juzgaba a las personas observando sus rostros»\n", encoding="utf-8")
            findings = lint.lint_book(paths)
            self.assertIn(lint.ERROR, _levels(findings, "ch-01"))

    def test_missing_anchor_section_warns(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            # Fixture summaries have no Anchor-quotes section → WARN, not ERROR.
            findings = lint.lint_book(paths)
            self.assertIn(lint.WARN, _levels(findings, "ch-01"))
            self.assertNotIn(lint.ERROR, _levels(findings, "ch-01"))


if __name__ == "__main__":
    unittest.main()
