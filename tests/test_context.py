"""Tests for lib.context — phase section sets + character scoping."""

import tempfile
import unittest
from pathlib import Path

from lib.context import build_context
from tests._fixtures import make_book


def _headers(bundle: str) -> list[str]:
    return [ln[2:] for ln in bundle.splitlines() if ln.startswith("# ")]


class Phases(unittest.TestCase):
    def _bundle(self, phase: str) -> str:
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=2)
            return build_context(paths, 3, phase=phase)

    def test_write_has_seam_and_voice_spine(self):
        h = "\n".join(_headers(self._bundle("write")))
        self.assertIn("Continuity seam", h)
        self.assertIn("Voice spine", h)
        self.assertIn("Shadow timeline", h)

    def test_plan_drops_style_and_craft(self):
        h = "\n".join(_headers(self._bundle("plan")))
        self.assertNotIn("Style guide", h)
        self.assertNotIn("Craft checklist", h)
        self.assertNotIn("Continuity seam", h)

    def test_critique_keeps_style_and_craft_drops_seam(self):
        h = "\n".join(_headers(self._bundle("critique")))
        self.assertIn("Style guide", h)
        self.assertIn("Craft checklist", h)
        self.assertNotIn("Continuity seam", h)

    def test_expand_drops_shadow_plan_story_seam(self):
        h = "\n".join(_headers(self._bundle("expand")))
        self.assertNotIn("Shadow timeline", h)
        self.assertNotIn("Story so far", h)
        self.assertNotIn("Continuity seam", h)
        self.assertNotIn("Voice spine", h)
        # but keeps the essentials for a texture pass
        self.assertIn("Seed envelope", h)
        self.assertIn("Style guide", h)
        self.assertIn("beat sheet", h)

    def test_expand_smaller_than_write(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=2)
            w = len(build_context(paths, 3, phase="write").split())
            e = len(build_context(paths, 3, phase="expand").split())
            self.assertLess(e, w)


class Scoping(unittest.TestCase):
    def test_short_name_and_angle_quote_alias_kept_when_named(self):
        # Ch1 beat names Bruno; the secondary «la callada» / short name should be
        # scoped by relevance. Force the secondary into the haystack via the beat.
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=0)
            # inject "callada" into ch1 outline beat so alias matches
            outline = paths.outline_md.read_text(encoding="utf-8")
            paths.outline_md.write_text(
                outline.replace("se presenta a Bruno en el taller.",
                                "Bruno y la callada en el taller."),
                encoding="utf-8",
            )
            bundle = build_context(paths, 1, phase="write")
            self.assertIn("la callada", bundle)  # alias-matched secondary kept

    def test_unmentioned_secondary_scoped_out(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d), chapters_written=0)
            bundle = build_context(paths, 1, phase="write")
            # Mauro is not named anywhere in ch1 signals → scoped out
            self.assertIn("scoped out this chapter", bundle)
            self.assertIn("Mauro", bundle.split("scoped out this chapter")[1][:200])


if __name__ == "__main__":
    unittest.main()
