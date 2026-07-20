"""Disk I/O for the world-state store: JSON in, dataclasses out.

The store is five files under a book's `state/` dir: `world.json`,
`entities.json`, `seeds.json`, `shadow.json`, and per-chapter event logs
`events/ch-NN.jsonl`. This module is the ONLY reader/writer; `world_tool.py`
drives it from the CLI, and nothing else edits the JSON by hand (a hook enforces
that, mirroring seeds.md/shadow.md).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .clock import Clock
from .events import Event, replay
from .graph import WorldGraph
from .state import Entity, WorldState
from .story import Seed, Truth


def _read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


# -- graph ------------------------------------------------------------------

def load_graph(state_dir: Path) -> WorldGraph:
    return WorldGraph.from_dict(_read_json(state_dir / "world.json", {"places": [], "edges": []}))


def save_graph(state_dir: Path, graph: WorldGraph) -> None:
    _write_json(state_dir / "world.json", graph.to_dict())


# -- entities ---------------------------------------------------------------

def load_entities(state_dir: Path) -> List[Entity]:
    return [Entity.from_dict(d) for d in _read_json(state_dir / "entities.json", [])]


def save_entities(state_dir: Path, entities: List[Entity]) -> None:
    _write_json(state_dir / "entities.json", [e.to_dict() for e in entities])


# -- story ------------------------------------------------------------------

def load_seeds(state_dir: Path) -> Dict[str, Seed]:
    return {d["id"]: Seed.from_dict(d) for d in _read_json(state_dir / "seeds.json", [])}


def save_seeds(state_dir: Path, seeds: Dict[str, Seed]) -> None:
    _write_json(state_dir / "seeds.json", [s.to_dict() for s in seeds.values()])


def load_truths(state_dir: Path) -> Dict[str, Truth]:
    return {d["id"]: Truth.from_dict(d) for d in _read_json(state_dir / "shadow.json", [])}


def save_truths(state_dir: Path, truths: Dict[str, Truth]) -> None:
    _write_json(state_dir / "shadow.json", [t.to_dict() for t in truths.values()])


# -- events -----------------------------------------------------------------

def _events_dir(state_dir: Path) -> Path:
    return state_dir / "events"


def load_events(state_dir: Path) -> List[Event]:
    """All events across every chapter log, unsorted (replay sorts)."""
    events: List[Event] = []
    ed = _events_dir(state_dir)
    if not ed.exists():
        return events
    for path in sorted(ed.glob("ch-*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    events.append(Event.from_dict(json.loads(line)))
    return events


def next_seq(state_dir: Path, chapter: int) -> int:
    """The next unused seq number in a chapter's log (0-based, contiguous)."""
    path = _events_dir(state_dir) / f"ch-{chapter:02d}.jsonl"
    if not path.exists():
        return 0
    n = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


def append_event(state_dir: Path, event: Event) -> None:
    """Append one event to its chapter log (creates the log if needed)."""
    ed = _events_dir(state_dir)
    ed.mkdir(parents=True, exist_ok=True)
    path = ed / f"ch-{event.chapter:02d}.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")


# -- convenience ------------------------------------------------------------

def replay_book(
    state_dir: Path,
    until_chapter: Optional[int] = None,
    until_seq: Optional[int] = None,
    clock: Optional[Clock] = None,
) -> WorldState:
    """Load the whole store and replay it to a cutoff — the commit check."""
    return replay(
        graph=load_graph(state_dir),
        entities=load_entities(state_dir),
        events=load_events(state_dir),
        seeds=load_seeds(state_dir),
        truths=load_truths(state_dir),
        until_chapter=until_chapter,
        until_seq=until_seq,
        clock=clock,
    )
