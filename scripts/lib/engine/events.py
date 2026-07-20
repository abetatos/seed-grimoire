"""Event sourcing: the typed log that is the single source of dynamic truth.

Everything that *happens* in the book is an event: a move, a clock advance, an
object changing hands, a character learning a seed, a truth revealed, a seed
planted/echoed/paid. The log is per chapter (`state/events/ch-NN.jsonl`); replay
reconstructs the `WorldState` at any moment.

Integrity lives in ONE place — the commit (`replay`). An impossible event does not
get caught by a later check; it fails to apply at all:

- **move** without an edge between here and there (a teleport),
- **travel** to an unreachable place,
- **time** that runs the clock backward,
- **drop/transfer** of something not held,
- **reveal** in a chapter the truth does not schedule (a leak past the cap),
- **plant/echo/payoff** in a chapter the seed does not schedule (off-plan touch).

Each is an unrepresentable state, not a rule to remember.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .clock import Clock
from .graph import WorldGraph
from .state import Entity, WorldState
from .story import Seed, Truth, SEED_KINDS

EVENT_TYPES = (
    "move", "travel", "time",
    "acquire", "drop", "transfer",
    "learn", "reveal",
    "plant", "echo", "payoff",
    "enter_scene", "exit_scene", "status",
)

# Touch kinds whose validity is the seed schedule.
TOUCH_KINDS = SEED_KINDS  # ("plant", "echo", "payoff")


class IntegrityError(ValueError):
    """An event that would produce an impossible state. Raised at replay/commit."""


@dataclass
class Event:
    chapter: int
    seq: int
    type: str
    data: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in EVENT_TYPES:
            raise IntegrityError(f"unknown event type {self.type!r}")

    @property
    def kind(self) -> str:
        # For touch events, `kind` == type — lets story.seed_status read Events.
        return self.type

    def to_dict(self) -> dict:
        return {"chapter": self.chapter, "seq": self.seq, "type": self.type, "data": dict(self.data)}

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(chapter=int(d["chapter"]), seq=int(d["seq"]), type=d["type"], data=dict(d.get("data", {})))


def sort_events(events: Iterable[Event]) -> List[Event]:
    return sorted(events, key=lambda e: (e.chapter, e.seq))


def touches_for(events: Iterable[Event], seed_id: str) -> List[Event]:
    """Every plant/echo/payoff event for a seed, in order — the touch-log."""
    return sort_events(e for e in events if e.type in TOUCH_KINDS and e.data.get("seed") == seed_id)


def initial_state(entities: Iterable[Entity], clock: Optional[Clock] = None) -> WorldState:
    """Build the book-open state from the roster (positions as declared)."""
    st = WorldState(clock=clock or Clock.of(1, "madrugada"))
    for ent in entities:
        st.entities[ent.id] = Entity.from_dict(ent.to_dict())
    return st


# -- per-type application ---------------------------------------------------

def _require_entity(st: WorldState, eid: str, ev: Event) -> Entity:
    ent = st.entities.get(eid)
    if ent is None:
        raise IntegrityError(f"ch{ev.chapter}.{ev.seq} {ev.type}: unknown entity {eid!r}")
    return ent


def _holder_of(st: WorldState, obj: str) -> Optional[str]:
    for eid, ent in st.entities.items():
        if obj in ent.holding:
            return eid
    return None


def _apply(st: WorldState, ev: Event, graph: WorldGraph, seeds: Dict[str, Seed], truths: Dict[str, Truth]) -> None:
    t = ev.type
    d = ev.data

    if t == "time":
        new = Clock.of(int(d["day"]), d["franja"])
        if new < st.clock:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} time: clock would go backward ({st.clock} -> {new})")
        st.clock = new

    elif t == "move":
        ent = _require_entity(st, d["entity"], ev)
        to = d["to"]
        if to not in graph.places:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} move: unknown place {to!r}")
        if ent.position is None:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} move: {ent.id!r} has no position to move from")
        if ent.position != to and not graph.adjacent(ent.position, to):
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} move: no edge {ent.position!r} -> {to!r} (teleport)")
        ent.position = to

    elif t == "travel":
        ent = _require_entity(st, d["entity"], ev)
        to = d["to"]
        if to not in graph.places:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} travel: unknown place {to!r}")
        if ent.position is None:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} travel: {ent.id!r} has no position to travel from")
        if ent.position != to and graph.path(ent.position, to) is None:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} travel: {to!r} unreachable from {ent.position!r}")
        ent.position = to

    elif t == "acquire":
        ent = _require_entity(st, d["entity"], ev)
        obj = d["object"]
        held_by = _holder_of(st, obj)
        if held_by is not None and held_by != ent.id:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} acquire: {obj!r} already held by {held_by!r}")
        if obj not in ent.holding:
            ent.holding.append(obj)
        if obj in st.entities:
            st.entities[obj].position = ent.position

    elif t == "drop":
        ent = _require_entity(st, d["entity"], ev)
        obj = d["object"]
        if obj not in ent.holding:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} drop: {ent.id!r} is not holding {obj!r}")
        ent.holding.remove(obj)
        if obj in st.entities:
            st.entities[obj].position = ent.position

    elif t == "transfer":
        src = _require_entity(st, d["from"], ev)
        dst = _require_entity(st, d["to"], ev)
        obj = d["object"]
        if obj not in src.holding:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} transfer: {src.id!r} is not holding {obj!r}")
        src.holding.remove(obj)
        if obj not in dst.holding:
            dst.holding.append(obj)
        if obj in st.entities:
            st.entities[obj].position = dst.position

    elif t == "learn":
        ent = _require_entity(st, d["entity"], ev)
        st.knowledge.setdefault(ent.id, set()).add(d["item"])

    elif t == "reveal":
        truth_id = d["truth"]
        truth = truths.get(truth_id)
        if truth is None:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} reveal: unknown truth {truth_id!r}")
        if not truth.allows_reveal(ev.chapter):
            raise IntegrityError(
                f"ch{ev.chapter}.{ev.seq} reveal: truth {truth_id!r} has no reveal cap in chapter {ev.chapter} (leak past cap)"
            )
        st.revealed.add(truth_id)

    elif t in TOUCH_KINDS:
        seed_id = d["seed"]
        seed = seeds.get(seed_id)
        if seed is None:
            raise IntegrityError(f"ch{ev.chapter}.{ev.seq} {t}: unknown seed {seed_id!r}")
        if not seed.schedules(t, ev.chapter):
            raise IntegrityError(
                f"ch{ev.chapter}.{ev.seq} {t}: seed {seed_id!r} does not schedule a {t} in chapter {ev.chapter} (off-plan touch)"
            )
        # A touch is a validated log entry; it changes no entity state.

    elif t == "enter_scene":
        ent = _require_entity(st, d["entity"], ev)
        st.on_stage.add(ent.id)

    elif t == "exit_scene":
        ent = _require_entity(st, d["entity"], ev)
        st.on_stage.discard(ent.id)

    elif t == "status":
        ent = _require_entity(st, d["entity"], ev)
        ent.status = d.get("status", "")

    else:  # pragma: no cover - guarded by Event.__post_init__
        raise IntegrityError(f"unhandled event type {t!r}")


def replay(
    graph: WorldGraph,
    entities: Iterable[Entity],
    events: Iterable[Event],
    seeds: Optional[Dict[str, Seed]] = None,
    truths: Optional[Dict[str, Truth]] = None,
    until_chapter: Optional[int] = None,
    until_seq: Optional[int] = None,
    clock: Optional[Clock] = None,
) -> WorldState:
    """Reconstruct the world state by applying events in order up to a cutoff.

    `until_chapter`/`until_seq` bound the replay (inclusive). Raises
    `IntegrityError` on the first impossible event — that is the single commit
    check the whole design leans on.
    """
    seeds = seeds or {}
    truths = truths or {}
    st = initial_state(entities, clock=clock)
    for ev in sort_events(events):
        if until_chapter is not None:
            if ev.chapter > until_chapter:
                break
            if ev.chapter == until_chapter and until_seq is not None and ev.seq > until_seq:
                break
        _apply(st, ev, graph, seeds, truths)
    return st
