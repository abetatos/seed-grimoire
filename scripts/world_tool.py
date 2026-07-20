#!/usr/bin/env python3
"""The only write gate to the world-state store.

The LLM never edits `state/*.json`; it proposes mutations in conversation and a
skill applies them through this CLI (the precedent is `mark_seed.py`). Every
mutation is validated by a full replay before it is kept, so an impossible event
is rejected at the door — teleports, backward clocks, off-plan touches and leaks
past a reveal cap never reach disk.

Usage (resolve the book by slug+number, or pass --state-dir directly):
    python scripts/world_tool.py add-place --state-dir DIR --id plaza --name "Plaza" --kind sala --parent aldea
    python scripts/world_tool.py connect   --state-dir DIR --a plaza --b casa --mode "a pie" --cost minutos
    python scripts/world_tool.py add-entity --state-dir DIR --id bruno --name Bruno --kind character --position casa
    python scripts/world_tool.py log-event  --state-dir DIR --chapter 1 --type move --entity bruno --to plaza
    python scripts/world_tool.py replay      --state-dir DIR [--until-chapter N]
    python scripts/world_tool.py where       --state-dir DIR --entity bruno [--until-chapter N]

Exit: 0 ok; 1 = the mutation would break integrity (rejected, nothing written); 2 = usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib.engine import store
from lib.engine.events import Event, IntegrityError, replay
from lib.engine.state import Entity


def _state_dir(args) -> Path:
    if args.state_dir:
        return Path(args.state_dir)
    if args.series_slug and args.book_number is not None:
        return book_paths(args.series_slug, args.book_number).state_dir
    raise SystemExit("error: pass --state-dir, or both --series-slug and --book-number")


def _validate(state_dir: Path) -> None:
    """Full replay — raises IntegrityError if the current store is impossible."""
    store.replay_book(state_dir)


# -- mutations --------------------------------------------------------------

def cmd_add_place(args) -> int:
    sd = _state_dir(args)
    graph = store.load_graph(sd)
    graph.add_place(args.id, args.name, args.kind, parent=args.parent, desc=args.desc or "", provenance=args.provenance or "")
    store.save_graph(sd, graph)
    print(f"place {args.id!r} added")
    return 0


def cmd_place_poi(args) -> int:
    sd = _state_dir(args)
    graph = store.load_graph(sd)
    graph.add_poi(args.place, args.poi)
    store.save_graph(sd, graph)
    print(f"poi {args.poi!r} added to {args.place!r}")
    return 0


def cmd_connect(args) -> int:
    sd = _state_dir(args)
    graph = store.load_graph(sd)
    graph.connect(args.a, args.b, args.mode, args.cost)
    store.save_graph(sd, graph)
    print(f"connected {args.a!r} — {args.b!r} ({args.mode}, {args.cost})")
    return 0


def cmd_add_entity(args) -> int:
    sd = _state_dir(args)
    entities = store.load_entities(sd)
    if any(e.id == args.id for e in entities):
        raise SystemExit(f"error: entity {args.id!r} already exists")
    entities.append(Entity(id=args.id, name=args.name, kind=args.kind, position=args.position, status=args.status or ""))
    store.save_entities(sd, entities)
    print(f"entity {args.id!r} added")
    return 0


def cmd_set_position(args) -> int:
    sd = _state_dir(args)
    entities = store.load_entities(sd)
    for e in entities:
        if e.id == args.entity:
            e.position = args.to
            store.save_entities(sd, entities)
            print(f"{args.entity!r} initial position set to {args.to!r}")
            return 0
    raise SystemExit(f"error: unknown entity {args.entity!r}")


def cmd_log_event(args) -> int:
    sd = _state_dir(args)
    data: dict = {}
    for key in ("entity", "to", "object", "item", "seed", "truth", "status", "day", "franja"):
        val = getattr(args, key, None)
        if val is not None:
            data[key] = int(val) if key == "day" else val
    if args.from_ is not None:
        data["from"] = args.from_
    seq = args.seq if args.seq is not None else store.next_seq(sd, args.chapter)
    # Build + dry-run replay WITH the new event before persisting — reject if
    # impossible (also catches an unknown --type at construction).
    try:
        event = Event(chapter=args.chapter, seq=seq, type=args.type, data=data)
        replay(
            graph=store.load_graph(sd),
            entities=store.load_entities(sd),
            events=store.load_events(sd) + [event],
            seeds=store.load_seeds(sd),
            truths=store.load_truths(sd),
        )
    except IntegrityError as exc:
        print(f"REJECTED (nothing written): {exc}", file=sys.stderr)
        return 1
    store.append_event(sd, event)
    print(f"event ch{event.chapter}.{event.seq} {event.type} logged")
    return 0


# -- reads ------------------------------------------------------------------

def cmd_replay(args) -> int:
    sd = _state_dir(args)
    try:
        st = store.replay_book(sd, until_chapter=args.until_chapter)
    except IntegrityError as exc:
        print(f"INTEGRITY ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"replay OK — clock {st.clock}; {len(st.entities)} entities")
    for eid in sorted(st.entities):
        e = st.entities[eid]
        print(f"  {eid}: {e.position}")
    return 0


def cmd_where(args) -> int:
    sd = _state_dir(args)
    try:
        st = store.replay_book(sd, until_chapter=args.until_chapter)
    except IntegrityError as exc:
        print(f"INTEGRITY ERROR: {exc}", file=sys.stderr)
        return 1
    pos = st.position_of(args.entity)
    print(pos if pos is not None else "(unplaced)")
    return 0


def _add_store_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--state-dir")
    p.add_argument("--series-slug")
    p.add_argument("--book-number", type=int)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add-place"); _add_store_args(p)
    p.add_argument("--id", required=True); p.add_argument("--name", required=True)
    p.add_argument("--kind", required=True); p.add_argument("--parent")
    p.add_argument("--desc"); p.add_argument("--provenance")
    p.set_defaults(func=cmd_add_place)

    p = sub.add_parser("place-poi"); _add_store_args(p)
    p.add_argument("--place", required=True); p.add_argument("--poi", required=True)
    p.set_defaults(func=cmd_place_poi)

    p = sub.add_parser("connect"); _add_store_args(p)
    p.add_argument("--a", required=True); p.add_argument("--b", required=True)
    p.add_argument("--mode", required=True); p.add_argument("--cost", required=True)
    p.set_defaults(func=cmd_connect)

    p = sub.add_parser("add-entity"); _add_store_args(p)
    p.add_argument("--id", required=True); p.add_argument("--name", required=True)
    p.add_argument("--kind", default="character"); p.add_argument("--position"); p.add_argument("--status")
    p.set_defaults(func=cmd_add_entity)

    p = sub.add_parser("set-position"); _add_store_args(p)
    p.add_argument("--entity", required=True); p.add_argument("--to", required=True)
    p.set_defaults(func=cmd_set_position)

    p = sub.add_parser("log-event"); _add_store_args(p)
    p.add_argument("--chapter", type=int, required=True); p.add_argument("--seq", type=int)
    p.add_argument("--type", required=True)
    p.add_argument("--entity"); p.add_argument("--to"); p.add_argument("--object")
    p.add_argument("--item"); p.add_argument("--seed"); p.add_argument("--truth")
    p.add_argument("--status"); p.add_argument("--day"); p.add_argument("--franja")
    p.add_argument("--from", dest="from_")
    p.set_defaults(func=cmd_log_event)

    p = sub.add_parser("replay"); _add_store_args(p)
    p.add_argument("--until-chapter", type=int)
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("where"); _add_store_args(p)
    p.add_argument("--entity", required=True); p.add_argument("--until-chapter", type=int)
    p.set_defaults(func=cmd_where)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
