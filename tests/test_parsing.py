"""Tests for lib.parsing — the shared, loud parser for the never-compress files."""

import unittest

from lib.parsing import (
    parse_chapter_list,
    parse_single_chapter,
    parse_id_list,
    parse_touch_log,
    strip_expand_markers,
)


class ParseChapterList(unittest.TestCase):
    def test_bare_and_comma_list(self):
        self.assertEqual(parse_chapter_list("12"), ([12], []))
        self.assertEqual(parse_chapter_list("15, 18, 20, 21"), ([15, 18, 20, 21], []))

    def test_chapter_word_prefixes(self):
        for raw in ("ch 12", "cap 12", "capítulo 12", "Chapter 12", "chapters 12"):
            nums, warns = parse_chapter_list(raw)
            self.assertEqual((nums, warns), ([12], []), raw)

    def test_empty_and_dash(self):
        for raw in ("", "  ", "—", "-", "none", "N/A"):
            self.assertEqual(parse_chapter_list(raw), ([], []), raw)

    def test_trailing_comma_no_warning(self):
        # empty token from a trailing comma must be skipped silently
        self.assertEqual(parse_chapter_list("12,"), ([12], []))

    def test_annotation_is_dropped_not_warned(self):
        # the live bare-digit-with-prose form: chapter kept, prose ignored.
        nums, warns = parse_chapter_list(
            "22 (el clímax lo pone en la propia mano de Bruno, sobre Mauro) → eco"
        )
        self.assertEqual(nums, [22])
        self.assertEqual(warns, [])

    def test_cross_book_deferral_yields_nothing(self):
        # "libro"/"book" means not-this-book: no chapter, NO warning.
        for raw in ("Libro II", "Libro III (color devuelto)", "Libros II-III",
                    "Book III", "libro 2, cap 3"):
            nums, warns = parse_chapter_list(raw)
            self.assertEqual((nums, warns), ([], []), raw)

    def test_malformed_token_warns_but_keeps_going(self):
        nums, warns = parse_chapter_list("12a")
        self.assertEqual(nums, [])
        self.assertEqual(len(warns), 1)
        self.assertIn("12a", warns[0])

    def test_mixed_good_and_bad(self):
        nums, warns = parse_chapter_list("12, xx, 18")
        self.assertEqual(nums, [12, 18])
        self.assertEqual(len(warns), 1)


class ParseSingleChapter(unittest.TestCase):
    def test_single(self):
        self.assertEqual(parse_single_chapter("3"), (3, []))

    def test_cross_book_is_none(self):
        self.assertEqual(parse_single_chapter("Libro II"), (None, []))

    def test_extra_numbers_warn(self):
        val, warns = parse_single_chapter("3 4")
        self.assertEqual(val, 3)
        self.assertEqual(len(warns), 1)


class ParseIdList(unittest.TestCase):
    def test_backtick_stripped(self):
        self.assertEqual(
            parse_id_list("el-blanco-frio, `borrarse-como-el-padre`"),
            ["el-blanco-frio", "borrarse-como-el-padre"],
        )

    def test_empty(self):
        self.assertEqual(parse_id_list("—"), [])


class ParseTouchLog(unittest.TestCase):
    def test_bullets(self):
        body = "- ch1: una imagen\n* ch5: otra\n+ ch9: tercera\n"
        self.assertEqual(
            parse_touch_log(body),
            ["ch1: una imagen", "ch5: otra", "ch9: tercera"],
        )

    def test_blank_lines_dropped(self):
        self.assertEqual(parse_touch_log("\n- a\n\n- b\n\n"), ["a", "b"])


class StripExpandMarkers(unittest.TestCase):
    def test_removes_banners_keeps_prose(self):
        text = (
            "prosa original.\n"
            "▼▼▼ INICIO EXPAND 1 (prosa AÑADIDA — no original) ▼▼▼\n"
            "prosa añadida.\n"
            "▲▲▲ FIN EXPAND 1 ▲▲▲\n"
            "más prosa.\n"
        )
        out = strip_expand_markers(text)
        self.assertNotIn("EXPAND", out)
        self.assertNotIn("▼", out)
        self.assertIn("prosa original.", out)
        self.assertIn("prosa añadida.", out)
        self.assertIn("más prosa.", out)


if __name__ == "__main__":
    unittest.main()
