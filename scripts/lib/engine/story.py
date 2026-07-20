"""Seeds and shadow truths as first-class engine data.

A `Seed` is a foreshadowing thread with a schedule (which chapters plant / echo /
pay it off). A `Truth` is a hidden fact with reveal caps (which chapters may
disclose it, and in what dose). Their *lifecycle* is the event log: plant/echo/
payoff and reveal events reference these ids, and their status at any moment is a
query over the touches so far — not a field someone remembers to update.

Two contract properties that used to be lint checks become structural here:
- **schedule sanity**: a plant/echo/payoff event in a chapter the seed does not
  schedule is rejected at commit (see events.py), so a touch off-schedule cannot
  be stored.
- **reveal caps**: a reveal in a chapter the truth does not schedule is likewise
  unrepresentable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

SEED_KINDS = ("plant", "echo", "payoff")

# Status names, ordered by lifecycle progress.
DORMANT = "dormant"
PLANTED = "planted"
ECHOING = "echoing"
PAID = "paid"


class StoryError(ValueError):
    """A malformed seed/truth definition."""


@dataclass
class Seed:
    id: str
    desc: str
    schedule: Dict[str, List[int]] = field(default_factory=dict)  # kind -> [chapters]
    notes: str = ""

    def __post_init__(self) -> None:
        for kind in self.schedule:
            if kind not in SEED_KINDS:
                raise StoryError(f"seed {self.id!r}: unknown schedule kind {kind!r}")

    def scheduled_chapters(self, kind: str) -> List[int]:
        return list(self.schedule.get(kind, []))

    def schedules(self, kind: str, chapter: int) -> bool:
        return chapter in self.schedule.get(kind, [])

    def to_dict(self) -> dict:
        return {"id": self.id, "desc": self.desc, "schedule": {k: list(v) for k, v in self.schedule.items()}, "notes": self.notes}

    @classmethod
    def from_dict(cls, d: dict) -> "Seed":
        return cls(id=d["id"], desc=d["desc"], schedule={k: list(v) for k, v in d.get("schedule", {}).items()}, notes=d.get("notes", ""))


@dataclass
class Truth:
    id: str
    desc: str
    reveal_caps: Dict[int, str] = field(default_factory=dict)  # chapter -> dose
    notes: str = ""

    def cap_at(self, chapter: int) -> str:
        return self.reveal_caps.get(chapter, "")

    def allows_reveal(self, chapter: int) -> bool:
        return chapter in self.reveal_caps

    def to_dict(self) -> dict:
        # JSON object keys are strings; keep chapters as strings on disk.
        return {"id": self.id, "desc": self.desc, "reveal_caps": {str(k): v for k, v in self.reveal_caps.items()}, "notes": self.notes}

    @classmethod
    def from_dict(cls, d: dict) -> "Truth":
        return cls(id=d["id"], desc=d["desc"], reveal_caps={int(k): v for k, v in d.get("reveal_caps", {}).items()}, notes=d.get("notes", ""))


# -- status queries over touches -------------------------------------------
# A "touch" is any object/dict exposing kind + chapter (a plant/echo/payoff
# event). These functions take plain (kind, chapter) pairs so story.py never
# depends on events.py.

def _pairs(touches: Iterable) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for t in touches:
        if isinstance(t, dict):
            out.append((t["kind"], int(t["chapter"])))
        else:
            out.append((t.kind, int(t.chapter)))
    return out


def seed_status(touches: Iterable, at_chapter: int) -> str:
    """Status of a seed given its touches, considering only chapters <= at_chapter."""
    kinds = {k for k, ch in _pairs(touches) if ch <= at_chapter}
    if "payoff" in kinds:
        return PAID
    if "echo" in kinds:
        return ECHOING
    if "plant" in kinds:
        return PLANTED
    return DORMANT


def due(seed: Seed, chapter: int) -> List[str]:
    """Which touch kinds the seed schedules exactly at `chapter` (the envelope)."""
    return [k for k in SEED_KINDS if seed.schedules(k, chapter)]


def overdue(seed: Seed, touches: Iterable, at_chapter: int) -> List[Tuple[str, int]]:
    """Scheduled (kind, chapter) with chapter < at_chapter that has no touch yet."""
    done = set(_pairs(touches))
    missed: List[Tuple[str, int]] = []
    for kind in SEED_KINDS:
        for ch in seed.scheduled_chapters(kind):
            if ch < at_chapter and (kind, ch) not in done:
                missed.append((kind, ch))
    return sorted(missed, key=lambda kc: (kc[1], kc[0]))
