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
    python scripts/world_tool.py log-event  --state-dir DIR --chapter 7 --type time --day 1 --franja mañana --story-pos 0  # a flashback, placed early
    python scripts/world_tool.py replay      --state-dir DIR [--until-chapter N]
    python scripts/world_tool.py where       --state-dir DIR --entity bruno [--until-chapter N]
    python scripts/world_tool.py path        --state-dir DIR --a vega --b altaluz
    python scripts/world_tool.py feasible    --state-dir DIR --a vega --b altaluz --t1-day 1 --t1-franja mañana --t2-day 3 --t2-franja mañana
    python scripts/world_tool.py copresent   --state-dir DIR --until-chapter 5                          # who shares a place at ch5's opening
    python scripts/world_tool.py copresent   --state-dir DIR --until-chapter 5 --expect-together bruno,mauro   # exit 1 if apart
    python scripts/world_tool.py copresent   --state-dir DIR --until-chapter 5 --expect-apart candido,bruno    # exit 1 if together

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
from lib.engine import queries as q
from lib.engine.clock import Clock, ClockError, elapsed_bucket
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
        event = Event(chapter=args.chapter, seq=seq, type=args.type, data=data, story_pos=args.story_pos)
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


def cmd_path(args) -> int:
    """Least-cost path a->b + its ordinal cost, or UNREACHABLE — the L1
    coverage check: every displacement the outline implies must have a path,
    else an edge is missing. Read-only; exit 1 when unreachable so a skill can
    branch on it, 2 for an unknown place."""
    sd = _state_dir(args)
    graph = store.load_graph(sd)
    for pid in (args.a, args.b):
        if pid not in graph.places:
            print(f"error: unknown place {pid!r}", file=sys.stderr)
            return 2
    route = graph.path(args.a, args.b)
    if route is None:
        print(f"UNREACHABLE: no path {args.a!r} -> {args.b!r} (missing edge)", file=sys.stderr)
        return 1
    cost = graph.travel_cost(args.a, args.b)
    print(f"{' -> '.join(route)}  ({cost})")
    return 0


def cmd_feasible(args) -> int:
    """Could someone leave place --a at clock t1 and stand in place --b by t2?
    The L2 temporal-coverage check — the dual of `path`: `path` asks whether a
    route exists at all, `feasible` asks whether it fits the time the plan gives
    the journey (graph cost vs. the ordinal span between two chapter clocks).
    Read-only; exit 1 when INFEASIBLE so a skill can branch on it, 2 for an
    unknown place or a malformed clock."""
    sd = _state_dir(args)
    graph = store.load_graph(sd)
    for pid in (args.a, args.b):
        if pid not in graph.places:
            print(f"error: unknown place {pid!r}", file=sys.stderr)
            return 2
    try:
        t1 = Clock.of(args.t1_day, args.t1_franja)
        t2 = Clock.of(args.t2_day, args.t2_franja)
    except ClockError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    ok = q.feasible(graph, args.a, args.b, t1, t2)
    cost = graph.travel_cost(args.a, args.b)
    span = elapsed_bucket(t1, t2)
    detail = f"cost {cost!r} vs. span {span!r} ({t1} -> {t2})"
    if ok:
        print(f"FEASIBLE: {args.a!r} -> {args.b!r} — {detail}")
        return 0
    reason = "unreachable" if cost is None else "not enough time"
    print(f"INFEASIBLE: {args.a!r} -> {args.b!r} — {reason} ({detail})", file=sys.stderr)
    return 1


def cmd_copresent(args) -> int:
    """Who shares a place at the opening of chapter --until-chapter — the L3
    itinerary-coverage check. Replays the log (moves/travels included) up to that
    story moment, then reports the copresent map + the meetings (2+ together), or
    asserts a specific arrangement the outline assumes:

      --expect-together a,b   the scene needs them in the same room  → exit 1 if apart
      --expect-apart    a,b   the scene needs them NOT to coincide   → exit 1 if together
      --place X               who could overhear a scene at X (its occupants)

    This is the dual of `path` (L1) and `feasible` (L2): it turns "and then they
    meet" from an outline hope into a computed fact. Read-only; exit 1 when an
    assertion fails so a skill can branch on it, 2 for an unknown entity/place."""
    sd = _state_dir(args)
    try:
        st = store.replay_book(sd, until_chapter=args.until_chapter)
    except IntegrityError as exc:
        print(f"INTEGRITY ERROR: {exc}", file=sys.stderr)
        return 1

    def _positions(csv: str):
        ids = [x.strip() for x in csv.split(",") if x.strip()]
        for eid in ids:
            if eid not in st.entities:
                print(f"error: unknown entity {eid!r}", file=sys.stderr)
                return None
        return {eid: st.position_of(eid) for eid in ids}

    if args.expect_together is not None:
        pos = _positions(args.expect_together)
        if pos is None:
            return 2
        places = set(pos.values())
        placed = [p for p in places if p is not None]
        if len(places) == 1 and None not in places:
            print(f"TOGETHER: {', '.join(sorted(pos))} all at {placed[0]!r} (ch{args.until_chapter})")
            return 0
        where = ", ".join(f"{e}={p!r}" for e, p in sorted(pos.items()))
        print(f"APART: {where} — not copresent at ch{args.until_chapter}", file=sys.stderr)
        return 1

    if args.expect_apart is not None:
        pos = _positions(args.expect_apart)
        if pos is None:
            return 2
        seen: dict = {}
        for eid, p in pos.items():
            if p is not None and p in seen:
                print(f"TOGETHER: {seen[p]!r} and {eid!r} both at {p!r} — should be apart at ch{args.until_chapter}", file=sys.stderr)
                return 1
            if p is not None:
                seen[p] = eid
        print(f"APART: {', '.join(sorted(pos))} in different places (ch{args.until_chapter})")
        return 0

    if args.place is not None:
        if args.place not in store.load_graph(sd).places:
            print(f"error: unknown place {args.place!r}", file=sys.stderr)
            return 2
        surface = q.overhear_surface(st, args.place)
        print(f"overhear @ {args.place!r} (ch{args.until_chapter}): {', '.join(surface) if surface else '(empty)'}")
        return 0

    groups = q.copresent(st)
    meets = q.meetings(st)
    print(f"copresent @ ch{args.until_chapter} (clock {st.clock}):")
    for place in sorted(groups):
        members = ", ".join(groups[place])
        tag = "  << meeting" if place in meets else ""
        print(f"  {place}: {members}{tag}")
    if not groups:
        print("  (no placed characters)")
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
    p.add_argument("--story-pos", type=int, default=None,
                   help="story-order override for a flashback chapter (default: == chapter)")
    p.set_defaults(func=cmd_log_event)

    p = sub.add_parser("replay"); _add_store_args(p)
    p.add_argument("--until-chapter", type=int)
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("where"); _add_store_args(p)
    p.add_argument("--entity", required=True); p.add_argument("--until-chapter", type=int)
    p.set_defaults(func=cmd_where)

    p = sub.add_parser("path"); _add_store_args(p)
    p.add_argument("--a", required=True); p.add_argument("--b", required=True)
    p.set_defaults(func=cmd_path)

    p = sub.add_parser("feasible"); _add_store_args(p)
    p.add_argument("--a", required=True); p.add_argument("--b", required=True)
    p.add_argument("--t1-day", type=int, required=True); p.add_argument("--t1-franja", required=True)
    p.add_argument("--t2-day", type=int, required=True); p.add_argument("--t2-franja", required=True)
    p.set_defaults(func=cmd_feasible)

    p = sub.add_parser("copresent"); _add_store_args(p)
    p.add_argument("--until-chapter", type=int, required=True)
    p.add_argument("--expect-together", help="comma-separated entity ids that must share a place")
    p.add_argument("--expect-apart", help="comma-separated entity ids that must NOT coincide")
    p.add_argument("--place", help="report who could overhear a scene at this place")
    p.set_defaults(func=cmd_copresent)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
