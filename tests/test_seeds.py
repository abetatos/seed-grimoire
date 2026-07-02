"""Tests for lib.seeds — surgical mutation invariants + parsing."""

import unittest

from lib import seeds as S


SEED_A = """## SEED: alpha
**Detail:** una imagen concreta
**Real meaning:** la verdad oculta
**Plant in:** 3
**Echo in:** 7, 11
**Payoff in:** 22 (en la mano de Bruno) → eco
**How to plant:** de pasada
**How to pay off:** sin explicar
**Status:** planted
"""

SEED_B = """## SEED: beta
**Detail:** otra
**Plant in:** 5
**Echo in:** —
**Payoff in:** Libro II (más adelante)
**Status:** planned
"""

TWO_SEEDS = "# Seeds — test\n\n" + SEED_A + "\n" + SEED_B


class Parsing(unittest.TestCase):
    def test_parses_both_and_gotcha(self):
        by_id = {s.id: s for s in _load(TWO_SEEDS)}
        self.assertEqual(by_id["alpha"].plant_in, 3)
        self.assertEqual(by_id["alpha"].echo_in, [7, 11])
        self.assertEqual(by_id["alpha"].payoff_in, 22)     # bare-digit gotcha kept
        self.assertIsNone(by_id["beta"].payoff_in)         # cross-book deferral

    def test_no_spurious_warnings(self):
        for s in _load(TWO_SEEDS):
            self.assertEqual(s.parse_warnings, [], s.id)

    def test_malformed_schedule_warns(self):
        text = SEED_A.replace("**Echo in:** 7, 11", "**Echo in:** 7, xx")
        seed = _load("# t\n" + text)[0]
        self.assertTrue(any("xx" in w for w in seed.parse_warnings))


class SurgicalStatus(unittest.TestCase):
    def test_only_target_status_changes(self):
        new, found = S.update_status_in_text(TWO_SEEDS, "alpha", "echoed-1")
        self.assertTrue(found)
        self.assertIn("**Status:** echoed-1", new)
        # beta's section is untouched byte-for-byte
        self.assertIn(SEED_B, new)

    def test_noop_is_byte_identical(self):
        new, found = S.update_status_in_text(TWO_SEEDS, "alpha", "planted")
        self.assertTrue(found)
        self.assertEqual(new, TWO_SEEDS)

    def test_unknown_id_not_found(self):
        new, found = S.update_status_in_text(TWO_SEEDS, "zzz", "paid_off")
        self.assertFalse(found)
        self.assertEqual(new, TWO_SEEDS)


class SurgicalRealized(unittest.TestCase):
    def test_creates_block_when_absent(self):
        new, found = S.append_realized_in_text(TWO_SEEDS, "alpha", "ch3: el gesto")
        self.assertTrue(found)
        self.assertIn("**Realized:**", new)
        self.assertIn("- ch3: el gesto", new)
        # inserted before Status, and beta untouched
        self.assertIn(SEED_B, new)
        seed = _load(new)[0]
        self.assertEqual(seed.realized, ["ch3: el gesto"])

    def test_appends_in_order(self):
        t, _ = S.append_realized_in_text(TWO_SEEDS, "alpha", "ch3: uno")
        t, _ = S.append_realized_in_text(t, "alpha", "ch7: dos")
        seed = _load(t)[0]
        self.assertEqual(seed.realized, ["ch3: uno", "ch7: dos"])


class Envelope(unittest.TestCase):
    def test_picks_plant_echo_payoff(self):
        seeds = _load(TWO_SEEDS)
        env3 = S.envelope_for_chapter(seeds, 3)
        self.assertEqual([s.id for s in env3["plant"]], ["alpha"])
        env7 = S.envelope_for_chapter(seeds, 7)
        self.assertEqual([s.id for s in env7["echo"]], ["alpha"])
        env22 = S.envelope_for_chapter(seeds, 22)
        self.assertEqual([s.id for s in env22["payoff"]], ["alpha"])


def _load(text: str):
    """Parse seeds from a raw string via a temp file (load_seeds takes a Path)."""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "seeds.md"
        p.write_text(text, encoding="utf-8")
        return S.load_seeds(p)


if __name__ == "__main__":
    unittest.main()
