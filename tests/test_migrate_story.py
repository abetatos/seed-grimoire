"""Tests for scripts/migrate_story.py — seeds.md/shadow.md -> world-state store.

The migration's contract is: move DEFINITIONS into the engine store, lose
NOTHING (coverage), and never fabricate the L5 reveal schedule.
"""

import unittest

import migrate_story
from lib.paths import book_paths


SEED_MD = """# Seeds — test

## SEED: el-blanco-frio
**Detail:** cuando Bruno obra, da un blanco que **no calienta**.
**Real meaning:** su tell de cura; carrier de naturaleza-de-bruno.
**Plant in:** 1
**Echo in:** 5, 11, 15
**Payoff in:** Libro II (alguien lo deduce, §12); en el Libro I solo se roza.
**How to plant:** describir la falta de calor.
**Dose:** plant vívido (1) + ecos oblicuos.
**Obligatory:** §14 El blanco frío de Bruno
**Status:** planned

## SEED: el-polvo-gris
**Detail:** el polvo ceniciento que queda donde el rito ha pasado.
**Real meaning:** la marca del drenaje.
**Plant in:** 1
**Echo in:** 8, 15
**Payoff in:** 22
**Status:** planned
"""

SHADOW_MD = """# Shadow timeline — writer-only

## Master truths

## SHADOW-TRUTH: naturaleza-de-bruno
**Truth:** Bruno es la **cura** — un Blanco×Negro.
**Mystery:** La naturaleza de Bruno
**Revealed-by:** el-blanco-frio
**Reveal cap:** suspected
**Status:** hidden
**Surfaced:**

## SHADOW-TRUTH: el-coste-del-don
**Truth:** El vacío le erosiona la identidad.
**Mystery:** El coste del don
**Revealed-by:** el-caldo
**Reveal cap:** sensed
**Status:** hidden
**Surfaced:**
"""


class TestSeedMigration(unittest.TestCase):
    def setUp(self):
        self.seeds, self.truths = migrate_story.build_store(SEED_MD, SHADOW_MD)

    def test_all_seeds_present(self):
        self.assertEqual(set(self.seeds), {"el-blanco-frio", "el-polvo-gris"})

    def test_detail_becomes_desc(self):
        s = self.seeds["el-blanco-frio"]
        self.assertIn("no calienta", s.desc)
        # desc is collapsed to one line
        self.assertNotIn("\n", s.desc)

    def test_schedule_maps_from_plant_echo_payoff(self):
        s = self.seeds["el-polvo-gris"]
        self.assertEqual(s.scheduled_chapters("plant"), [1])
        self.assertEqual(s.scheduled_chapters("echo"), [8, 15])
        self.assertEqual(s.scheduled_chapters("payoff"), [22])

    def test_deferred_payoff_not_in_schedule_but_prose_preserved(self):
        s = self.seeds["el-blanco-frio"]
        # "Libro II" is cross-book → no payoff chapter in THIS book...
        self.assertEqual(s.scheduled_chapters("payoff"), [])
        # ...but the deferred-payoff prose must survive verbatim in notes.
        self.assertIn("Libro II", s.notes)
        self.assertIn("§12", s.notes)

    def test_nonschedule_fields_preserved_in_notes(self):
        s = self.seeds["el-blanco-frio"]
        for fragment in ("Real meaning", "su tell de cura", "How to plant",
                         "Dose", "Obligatory", "§14 El blanco frío", "planned"):
            self.assertIn(fragment, s.notes)

    def test_detail_not_duplicated_into_notes(self):
        # Detail is the one field that becomes desc, so it is skipped in notes.
        s = self.seeds["el-blanco-frio"]
        self.assertNotIn("**Detail:**", s.notes)


class TestTruthMigration(unittest.TestCase):
    def setUp(self):
        self.seeds, self.truths = migrate_story.build_store(SEED_MD, SHADOW_MD)

    def test_all_truths_present(self):
        self.assertEqual(set(self.truths), {"naturaleza-de-bruno", "el-coste-del-don"})

    def test_truth_becomes_desc(self):
        t = self.truths["naturaleza-de-bruno"]
        self.assertIn("cura", t.desc)

    def test_reveal_caps_left_empty_for_L5(self):
        # The per-chapter reveal schedule is L5 work, not in the file.
        for t in self.truths.values():
            self.assertEqual(t.reveal_caps, {})

    def test_cap_level_and_fields_preserved_in_notes(self):
        t = self.truths["naturaleza-de-bruno"]
        self.assertIn("suspected", t.notes)   # the book-wide cap LEVEL
        self.assertIn("Mystery", t.notes)
        self.assertIn("Revealed-by", t.notes)
        self.assertIn("hidden", t.notes)      # status


class TestCoverage(unittest.TestCase):
    def test_clean_migration_has_no_problems(self):
        seeds, truths = migrate_story.build_store(SEED_MD, SHADOW_MD)
        cov = migrate_story.verify_coverage(SEED_MD, SHADOW_MD, seeds, truths)
        self.assertTrue(cov.ok, cov.problems)

    def test_dropped_field_is_caught(self):
        seeds, truths = migrate_story.build_store(SEED_MD, SHADOW_MD)
        # Tamper: wipe one seed's notes → its non-schedule fields are now lost.
        seeds["el-blanco-frio"].notes = ""
        cov = migrate_story.verify_coverage(SEED_MD, SHADOW_MD, seeds, truths)
        self.assertFalse(cov.ok)
        self.assertTrue(any("el-blanco-frio" in p for p in cov.problems))

    def test_dropped_schedule_is_caught(self):
        seeds, truths = migrate_story.build_store(SEED_MD, SHADOW_MD)
        seeds["el-polvo-gris"].schedule["echo"] = [8]  # drop 15
        cov = migrate_story.verify_coverage(SEED_MD, SHADOW_MD, seeds, truths)
        self.assertFalse(cov.ok)
        self.assertTrue(any("echo" in p for p in cov.problems))

    def test_missing_seed_is_caught(self):
        seeds, truths = migrate_story.build_store(SEED_MD, SHADOW_MD)
        del seeds["el-polvo-gris"]
        cov = migrate_story.verify_coverage(SEED_MD, SHADOW_MD, seeds, truths)
        self.assertFalse(cov.ok)
        self.assertTrue(any("id set differs" in p for p in cov.problems))


class TestTouchLogPreserved(unittest.TestCase):
    def test_realized_touches_survive_in_notes(self):
        seed_md = """# Seeds

## SEED: s1
**Detail:** algo.
**Plant in:** 1
**Echo in:** 3
**Realized:**
- ch1: la imagen concreta que se usó
- ch3: el eco que realmente cayó
**Status:** echoed-1
"""
        seeds, truths = migrate_story.build_store(seed_md, "")
        s = seeds["s1"]
        self.assertIn("la imagen concreta que se usó", s.notes)
        self.assertIn("el eco que realmente cayó", s.notes)
        cov = migrate_story.verify_coverage(seed_md, "", seeds, truths)
        self.assertTrue(cov.ok, cov.problems)

    def test_lost_touch_is_caught(self):
        seed_md = """# Seeds

## SEED: s1
**Detail:** algo.
**Plant in:** 1
**Realized:**
- ch1: la imagen concreta que se usó
**Status:** planted
"""
        seeds, truths = migrate_story.build_store(seed_md, "")
        seeds["s1"].notes = "**Status:** planted"  # touch dropped
        cov = migrate_story.verify_coverage(seed_md, "", seeds, truths)
        self.assertFalse(cov.ok)
        self.assertTrue(any("realized touch" in p for p in cov.problems))


class TestElVitralIntegration(unittest.TestCase):
    """The real book must migrate with zero coverage problems (dry run only —
    no writes, so the test is side-effect free)."""

    def test_el_vitral_migrates_clean(self):
        paths = book_paths("el-vitral", 1)
        if not paths.seeds_md.exists():
            self.skipTest("el-vitral book-01 not present")
        cov, view = migrate_story.migrate_book(paths, dry_run=True)
        self.assertTrue(cov.ok, cov.problems)
        self.assertIn("Seeds", view)
        self.assertIn("Shadow truths", view)


class TestRoundTrip(unittest.TestCase):
    def test_store_reload_is_stable(self):
        from lib.engine.story import Seed, Truth
        seeds, truths = migrate_story.build_store(SEED_MD, SHADOW_MD)
        # to_dict -> from_dict must round-trip every field the store persists.
        for s in seeds.values():
            self.assertEqual(Seed.from_dict(s.to_dict()).to_dict(), s.to_dict())
        for t in truths.values():
            self.assertEqual(Truth.from_dict(t.to_dict()).to_dict(), t.to_dict())


if __name__ == "__main__":
    unittest.main()
