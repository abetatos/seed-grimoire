"""Tests for the deterministic prose-tic auditor (explanatory-simile density)."""

import tempfile
import unittest
from pathlib import Path

from scripts.lib import prose_lint
from tests._fixtures import make_book


class TestSplitScenes(unittest.TestCase):
    def test_no_break_is_one_scene(self):
        self.assertEqual(len(prose_lint.split_scenes("una sola escena.")), 1)

    def test_splits_on_markers(self):
        text = "escena uno.\n\n* * *\n\nescena dos.\n\n---\n\nescena tres."
        self.assertEqual(len(prose_lint.split_scenes(text)), 3)

    def test_asterisks_and_dots(self):
        text = "a\n***\nb\n· · ·\nc"
        self.assertEqual(len(prose_lint.split_scenes(text)), 3)


class TestFindSimiles(unittest.TestCase):
    def test_igual_que(self):
        self.assertEqual(
            len(prose_lint.find_similes("frío, igual que el calor de una piedra")), 1
        )

    def test_comma_como(self):
        self.assertEqual(len(prose_lint.find_similes("sin miedo, como se repite")), 1)

    def test_como_article(self):
        self.assertEqual(
            len(prose_lint.find_similes("iluminada como una moneda")), 1
        )

    def test_bare_como_is_not_matched(self):
        # "como" as "since"/"as" must not fire, or the check is pure noise.
        self.assertEqual(len(prose_lint.find_similes("como no había nadie, salió")), 0)

    def test_comma_como_counted_once(self):
        # ", como una" would match two sub-patterns; finditer must count it once.
        self.assertEqual(len(prose_lint.find_similes("brilló, como una moneda")), 1)

    def test_cual_not_cual_accented(self):
        self.assertEqual(len(prose_lint.find_similes("blanco cual nieve")), 1)
        self.assertEqual(len(prose_lint.find_similes("¿cuál era el pozo?")), 0)


class TestAuditProse(unittest.TestCase):
    def test_clean_prose_no_finding(self):
        text = "Bruno bajó al pueblo. Midió a la gente por las manos. " * 40
        scenes, findings = prose_lint.audit_prose(text)
        self.assertEqual(findings, [])

    def test_simile_heavy_scene_flags(self):
        # Five explanatory similes in a short scene → over the rate ceiling.
        text = (
            "El verde se iba, igual que el calor de una piedra. "
            "Los ojos le pasaban como el agua por encima. "
            "Cayó, como una moneda. "
            "Ardía como el primer trago de algo caliente. "
            "Se repetía, como una canción sin final."
        )
        scenes, findings = prose_lint.audit_prose(text)
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0].count, 5)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].level, prose_lint.WARN)

    def test_below_floor_does_not_flag(self):
        # One simile, even in a tiny scene, is under the absolute floor.
        text = "Cayó al pozo, como una moneda."
        _, findings = prose_lint.audit_prose(text)
        self.assertEqual(findings, [])

    def test_thresholds_are_tunable(self):
        text = "Cayó como una piedra. Brilló como una moneda."
        _, strict = prose_lint.audit_prose(text, min_count=2, rate_per_1000=0.0)
        self.assertEqual(len(strict), 1)
        _, loose = prose_lint.audit_prose(text, min_count=99, rate_per_1000=4.0)
        self.assertEqual(loose, [])


class TestNamedTics(unittest.TestCase):
    def test_no_x_sino_y(self):
        n, ex = prose_lint.count_no_x_sino_y("No era verde, sino gris del todo.")
        self.assertEqual(n, 1)
        self.assertTrue(ex)

    def test_como_si_per_paragraph(self):
        text = "Miró como si supiera, temió como si doliera.\n\notro párrafo tranquilo."
        worst, _ = prose_lint.max_como_si_per_paragraph(text)
        self.assertEqual(worst, 2)

    def test_repetition_emphasis_identical(self):
        n, _ = prose_lint.count_repetition_emphasis("Duraba y paraba. Duraba y paraba.")
        self.assertEqual(n, 1)

    def test_repetition_emphasis_short_echo(self):
        n, _ = prose_lint.count_repetition_emphasis("Volvían más grises. Volvían menos.")
        self.assertEqual(n, 1)

    def test_anaphora_run(self):
        best, _ = prose_lint.max_anaphora_run("Volvía. Volvía otra vez. Volvía siempre.")
        self.assertEqual(best, 3)

    def test_no_false_anaphora(self):
        best, _ = prose_lint.max_anaphora_run("Bajó. Subió. Miró la calle.")
        self.assertEqual(best, 1)

    def test_gerund_opener(self):
        n, _ = prose_lint.gerund_opener_count("Corriendo, llegó tarde. Se sentó.")
        self.assertEqual(n, 1)


class TestChapterTics(unittest.TestCase):
    def test_over_cap_flag(self):
        # Two "no X, sino Y" in one (single-scene) chapter, cap 1/scene → over.
        text = ("No era verde, sino gris. Caminó un rato largo por la vega. "
                "No fue miedo, sino algo peor.")
        cfg = prose_lint.ProseLintConfig(caps=dict(prose_lint.DEFAULT_CAPS),
                                         reserved=[], extra_patterns=[],
                                         source="defaults")
        tics = prose_lint.audit_chapter_tics(text, cfg)
        nxs = next(t for t in tics if t.name == "no X, sino Y")
        self.assertTrue(nxs.over)

    def test_clean_chapter_no_flags(self):
        text = "Bruno bajó al pueblo. Midió a la gente por las manos. " * 20
        cfg = prose_lint.ProseLintConfig(caps=dict(prose_lint.DEFAULT_CAPS),
                                         reserved=[], extra_patterns=[],
                                         source="defaults")
        self.assertFalse(any(t.over for t in prose_lint.audit_chapter_tics(text, cfg)))


class TestConfig(unittest.TestCase):
    def test_missing_file_uses_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            paths = make_book(Path(d))
            cfg = prose_lint.load_config(paths)
            self.assertEqual(cfg.source, "defaults")
            self.assertEqual(cfg.reserved, [])
            self.assertEqual(cfg.caps["no_x_sino_y_per_scene"], 1)

    def test_reserved_allowed_chapters_from_seed_schedule(self):
        # SEED el-pozo in _fixtures: plant 1, echo 2, payoff 3.
        seed_chapters = {"el-pozo": {1, 2, 3}}
        data = {"reserved": [{"word": "pozo", "pattern": r"\bpozo\w*", "seeds": ["el-pozo"]}]}
        cfg = prose_lint.parse_config(data, seed_chapters)
        self.assertEqual(cfg.reserved[0].allowed_chapters, {1, 2, 3})

    def test_reserved_out_of_schedule_flagged(self):
        seed_chapters = {"s": {1}}
        data = {"reserved": [{"word": "apagar", "pattern": r"\bapag\w+", "seeds": ["s"]}]}
        cfg = prose_lint.parse_config(data, seed_chapters)
        # chapter 1 scheduled, chapter 2 not.
        self.assertTrue(prose_lint.audit_reserved(1, "se apagaba todo", cfg)[0].scheduled)
        self.assertFalse(prose_lint.audit_reserved(2, "se apagaba todo", cfg)[0].scheduled)


class TestCrossChapter(unittest.TestCase):
    def test_signature_word_across_chapters(self):
        chapters = {
            1: "La ventana daba al patio gris.",
            2: "Cruzó frente a la ventana cerrada.",
            3: "La ventana temblaba con el viento.",
        }
        cfg = prose_lint.ProseLintConfig(caps={}, reserved=[], extra_patterns=[],
                                         source="defaults")
        rep = prose_lint.audit_cross_chapter(chapters, cfg)
        self.assertIn("ventana", [s.word for s in rep.signature_words])

    def test_opening_echo_detected(self):
        chapters = {
            1: "Bruno bajó al pueblo al alba con el recado en la mano.",
            2: "Bruno bajó al pueblo al alba con la moneda en la mano.",
        }
        cfg = prose_lint.ProseLintConfig(caps={}, reserved=[], extra_patterns=[],
                                         source="defaults")
        rep = prose_lint.audit_cross_chapter(chapters, cfg)
        self.assertTrue(rep.opening_echoes)

    def test_proper_nouns_not_signature_words(self):
        # "Bruno" recurs but is a proper noun (capitalised) → excluded.
        chapters = {1: "Bruno anduvo.", 2: "Bruno miró.", 3: "Bruno calló."}
        cfg = prose_lint.ProseLintConfig(caps={}, reserved=[], extra_patterns=[],
                                         source="defaults")
        rep = prose_lint.audit_cross_chapter(chapters, cfg)
        self.assertNotIn("bruno", [s.word for s in rep.signature_words])


if __name__ == "__main__":
    unittest.main()
