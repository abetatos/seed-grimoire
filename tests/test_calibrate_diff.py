"""Tests for scripts/calibrate_diff.py — sentence alignment + delta rendering."""

import unittest

import calibrate_diff
from lib import prose_lint


class TestAlign(unittest.TestCase):
    def test_rewrite_pairs_matched(self):
        before = ["El pozo estaba seco, como una boca muda.",
                  "Bruno se acercó al brocal."]
        after = ["El pozo estaba seco.",
                 "Bruno se acercó al brocal y tocó la piedra."]
        pairs, cuts, adds = calibrate_diff.align(before, after)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(cuts, [])
        self.assertEqual(adds, [])
        # Each pair keeps its own before/after aligned by best ratio.
        self.assertTrue(pairs[0][0].startswith("El pozo"))
        self.assertTrue(pairs[0][1].startswith("El pozo"))

    def test_pure_cut(self):
        # A sentence flanked by equal anchors is a clean 'delete' opcode → cut.
        before = ["Ancla estable uno.", "Frase que el autor elimina.", "Ancla estable dos."]
        after = ["Ancla estable uno.", "Ancla estable dos."]
        pairs, cuts, adds = calibrate_diff.align(before, after)
        self.assertEqual(pairs, [])
        self.assertEqual(len(cuts), 1)
        self.assertEqual(adds, [])

    def test_pure_add(self):
        before = ["Ancla estable uno.", "Ancla estable dos."]
        after = ["Ancla estable uno.", "Frase nueva intercalada.", "Ancla estable dos."]
        pairs, cuts, adds = calibrate_diff.align(before, after)
        self.assertEqual(pairs, [])
        self.assertEqual(cuts, [])
        self.assertEqual(len(adds), 1)

    def test_identical_lists_no_changes(self):
        s = ["Una frase.", "Otra frase distinta."]
        pairs, cuts, adds = calibrate_diff.align(s, list(s))
        self.assertEqual((pairs, cuts, adds), ([], [], []))


class TestRender(unittest.TestCase):
    def _cfg(self):
        return prose_lint.ProseLintConfig(caps=dict(prose_lint.DEFAULT_CAPS),
                                          reserved=[], extra_patterns=[],
                                          source="defaults")

    def test_report_shows_simile_delta(self):
        before = ("El pozo estaba seco, como una boca muda. "
                  "La luz caía igual que la ceniza sobre el tejado.")
        after = "El pozo estaba seco. La luz caía sobre el tejado."
        report = calibrate_diff.render("capítulo 1", before, after, self._cfg())
        self.assertIn("# Calibración", report)
        self.assertIn("símil explicativo", report)
        # Two similes removed → the tic table shows the drop.
        self.assertIn("2", report)
        self.assertIn("Reescrituras", report)

    def test_no_diff_reports_no_changes(self):
        text = "Una frase estable que no cambia entre versiones."
        report = calibrate_diff.render("capítulo 1", text, text, self._cfg())
        self.assertIn("Sin diferencias", report)


if __name__ == "__main__":
    unittest.main()
