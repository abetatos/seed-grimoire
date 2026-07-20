---
name: plan-knowledge
description: Build layer L5 (the knowledge layer — "the something more") of a book's plan. Lays two axes over the scene list L4 produced: the READER's reveal ladder (each shadow truth's reveal_caps — which chapters may move the reader, and to what dose: hidden→sensed→suspected→confirmed) and CHARACTER knowledge (learn/reveal events + who_knows). Derives both from shadow.md's prose (Reveal cap / Confirm in / Revealed-by carrier seeds), authors them into the store, and verifies that no secret is disclosed past its cap and no secret leaks to a character the plan keeps ignorant (who-knows --expect-ignorant) — an impossible disclosure surfaces in the plan, not on the page. Run once per book after plan-layout (L4). The last plan layer before critique-plan's deep audit.
---

# plan-knowledge (L5 — the knowledge layer)

You are running **plan-knowledge**, the last layer of the RESTRUCTURE-V2 plan
stack — "el algo más". L1-L4 fixed *where / when / who-is-where / what-scene*.
L5 fixes **what is known, by whom, and how far the reader has been moved** at
every point. It lays two axes over L4's scene list:

- **The reader's reveal ladder** — for each shadow **truth**, its `reveal_caps`:
  the chapters that may move the reader and how far (`hidden → sensed → suspected
  → confirmed`; a decoy runs `misled → convinced → inverted`). A `reveal` event in
  a chapter with no cap — or past the top cap — is **unrepresentable**: the leak
  fails to commit.
- **Character knowledge** — `learn` events + `who_knows`: who in the world knows
  a fact at a given moment. Combined with L4's **overhear surface** (the room's
  occupants), this is the catch the whole stack was built for: *a secret said in a
  room where `who_knows` proves the wrong ears are present shows up in the plan,
  before a word of prose.*

This layer is **author-in-the-loop by design**. You PROPOSE the reveal ladder and
the knowledge map as readable tables; the author corrects; only then do you author
them into the store and verify. The ladder is theirs — the reader's journey is the
book's most load-bearing craft decision.

> **Runs in the main thread.** Like the rest of the plan stack, this is an
> interactive decision gate — it does NOT self-dispatch to a subagent.

## When to invoke

- The author says "do L5", "the knowledge layer", "the reveal ladder", "who knows
  what", or is walking the RESTRUCTURE-V2 layer stack for a book.
- Preconditions: L1-L4 are done — the store has geography, clocks, itineraries and
  `plan/layout.md`. `plan/shadow.md` (truths + reveal caps in prose) and
  `plan/seeds.md` (carrier seeds) exist. The migrated store's `state/shadow.json`
  holds the truths (with `reveal_caps` still empty until L5 fills them).

## What L5 is (and is not)

- **Is:** for every truth, a `reveal_caps` map (chapter → dose) that turns
  `shadow.md`'s prose ladder into a commit constraint; the `reveal` events where a
  truth surfaces; the `learn` events where a character acquires a fact; and the
  `who_knows` assertions that keep a secret with the right people and away from the
  wrong ones.
- **Is not:** the prose that *achieves* a dose. L5 says "by chapter 13 the reader
  may reach *suspected* on `altaluz-es-escaparate`"; it does not write the scene
  that gets them there — that is write-time, and `critique-chapter` / `naive-reader`
  measure whether the prose landed *at* the cap and not past it. L5 is the contract;
  the chapter is the performance.

## The two axes, and why the cap is the reader's state

- **Reader ladder (`reveal_caps`).** The dose is **the reader's interior state**,
  never the writer's loudness. `suspected` means "the reader may suspect", not
  "state it suspiciously". A cap only ever **rises** down the book (a truth does not
  un-reveal); author the cap at the chapters where a **carrier seed** lands (its
  echo/payoff/turn), never higher than the truth's `Reveal cap`. A truth that pays
  off in a later book **caps below `confirmed`** in this one.
- **Character knowledge (`learn` / `who_knows`).** Independent of the reader. A
  character may know from page one what the reader learns at the climax (Mauro
  knows what Bruno is; the reader crosses to *suspected* only at 13). Log a `learn`
  where a character acquires a fact; use `who-knows --expect-ignorant` to prove a
  secret has **not** leaked to someone the plan keeps in the dark, and
  `--expect-knows` where a scene needs someone to already know.
- **The join is L4's overhear surface.** For a scene that must stay private, L4's
  `--place` gives the room's occupants; L5's `who_knows` gives who among them knows.
  A truth spoken where an ignorant-but-present character would hear it is an
  impossible disclosure — catch it here.

## Hard rules

- **The cap names the reader's state, never the writer's volume.** Reject any plan
  note that says "make it obvious" / "hard hint" — that defeats the shadow. Author
  `hidden/sensed/suspected/confirmed` (or the decoy ladder), nothing else.
- **Caps only rise, and never above the truth's ceiling.** A truth's caps are
  non-decreasing across chapters; the top cap ≤ its `shadow.md` `Reveal cap`. A
  truth that resolves in a later book must stay below `confirmed` here — its full
  reveal is not this book's to spend.
- **Author caps only where a carrier lands.** `shadow.md`'s `Revealed-by` seeds and
  `Confirm in` pin the chapters. Put a cap where a carrier seed echoes/pays or where
  `Confirm in` says — not on a chapter the truth has no presence in.
- **A reveal needs a cap; a leak past the cap is unrepresentable.** Log a `reveal`
  only in a chapter the truth caps. The engine rejects a reveal with no cap at the
  door — that is the guardrail, do not work around it.
- **Keep the secret off the wrong ears.** For every truth the plan hides from a
  character, assert `who-knows --expect-ignorant <char>` at the chapters they share
  a room with someone who knows (or with the reveal). A failing assert is a real
  leak — fix the knowledge map or the scene, do not silence the check.
- **Never hand-edit `state/*.json` or `plan/shadow.md`.** Author reveal caps ONLY
  through `world_tool.py set-reveal-cap`, and knowledge ONLY through `log-event
  --type learn|reveal` (a hook blocks direct edits of the store and of the never-
  compress `shadow.md`). Both replay-validate before writing.
- **Idempotent retrofit.** If a truth already has caps (a re-run), reconcile —
  propose a change, do not stack a second conflicting cap on the same chapter.

## Steps

### 1. Read the knowledge sources

Read, in this order:
- `plan/shadow.md` — the **work-list**. For each truth: its `Reveal cap` (the
  ceiling), its `Revealed-by` carrier seeds, any `Confirm in`, its `Decoy` ladder,
  and what the *antagonist/other characters* know that the POV does not.
- `plan/seeds.md` — the carrier seeds' plant/echo/payoff/turn chapters: these are
  where the reader is moved, so these are where the caps sit.
- `plan/layout.md` (L4) — the scene list and, crucially, the **overhear surface**
  of any scene that must stay private (who is in the room).
- The store truths: `state/shadow.json` (via `store.load_truths`) — the ids and
  their current (empty) `reveal_caps`.
- `notes/decisions.md` — any binding reveal/knowledge choice already agreed.
- The critique's plan verdict if one exists (`notes/critique-plan.md`): a
  **`[shadow-thin]`** SHOULD is L5's to resolve — see step 2's truth-floor check.

### 2. Resolve the truth floor (the `shadow-thin` prerequisite)

Before laying caps, check the truth count against the critique floor (≈12 for a
~24-chapter series book). If `critique-plan` flagged `[shadow-thin]`, the missing
truths must be **authored first** — a cap ladder needs a truth to hang on:

- Draft the missing truths (typically the antagonist's own interior truth and any
  subplot with no book-I hidden layer) as `AskUserQuestion` choices — each a
  concrete truth with a proposed `Reveal cap`, `Revealed-by` carrier and `Mystery`
  (or writer-truth) tag. The author confirms or rewrites.
- Add each confirmed truth to `shadow.md` (the never-compress source) and to the
  store. **Note:** `shadow.md` is hook-protected and `mark_truth.py` only advances
  status, so authoring a *new* truth is the deferred `mark_truth --add` path — until
  it lands, the author adds the block to `shadow.md` and you re-run `migrate_story`
  (or add the `Truth` to the store) so `shadow.json` carries it. Flag this to the
  author rather than silently skipping the floor.

Only once the floor is met do you lay caps over the full truth set.

### 3. Derive the proposal

Build two tables.

**Reveal ladder** — one row per truth:
`truth | ceiling (shadow Reveal cap) | caps to author (chapter → dose, from carriers) | reveal events to log | reader journey (one line)`

The caps must be non-decreasing and ≤ ceiling. Show the carrier seed that justifies
each cap. Mark any truth whose ladder you had to infer because `shadow.md` was terse.

**Character knowledge** — one row per fact that matters:
`fact/item | who knows it, from when (learn events) | who must stay ignorant (expect-ignorant checks) | which scene tests it`

Cross-reference L4's private scenes: for each, list the overhear surface and confirm
every present character either may know or is covered by an `expect-ignorant` assert.
Any scene where an ignorant-but-present character would hear a truth is a **FLAG**.

### 4. Present + STOP for author review

Show both tables. Call out: every cap you *inferred*; every truth still below its
ceiling on purpose (a later-book payoff); every `expect-ignorant` the plan relies on;
and every FLAG where a private scene has the wrong ears. Route the binding calls
through `AskUserQuestion` (e.g. "Does the reader reach *suspected* on Bruno's nature
at 13, or hold at *sensed* until 18?", "Does Mauro know what Bruno is from chapter 1,
or only suspect until 6?"). Then STOP — author nothing until the ladder is signed off.

### 5. Apply the confirmed knowledge layer

Author, in story order:
```
# a reader-ladder cap (never above the truth's ceiling)
python scripts/world_tool.py set-reveal-cap --series-slug S --book-number N \
    --truth altaluz-es-escaparate --chapter 13 --dose suspected
# the reveal that spends it
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 13 --type reveal --truth altaluz-es-escaparate
# a character acquiring a fact
python scripts/world_tool.py log-event --series-slug S --book-number N \
    --chapter 1 --type learn --entity mauro --item naturaleza-de-bruno
```
Each replay-validates; a reveal with no cap, or above it, is `REJECTED (nothing
written)` — read the error, it means the ladder and the reveal disagree.

### 6. Verify coverage

- `python scripts/world_tool.py replay …` must print `replay OK`.
- **Reveal caps:** every truth that surfaces in-book has a cap at each surfacing
  chapter and a top cap = its intended reader ceiling; no truth is capped
  `confirmed` that pays off in a later book.
- **No leaks:** for each secret the plan hides from a character, run
  `who-knows --item <truth/fact> --until-chapter K --expect-ignorant <char>` at the
  chapters that matter (especially where they share L4's overhear surface). All must
  pass. Where a scene needs someone to know, `--expect-knows` must pass too.
- **Private scenes clean:** re-walk L4's private scenes; confirm no overhear-present
  character is an unintended knower.

### 7. Report + hand off

Summarize: the reveal-ladder table (every truth → its caps + reader journey), the
knowledge map (who knows what, and the `expect-ignorant` walls that hold), and any
residual FLAG the author deferred. Note the truth count now meets the floor.

Then hand off. **L5 is the last plan layer.** With geography, clock, cast, layout
AND knowledge in the store, the plan is dense enough that **`critique-plan`'s deep
audit** can find a broken disclosure, an impossible witness, or a seed with no
carrier scene *in the plan* — the failure caught where it is cheap. From here the
loop is: `critique-plan` (deep) → fix → **write-time**, where `plan-chapter` reads
the computed opening state (`render_opening_state`, the caps, the overhear surface)
and the smith writes to a contract that cannot drift. Leave every truth on an honest
ladder and every secret behind the right wall.

## Notes

- L5 writes `reveal` caps onto truths and `learn`/`reveal` events into the logs. It
  does not move anyone or change a scene — bodies and stages are L3/L4.
- The reader ladder (`reveal_caps`) and character knowledge (`learn`) are
  independent axes; do not conflate them. A character knowing a fact does not move
  the reader, and a reveal moving the reader does not teach a character.
- `who_knows` tracks facts a `learn` event added; a truth id is a fine "item" to
  track when you want "who in the world knows this truth". The reader's state in
  that truth is the separate `reveal_caps` axis.
- If the book has no L4 layout yet, stop and run `plan-layout` first; a knowledge
  layer with no scenes to place secrets in has no overhear surface to reason over.
