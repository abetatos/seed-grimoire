"""Tests for lib.quotes — critique quote extraction + verification."""

import unittest

from lib import quotes


class Extraction(unittest.TestCase):
    def test_four_quote_styles(self):
        # angle, straight, curly-double, curly-single — each ≥4 words.
        bullet = ('**[x]** — «el gris que mira caras» y "una luz que no calienta" '
                  'y “el pozo sin brocal cae” y ‘midió a la gente así’ → fix')
        spans = quotes.extract_quoted_spans(bullet)
        self.assertEqual(len(spans), 4)
        self.assertIn("el gris que mira caras", spans)
        self.assertIn("una luz que no calienta", spans)

    def test_short_spans_and_file_refs_ignored(self):
        # "setup.md:194" and short 1-2 word quotes are references, not evidence.
        bullet = '**[consistencia]** — `setup.md:194` dice "Saúl" → corregir a Olmo'
        self.assertEqual(quotes.extract_quoted_spans(bullet), [])

    def test_min_words_floor_is_tunable(self):
        bullet = 'dice "dos palabras" aquí'
        self.assertEqual(quotes.extract_quoted_spans(bullet, min_words=4), [])
        self.assertEqual(quotes.extract_quoted_spans(bullet, min_words=2),
                         ["dos palabras"])

    def test_emphasis_wrapped_quote(self):
        bullet = '**[tic]** — *"el hilo verde a medio tejer"* → oblicuo'
        self.assertEqual(quotes.extract_quoted_spans(bullet),
                         ["el hilo verde a medio tejer"])


class Verification(unittest.TestCase):
    CHAPTER = ("Bruno bajó al pueblo al alba. Una luz que no calienta le "
               "enfrió la nuca. El telar de la madre presidía el cuarto vacío.")

    def test_real_quote_verifies(self):
        f = quotes.verify_quotes(["una luz que no calienta"],
                                 {"chapter": self.CHAPTER})
        self.assertTrue(f[0].verified)
        self.assertEqual(f[0].where, "chapter")

    def test_fabricated_quote_fails(self):
        f = quotes.verify_quotes(["un dragón escupió fuego azul"],
                                 {"chapter": self.CHAPTER})
        self.assertFalse(f[0].verified)
        self.assertIsNone(f[0].where)

    def test_source_file_quote_passes_via_secondary_haystack(self):
        # A finding may quote the rule it says the chapter breaks.
        f = quotes.verify_quotes(["el POV de esa hebra es Olmo"],
                                 {"chapter": self.CHAPTER,
                                  "setup.md": "En el plan, el POV de esa hebra es Olmo."})
        self.assertTrue(f[0].verified)
        self.assertEqual(f[0].where, "setup.md")

    def test_curly_vs_straight_and_accents(self):
        # Curly quotes / NFKC differences must not defeat a real match; accents
        # are preserved (they carry meaning), and casing is ignored.
        chapter = "El niño Bruno midió a la gente por las manos."
        self.assertTrue(quotes.verify_quotes(["Midió a la gente por las manos"],
                                             {"chapter": chapter})[0].verified)

    def test_ellipsis_requires_ordered_fragments(self):
        chapter = "Entró en la casa. Miró el telar. Salió sin decir nada."
        # both fragments present, in order → verified
        self.assertTrue(quotes.verify_span("Entró en la casa … Salió sin decir nada",
                                           quotes.normalize(chapter)))
        # out of order → not verified
        self.assertFalse(quotes.verify_span("Salió sin decir nada … Entró en la casa",
                                            quotes.normalize(chapter)))


if __name__ == "__main__":
    unittest.main()
