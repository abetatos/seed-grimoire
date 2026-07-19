"""Tests for lib.token_report — the Phase-0 per-phase token instrument."""

import unittest

from lib.token_report import (
    CONTEXT_CEILING, OUTPUT_TARGET, analyze, context_size,
)


def _assistant(skill=None, out=0, inp=0, cache_read=0, cache_create=0, sidechain=False):
    return {
        "type": "assistant",
        "attributionSkill": skill,
        "isSidechain": sidechain,
        "message": {"usage": {
            "input_tokens": inp,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_create,
            "output_tokens": out,
        }},
    }


class ContextSize(unittest.TestCase):
    def test_sums_fresh_and_cached(self):
        self.assertEqual(
            context_size({"input_tokens": 100, "cache_read_input_tokens": 20,
                          "cache_creation_input_tokens": 5}), 125)

    def test_missing_fields_default_zero(self):
        self.assertEqual(context_size({}), 0)


class Analyze(unittest.TestCase):
    def test_output_bucketed_by_phase(self):
        r = analyze([
            _assistant("write-chapter", out=100),
            _assistant("write-chapter", out=50),
            _assistant("update-canon", out=30),
        ])
        by = {p.phase: p.output_tokens for p in r.phases}
        self.assertEqual(by, {"write-chapter": 150, "update-canon": 30})
        self.assertEqual(r.total_output, 180)

    def test_phases_sorted_by_output_desc(self):
        r = analyze([
            _assistant("plan-chapter", out=10),
            _assistant("write-chapter", out=200),
        ])
        self.assertEqual([p.phase for p in r.phases], ["write-chapter", "plan-chapter"])

    def test_none_skill_bucketed_as_conductor(self):
        r = analyze([_assistant(None, out=42)])
        self.assertEqual(r.phases[0].phase, "(conductor/other)")
        self.assertEqual(r.phases[0].output_tokens, 42)

    def test_sidechain_kept_separate(self):
        r = analyze([
            _assistant("write-chapter", out=100, inp=90_000),
            _assistant("critique", out=999, inp=90_000, sidechain=True),
        ])
        self.assertEqual(r.total_output, 100)          # side output excluded
        self.assertEqual(r.sidechain_output, 999)
        self.assertEqual(r.sidechain_messages, 1)
        # the huge sidechain context must NOT count toward the main-thread peak
        self.assertEqual(r.peak_context, 90_000)

    def test_peak_context_is_max_over_main_thread(self):
        r = analyze([
            _assistant("write-chapter", inp=10_000, cache_read=20_000),   # 30k
            _assistant("write-chapter", inp=50_000, cache_read=60_000),   # 110k
            _assistant("update-canon", inp=5_000),                        # 5k
        ])
        self.assertEqual(r.peak_context, 110_000)

    def test_non_assistant_records_ignored(self):
        r = analyze([
            {"type": "user", "message": {"content": "hi"}},
            {"type": "system"},
            _assistant("write-chapter", out=10),
        ])
        self.assertEqual(r.total_output, 10)
        self.assertEqual(len(r.phases), 1)

    def test_threshold_flags(self):
        under = analyze([_assistant("write-chapter", out=10, inp=1_000)])
        self.assertFalse(under.over_ceiling)
        self.assertFalse(under.over_target)
        over = analyze([
            _assistant("write-chapter", out=OUTPUT_TARGET + 1, inp=CONTEXT_CEILING + 1),
        ])
        self.assertTrue(over.over_ceiling)
        self.assertTrue(over.over_target)


if __name__ == "__main__":
    unittest.main()
