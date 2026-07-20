"""The queries that make the engine worth having.

These are what `plan-chapter` and `critique-plan` ask so a scene is only ever
built with people who can actually be there, hearing only what they could hear.
An impossible witness or an impossible meeting shows up in the *plan*, before a
word of prose is written.

All queries read a `WorldState` (already replayed to the moment in question) plus
the graph/clock — they never mutate.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .clock import Clock, elapsed_bucket
from .graph import COST_INDEX, WorldGraph
from .state import WorldState


def where(state: WorldState, entity_id: str) -> Optional[str]:
    """The place id of an entity at this state's moment (None if unplaced)."""
    return state.position_of(entity_id)


def copresent(state: WorldState, kind: Optional[str] = "character") -> Dict[str, List[str]]:
    """Map each occupied place → the entities sharing it (who coincides with whom).

    Restricted to entities of `kind` (default characters); pass kind=None for all.
    Places with a single occupant are included — copresence with the empty set is
    still useful ("who is where"); callers filter for len>1 when they want meetings.
    """
    groups: Dict[str, List[str]] = {}
    for eid, ent in state.entities.items():
        if ent.position is None:
            continue
        if kind is not None and ent.kind != kind:
            continue
        groups.setdefault(ent.position, []).append(eid)
    return {place: sorted(members) for place, members in groups.items()}


def meetings(state: WorldState, kind: Optional[str] = "character") -> Dict[str, List[str]]:
    """Places where 2+ entities of `kind` coincide — the possible encounters."""
    return {p: m for p, m in copresent(state, kind=kind).items() if len(m) > 1}


def overhear_surface(state: WorldState, place_id: str, kind: Optional[str] = "character") -> List[str]:
    """Who can overhear a scene at `place_id` — everyone standing in it."""
    return sorted(
        eid
        for eid, ent in state.entities.items()
        if ent.position == place_id and (kind is None or ent.kind == kind)
    )


def feasible(graph: WorldGraph, from_place: str, to_place: str, t1: Clock, t2: Clock) -> bool:
    """Could someone at `from_place` at t1 be at `to_place` by t2?

    True iff a path exists and its aggregate ordinal travel cost fits within the
    ordinal span t1→t2. Coarse by construction — it catches gross impossibilities
    (two provinces away next chapter), which is the point at plan time.
    """
    if from_place == to_place:
        return t2 >= t1
    if t2 < t1:
        return False
    cost = graph.travel_cost(from_place, to_place)
    if cost is None:
        return False  # unreachable
    return COST_INDEX[cost] <= COST_INDEX[elapsed_bucket(t1, t2)]


def feasible_entity(graph: WorldGraph, state_t1: WorldState, entity_id: str, to_place: str, t2: Clock) -> bool:
    """`feasible` sugar: uses the entity's position/clock in state_t1 as the origin."""
    frm = state_t1.position_of(entity_id)
    if frm is None:
        return False
    return feasible(graph, frm, to_place, state_t1.clock, t2)


def who_knows(state: WorldState, item: str) -> List[str]:
    """Entities whose knowledge includes a seed id or fact at this moment."""
    return sorted(eid for eid, items in state.knowledge.items() if item in items)
