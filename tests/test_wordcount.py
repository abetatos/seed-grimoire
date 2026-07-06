"""Tests for lib.wordcount — prose counting excludes scaffolding."""

import unittest

from lib import wordcount as W


class CountWords(unittest.TestCase):
    def test_headers_excluded(self):
        self.assertEqual(W.count_words("# Capítulo 1 — Título\n\nuna dos tres"), 3)

    def test_expand_markers_excluded(self):
        with_markers = (
            "una dos tres\n"
            "▼▼▼ INICIO EXPAND 1 (prosa AÑADIDA — no original) ▼▼▼\n"
            "cuatro cinco\n"
            "▲▲▲ FIN EXPAND 1 ▲▲▲\n"
        )
        # 5 prose words; the banner lines (which contain words like EXPAND,
        # INICIO, prosa...) must NOT be counted.
        self.assertEqual(W.count_words(with_markers), 5)

    def test_no_target_validation_api(self):
        # Guard the invariant: this module must never grow back a
        # count-vs-target report the pipeline could show the model.
        self.assertFalse(hasattr(W, "report"))
        self.assertFalse(hasattr(W, "WordcountReport"))


if __name__ == "__main__":
    unittest.main()
