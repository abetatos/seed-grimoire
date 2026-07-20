"""Computed Markdown views — the only thing the LLM ever reads from the engine.

The store is JSON; these render the human/LLM-facing surfaces the write and
critique bundles inject. Because they are *computed* from the replayed state,
they cannot drift from the truth the way a hand-written `continuity-chNN.md` could.

- `render_opening_state(N)` — where everyone is, the clock, what the POV knows at
  the moment chapter N opens. Replaces the hand-written continuity note.
- `render_place(id)` — a scenography card: containment, POIs, and the exits with
  their travel cost, so a scene knows its stage and its ways out.
- `render_itinerary(char)` — a character's chapter-by-chapter positions.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .events import Event, sort_events
from .graph import WorldGraph
from .state import WorldState


def _place_name(graph: WorldGraph, place_id: Optional[str]) -> str:
    if place_id is None:
        return "—"
    place = graph.places.get(place_id)
    return place.name if place else place_id


def render_opening_state(state: WorldState, chapter: int, graph: WorldGraph, pov: Optional[str] = None) -> str:
    lines: List[str] = [f"### Estado del mundo al abrir el cap {chapter}", ""]
    lines.append(f"- **Reloj:** {state.clock}")
    lines.append("")
    lines.append("**Dónde está cada uno:**")
    chars = sorted(
        (e for e in state.entities.values() if e.kind == "character"),
        key=lambda e: e.name,
    )
    for ent in chars:
        loc = _place_name(graph, ent.position)
        extra = f" — {ent.status}" if ent.status else ""
        held = f" (lleva: {', '.join(ent.holding)})" if ent.holding else ""
        lines.append(f"- {ent.name}: {loc}{extra}{held}")
    if pov is not None and pov in state.entities:
        known = sorted(state.knowledge.get(pov, set()))
        lines.append("")
        pov_name = state.entities[pov].name
        if known:
            lines.append(f"**Lo que {pov_name} (POV) ya sabe:** " + ", ".join(known))
        else:
            lines.append(f"**Lo que {pov_name} (POV) ya sabe:** (nada registrado aún)")
    return "\n".join(lines) + "\n"


def render_place(graph: WorldGraph, place_id: str) -> str:
    place = graph.places.get(place_id)
    if place is None:
        return f"### Lugar desconocido: {place_id}\n"
    lines: List[str] = [f"### {place.name}  ·  {place.kind}"]
    if place.parent:
        lines.append(f"- **En:** {_place_name(graph, place.parent)}")
    if place.desc:
        lines.append(f"- {place.desc}")
    if place.pois:
        lines.append(f"- **Puntos:** {', '.join(place.pois)}")
    exits: List[str] = []
    for nb, ci in sorted(graph._adj.get(place_id, [])):
        # find the edge for its mode/cost label
        mode = cost = "?"
        for e in graph.edges:
            if {e.a, e.b} == {place_id, nb}:
                mode, cost = e.mode, e.cost
                break
        exits.append(f"{_place_name(graph, nb)} ({mode}, {cost})")
    if exits:
        lines.append("- **Salidas:** " + "; ".join(exits))
    if place.provenance:
        lines.append(f"- _procedencia: {place.provenance}_")
    return "\n".join(lines) + "\n"


def render_itinerary(events: Iterable[Event], entity_id: str, graph: WorldGraph, initial: Optional[str] = None) -> str:
    """Chapter-by-chapter positions for one character, from move/travel events."""
    lines: List[str] = [f"### Itinerario: {entity_id}", ""]
    pos = initial
    rows: List[str] = []
    if initial is not None:
        rows.append(f"- inicio: {_place_name(graph, initial)}")
    for ev in sort_events(events):
        if ev.type in ("move", "travel") and ev.data.get("entity") == entity_id:
            pos = ev.data.get("to")
            rows.append(f"- cap {ev.chapter}: → {_place_name(graph, pos)}")
    if not rows:
        rows.append("- (sin desplazamientos registrados)")
    return "\n".join(lines + rows) + "\n"
