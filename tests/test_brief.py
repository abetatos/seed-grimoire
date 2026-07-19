"""Tests for lib.brief — the merged per-chapter brief (Movement 2)."""

import unittest

from lib import brief


SAMPLE = """# Brief — chapter 03

> intro blurb

## Decisiones

- El POV es Bruno.
- La fiesta se corta.

## Estado que no se puede contradecir

- Bruno: ileso.
- El prisma sigue en el cajón.

## Arrastre

- Rimar las-manos-del-lector en el cap 4.
"""


class SplitBrief(unittest.TestCase):
    def test_splits_all_three_sections(self):
        s = brief.split_brief(SAMPLE)
        self.assertEqual(brief.section(s, brief.SEC_DECISIONS),
                         "- El POV es Bruno.\n- La fiesta se corta.")
        self.assertIn("prisma sigue", brief.section(s, brief.SEC_STATE))
        self.assertIn("Rimar", brief.section(s, brief.SEC_ARRASTRE))

    def test_missing_section_is_empty(self):
        s = brief.split_brief("# Brief\n\n## Decisiones\n\n- x\n")
        self.assertEqual(brief.section(s, brief.SEC_STATE), "")
        self.assertEqual(brief.section(s, brief.SEC_ARRASTRE), "")

    def test_empty_text_is_empty_dict(self):
        self.assertEqual(brief.split_brief(""), {})
        self.assertEqual(brief.section(brief.split_brief(""), brief.SEC_DECISIONS), "")

    def test_template_roundtrips_through_split(self):
        # The scaffold plan-chapter fills must always parse into the three named
        # sections, with an empty Arrastre marked so context.py drops it.
        s = brief.split_brief(brief.template(3))
        self.assertIn(brief.SEC_DECISIONS, s)
        self.assertIn(brief.SEC_STATE, s)
        arr = brief.section(s, brief.SEC_ARRASTRE)
        self.assertTrue(any(mk.lower() in arr.lower() for mk in brief.ARRASTRE_EMPTY))


if __name__ == "__main__":
    unittest.main()
