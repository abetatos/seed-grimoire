"""Entities and the instantaneous world state.

An `Entity` is a character or a key object with a position (a place id), a free
status, and what it is holding. A `WorldState` is the whole world at one instant:
the clock, every entity's position/status/holding, who knows what, and who is
currently on stage in the live scene. States are never authored by hand — they
are produced by replaying the event log (see events.py) up to a chosen moment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .clock import Clock

ENTITY_KINDS = ("character", "object")


class StateError(ValueError):
    """An impossible state mutation (missing entity, holding what you lack)."""


@dataclass
class Entity:
    id: str
    name: str
    kind: str = "character"
    position: Optional[str] = None  # place id
    status: str = ""
    holding: List[str] = field(default_factory=list)  # object ids

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "position": self.position,
            "status": self.status,
            "holding": list(self.holding),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Entity":
        return cls(
            id=d["id"],
            name=d["name"],
            kind=d.get("kind", "character"),
            position=d.get("position"),
            status=d.get("status", ""),
            holding=list(d.get("holding", [])),
        )


@dataclass
class WorldState:
    clock: Clock
    entities: Dict[str, Entity] = field(default_factory=dict)
    knowledge: Dict[str, Set[str]] = field(default_factory=dict)  # entity_id -> {seed_id|fact}
    on_stage: Set[str] = field(default_factory=set)  # entities in the live scene
    revealed: Set[str] = field(default_factory=set)  # truth ids disclosed so far

    # -- reads --------------------------------------------------------------
    def position_of(self, entity_id: str) -> Optional[str]:
        ent = self.entities.get(entity_id)
        return None if ent is None else ent.position

    def knows(self, entity_id: str, item: str) -> bool:
        return item in self.knowledge.get(entity_id, set())

    def entities_at(self, place_id: str) -> List[str]:
        return sorted(eid for eid, e in self.entities.items() if e.position == place_id)

    def copy(self) -> "WorldState":
        return WorldState(
            clock=self.clock,
            entities={eid: Entity.from_dict(e.to_dict()) for eid, e in self.entities.items()},
            knowledge={eid: set(items) for eid, items in self.knowledge.items()},
            on_stage=set(self.on_stage),
            revealed=set(self.revealed),
        )
