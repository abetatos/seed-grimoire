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

    def test_thresholds(self):
        rep = W.report(5000, 8000, 12000)
        self.assertTrue(rep.is_too_short)      # < 80% of 8000 = 6400
        rep2 = W.report(8000, 8000, 12000)
        self.assertTrue(rep2.in_range)
        rep3 = W.report(16000, 8000, 12000)
        self.assertTrue(rep3.is_too_long)      # > 130% of 12000 = 15600


if __name__ == "__main__":
    unittest.main()
