"""Tests for the store-backed deep plan audit (critique-plan L1-L5 pass)."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from lib import shadows as SH
from lib.engine import store
from lib.engine.graph import WorldGraph
from lib.engine.state import Entity
from lib.engine.events import Event
from lib.engine.story import Seed, Truth

# audit_plan_store lives under .claude (not on the package path); load by location.
_AUD = Path(__file__).resolve().parents[1] / ".claude/skills/critique-plan/scripts/audit_plan_store.py"
_spec = importlib.util.spec_from_file_location("audit_plan_store", _AUD)
AUD = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AUD)


def _tiers(findings):
    return {(t, itype) for t, itype, _ in findings}


class Helpers(unittest.TestCase):
    def test_reveal_level_index(self):
        self.assertEqual(AUD._reveal_level_index("hidden"), 0)
        self.assertEqual(AUD._reveal_level_index("suspected"), 2)
        # decoy doses map onto the reader ladder: misled≈1, convinced≈2, inverted≈3
        self.assertEqual(AUD._reveal_level_index("misled"), 1)
        self.assertEqual(AUD._reveal_level_index("inverted"), 3)
        self.assertIsNone(AUD._reveal_level_index("brillante"))

    def test_ladder_of(self):
        self.assertEqual(AUD._ladder_of(["hidden", "suspected"]), "reader")
        self.assertEqual(AUD._ladder_of(["misled", "convinced"]), "decoy")
        self.assertIsNone(AUD._ladder_of(["hidden", "convinced"]))  # mixed

    def test_layout_chapter_seeds(self):
        layout = (
            "## Cap 1 · x\n- Seeds: `alfa`(plant) · `beta`(plant) · `no-un-seed`.\n\n"
            "## Cap 2 · y\n- Seeds: `alfa`(echo).\n"
        )
        got = AUD.layout_chapter_seeds(layout, {"alfa", "beta"})
        self.assertEqual(got[1], {"alfa", "beta"})  # non-seed backtick ignored
        self.assertEqual(got[2], {"alfa"})

    def test_layout_accepts_english_header(self):
        # a non-Spanish layout must still parse (else every seed flags un-carried)
        got = AUD.layout_chapter_seeds("## Chapter 1 · x\n- Seeds: `alfa`.\n", {"alfa"})
        self.assertEqual(got[1], {"alfa"})


class Checks(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.sd = Path(self._tmp.name)
        g = WorldGraph()
        g.add_place("region", "Region", "region")
        g.add_place("plaza", "Plaza", "sala", parent="region")
        g.add_place("casa", "Casa", "sala", parent="region")
        g.connect("plaza", "casa", "a pie", "minutos")
        store.save_graph(self.sd, g)
        store.save_entities(self.sd, [Entity(id="bruno", name="Bruno", kind="character", position="casa")])
        store.save_seeds(self.sd, {"alfa": Seed(id="alfa", desc="a", schedule={"plant": [1], "echo": [2]})})
        store.save_truths(self.sd, {})
        store.append_event(self.sd, Event(chapter=1, seq=0, type="time", data={"day": 1, "franja": "mañana"}))

    def tearDown(self):
        self._tmp.cleanup()

    def test_replay_clean(self):
        self.assertEqual(AUD.check_replay(self.sd), [])

    def test_seed_carrier_coverage(self):
        # layout carries alfa's plant@1 but NOT its echo@2 → one seed-no-carrier
        layout = "## Cap 1 · x\n- Seeds: `alfa`(plant).\n\n## Cap 2 · y\n- Seeds: `otro`.\n"
        findings = AUD.check_seed_carriers(self.sd, declared=2, layout_text=layout)
        self.assertEqual(_tiers(findings), {(AUD.SHOULD, "seed-no-carrier")})
        self.assertIn("echo", findings[0][2])
        # fully carried → clean
        layout2 = "## Cap 1 · x\n- Seeds: `alfa`.\n\n## Cap 2 · y\n- Seeds: `alfa`.\n"
        self.assertEqual(AUD.check_seed_carriers(self.sd, 2, layout2), [])
        # a later-book touch (ch > declared) is out of range, never flagged
        self.assertEqual(AUD.check_seed_carriers(self.sd, 1, "## Cap 1 · x\n- Seeds: `alfa`.\n"), [])
        # missing layout → a single layout-missing SHOULD
        self.assertEqual(_tiers(AUD.check_seed_carriers(self.sd, 2, None)), {(AUD.SHOULD, "layout-missing")})
        # declared=0 (setup unreadable) must NOT silently skip every touch — the
        # un-carried echo@2 is still flagged
        self.assertEqual(_tiers(AUD.check_seed_carriers(self.sd, 0, layout)),
                         {(AUD.SHOULD, "seed-no-carrier")})

    def test_graph_isolated_node(self):
        self.assertEqual(AUD.check_graph_reachable(self.sd), [])  # plaza/casa edged, region is parent
        g = store.load_graph(self.sd)
        g.add_place("isla", "Isla", "sala", parent="region")  # a leaf with no edge
        store.save_graph(self.sd, g)
        self.assertEqual(_tiers(AUD.check_graph_reachable(self.sd)), {(AUD.SHOULD, "graph-isolated")})

    def test_reveal_reader_above_cap_is_must(self):
        store.save_truths(self.sd, {"t": Truth(id="t", desc="d", reveal_caps={13: "confirmed"})})
        shadow = [SH.Truth(id="t", reveal_cap="suspected", revealed_by=["alfa"])]
        self.assertEqual(_tiers(AUD.check_reveal_ladder(self.sd, shadow)),
                         {(AUD.MUST, "reveal-above-cap")})

    def test_reveal_decoy_convinced_under_sensed_is_should(self):
        # decoy stops at `convinced` (never inverts) — reveals nothing of the truth,
        # so no MUST; but it runs deeper than shadow's mapped cap → a SHOULD nudge.
        store.save_truths(self.sd, {"p": Truth(id="p", desc="d", reveal_caps={1: "misled", 9: "convinced"})})
        shadow = [SH.Truth(id="p", reveal_cap="sensed", decoy="the saint comes", revealed_by=["alfa"])]
        self.assertEqual(_tiers(AUD.check_reveal_ladder(self.sd, shadow)),
                         {(AUD.SHOULD, "decoy-ceiling")})

    def test_reveal_decoy_inverted_early_is_must(self):
        store.save_truths(self.sd, {"p": Truth(id="p", desc="d", reveal_caps={9: "inverted"})})
        shadow = [SH.Truth(id="p", reveal_cap="sensed", decoy="the saint comes", revealed_by=["alfa"])]
        self.assertEqual(_tiers(AUD.check_reveal_ladder(self.sd, shadow)),
                         {(AUD.MUST, "reveal-above-cap")})

    def test_reveal_uncapped_surfacing_truth_is_should(self):
        store.save_truths(self.sd, {"t": Truth(id="t", desc="d", reveal_caps={})})
        shadow = [SH.Truth(id="t", reveal_cap="suspected", revealed_by=["alfa"])]
        self.assertEqual(_tiers(AUD.check_reveal_ladder(self.sd, shadow)),
                         {(AUD.SHOULD, "reveal-uncapped")})

    def test_reveal_nonmonotonic_is_should(self):
        store.save_truths(self.sd, {"t": Truth(id="t", desc="d", reveal_caps={5: "suspected", 9: "sensed"})})
        shadow = [SH.Truth(id="t", reveal_cap="suspected", revealed_by=["alfa"])]
        self.assertIn((AUD.SHOULD, "reveal-nonmonotonic"), _tiers(AUD.check_reveal_ladder(self.sd, shadow)))

    def test_truth_parity(self):
        store.save_truths(self.sd, {"only-store": Truth(id="only-store", desc="d")})
        findings = AUD.check_truth_parity(self.sd, {"only-shadow"})
        self.assertEqual(_tiers(findings), {(AUD.SHOULD, "truth-parity")})
        self.assertEqual(len(findings), 2)  # one each direction


class Gating(unittest.TestCase):
    def test_no_store_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "report.md"
            rc = AUD.main(["--series-slug", "does-not-exist", "--book-number", "1",
                           "--output", str(out)])
            self.assertEqual(rc, 0)
            self.assertIn("not migrated", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
