---
name: plan-cast
description: Build layer L3 (the cast's itineraries) of a book's plan — where every named character, on-page AND off-page, stands at the opening of each chapter. Reads L1's graph + L2's clock + the outline's implied movements, proposes a per-character itinerary as a readable table, lets the author correct, then logs each displacement as a world_tool move/travel event in story order and verifies with copresent that every meeting the outline assumes actually has its people in the room — and every secret has the wrong ears out of it. Run once per book after plan-time (L2), before L4 (chapter layout).
---

# plan-cast (L3 — the cast's itineraries)

You are running **plan-cast**, the character layer of the RESTRUCTURE-V2 plan
stack. L1 fixed *where* (the graph), L2 fixed *when* (the clock). L3 fixes *who
is where, chapter by chapter* — the itinerary of every named character, including
the ones the reader never sees move (the antagonist crosses the map off-page; the
convoy climbs to the vega between chapters). Once the cast is placed, "and then
they meet" stops being a hope in the outline and becomes a computed fact:
`copresent()` reports who actually shares a room at a chapter's opening, so a
meeting the outline assumes but the geography forbids — or a secret spoken in
front of ears that L2's clock proves could be there — surfaces in the *plan*,
before a word of prose.

This layer is **author-in-the-loop by design**. You PROPOSE the whole cast's
movement as a readable table in chat; the author corrects; only then do you log
it into the store and verify. The itineraries are theirs — you are drafting them,
not deciding them.

> **Runs in the main thread.** Like plan-space, plan-time and plan-chapter, this
> is an interactive decision gate — it must talk to the author at the review
> stop, so it does NOT self-dispatch to a subagent.

## When to invoke

- The author says "place the cast", "do L3", "the itineraries", "who is where",
  or is walking the RESTRUCTURE-V2 layer stack for a book.
- Preconditions: L1 and L2 are done — `state/world.json` + `state/entities.json`
  exist and every chapter has an opening `time` stamp in `state/events/ch-NN.jsonl`
  (run `plan-space` then `plan-time` first if not), and `plan/outline.md` exists.
  L3 adds the first `move`/`travel` events to the per-chapter logs (until now they
  held only the L2 opening clocks).

## What L3 is (and is not)

- **Is:** for every **named** character (POV and secondary) and every off-page
  mover the plan tracks (an antagonist, a convoy treated as an entity), the place
  they stand at the **opening of each chapter** — expressed as the *displacements*
  between chapters (a `move` to an adjacent place, a `travel` across a
  multi-leg route). Plus a verification that every encounter the outline assumes
  has its people copresent, and every scene that must stay private does not.
- **Is not:** a scene-by-scene blocking chart. L3 places each character at the
  chapter *opening*; who walks in halfway through a scene, who steps out, who is
  on stage line by line is L4/write-time (`enter_scene`/`exit_scene` events). L3
  is the coarse cast skeleton L4 refines. It is also **not** knowledge — who
  *knows* what and who may *overhear* a secret is L5; L3 only fixes bodies in
  rooms (though `--place` reports the overhear *surface*, the room's occupants,
  which L5 will reason over).

## Copresence, meetings, and the overhear surface

`copresent(t)` groups every placed character by the place they occupy at moment
`t`; a **meeting** is any place with 2+ of them. The **overhear surface** of a
scene is simply the room's occupants — everyone who is bodily present and so
*could* hear it (L5 decides who does). A displacement is logged as a `move` (to
an adjacent place, one edge) or a `travel` (across a route the graph can path but
that isn't a single edge); the engine rejects a `move` with no edge (a teleport)
and a `travel` to an unreachable place at the commit, so an impossible itinerary
never reaches disk. This is coarse on purpose — L3 catches gross impossibilities
(the outline has two people meet who the map and clock keep a province apart),
which is what matters at plan time.

## Hard rules

- **Place the OFF-page cast, not just the POV.** The whole point of L3 is the
  mover the reader never watches move: the antagonist closing distance, the
  convoy climbing between chapters, a secondary who must already be somewhere when
  a later scene needs them. If the outline assumes someone has arrived, their
  itinerary must put them there — logged, feasible, and copresent-checked. A POV
  character the prose already tracks is the easy half; the off-page half is why
  this layer exists.
- **Every displacement must be feasible AND already blessed by L2.** Before you
  log a character moving A→B between chapter M and chapter N, that displacement's
  feasibility was (or should have been) checked in L2 against the two chapters'
  clocks. If L3 discovers a movement L2 never saw (an off-page journey the visible
  outline hid), run `feasible` for it now; an `INFEASIBLE` result is a real catch
  — resolve it with the author (loosen the calendar back in L2, or the route in
  L1), do not log an impossible itinerary. The commit will reject a teleport
  outright; feasibility catches the subtler "no time to walk it" that the graph
  alone can't see.
- **Log displacements in STORY order.** Like L2's clocks, moves replay on the
  story timeline (`story_order`); a character's positions must be consistent along
  that axis. For a chronological book that is chapter order. A flashback chapter's
  moves carry the same `--story-pos` its L2 clock did, so the character's body is
  where it chronologically was, not where the reading order would put it.
- **`move` vs `travel`.** Use `move` for a step to an **adjacent** place (one
  edge) — the strict check (a teleport is rejected). Use `travel` for a
  cross-map displacement the graph can *path* but that spans several edges (the
  convoy's multi-leg climb) — it validates reachability, not adjacency. Prefer
  `move` where the places are adjacent; reach for `travel` only for genuine
  multi-leg journeys.
- **Do not invent movement the outline does not imply.** A character the outline
  leaves in place stays in place — you do not need to log anything for them (their
  L1 opening position holds across chapters until an event moves them). Log a
  displacement only where the outline (or the shadow's off-page choreography)
  actually moves someone. Silence means "still there", not "unknown".
- **The opening position is L1's; L3 moves from it.** A character's book-open
  place was set in L1 (`add-entity --position`). L3 never re-declares an opening
  position — it logs the *changes*. The first chapter where a character is
  somewhere new gets the `move`/`travel`; the chapters before it inherit L1.
- **Reveal caps and knowledge stay untouched here** — who *knows* and who may
  *learn*/*overhear* is L5. L3 places bodies; it does not log `learn`/`reveal`.
- **Never hand-edit `state/*.json` or `state/events/*.jsonl`.** Log itineraries
  ONLY through `world_tool.py log-event --type move|travel` (a PreToolUse hook
  blocks direct edits). Every mutation replay-validates before writing, so a
  teleport or an unreachable travel is rejected at the door.
- **Idempotent retrofit.** If a character already has displacement events (a
  re-run), reconcile against them — propose a change, do not append a second
  conflicting move.

## Steps

### 1. Read the cast sources

Read, in this order:
- `plan/outline.md` — the **work-list**. For each chapter, extract: (a) every
  named character present in the scene(s); (b) every displacement the outline
  states or implies for anyone, on- or off-page ("Bruno reaches Altaluz", "by now
  the convoy has climbed to the vega", "Cándido is closing in"); (c) every
  **encounter** the outline assumes (X and Y meet, confront, travel together) and
  every scene that must stay **private** (a secret said to one person, a
  conversation no third party should share).
- `state/world.json` + `state/entities.json` (via the graph / `render_place`) —
  the L1 geography and the cast's opening positions you move from.
- The L2 clocks — either from `notes/decisions.md` / the plan-time report, or by
  reading `state/events/ch-NN.jsonl`'s opening `time` stamps — so each
  displacement is measured against the right chapter clocks.
- `plan/shadow.md` (slice) — the hidden choreography: the off-page mover whose
  itinerary the visible outline deliberately hides. This is the richest source
  for the off-page half of L3.
- `notes/decisions.md` + `notes/decisions-chNN.md` — any binding placement already
  agreed with the author; treat as a constraint.
- Written chapters' continuity: if `chapters/NN.md` + `notes/continuity-chNN.md`
  exist, read where the prose already put each character so the itinerary matches.

### 2. Derive the proposal

Build one itinerary table and one meetings table.

**Itineraries** — one row per named character (POV + secondary + off-page mover):
`character | opening place (L1) | ch-by-ch: where they are | displacements to log (from→to, chapter, move/travel)`

A blank cell means "unchanged from the previous chapter". Only the chapters where
someone *changes* place generate an event. Mark the off-page movers explicitly —
they are the ones most likely to be wrong.

**Meetings & privacy** — one row per encounter or secret the outline assumes:
`assumption (X meets Y at ch N / secret S said to Z at ch M, not before W) | place | expected copresent? | expected apart?`

For each, note which `copresent` assertion will verify it
(`--expect-together` for a meeting, `--expect-apart` for a scene that must stay
private). Any assumption you cannot satisfy with the itineraries — the people
can't be in the same room, or the wrong person is — is a FLAG to resolve with the
author before applying.

### 3. Present + STOP for author review

Show both tables in chat. Call out: every off-page itinerary you *inferred*
(these are the least certain); every displacement whose feasibility is tight;
every meeting or privacy assumption and how it will be checked; and any FLAG where
the geography/clock can't satisfy what the outline assumes. Then STOP.

Route the binding calls through `AskUserQuestion` (e.g. "Does Cándido reach
Altaluz by chapter 16, or only start climbing then?", "Is Mauro in the room for
the chapter-9 confession, or does the scene need him out?"). Let free-text
corrections rewrite any row. Do not log anything until the author signs off on the
itineraries.

### 4. Apply the confirmed itineraries via world_tool

Resolve the store with `--series-slug S --book-number N` (or `--state-dir`). Log
each displacement in **story order**, as a `move` (adjacent) or `travel`
(multi-leg). Log it in the chapter whose opening the character is newly in the new
place:

```
# an adjacent step
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 5 --type move --entity bruno --to altaluz
# a multi-leg off-page journey
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 16 --type travel --entity candido --to altaluz
# a flashback chapter's move carries the same story-pos its L2 clock did
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 7 --type move --entity mauro --to taller --story-pos 0
```

Each `log-event` replays the whole store with the new event before keeping it, so
a teleport (`move` with no edge) or an unreachable `travel` is `REJECTED (nothing
written)` — read the error; it means the itinerary asks for a displacement the
graph forbids. Fix the route (back to L1) or the placement; do not force.

### 5. Verify coverage

- `python scripts/world_tool.py replay --series-slug S --book-number N` must
  print `replay OK` — the itineraries, clocks and positions form one valid state.
- For **each meeting/privacy assumption** from step 2, assert it at the right
  chapter:
  ```
  python scripts/world_tool.py copresent --series-slug S --book-number N \
      --until-chapter 16 --expect-together candido,bruno
  python scripts/world_tool.py copresent --series-slug S --book-number N \
      --until-chapter 9 --expect-apart mauro,cure-witness
  ```
  `--expect-together` exits 1 (`APART`) if the meeting's people are not in one
  room; `--expect-apart` exits 1 (`TOGETHER`) if a scene that must stay private
  has the wrong person present. Either failure is a real catch — go back to step 3
  and fix the itinerary (or, if the geography can't allow it, back to L1/L2). Do
  not finish L3 with a meeting the plan cannot stage.
- Sanity-scan the plain report at a few key chapters
  (`copresent --until-chapter N`) and confirm the room matches the outline's cast
  for that scene — nobody the outline forgot to move is still frozen at their L1
  opening place when the story needs them elsewhere.

### 6. Report + hand off to L4

Summarize what landed: the itinerary table (every character → their chapter-by-
chapter place, with the displacements logged), and the meetings table (every
assumed encounter/secret → verified copresent/apart with its chapter). List any
residual FLAG the author chose to defer.

Then hand off: **L4 (chapter layout)** now has geography, clock AND cast, so it
can derive each chapter's scene list — place, clock, who is present, who speaks /
who stays silent / who could overhear (the overhear surface L3 computes) — coarse
for the whole book so `critique-plan` can audit it, fine just-in-time in
`plan-chapter`. L3 is the cast placement L4 builds its scenes on — leave every
character on a feasible itinerary and every assumed meeting copresent.

## Notes

- L3 writes `move`/`travel` events into `state/events/ch-NN.jsonl`, after the L2
  opening `time` stamp. A chapter with no cast change logs no L3 event — the
  previous positions simply hold, which is the correct default.
- `copresent` reads the state replayed to a chapter's **opening**. A meeting that
  only happens *mid-chapter* (someone arrives partway through) is an
  `enter_scene` at write-time, not an L3 opening placement — if the outline's
  encounter is intra-chapter, note it for L4 rather than forcing an opening
  copresence that isn't true.
- If the book has no L2 clocks yet (`state/events/ch-NN.jsonl` has no `time`
  stamps), stop and run `plan-time` first; an itinerary with no calendar cannot
  have its journeys checked for feasibility.
