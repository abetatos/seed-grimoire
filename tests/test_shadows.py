"""Tests for lib.shadows — truth parsing, surgical mutation, reveal derivation."""

import tempfile
import unittest
from pathlib import Path

from lib import shadows as SH


TRUTH_A = """## SHADOW-TRUTH: t-alpha
**Truth:** el padre fue borrado por el prisma
**Revealed-by:** el-prisma-lee-drena, borrarse-como-el-padre
**Reveal cap:** suspected
**Status:** hidden
"""

TRUTH_B = """## SHADOW-TRUTH: t-beta
**Truth:** exposición sin siembra
**Confirm in:** 13
**Reveal cap:** confirmed
**Status:** hidden
"""

DOC = "# Shadow — test\n\n## Master truths\n\n" + TRUTH_A + "\n" + TRUTH_B


def _load(text: str):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "shadow.md"
        p.write_text(text, encoding="utf-8")
        return SH.load_truths(p)


class Parsing(unittest.TestCase):
    def test_fields(self):
        by_id = {t.id: t for t in _load(DOC)}
        self.assertEqual(by_id["t-alpha"].revealed_by,
                         ["el-prisma-lee-drena", "borrarse-como-el-padre"])
        self.assertEqual(by_id["t-alpha"].reveal_cap, "suspected")
        self.assertEqual(by_id["t-beta"].confirm_in, 13)

    def test_no_spurious_warnings(self):
        for t in _load(DOC):
            self.assertEqual(t.parse_warnings, [], t.id)


class SurgicalStatus(unittest.TestCase):
    def test_only_target_changes(self):
        new, found = SH.update_truth_status_in_text(DOC, "t-alpha", "sensed")
        self.assertTrue(found)
        self.assertIn("**Status:** sensed", new)
        self.assertIn(TRUTH_B, new)  # beta untouched

    def test_noop_identical(self):
        new, found = SH.update_truth_status_in_text(DOC, "t-alpha", "hidden")
        self.assertTrue(found)
        self.assertEqual(new, DOC)


class SurfacedLog(unittest.TestCase):
    def test_append_creates_block(self):
        new, found = SH.append_surfaced_in_text(DOC, "t-alpha", "ch5 [sensed]: el hueco")
        self.assertTrue(found)
        self.assertIn("**Surfaced:**", new)
        self.assertIn("- ch5 [sensed]: el hueco", new)
        self.assertIn(TRUTH_B, new)


class DeriveStatus(unittest.TestCase):
    def test_clamped_by_cap(self):
        t = _load(DOC)[0]  # t-alpha, cap=suspected
        # both carriers paid_off would push to confirmed, but cap holds at suspected
        status = SH.derive_status(t, {
            "el-prisma-lee-drena": "paid_off",
            "borrarse-como-el-padre": "paid_off",
        })
        self.assertEqual(status, "suspected")

    def test_planted_seed_gives_sensed(self):
        t = _load(DOC)[0]
        status = SH.derive_status(t, {"el-prisma-lee-drena": "planted"})
        self.assertEqual(status, "sensed")

    def test_seedless_keeps_stored(self):
        t = _load(DOC)[1]  # t-beta, no revealed_by
        self.assertEqual(SH.derive_status(t, {}), "hidden")


if __name__ == "__main__":
    unittest.main()
