"""Tests for lib.verdict — computed PASS/REVISE/REJECT thresholds + tags."""

import unittest

from lib.verdict import compute_verdict


def _doc(must=(), should=(), consider=()):
    parts = ["# Critique — chapter 1\n", "**Verdict:** (to be computed)\n"]
    parts.append("## MUST fix\n" + "\n".join(f"- {m}" for m in must) + "\n")
    parts.append("## SHOULD fix\n" + "\n".join(f"- {s}" for s in should) + "\n")
    parts.append("## CONSIDER\n" + "\n".join(f"- {c}" for c in consider) + "\n")
    parts.append("## What works\n- something landed\n")
    return "\n".join(parts)


class Thresholds(unittest.TestCase):
    def test_pass_zero_must_few_should(self):
        v = compute_verdict(_doc(should=["**[antipattern]** delve", "**[subtext]** flat"]))
        self.assertEqual(v.verdict, "PASS")
        self.assertEqual((v.must, v.should), (0, 2))

    def test_should_over_cap_is_revise(self):
        v = compute_verdict(_doc(should=[f"**[x]** item {i}" for i in range(4)]))
        self.assertEqual(v.verdict, "REVISE")  # 4 > chapter cap 3

    def test_nonstructural_must_is_revise(self):
        v = compute_verdict(_doc(must=["**[reveal-leak]** softened line"]))
        self.assertEqual(v.verdict, "REVISE")

    def test_structural_must_is_reject(self):
        v = compute_verdict(_doc(must=["**[missing-beat]** the confrontation never happens"]))
        self.assertEqual(v.verdict, "REJECT")
        self.assertEqual(v.reject_tags, ["missing-beat"])

    def test_wordcount_under_60_is_reject_but_80_is_not(self):
        self.assertEqual(compute_verdict(_doc(must=["**[wordcount-under-60]** 55%"])).verdict, "REJECT")
        # a mere shortfall tag not in the reject vocab → REVISE (T19)
        self.assertEqual(compute_verdict(_doc(should=["**[wordcount-short]** 75%"])).verdict, "PASS")

    def test_plan_cap_is_six(self):
        doc = _doc(should=[f"**[x]** {i}" for i in range(6)])
        self.assertEqual(compute_verdict(doc, target="plan").verdict, "PASS")
        doc7 = _doc(should=[f"**[x]** {i}" for i in range(7)])
        self.assertEqual(compute_verdict(doc7, target="plan").verdict, "REVISE")

    def test_subbullets_not_counted(self):
        doc = (
            "## MUST fix\n"
            "- **[reveal-leak]** the line\n"
            "  - detail sub-bullet\n"
            "  - another sub-bullet\n"
            "## SHOULD fix\n## CONSIDER\n"
        )
        v = compute_verdict(doc)
        self.assertEqual(v.must, 1)

    def test_unknown_target_raises(self):
        with self.assertRaises(ValueError):
            compute_verdict(_doc(), target="nope")


if __name__ == "__main__":
    unittest.main()
