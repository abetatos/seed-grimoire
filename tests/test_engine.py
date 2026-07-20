"""Tests for the world-state engine (RESTRUCTURE-V2 Phase 1).

Covers the modules in isolation plus a fixture-world integration that exercises
the Phase-1 acceptance criteria: where / copresent / feasible / replay, and the
four commit-integrity rejections (teleport, backward clock, transfer-without-
holding, reveal-past-cap) plus the off-plan touch.
"""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from lib.engine.graph import WorldGraph, GraphError, aggregate_cost
from lib.engine.clock import Clock, ClockError, elapsed_bucket, elapsed_steps
from lib.engine.state import Entity, WorldState
from lib.engine.story import Seed, Truth, seed_status, due, overdue, DORMANT, PLANTED, ECHOING, PAID
from lib.engine.events import Event, IntegrityError, replay, touches_for
from lib.engine import queries as q
from lib.engine import render, store

import world_tool


# --------------------------------------------------------------------------
# graph
# --------------------------------------------------------------------------
class GraphTests(unittest.TestCase):
    def _g(self):
        g = WorldGraph()
        g.add_place("valle", "Valle", "region")
        g.add_place("aldea", "Aldea", "aldea", parent="valle")
        g.add_place("plaza", "Plaza", "sala", parent="aldea")
        g.add_place("casa", "Casa", "sala", parent="aldea")
        g.add_place("granero", "Granero", "sala", parent="aldea")
        g.add_place("puerto", "Puerto", "ciudad", parent="valle")
        g.connect("plaza", "casa", "a pie", "minutos")
        g.connect("plaza", "granero", "a pie", "minutos")
        g.connect("casa", "granero", "a pie", "horas")
        g.connect("plaza", "puerto", "carro", "días")
        return g

    def test_path_and_adjacency(self):
        g = self._g()
        self.assertTrue(g.adjacent("plaza", "casa"))
        self.assertFalse(g.adjacent("casa", "puerto"))
        self.assertEqual(g.path("casa", "puerto"), ["casa", "plaza", "puerto"])
        self.assertIsNone(g.path("plaza", "isla"))  # unknown place

    def test_travel_cost_is_least_cost_path(self):
        g = self._g()
        # direct casa-granero is horas(1); via plaza is minutos+minutos = 0 → cheaper
        self.assertEqual(g.travel_cost("casa", "granero"), "minutos")
        self.assertEqual(g.travel_cost("casa", "puerto"), "días")  # 0 + 4 clamped
        self.assertEqual(g.travel_cost("plaza", "plaza"), "minutos")

    def test_contains_walks_parent_chain(self):
        g = self._g()
        self.assertTrue(g.contains("valle", "plaza"))
        self.assertTrue(g.contains("aldea", "casa"))
        self.assertTrue(g.contains("valle", "puerto"))
        self.assertFalse(g.contains("aldea", "puerto"))
        self.assertFalse(g.contains("plaza", "valle"))

    def test_bad_mutations_raise(self):
        g = self._g()
        with self.assertRaises(GraphError):
            g.add_place("x", "X", "planet")  # bad kind
        with self.assertRaises(GraphError):
            g.add_place("plaza", "dup", "sala")  # duplicate id
        with self.assertRaises(GraphError):
            g.connect("plaza", "nope", "a pie", "minutos")  # unknown place
        with self.assertRaises(GraphError):
            g.connect("plaza", "casa", "a pie", "siglos")  # bad cost

    def test_serialization_round_trip(self):
        g = self._g()
        g2 = WorldGraph.from_dict(g.to_dict())
        self.assertEqual(g2.path("casa", "puerto"), ["casa", "plaza", "puerto"])
        self.assertTrue(g2.contains("valle", "plaza"))

    def test_aggregate_cost_clamps(self):
        self.assertEqual(aggregate_cost([1, 1]), "medio-día")
        self.assertEqual(aggregate_cost([4, 4, 4]), "días")  # clamp
        self.assertEqual(aggregate_cost([]), "minutos")


# --------------------------------------------------------------------------
# clock
# --------------------------------------------------------------------------
class ClockTests(unittest.TestCase):
    def test_ordering_is_monotonic(self):
        a = Clock.of(1, "madrugada")
        b = Clock.of(1, "mañana")
        c = Clock.of(2, "madrugada")
        self.assertTrue(a < b < c)
        self.assertTrue(c >= b)
        self.assertFalse(c < a)

    def test_of_rejects_bad_values(self):
        with self.assertRaises(ClockError):
            Clock.of(1, "amanecer")
        with self.assertRaises(ClockError):
            Clock.of(0, "mañana")

    def test_elapsed_bucket(self):
        c1 = Clock.of(1, "madrugada")
        self.assertEqual(elapsed_bucket(c1, c1), "minutos")
        self.assertEqual(elapsed_bucket(c1, Clock.of(1, "mañana")), "horas")
        self.assertEqual(elapsed_bucket(c1, Clock.of(1, "tarde")), "medio-día")
        self.assertEqual(elapsed_bucket(c1, Clock.of(2, "madrugada")), "día")
        self.assertEqual(elapsed_bucket(c1, Clock.of(5, "mañana")), "días")
        # backward span collapses to the floor bucket
        self.assertEqual(elapsed_bucket(Clock.of(3, "noche"), c1), "minutos")

    def test_round_trip(self):
        c = Clock.of(4, "tarde")
        self.assertEqual(Clock.from_dict(c.to_dict()), c)
        self.assertEqual(str(c), "día 4, tarde")


# --------------------------------------------------------------------------
# story
# --------------------------------------------------------------------------
class StoryTests(unittest.TestCase):
    def test_seed_status_progresses(self):
        touches = [
            {"kind": "plant", "chapter": 1},
            {"kind": "echo", "chapter": 3},
            {"kind": "payoff", "chapter": 9},
        ]
        self.assertEqual(seed_status(touches, 0), DORMANT)
        self.assertEqual(seed_status(touches, 1), PLANTED)
        self.assertEqual(seed_status(touches, 3), ECHOING)
        self.assertEqual(seed_status(touches, 9), PAID)

    def test_due_and_overdue(self):
        seed = Seed(id="s1", desc="the well", schedule={"plant": [1], "echo": [3], "payoff": [9]})
        self.assertEqual(due(seed, 1), ["plant"])
        self.assertEqual(due(seed, 3), ["echo"])
        self.assertEqual(due(seed, 2), [])
        # by chapter 5 the plant is done but the echo (ch3) never fired
        touches = [{"kind": "plant", "chapter": 1}]
        self.assertEqual(overdue(seed, touches, 5), [("echo", 3)])

    def test_seed_bad_kind_rejected(self):
        with self.assertRaises(Exception):
            Seed(id="s", desc="d", schedule={"sprout": [1]})

    def test_truth_reveal_caps(self):
        t = Truth(id="t1", desc="assassin", reveal_caps={3: "hint", 9: "full"})
        self.assertTrue(t.allows_reveal(3))
        self.assertFalse(t.allows_reveal(1))
        self.assertEqual(t.cap_at(9), "full")
        self.assertEqual(Truth.from_dict(t.to_dict()).reveal_caps, {3: "hint", 9: "full"})


# --------------------------------------------------------------------------
# fixture world for events / queries / render / store
# --------------------------------------------------------------------------
def fixture_graph():
    g = WorldGraph()
    g.add_place("valle", "Valle", "region")
    g.add_place("aldea", "Aldea", "aldea", parent="valle")
    g.add_place("plaza", "Plaza", "sala", parent="aldea", pois=["el pozo"])
    g.add_place("casa", "Casa", "sala", parent="aldea")
    g.add_place("granero", "Granero", "sala", parent="aldea")
    g.add_place("puerto", "Puerto", "ciudad", parent="valle")
    g.add_place("isla", "Isla", "aldea", parent="valle")  # unreachable
    g.connect("plaza", "casa", "a pie", "minutos")
    g.connect("plaza", "granero", "a pie", "minutos")
    g.connect("casa", "granero", "a pie", "horas")
    g.connect("plaza", "puerto", "carro", "días")
    return g


def fixture_entities():
    return [
        Entity(id="bruno", name="Bruno", position="casa"),
        Entity(id="sela", name="Sela", position="plaza"),
        Entity(id="mauro", name="Mauro", position="puerto"),
        Entity(id="farol", name="Farol", kind="object", position="granero"),
    ]


class EventsReplayTests(unittest.TestCase):
    def setUp(self):
        self.g = fixture_graph()
        self.ents = fixture_entities()

    def _replay(self, events, **kw):
        return replay(self.g, self.ents, events, **kw)

    def test_basic_replay_moves_and_clock(self):
        events = [
            Event(1, 0, "time", {"day": 1, "franja": "mañana"}),
            Event(1, 1, "move", {"entity": "bruno", "to": "plaza"}),
            Event(1, 2, "move", {"entity": "sela", "to": "casa"}),
            Event(1, 3, "move", {"entity": "mauro", "to": "plaza"}),
        ]
        st = self._replay(events)
        self.assertEqual(st.position_of("bruno"), "plaza")
        self.assertEqual(st.position_of("sela"), "casa")
        self.assertEqual(st.position_of("mauro"), "plaza")
        self.assertEqual(str(st.clock), "día 1, mañana")

    def test_until_cutoff(self):
        events = [
            Event(1, 0, "move", {"entity": "bruno", "to": "plaza"}),
            Event(2, 0, "move", {"entity": "bruno", "to": "casa"}),
        ]
        st = self._replay(events, until_chapter=1)
        self.assertEqual(st.position_of("bruno"), "plaza")  # ch2 move not applied

    def test_reject_teleport(self):
        # casa -> puerto has no direct edge
        with self.assertRaises(IntegrityError):
            self._replay([Event(1, 0, "move", {"entity": "bruno", "to": "puerto"})])

    def test_travel_allows_multi_leg(self):
        # travel (not move) may cross a path
        st = self._replay([Event(1, 0, "travel", {"entity": "bruno", "to": "puerto"})])
        self.assertEqual(st.position_of("bruno"), "puerto")

    def test_reject_unreachable_travel(self):
        with self.assertRaises(IntegrityError):
            self._replay([Event(1, 0, "travel", {"entity": "bruno", "to": "isla"})])

    def test_reject_backward_clock(self):
        with self.assertRaises(IntegrityError):
            self._replay([
                Event(1, 0, "time", {"day": 2, "franja": "mañana"}),
                Event(1, 1, "time", {"day": 1, "franja": "noche"}),
            ])

    def test_object_transfer_and_reject_without_holding(self):
        # bruno acquires the farol (must be co-located logic is lax; acquire sets pos)
        good = [
            Event(1, 0, "acquire", {"entity": "bruno", "object": "farol"}),
            Event(1, 1, "transfer", {"from": "bruno", "to": "sela", "object": "farol"}),
        ]
        st = self._replay(good)
        self.assertIn("farol", st.entities["sela"].holding)
        self.assertNotIn("farol", st.entities["bruno"].holding)
        # transferring what you don't hold is impossible
        with self.assertRaises(IntegrityError):
            self._replay([Event(1, 0, "transfer", {"from": "bruno", "to": "sela", "object": "farol"})])

    def test_reject_reveal_past_cap(self):
        truths = {"t1": Truth(id="t1", desc="x", reveal_caps={3: "full"})}
        with self.assertRaises(IntegrityError):
            self._replay([Event(1, 0, "reveal", {"truth": "t1"})], truths=truths)
        # allowed in chapter 3
        st = self._replay([Event(3, 0, "reveal", {"truth": "t1"})], truths=truths)
        self.assertIn("t1", st.revealed)

    def test_reject_off_schedule_touch(self):
        seeds = {"s1": Seed(id="s1", desc="well", schedule={"plant": [1]})}
        with self.assertRaises(IntegrityError):
            self._replay([Event(2, 0, "plant", {"seed": "s1", "cita": "x"})], seeds=seeds)
        # on-schedule is fine and shows up in the touch-log
        events = [Event(1, 0, "plant", {"seed": "s1", "cita": "el pozo sin brocal"})]
        self._replay(events, seeds=seeds)
        self.assertEqual(len(touches_for(events, "s1")), 1)

    def test_learn_feeds_who_knows(self):
        events = [Event(1, 0, "learn", {"entity": "bruno", "item": "s1"})]
        st = self._replay(events)
        self.assertEqual(q.who_knows(st, "s1"), ["bruno"])


class QueriesTests(unittest.TestCase):
    def setUp(self):
        self.g = fixture_graph()
        self.st = replay(self.g, fixture_entities(), [
            Event(1, 0, "time", {"day": 1, "franja": "mañana"}),
            Event(1, 1, "move", {"entity": "mauro", "to": "plaza"}),
        ])

    def test_where(self):
        self.assertEqual(q.where(self.st, "sela"), "plaza")
        self.assertEqual(q.where(self.st, "mauro"), "plaza")
        self.assertIsNone(q.where(self.st, "ghost"))

    def test_copresent_and_meetings(self):
        cp = q.copresent(self.st)
        self.assertEqual(cp["plaza"], ["mauro", "sela"])
        self.assertEqual(cp["casa"], ["bruno"])
        meets = q.meetings(self.st)
        self.assertEqual(list(meets), ["plaza"])  # only plaza has 2+

    def test_overhear_surface(self):
        self.assertEqual(q.overhear_surface(self.st, "plaza"), ["mauro", "sela"])

    def test_feasible(self):
        m, t = Clock.of(1, "mañana"), Clock.of(1, "tarde")
        # adjacent, plenty of time
        self.assertTrue(q.feasible(self.g, "plaza", "casa", m, t))
        # far (días) but only medio-día available → not feasible
        self.assertFalse(q.feasible(self.g, "plaza", "puerto", m, t))
        # far but five days → feasible
        self.assertTrue(q.feasible(self.g, "plaza", "puerto", m, Clock.of(6, "mañana")))
        # unreachable place → never feasible
        self.assertFalse(q.feasible(self.g, "plaza", "isla", m, Clock.of(9, "noche")))

    def test_feasible_entity_uses_position(self):
        self.assertTrue(q.feasible_entity(self.g, self.st, "sela", "casa", Clock.of(1, "tarde")))
        self.assertFalse(q.feasible_entity(self.g, self.st, "sela", "puerto", Clock.of(1, "tarde")))


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.g = fixture_graph()
        self.events = [
            Event(1, 0, "time", {"day": 2, "franja": "tarde"}),
            Event(1, 1, "move", {"entity": "bruno", "to": "plaza"}),
            Event(1, 2, "learn", {"entity": "bruno", "item": "s1"}),
        ]
        self.st = replay(self.g, fixture_entities(), self.events)

    def test_opening_state(self):
        out = render.render_opening_state(self.st, 2, self.g, pov="bruno")
        self.assertIn("Estado del mundo al abrir el cap 2", out)
        self.assertIn("día 2, tarde", out)
        self.assertIn("Bruno: Plaza", out)
        self.assertIn("Mauro: Puerto", out)
        self.assertIn("s1", out)  # POV knowledge

    def test_render_place_shows_exits(self):
        out = render.render_place(self.g, "plaza")
        self.assertIn("Plaza", out)
        self.assertIn("el pozo", out)
        self.assertIn("Casa", out)   # an exit
        self.assertIn("minutos", out)

    def test_itinerary(self):
        out = render.render_itinerary(self.events, "bruno", self.g, initial="casa")
        self.assertIn("Itinerario: bruno", out)
        self.assertIn("cap 1", out)
        self.assertIn("Plaza", out)


# --------------------------------------------------------------------------
# store + world_tool CLI (the write gate)
# --------------------------------------------------------------------------
class WorldToolTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.sd = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, *argv):
        # subcommand first, then the shared --state-dir flag; swallow CLI chatter
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return world_tool.main([*argv, "--state-dir", str(self.sd)])

    def _build_min_world(self):
        self.assertEqual(self._run("add-place", "--id", "plaza", "--name", "Plaza", "--kind", "sala"), 0)
        self.assertEqual(self._run("add-place", "--id", "casa", "--name", "Casa", "--kind", "sala"), 0)
        self.assertEqual(self._run("add-place", "--id", "isla", "--name", "Isla", "--kind", "sala"), 0)
        self.assertEqual(self._run("connect", "--a", "plaza", "--b", "casa", "--mode", "a pie", "--cost", "minutos"), 0)
        self.assertEqual(self._run("add-entity", "--id", "bruno", "--name", "Bruno", "--position", "casa"), 0)

    def test_round_trip_and_replay(self):
        self._build_min_world()
        self.assertEqual(self._run("log-event", "--chapter", "1", "--type", "time", "--day", "1", "--franja", "mañana"), 0)
        self.assertEqual(self._run("log-event", "--chapter", "1", "--type", "move", "--entity", "bruno", "--to", "plaza"), 0)
        # persisted store round-trips through the loader
        st = store.replay_book(self.sd)
        self.assertEqual(st.position_of("bruno"), "plaza")
        # events got contiguous seqs
        self.assertEqual(store.next_seq(self.sd, 1), 2)

    def test_rejected_event_writes_nothing(self):
        self._build_min_world()
        # casa -> isla is not adjacent → rejected, nothing appended
        rc = self._run("log-event", "--chapter", "1", "--type", "move", "--entity", "bruno", "--to", "isla")
        self.assertEqual(rc, 1)
        self.assertEqual(store.next_seq(self.sd, 1), 0)  # log untouched
        self.assertFalse(store.load_events(self.sd))

    def test_where_command(self):
        self._build_min_world()
        self.assertEqual(self._run("where", "--entity", "bruno"), 0)


if __name__ == "__main__":
    unittest.main()
