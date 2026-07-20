---
name: plan-space
description: Build layer L1 (the world graph) of a book's plan — the spatial contract every later layer reuses. Reads the outline's Where/when + canon/world.md, proposes the whole graph (places, containment, edges with ordinal costs, POIs) as readable tables, lets the author correct, then applies it to the world-state store via world_tool. Produces state/world.json and initial entity positions. Run once per book after plan-book's outline (L0) exists and the book's store has been migrated (migrate_story.py), before L2 (plan-time).
---

# plan-space (L1 — the world graph)

You are running **plan-space**, the first spatial layer of the RESTRUCTURE-V2
plan stack. The outline (L0) says *what* happens in each chapter; L1 fixes
*where* — the geography as a **graph** the engine can query, so that from L2 on
"can this character be there by that chapter?" is a computed answer, not a fact
someone typed and hoped was right.

This layer is **author-in-the-loop by design**. You PROPOSE the whole graph as
readable tables in chat; the author corrects; only then do you apply it to the
store. The graph is theirs — you are drafting it, not deciding it.

> **Runs in the main thread.** Unlike the critique/scribe/smith skills, this is
> an interactive decision gate (like plan-chapter) — it must talk to the author
> at the review stop, so it does NOT self-dispatch to a subagent.

## When to invoke

- The author says "map the world", "build the geography", "do L1", "the spatial
  layer", or is walking the RESTRUCTURE-V2 layer stack for a book.
- Preconditions: `plan/outline.md` exists (L0), and the book has a migrated
  store — `state/seeds.json` present (run `migrate_story.py` first if not). L1
  writes `state/world.json` + `state/entities.json`, which were absent until now.

## What L1 is (and is not)

- **Is:** every place the story ENTERS (a scene happens there), nested by
  containment (region ⊃ ciudad/aldea ⊃ edificio ⊃ sala; `camino` for a route you
  can be *on* mid-journey), plus edges covering **every displacement the outline
  implies**, each with an ordinal travel cost and a mode.
- **Is not:** a full atlas. A place the story never enters does not exist in the
  graph. A POI is added **only where a beat needs it** (the pozo exists because
  Sela falls into it; do not decorate). No coordinates, no minutes, no map — the
  plan bans clock arithmetic beyond ordinals.

## Hard rules

- **Do not invent geography the author has not blessed.** `canon/world.md` marks
  places `[FIJO]` (fixed) vs. "libre para escribir" (free). Reproduce `[FIJO]`
  places and their sensory anchors faithfully; propose freely only where the
  canon says free — and even then, propose, let the author accept or rewrite.
- **Every scene-place must exist; every displacement must have a path.** If the
  outline moves someone from A to B, the graph needs a route A→B. A displacement
  with no path is a MISSING EDGE — surface it, never paper over it. This
  coverage is exactly what makes L2's `feasible()` meaningful.
- **POIs only where a beat needs one.** A point of interest is justified by a
  specific outline/seed beat, not by "it would be nice".
- **Costs are ordinal buckets only:** `minutos < horas < medio-día < día < días`.
  Pick the coarse bucket; the engine sums and clamps along a path. Never a number
  of minutes.
- **Provenance for what the page has already shown.** A place a written chapter
  already staged (e.g. ch1's plaza/casa/pozo, blessed in the fragment) carries a
  `--provenance` note so later chapters rhyme with the prose, not just the plan.
- **Spanish for in-world ids and names** (places, POIs). Keep the stable id
  short and slug-like (`vega-parda`, `pozo`, `taller-del-padre`).
- **Never hand-edit `state/*.json`.** Apply the graph ONLY through
  `world_tool.py` (a PreToolUse hook blocks direct Edit/Write of the store). It
  replay-validates every mutation before writing.
- **Idempotent retrofit.** If `state/world.json` already has places (a re-run),
  reconcile against them — add what's missing, propose changes to what differs,
  never blindly duplicate.

## Steps

### 1. Read the spatial sources

Read, in this order:
- `plan/outline.md` — the **work-list**. Extract two things: (a) every place a
  scene *enters*, chapter by chapter; (b) every *displacement* (a character
  moving from one place to another, on or between chapters), including the ones
  the outline only implies ("this year the convoy climbs up to the vega").
- `canon/world.md` — named places, `[FIJO]` vs. free, sensory anchors, political
  position, containment hints (which aldea is in which region).
- `plan/shadow.md` (slice) — hidden geography the visible outline hides: an
  antagonist moving off-page, a place whose *real* function differs from its
  apparent one (it still needs a node and edges so the off-page itinerary in L3
  is feasible).
- `notes/decisions.md` — any binding location choice already made with the
  author; treat as a constraint.
- Written chapters' provenance: if `chapters/NN.md` exist, note the places they
  already staged so those nodes carry provenance.

### 2. Derive the proposal

Build two tables and a coverage list:

**Places** — one row per place the story enters:
`id | name | kind | parent | POIs | provenance / why it exists`

Order matters for application: a parent must be added before its children
(region → aldea → edificio → sala). POIs list only beat-justified points.

**Edges** — one row per travel leg needed to cover the displacements:
`a — b | mode | cost | covers (which outline displacement)`

**Displacement coverage** — list every displacement from step 1 and the path
that will carry it. Any displacement with no planned path is a FLAG to resolve
with the author (a missing edge, or a place you have not added yet).

### 3. Present + STOP for author review

Show the tables in chat. Call out: `[FIJO]` places reproduced vs. places you are
proposing freely; any POI and the beat that justifies it; every displacement and
its cost; and any coverage FLAG. Then STOP.

Route the binding calls through `AskUserQuestion` (e.g. "Is the convoy route
Solio→Term→la Alberca→Vega Parda, or does it skip the llano?", "Altaluz is how
far from the vega — `día` or `días`?"). Let free-text corrections rewrite any row.
Do not apply anything until the author signs off on the graph.

### 4. Apply the confirmed graph via world_tool

Resolve the store with `--series-slug S --book-number N` (or `--state-dir`).
Apply in dependency order:

```
# places: parents first
python scripts/world_tool.py add-place --series-slug S --book-number N \
    --id vega-parda --name "Vega Parda" --kind aldea --parent <region> \
    --desc "…" --provenance "cap 1: mancha apagada, el telar, el pozo"
# POIs, only the beat-justified ones
python scripts/world_tool.py place-poi --series-slug S --book-number N \
    --place vega-parda --poi pozo
# edges: both places must already exist
python scripts/world_tool.py connect --series-slug S --book-number N \
    --a vega-parda --b altaluz --mode carro --cost día
```

Then place the cast's **opening** positions (chapter-1 start), which L2/L3 build
on:

```
python scripts/world_tool.py add-entity --series-slug S --book-number N \
    --id bruno --name Bruno --kind character --position vega-parda
```

Add the off-page movers the shadow needs (the antagonist, the convoy as an
entity if the plan treats it as one) so L3 can give them itineraries.

If a `connect`/`add-place` is rejected, read the error — it is usually an
unknown parent or a place added out of order. Fix the order; do not force.

### 5. Verify coverage

- `python scripts/world_tool.py replay --series-slug S --book-number N` must
  print `replay OK` (the graph + opening positions form a valid state).
- For **each displacement** from step 2, run
  `python scripts/world_tool.py path --a <from> --b <to>`. A `UNREACHABLE`
  result (exit 1) is a missing edge — go back to step 3 with the author. Do not
  finish L1 with an uncovered displacement.
- Sanity: no scene-place is isolated (every place a scene enters has at least
  one edge), and no place exists that no scene needs (trim decoration).

### 6. Report + hand off to L2

Summarize what landed: N places, M edges, the cast's opening positions, and the
displacement-coverage table (every displacement → its path + cost). Render a few
key `render_place` cards (via the engine's `render_place`) so the author sees the
computed geography as the writer will. List any residual FLAG the author chose to
defer.

Then hand off: **L2 (plan-time)** assigns the per-chapter clock and, the moment it
does, `feasible()` turns this graph's costs into the first real catch of an
impossible journey. L1 is the ground L2 stands on — leave it covered.

## Notes

- This skill fills `state/world.json` + `state/entities.json`. It does **not**
  log events (moves belong to L3/write-time). Opening positions are set via
  `add-entity --position` / `set-position`, which are initial state, not events.
- Reveal caps stay empty here — the knowledge layer is L5, not L1.
- If the book has no migrated store yet, stop and run `migrate_story.py` first;
  L1 is meaningless without the seed/shadow store the later layers query.
