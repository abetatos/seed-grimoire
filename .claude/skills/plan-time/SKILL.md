---
name: plan-time
description: Build layer L2 (the book's clock) of a book's plan — the temporal contract that turns L1's geography into feasibility. Reads the outline's when + L1's graph, proposes a per-chapter opening clock (día, franja) as a readable table, lets the author correct, then stamps each chapter's opening via world_tool's time event and verifies that EVERY outline displacement is feasible (graph cost fits the span between departure and arrival chapters). Run once per book after plan-space (L1) has produced state/world.json, before L3 (plan-cast / itineraries).
---

# plan-time (L2 — the book's clock)

You are running **plan-time**, the temporal layer of the RESTRUCTURE-V2 plan
stack. L1 fixed *where* — the geography as a graph with ordinal travel costs. L2
fixes *when* — the book's calendar, so that "can this character cross the map in
time to be there by that chapter?" stops being a hope and becomes a computed
answer: `feasible()` compares L1's travel cost against the span L2 gives the
journey. L1 without L2 knows the road exists; L2 is what knows there were enough
days to walk it.

This layer is **author-in-the-loop by design**. You PROPOSE the whole calendar as
a readable table in chat; the author corrects; only then do you stamp it into the
store and verify. The clock is theirs — you are drafting it, not deciding it.

> **Runs in the main thread.** Like plan-space and plan-chapter, this is an
> interactive decision gate — it must talk to the author at the review stop, so
> it does NOT self-dispatch to a subagent.

## When to invoke

- The author says "set the clock", "do L2", "the temporal layer", "the calendar",
  or is walking the RESTRUCTURE-V2 layer stack for a book.
- Preconditions: L1 is done — `state/world.json` + `state/entities.json` exist
  (run `plan-space` first if not), and `plan/outline.md` exists. L2 writes the
  first entries into `state/events/ch-NN.jsonl` (the per-chapter opening `time`
  stamps), which were absent until now.

## What L2 is (and is not)

- **Is:** one **opening clock** — a `(día, franja)` pair — for every chapter, laid
  on a single monotonic timeline, plus a verification that every displacement L1
  had to cover actually **fits in time** between the chapter it departs and the
  chapter it must arrive by.
- **Is not:** a scene-by-scene timeline. L2 stamps the *opening* of each chapter,
  not every beat inside it — intra-chapter time (a scene that runs from mañana to
  noche) is L3/write-time, emitted as further `time` events after L2's opening
  stamp. L2 is the coarse skeleton the fine clock hangs on. It is also **not** a
  real calendar with dates or hours: time is `día N` + a named `franja`, and
  arithmetic is ordinal only (`minutos < horas < medio-día < día < días`).

## The franjas and the ordinal span

The day's parts, earliest first: `madrugada < mañana < mediodía < tarde < noche`.
The engine maps the gap between two clocks onto a travel-cost bucket
(`elapsed_bucket`): same franja → `minutos`, one franja → `horas`, within a day →
`medio-día`, about a day → `día`, more than a day → `días`. A displacement is
**feasible** iff its L1 travel cost is ≤ the bucket of the span it is given. This
is coarse on purpose — L2 catches gross impossibilities (two provinces away next
chapter), which is what matters at plan time.

## Hard rules

- **The clock only ever advances — in STORY order.** The engine sorts events by
  story time (`story_order`), and each chapter's opening clock must be ≥ the
  previous chapter's *in that order*. Equal is fine (two chapters the same
  morning); a clock that runs backward on the story timeline is an unrepresentable
  state the engine rejects at commit. Presentation order (the chapter number) is a
  separate axis — for a chronological book the two coincide, so you stamp chapters
  1, 2, 3… with non-decreasing clocks and never think about it.
- **A flashback is representable — place it at its story position, don't FLAG it.**
  A chapter told out of chronological order (chapter 7 narrates día −30) carries an
  earlier clock than the chapters around it. Do NOT stamp it in presentation order
  (that clock would run backward and be rejected). Instead:
  - **Number days by absolute story time**, earliest depicted moment = día 1. If
    the book opens in the present but contains an earlier flashback, the flashback
    gets the low día numbers and the present gets the higher ones. Day 1 is the
    earliest thing the book *shows*, not the first thing it *narrates*.
  - **Give the flashback chapter a `--story-pos`** on its `time` stamp: an integer
    that slots it into its chronological place (e.g. `--story-pos 0` to sit before
    chapter 1). Its events then replay in story order and the clock stays
    monotonic. Confirm the placement with the author — where on the real timeline
    the flashback sits is a story fact only they can pin.
  - The feasibility pass then measures the flashback's own displacements against
    its real (earlier) clocks — consistently, because story order is what
    `feasible()` reads.
- **Do not invent a calendar the outline does not imply.** The outline says how
  much time passes ("that winter", "three days later", "the same night"). Read the
  elapsed time from it; where it is silent, propose the *smallest* span the beats
  need and let the author stretch it. Pin a franja only where a beat implies one (a
  dawn burial, a night raid); otherwise propose one and let the author move it.
- **Every displacement must be feasible.** For each displacement L1 covered, the
  span between its departure chapter's clock and its arrival chapter's clock must
  absorb the travel cost. An `INFEASIBLE` result is a real catch — resolve it, do
  not paper over it (loosen the calendar, or if the road itself is too long, go
  back to L1). This feasibility pass is the entire reason L2 exists.
- **L2 owns each chapter's opening clock; write-time inherits it.** The opening
  `time` stamp L2 writes is the anchor the chapter's write-time manifest builds on.
  The manifest emits `time` events only for advances *within* the chapter; it never
  re-stamps the opening. Record this so the smith and update-canon do not collide
  with L2. *(This is a binding architectural choice — that plan-time clocks live as
  `time` events in the log, so the log carries a plan commitment, not only what the
  page staged. Confirm it with the author before applying if it has not been
  settled.)*
- **Ordinal time only** — never a number of hours or a real date. `día N` +
  franja, nothing finer.
- **Never hand-edit `state/*.json` or `state/events/*.jsonl`.** Stamp the clock
  ONLY through `world_tool.py log-event --type time` (a PreToolUse hook blocks
  direct edits of the store). Every mutation replay-validates before writing, so a
  backward clock is rejected at the door.
- **Idempotent retrofit.** If a chapter already has an opening `time` stamp (a
  re-run), reconcile against it — propose a change, do not append a second
  conflicting stamp.

## Steps

### 1. Read the temporal sources

Read, in this order:
- `plan/outline.md` — the **work-list**. Extract, chapter by chapter: (a) any
  explicit elapsed time between chapters ("a week later", "the next morning",
  "that autumn"); (b) any beat that pins a franja (a dawn, a vigil, a night); (c)
  every **displacement** already identified in L1 (a character moving A→B), noting
  which chapter it *departs* and which chapter it must have *arrived* by — the
  feasibility pass needs both endpoints.
- `state/world.json` (via `render_place` / the graph) — the L1 travel costs each
  displacement will be measured against. You are not re-deriving geography here,
  only reading the costs L1 already blessed.
- `plan/shadow.md` (slice) — the hidden timeline: an off-page mover whose journey
  must also fit the calendar (their itinerary is L3, but their clock has to be
  possible, so a beat that requires them to have arrived constrains L2).
- `notes/decisions.md` + `notes/decisions-chNN.md` — any binding time choice
  already made with the author; treat as a constraint.
- Written chapters' continuity: if `chapters/NN.md` + `notes/continuity-chNN.md`
  exist, read the clock they already established so the stamp matches the prose.

### 2. Derive the proposal

Build two tables:

**Chapter clock** — one row per chapter:
`chapter | día | franja | elapsed since prev | why (the outline cue)`

The clocks must be non-decreasing down the table. Where the outline is silent on a
gap, propose the smallest span the beats need and say so, so the author sees where
you invented and can stretch it.

**Feasibility** — one row per displacement L1 covered:
`displacement (entity: A→B) | departs ch | arrives-by ch | L1 cost | span | feasible?`

Compute `span` as the `elapsed_bucket` between the departure chapter's clock and
the arrival chapter's clock, and mark feasible iff `L1 cost ≤ span`. Any row that
does not fit is a FLAG to resolve with the author before applying.

### 3. Present + STOP for author review

Show both tables in chat. Call out: every gap you *invented* because the outline
was silent; every franja you *pinned* vs. *proposed*; any flashback FLAG; and
every displacement that is tight or infeasible. Then STOP.

Route the binding calls through `AskUserQuestion` (e.g. "How long between the
cosecha and the convoy reaching the vega — `día` or `días`?", "Does chapter 3 open
the same night as chapter 2, or the next morning?"). Let free-text corrections
rewrite any row. Do not stamp anything until the author signs off on the calendar.

### 4. Apply the confirmed calendar via world_tool

Resolve the store with `--series-slug S --book-number N` (or `--state-dir`). Stamp
each chapter's opening clock **in story order** (so the clock never has to jump
backward); for a chronological book that is just chapter order. A flashback
chapter also passes `--story-pos <n>` to slot it into its real chronological place
(see the flashback rule above):

```
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 1 --type time --day 1 --franja mañana
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 2 --type time --day 1 --franja noche
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 3 --type time --day 3 --franja mañana
```

Each `log-event` replays the whole store with the new stamp before keeping it, so
a backward clock is `REJECTED (nothing written)` — read the error, it means two
chapters are out of temporal order (or a flashback slipped in). Fix the order or
the value; do not force.

### 5. Verify feasibility

- `python scripts/world_tool.py replay --series-slug S --book-number N` must print
  `replay OK` — the calendar plus L1's positions form a valid state, and the clock
  advances monotonically across every chapter.
- For **each displacement** from step 2, run `feasible` with the two chapter
  clocks:
  ```
  python scripts/world_tool.py feasible --series-slug S --book-number N \
      --a vega-parda --b altaluz \
      --t1-day <departs-día> --t1-franja <departs-franja> \
      --t2-day <arrives-día> --t2-franja <arrives-franja>
  ```
  A `FEASIBLE` (exit 0) confirms the journey fits. An `INFEASIBLE` (exit 1) is
  either **not enough time** (go back to step 3 and loosen the calendar with the
  author) or **unreachable** (a hole L1 left — go back to plan-space). Do not
  finish L2 with an infeasible displacement.

### 6. Report + hand off to L3

Summarize what landed: the chapter-clock table (every chapter → its opening clock
and the elapsed span), and the feasibility table (every displacement → FEASIBLE
with its cost-vs-span). List any residual FLAG the author chose to defer (a
flashback left unstamped, a deliberately tight journey).

Then hand off: **L3 (plan-cast / itineraries)** now has both a graph and a clock,
so it can place the off-page movers on itineraries and `copresent()` / `meetings()`
turn into real answers — who is actually in the room when a scene happens, and who
could not possibly be. L2 is the timeline L3 walks its characters along — leave
every chapter stamped and every displacement feasible.

## Notes

- L2 writes only `time` events (the per-chapter opening stamps) into
  `state/events/ch-NN.jsonl`. It does **not** move anyone — moves and travels are
  L3/write-time, logged *after* the opening stamp. The opening clock is the anchor;
  everything else in the chapter's log advances from it.
- Reveal caps and knowledge stay untouched here — that is L5 (plan-knowledge), not
  L2.
- If the book has no L1 graph yet (`state/world.json` absent), stop and run
  `plan-space` first; a clock with no geography to measure against cannot check a
  single feasibility.
