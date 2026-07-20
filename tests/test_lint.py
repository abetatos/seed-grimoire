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

    def test_missing_brief_warns(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            # No brief-ch01.md → WARN for a locked chapter (ch1 < highest).
            findings = lint.lint_book(paths)
            self.assertIn(lint.WARN, _levels(findings, "brief-ch01"))

    def test_present_brief_no_warn(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=3)
            paths.chapter_brief_md(1).write_text("# Brief — 1\n", encoding="utf-8")
            findings = lint.lint_book(paths)
            self.assertNotIn("brief-ch01", [f.where for f in findings])

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


class WorldReplay(unittest.TestCase):
    """Check 8 runs only when the book has a state store, and turns a broken
    event log into an ERROR at lint time."""

    def _store(self, paths):
        from lib.engine import store as engine_store
        from lib.engine.graph import WorldGraph
        from lib.engine.state import Entity
        graph = WorldGraph()
        graph.add_place("plaza", "La Plaza", "sala")
        graph.add_place("casa", "La Casa", "edificio")
        graph.connect("plaza", "casa", "a pie", "minutos")
        engine_store.save_graph(paths.state_dir, graph)
        engine_store.save_entities(
            paths.state_dir, [Entity(id="bruno", name="Bruno", kind="character", position="casa")])
        return engine_store

    def test_no_store_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=0)
            findings = lint.check_world_replay(paths)
            self.assertEqual(findings, [])

    def test_clean_store_passes(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=0)
            es = self._store(paths)
            from lib.engine.events import Event
            es.append_event(paths.state_dir,
                            Event(chapter=1, seq=0, type="move", data={"entity": "bruno", "to": "plaza"}))
            findings = lint.lint_book(paths)
            self.assertNotIn(lint.ERROR, _levels(findings, "state/events"))

    def test_teleport_errors(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=0)
            es = self._store(paths)
            # add an isolated place and move to it with no edge → teleport
            graph = es.load_graph(paths.state_dir)
            graph.add_place("lejos", "Muy Lejos", "region")
            es.save_graph(paths.state_dir, graph)
            from lib.engine.events import Event
            es.append_event(paths.state_dir,
                            Event(chapter=1, seq=0, type="move", data={"entity": "bruno", "to": "lejos"}))
            findings = lint.lint_book(paths)
            self.assertIn(lint.ERROR, _levels(findings, "state/events"))


if __name__ == "__main__":
    unittest.main()
