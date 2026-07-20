"""The spatial graph: the world's geography as a hierarchical, connected graph.

Nodes are `Place`s nested by containment (region ⊃ ciudad ⊃ edificio ⊃ sala).
Edges are qualitative travel legs with an *ordinal* cost — no minutes, no
coordinates, no map. The whole point is that "can X be in Y by chapter N?" is a
graph query, not a fact someone typed and hoped was right.

Costs are ordinal buckets (minutos < horas < medio-día < día < días). A journey's
cost is the least-cost path's summed bucket, clamped to the top bucket — coarse on
purpose (the plan bans clock arithmetic beyond ordinals). It is enough to catch a
gross impossibility (a character two provinces away next chapter), which is what
the planner needs.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Hierarchy kinds, coarse-to-fine. `camino` (a road/route) is a place you can be
# *on* while travelling, so scenes can happen mid-journey.
PLACE_KINDS = ("region", "ciudad", "aldea", "edificio", "sala", "camino")

# Ordinal travel-cost buckets, cheapest first. Index is the ordinal magnitude.
COSTS = ("minutos", "horas", "medio-día", "día", "días")
COST_INDEX = {c: i for i, c in enumerate(COSTS)}
_MAX_COST = len(COSTS) - 1


class GraphError(ValueError):
    """A malformed graph mutation (unknown place, bad kind, bad cost bucket)."""


@dataclass
class Place:
    id: str
    name: str
    kind: str
    parent: Optional[str] = None
    pois: List[str] = field(default_factory=list)
    desc: str = ""
    provenance: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "parent": self.parent,
            "pois": list(self.pois),
            "desc": self.desc,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Place":
        return cls(
            id=d["id"],
            name=d["name"],
            kind=d["kind"],
            parent=d.get("parent"),
            pois=list(d.get("pois", [])),
            desc=d.get("desc", ""),
            provenance=d.get("provenance", ""),
        )


@dataclass
class Edge:
    a: str
    b: str
    mode: str  # a pie / a caballo / carro / barca ...
    cost: str  # one of COSTS

    def to_dict(self) -> dict:
        return {"a": self.a, "b": self.b, "mode": self.mode, "cost": self.cost}

    @classmethod
    def from_dict(cls, d: dict) -> "Edge":
        return cls(a=d["a"], b=d["b"], mode=d["mode"], cost=d["cost"])


def aggregate_cost(indices: List[int]) -> str:
    """Sum ordinal bucket indices along a path, clamped to the top bucket."""
    total = min(sum(indices), _MAX_COST)
    return COSTS[total]


class WorldGraph:
    def __init__(self) -> None:
        self.places: Dict[str, Place] = {}
        self.edges: List[Edge] = []
        self._adj: Dict[str, List[Tuple[str, int]]] = {}

    # -- construction -------------------------------------------------------
    def add_place(
        self,
        id: str,
        name: str,
        kind: str,
        parent: Optional[str] = None,
        pois: Optional[List[str]] = None,
        desc: str = "",
        provenance: str = "",
    ) -> Place:
        if kind not in PLACE_KINDS:
            raise GraphError(f"unknown place kind {kind!r} (expected one of {PLACE_KINDS})")
        if id in self.places:
            raise GraphError(f"place {id!r} already exists")
        if parent is not None and parent not in self.places:
            raise GraphError(f"parent {parent!r} of {id!r} does not exist")
        place = Place(id=id, name=name, kind=kind, parent=parent, pois=list(pois or []), desc=desc, provenance=provenance)
        self.places[id] = place
        self._adj.setdefault(id, [])
        return place

    def add_poi(self, place_id: str, poi: str) -> None:
        if place_id not in self.places:
            raise GraphError(f"place {place_id!r} does not exist")
        if poi not in self.places[place_id].pois:
            self.places[place_id].pois.append(poi)

    def connect(self, a: str, b: str, mode: str, cost: str) -> Edge:
        for pid in (a, b):
            if pid not in self.places:
                raise GraphError(f"cannot connect: place {pid!r} does not exist")
        if cost not in COST_INDEX:
            raise GraphError(f"unknown cost bucket {cost!r} (expected one of {COSTS})")
        edge = Edge(a=a, b=b, mode=mode, cost=cost)
        self.edges.append(edge)
        ci = COST_INDEX[cost]
        self._adj.setdefault(a, []).append((b, ci))
        self._adj.setdefault(b, []).append((a, ci))  # undirected
        return edge

    # -- queries ------------------------------------------------------------
    def adjacent(self, a: str, b: str) -> bool:
        """True iff there is a direct edge a—b."""
        return any(nb == b for nb, _ in self._adj.get(a, []))

    def path(self, a: str, b: str) -> Optional[List[str]]:
        """Least-cost path a→b (list of place ids), or None if unreachable."""
        found = self._dijkstra(a, b)
        return None if found is None else found[0]

    def travel_cost(self, a: str, b: str) -> Optional[str]:
        """Aggregate ordinal cost of the least-cost path a→b, or None."""
        if a == b:
            return COSTS[0]
        found = self._dijkstra(a, b)
        if found is None:
            return None
        _, indices = found
        return aggregate_cost(indices)

    def contains(self, region: str, place: str) -> bool:
        """True iff `place` is `region` or nested under it via the parent chain."""
        if region not in self.places or place not in self.places:
            return False
        cur: Optional[str] = place
        seen = set()
        while cur is not None and cur not in seen:
            if cur == region:
                return True
            seen.add(cur)
            cur = self.places[cur].parent
        return False

    def _dijkstra(self, a: str, b: str) -> Optional[Tuple[List[str], List[int]]]:
        if a not in self.places or b not in self.places:
            return None
        # priority queue of (total_cost, place, path, cost_indices)
        pq: List[Tuple[int, str, List[str], List[int]]] = [(0, a, [a], [])]
        best: Dict[str, int] = {a: 0}
        while pq:
            total, node, path, indices = heapq.heappop(pq)
            if node == b:
                return path, indices
            if total > best.get(node, total):
                continue
            for nb, ci in self._adj.get(node, []):
                nt = total + ci
                if nt < best.get(nb, nt + 1):
                    best[nb] = nt
                    heapq.heappush(pq, (nt, nb, path + [nb], indices + [ci]))
        return None

    # -- serialization ------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "places": [p.to_dict() for p in self.places.values()],
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WorldGraph":
        g = cls()
        # places first (parents may be referenced), tolerating any order by
        # inserting parentless, then patching parents.
        for pd in d.get("places", []):
            place = Place.from_dict(pd)
            g.places[place.id] = place
            g._adj.setdefault(place.id, [])
        for ed in d.get("edges", []):
            edge = Edge.from_dict(ed)
            ci = COST_INDEX.get(edge.cost)
            if ci is None:
                raise GraphError(f"unknown cost bucket {edge.cost!r} in stored edge")
            g.edges.append(edge)
            g._adj.setdefault(edge.a, []).append((edge.b, ci))
            g._adj.setdefault(edge.b, []).append((edge.a, ci))
        return g
