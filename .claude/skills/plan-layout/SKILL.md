---
name: plan-layout
description: Build layer L4 (the chapter layout) of a book's plan — the per-chapter scene list derived from L1-L3. For every chapter, decompose it into ordered scenes; each scene's stage (place), clock and cast are COMPUTED from the graph/clock/itineraries (they cannot drift), while who speaks / who stays silent, the work the scene turns on, and its tempo are authored. Verifies every scene against the store (its place exists, its cast is who the itineraries actually put there, its overhear surface is the room's occupants), logs the intra-chapter displacements/clock-advances the outline pins, and writes plan/layout.md. Coarse for the whole book so critique-plan can audit it; plan-chapter refines it fine just-in-time. Run once per book after plan-cast (L3), before L5 (plan-knowledge).
---

# plan-layout (L4 — the chapter layout)

You are running **plan-layout**, the layout layer of the RESTRUCTURE-V2 plan
stack. L1 fixed *where* (the graph), L2 fixed *when* (the clock), L3 fixed *who
is where, chapter by chapter* (the itineraries). L4 turns those three into the
**scene list of every chapter**: each chapter broken into its ordered scenes, and
each scene given a stage, a clock, a cast, an overhear surface, the work it turns
on, and a tempo. The physics half of each scene — *where* it stands, *when* it
happens, *who is in the room* — is **computed** from L1-L3, so it cannot drift
from the truth; the craft half — who speaks vs. who stays silent, what the scene
is *for*, how fast it moves — is what you author. Once the book is laid out this
way, "this scene happens here with these people" stops being a note in the outline
and becomes a fact the engine already blessed: a scene planned at a stage nobody
can reach, or with a witness the itineraries keep a province away, surfaces in the
*plan*, before a word of prose.

This layer is **author-in-the-loop by design**. You PROPOSE the whole book's
scene list as readable per-chapter tables in chat; the author corrects; only then
do you log the intra-chapter events and write `plan/layout.md`. The layout is
theirs — you are drafting it, not deciding it.

> **Runs in the main thread.** Like plan-space, plan-time, plan-cast and
> plan-chapter, this is an interactive decision gate — it must talk to the author
> at the review stop, so it does NOT self-dispatch to a subagent.

## When to invoke

- The author says "lay out the chapters", "do L4", "the scene list", "the chapter
  layout", or is walking the RESTRUCTURE-V2 layer stack for a book.
- Preconditions: L1, L2 and L3 are done — `state/world.json` + `state/entities.json`
  exist, every chapter has an opening `time` stamp, and the cast's displacements
  are logged in `state/events/ch-NN.jsonl` (run `plan-space` → `plan-time` →
  `plan-cast` first if not), and `plan/outline.md` exists. L4 writes
  `plan/layout.md` (absent until now) and may add intra-chapter `move`/`travel`/
  `time` events where the outline pins a within-chapter change of stage or clock.

## What L4 is (and is not)

- **Is:** for every chapter, an **ordered list of scenes**. Each scene carries:
  the **stage** (an L1 place), the **clock** (an L2 franja), the **cast present**
  (computed from L3's itineraries — `copresent` at that chapter), the **overhear
  surface** (the room's occupants — `--place`), the **work** the scene turns on
  (the labor / confrontation / discovery it exists to stage), **who speaks and who
  stays silent** among the present, and a **tempo** (lento / medio / rápido + any
  named pause). It is **coarse for the whole book** — stage + cast + work, enough
  for `critique-plan` to audit exposure and carrier-scene coverage across all
  chapters at once.
- **Is not:** the fine chapter contract. Line-by-line staging (who walks on mid-
  scene, exact exits), the finished dialogue design, and the beat-level tempo are
  refined **just-in-time in `plan-chapter`** for the chapter about to be written —
  L4 is the coarse skeleton that refinement hangs on. It is also **not**
  knowledge: who *knows* what, who *learns* in a scene, and which reveal a scene
  is capped by is **L5** (`plan-knowledge`). L4 computes the overhear *surface*
  (who could hear); L5 decides who does, and whether a secret may be said in that
  room at all.

## The computed half vs. the authored half

Half of every scene row is **not yours to type** — it is read from the store so it
can never contradict L1-L3:

- **stage** must be a place that exists in the graph (`render_place` / `path`).
- **cast present** is `copresent(--until-chapter N)` restricted to the scene's
  stage — the characters the itineraries actually put in that room at that chapter.
  If you want someone in a scene who copresence says is elsewhere, that is not a
  layout choice — it is a broken itinerary (fix it in L3) or an intra-chapter
  arrival (log the `move`, see below), never a name you write into the table by
  hand.
- **overhear surface** is `--place <stage> --until-chapter N` — everyone bodily
  present, i.e. everyone who *could* hear the scene.

The other half is **authored** — it is the craft the engine has no opinion on:

- **work** — what the scene is *for* (the cosecha, the measuring, the
  confrontation, the discovery). One phrase.
- **speaks / silent** — of the present cast, who carries the scene and who is in
  the room but says nothing. (Who *may* speak a secret is L5; who *does* the
  talking is layout.)
- **tempo** — lento / medio / rápido, plus any named pause. The book's tempo is
  planned here, in the scene where it is decided — not in a rule.

## Hard rules

- **Never hand-type the computed half.** stage, cast-present and overhear surface
  come from the store (`copresent` / `--place` / `render_place`), not from your
  memory of the outline. If the computed cast of a scene is not the cast the
  outline's scene needs, you have found a real defect — resolve it upstream (L3
  itinerary, or an intra-chapter `move`), do not overwrite the computed value to
  make the table look right. The whole point of L4 is that this half cannot lie.
- **A scene's stage must exist and its cast must be copresent there.** Every scene
  is placed at a graph node the story enters; its present cast is a subset of who
  `copresent` puts at that node at that chapter. A scene whose stage has no node
  is an L1 gap; a scene whose needed person is not copresent is an L3 gap. Both
  surface here — send them back, do not paper over them.
- **Log intra-chapter changes of stage or clock as store events; leave inter-
  chapter ones to L3.** L3 logged the displacements that land a character in a new
  place at the *next* chapter's opening. L4 logs the ones that happen *within* a
  chapter — a character who is in the plaza in scene 1 and the taller in scene 3
  gets a ch-N `move`/`travel`; a chapter whose last scene is a franja later than
  its opening gets a ch-N `time`. Log ONLY where the outline actually moves someone
  or advances the clock inside the chapter; a chapter whose scenes all share one
  stage and one franja logs nothing new. (Because `copresent --until-chapter N`
  replays *all* of chapter N's events, an intra-chapter move correctly leaves the
  character at their end-of-chapter stage for chapter N+1's opening — which is
  exactly what L3's next-chapter positions assume.)
- **Fine line-by-line staging is NOT L4.** Do not log an `enter_scene`/`exit_scene`
  for every scene of every chapter — on-stage presence beat by beat is write-time /
  `plan-chapter`. L4's granularity is the scene *opening*: where it stands, when,
  and who is in the room. Note a mid-scene arrival as a layout annotation for
  `plan-chapter` to stage, do not force a coarse `enter_scene` now.
- **Knowledge and reveal caps stay untouched here.** Who *knows*, who *learns*,
  and which reveal a scene is capped by is L5. L4 records the overhear *surface*
  (bodies in the room) and hands it to L5; it logs no `learn`/`reveal`.
- **Tempo lives in the scene, not in a rule.** The structural tempo (lento / medio
  / rápido + named pauses) is planned per scene in `layout.md`. Do not push it into
  `style.md` or a craft rule — pace is planned where it is decided.
- **Never hand-edit `state/*.json` or `state/events/*.jsonl`.** Log intra-chapter
  events ONLY through `world_tool.py log-event` (a PreToolUse hook blocks direct
  edits). `plan/layout.md` is a normal plan file — write it directly.
- **Idempotent retrofit.** If `plan/layout.md` already exists (a re-run), reconcile
  against it — propose changes, do not blindly duplicate scenes. If an intra-chapter
  event is already logged, do not append a second conflicting one.

## Steps

### 1. Read the layout sources

Read, in this order:
- `plan/outline.md` — the **work-list**. For each chapter, extract the scenes it
  implies: each distinct stage/moment/beat, the work it turns on, and any within-
  chapter change of place or time ("later, at the taller…", "by nightfall…").
- The computed physics, per chapter, from the store (do NOT re-derive by hand):
  - `python scripts/world_tool.py copresent --series-slug S --book-number N --until-chapter K`
    — who shares each stage at chapter K's opening (the cast-present source).
  - `python scripts/world_tool.py copresent … --until-chapter K --place <stage>`
    — the overhear surface of a given stage.
  - `render_opening_state(K)` / `render_place(id)` (via the engine) — the clock at
    K's opening and each stage's scenography card.
- `plan/shadow.md` (slice) — the hidden work of a scene: a scene whose *apparent*
  purpose hides its real one, and any off-page pressure a scene must register.
- `plan/seeds.md` — every seed due to be planted/echoed/paid in each chapter needs
  a **carrier scene** in the layout; note which scene carries which seed (its
  detailed placement is L5/write-time, but a seed with no scene to land in is a
  layout gap to catch now).
- `notes/decisions.md` + `notes/decisions-chNN.md` — any binding scene choice
  already agreed with the author; treat as a constraint.
- Written chapters: if `chapters/NN.md` + `notes/continuity-chNN.md` exist, read
  the scenes the prose already staged so the layout matches, not overwrites, them.

### 2. Derive the proposal

Build one **scene table per chapter** (or one big table keyed by chapter). One row
per scene:

`ch.scene | stage (L1) | clock (L2) | present (copresent, computed) | overhear (--place, computed) | work | speaks / silent | tempo`

Fill the computed columns (stage / clock / present / overhear) from the store
queries in step 1 — mark any value you had to *assume* because the outline was
silent. Fill work / speaks-silent / tempo as your authored proposal. Below the
table, list:
- **Intra-chapter events to log** — every within-chapter `move`/`travel`/`time`
  the scene sequence implies (character, from→to or franja, chapter).
- **Seed carriers** — each seed due in the chapter → the scene that carries it (or
  a FLAG: a due seed with no carrier scene).
- **FLAGS** — any scene whose needed cast is not copresent, whose stage has no
  node, or whose seed has no carrier: the layer's real catches.

### 3. Present + STOP for author review

Show the per-chapter scene tables in chat. Call out: every value you had to
*assume* because the outline was silent; every intra-chapter event you propose to
log; every seed-carrier assignment (and any uncarried seed); and every FLAG where
the computed physics can't stage what the outline assumes. Then STOP.

Route the binding calls through `AskUserQuestion` (e.g. "Does chapter 5 stay in
the taller the whole chapter, or does the second scene move up to the mirador?",
"Is the confession its own scene, or folded into the meal scene?", "Which scene
plants the seed of the cracked mirror — the arrival or the vigil?"). Let free-text
corrections rewrite any row. Do not log or write anything until the author signs
off on the layout.

### 4. Apply the confirmed layout

Two writes, in this order:

1. **Log the intra-chapter events** the author blessed, in story order, via
   `world_tool.py` (adjacent step → `move`, multi-leg → `travel`, clock advance →
   `time`). A flashback chapter's intra-chapter events carry the same
   `--story-pos` its L2 clock did.
   ```
   # a within-chapter relocation
   python scripts/world_tool.py log-event --series-slug S --book-number N \
       --chapter 5 --type move --entity bruno --to mirador
   # a within-chapter clock advance (a scene at a later franja than the opening)
   python scripts/world_tool.py log-event --series-slug S --book-number N \
       --chapter 5 --type time --day 12 --franja noche
   ```
   Each `log-event` replays the whole store before keeping it, so an impossible
   intra-chapter change (a teleport, a backward clock) is `REJECTED (nothing
   written)` — read the error, fix the stage or the order, do not force.

2. **Write `plan/layout.md`** — the per-chapter scene list. Keep the computed
   columns exactly as the store returns them (do not paraphrase a cast). Mark the
   authored columns clearly. This file is the coarse layout `critique-plan` audits
   and `plan-chapter` refines.

### 5. Verify coverage

- `python scripts/world_tool.py replay --series-slug S --book-number N` must print
  `replay OK` — the new intra-chapter events plus L1-L3 form one valid state, and
  the clock still advances monotonically.
- For **each scene** in the layout, confirm its computed half against the store:
  the stage resolves (`path`/`render_place`), and the present cast + overhear
  surface match what `copresent --until-chapter K [--place <stage>]` returns. Any
  mismatch means the table drifted from the truth — regenerate the computed column
  from the query, do not keep the hand-typed value.
- For **each seed** due in a chapter, confirm the layout names a carrier scene. A
  due seed with no carrier is a real gap — resolve it with the author (add/repoint
  a scene) before finishing.
- Sanity-scan a few key chapters: the scene list matches the outline's beats, no
  chapter is a single undifferentiated block where the outline clearly has
  distinct stages, and no scene strands a character the itineraries moved.

### 6. Report + hand off to L5

Summarize what landed: the per-chapter scene count and, for each chapter, its
scenes' stages + casts (computed) and work + tempo (authored); the intra-chapter
events logged; the seed-carrier map; and any residual FLAG the author chose to
defer.

Then hand off: **L5 (plan-knowledge)** now has, for every scene, the exact
overhear surface L4 computed — so "who *knows* this, and may this secret be said
in *this* room?" becomes a real question. L5 lays the `learn`/`reveal` events and
the reveal caps over the scene list, and `who_knows()` + the reveal-cap commit
check turn an impossible disclosure (a secret spoken in front of ears the caps
forbid) into a plan-time catch. L4 is the stage L5's knowledge plays out on —
leave every scene on a real stage with a computed, honest cast.

## Notes

- L4 adds no new engine command — it is built entirely on the queries L1-L3
  already landed (`copresent`, `path`, `render_place`, `render_opening_state`).
  That the layer needs no new physics is the sign the stack is paying off: the
  scene's stage, clock and cast are all *already computable*, so L4 only has to
  author the craft and log the intra-chapter deltas.
- `copresent` reads the state replayed to a chapter's opening (all of that
  chapter's already-logged events applied). A scene whose cast changes *mid-scene*
  (someone arrives partway) is an `enter_scene` at write-time — note it as a
  `plan-chapter` annotation, do not force a coarse opening copresence that isn't
  true for the whole scene.
- The coarse whole-book layout is deliberately shallow on dialogue and beat-level
  tempo — that fineness is `plan-chapter`'s job for the one chapter about to be
  written. L4's job is that *every* chapter has an audited scene skeleton, so
  `critique-plan` can see exposure and seed-carrier gaps across the whole book at
  once.
- If the book has no L3 itineraries yet (`state/events/ch-NN.jsonl` holds only
  `time` stamps, no `move`/`travel`), stop and run `plan-cast` first; a scene
  list with no cast to compute cannot verify a single present-set.
