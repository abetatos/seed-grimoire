---
name: plan-book
description: Turn an approved `setup.md` into the full plan a writer can execute against. Produces `plan/outline.md` (visible chapter beats), `plan/shadow.md` (writer-only hidden truth), `plan/seeds.md` (foreshadowing catalog), `plan/arcs.md` (character arcs), and the initial `canon/` files (characters, factions, magic, world, timeline). Use this after `book-setup` is complete and before the first chapter is written.
---

# plan-book

You are running the **plan-book** skill. Your job is to take a finished
`setup.md` and produce a planning bundle the chapter writer can execute
against without ambiguity.

## When to invoke

- The user says "plan the book", "outline", "let's break this into
  chapters", or "make the seed list".
- `setup.md` exists at `output/<series>/book-NN/setup.md` and is
  reasonably complete.

## Hard rules

- **Do not invent plot details the user has not approved.** Propose,
  let them accept or rewrite. The plan is theirs.
- **Shadow and seeds are sacred.** Write them in full. They will never
  be compressed. If the user pushes you to "summarize the shadow", say
  no — it loses its purpose.
- **Locked decisions are binding — even on a regeneration.** If
  `notes/decisions.md` exists, read it first and treat every entry as a
  constraint the plan must satisfy. A re-plan or `--force` rebuild must NOT
  silently overwrite an authored choice (a magic-system call, a reveal-timing
  rule, a name). If new planning would contradict a locked decision, STOP and
  surface the conflict to the author; do not quietly drop it. This is the
  guard against a `reset-a-0` erasing choices made together.
- **Every chapter outline must contain three beat types:** plot beats,
  texture beats, subtext beats. A chapter that's only plot beats will
  come out short and dry.
- **Seeds are deterministic.** Every seed must have a `plant_in` chapter,
  optional `echo_in` chapters, and a `payoff_in` chapter. The writer
  consults the per-chapter envelope on every chapter.
- **Use Spanish names for in-world content** (places, factions, magic
  terms) unless the user has specified otherwise. Keep agent-facing
  metadata in English.
- The user can leave parts as `> TODO:` if they're not ready. The
  chapter writer will refuse to start when a target chapter has a
  TODO-only beat sheet.

## Inputs you must read first

- `output/<series>/book-NN/setup.md` — the source of truth.
- `references/fantasy-beats.md` — three-act adapted structure, subplot
  weaving, character arcs.
- `references/seed-craft.md` — how to plant, echo, pay off without
  telegraphing (incl. trigger / dose / resolution-image fields).
- `output/<series>/book-NN/notes/decisions.md` — authored locked choices, if
  any. **Binding** (see Hard rules).
- `references/magic-design-checklist.md` — only if magic still needs
  detail.
- If this is book N>1 of a series:
  - `output/<series>/series.md`
  - `output/<series>/series-state.md`
  - `output/<series>/book-(N-1)/summaries/book-summary.md`

## Steps

### 1. Bootstrap the skeletons

If `plan/outline.md` does not exist yet (or the user asks to "redo"
the plan):

```bash
python3 .claude/skills/plan-book/scripts/bootstrap_plan.py \
    --series-slug <slug> \
    --book-number <N>
```

This reads `setup.md` and writes skeletons for:
- `plan/outline.md` — one section per chapter with TODO bullets
- `plan/shadow.md` — overview + act sections + per-chapter sections
- `plan/seeds.md` — header + format reference (empty)
- `plan/arcs.md` — one section per principal
- `canon/characters.md`, `canon/factions.md`, `canon/magic.md`,
  `canon/world.md`, `canon/timeline.md`

If files already exist, the script refuses unless `--force` is passed.

### 2. Plan in this order

The order matters — each step depends on the prior one. Do not jump
ahead.

#### 2a. Confirm act structure

Open `plan/outline.md` and inspect the act boundaries the script picked
(based on chapter count). Confirm with the user:
- Act 1 length feels right for a slow-immersion inhabitation?
- Midpoint sits where the user wants the overturn?
- Act 3 has enough room for the climax and resolution?

If the user wants different boundaries, **edit the act headers in
`outline.md` directly** before filling chapters.

#### 2b. Fill the shadow timeline first

Yes — *before* the outline. The shadow is the spine; without it, the
outline drifts.

Walk the user through `shadow.md`:

1. **Overview** — In 5-10 sentences, what is *really* happening behind
   the surface story? What's the secret history?
2. **Master truths** — facts true in the world but hidden from the
   **reader**, as `## SHADOW-TRUTH` records. Aim for MANY (~12-20 for a
   25-chapter book), not a thin handful: the protagonist's hidden nature,
   EACH antagonist's agenda, EACH institution's real function, the secret
   history, EACH major subplot. Each truth declares `Revealed-by:` (its
   carrier seed ids — the schedule lives there, do NOT re-schedule), a
   `Reveal cap:` (loudest it may sound in this book; later-book payoffs cap
   below `confirmed`), and `Status: hidden`. The reveal ladder names the
   **reader's** interior state, never the writer's force:
   `hidden → sensed → suspected → confirmed`. See the skeleton in
   `shadow.md` for the exact record shape.
   - **Misreads (optional `Decoy:`).** When the reader should actively
     believe the *opposite* of a truth — not merely not-know it — add a
     `**Decoy:**` line stating the FALSE belief. Its carrier seeds then build
     that wrong belief and a later carrier payoff inverts it; the ladder reads
     `misled → convinced → inverted` and `Reveal cap` bounds how sure of the lie
     the reader may get. Use only for a belief carried across chapters (a
     one-scene red herring is just a seed). See `references/seed-craft.md` §
     "Misreads".
   - **Cover the grimoire's §14b master mysteries.** Every mystery the
     grimoire marks as *introduced in this book* MUST have a truth here,
     tagged `**Mystery:** <exact §14b name>`. `critique-plan` flags any
     mystery with no truth — do not leave a promised mystery uncarried.
3. **Per act** — For each act, what does the antagonist (or fate, or
   the world) know that the protagonist doesn't? What's the real cause
   beneath the visible event?
4. **Per chapter (skip chapters where there's no hidden layer)** —
   what does this chapter look like vs. what's actually happening?

Push back if the user offers "things just happen" — there must be a
hidden mover. Even in low-mystery fantasy, the reader's understanding
catches up to the writer's. Plan that gap.

#### 2c. Build the seeds catalog

Open `plan/seeds.md` and add seeds with the user. Each seed:

- **id** — short stable handle (e.g., `boy-with-scar`, `copper-ring`,
  `bell-at-sundown`). Used by the writer to mark planted/echoed/paid.
- **Detail** — the concrete surface thing the reader sees.
- **Real meaning** — what it actually signifies (hidden).
- **Plant in** — chapter number.
- **Echo in** — chapter numbers (0-3 entries; more is over-flagging).
- **Payoff in** — chapter number.
- **How to plant** — one-line instruction. Reference `references/seed-craft.md`.
- **How to pay off** — one-line instruction.
- **Trigger** — for any seed whose payoff is an *event* (something breaks,
  fires, collapses, is discovered): the **intrinsic, already-seeded cause**
  that makes it fire at that moment. The trigger must itself be planted —
  never a convenient external actor that arrives only to cause the event (no
  just-in-time horse, storm, or stranger). If a payoff has no credible
  intrinsic trigger yet, that is a plan gap to fix now, not at writing time.
- **Dose** — the telegraph budget: how many touches, how loud, derived from
  the plant→payoff distance. Rule: a payoff **≤2 chapters** from its plant
  gets **one quiet touch** and is **never re-described** at the payoff
  chapter's opening; wider gaps may carry echoes. Write it explicitly so the
  writer cannot over-telegraph (this is the "se ve venir a kilómetros" guard).
  A close payoff is fine — it needs this extra discipline plus an intrinsic
  `Trigger`, not avoidance.
- **Resolution image** — *(optional, for emotional/sensory through-lines)* the
  exact planted image that the payoff **inverts or transforms** (e.g. a cold
  felt in the chest in ch 1 that the magic discharge empties at the climax).
  This is what makes a book feel *woven* rather than a list of reveals.
- **Obligatory** — *(only for seeds that realize a grimoire §14 loaded gun)*
  `§14 <exact name>` from the grimoire table. **Every §14 loaded gun whose
  "Siembra en" includes this book MUST have a seed carrying this tag** — that
  is how `critique-plan` proves no obligatory planting was forgotten. (This is
  the check that would have caught a missing `primer-uso-honesto`.)
- **Status:** start as `planned`.

Aim for **8-15 seeds per book minimum** for an epic fantasy. Of those:
- ~30% small (single sensory details — a smell, a scar, a hand
  movement)
- ~50% medium (a recurring character, a misread relationship, a held
  object)
- ~20% large (a hidden identity, an inherited debt, a misnamed event)

**Distribute plants across act 1 and early act 2.** Payoffs cluster in
act 2B and act 3. Echoes scatter in between. A chapter with both a
plant AND a payoff for *different* seeds is fine; the same seed should
not plant and pay off in adjacent chapters.

Use `references/seed-craft.md` to coach the user on each seed's
instructions. If the user offers a seed that telegraphs ("the strange
old man with the prophecy"), push them toward a craftier version
("the old man who fixes the well in chapter 2 and never quite leaves
the village").

#### 2c-bis. Weave the emotional spine

After the plot seeds, identify the **2-3 emotional/sensory through-lines**
that should make the book feel *woven* (the author's "todo muy hilado").
Each is a felt image planted early whose payoff is the **same image
transformed**, not a separate fact — e.g. a cold in the chest planted in ch 1
that the climax empties or releases. For each through-line, add a
**resolution-type seed** with a `Resolution image` field naming the plant
image and how the payoff inverts it. A book with zero resolution-type seeds
will pay off its plot but feel mechanical; flag that.

#### 2d. Character arcs

Open `plan/arcs.md`. For each principal:

- Wound, Want, Need, Lie — pull from `setup.md` if filled.
- **Waypoints** — give each arc concrete chapter milestones:
  - State at start
  - First crack (which chapter the wound first stings)
  - Midpoint shift
  - All-is-lost low
  - Decision moment (which chapter)
  - End-state
- **Transformation type** — positive, negative, or tragic.

The protagonist's decision moment should align with the climax. A
secondary character's decision moment can sit in act 2B and inform
the protagonist's climax.

Then close the file with a **"Sliding scales" block** (see the one in
`output/el-vitral/book-01/plan/arcs.md` as the model): for each principal,
place the three dials — **competence / proactivity / sympathy** — at start
and end, and name which chapters move which dial. A character low on two
dials must be high on at least one; an arc *is* a dial moved on purpose;
a dial that stays flat must be flat *by design* (name why). Mark which
POVs carry the per-chapter proactivity rule (the POV chooses at least once
per chapter — observer/hider protagonists always carry it). This block is
diagnostic for plan and critique only; prose never mentions dials.

#### 2e. The visible outline

Now fill `plan/outline.md`, **chapter by chapter, in order**. For each
chapter:

- **Title** — working title; can change.
- **POV** — which character.
- **Where / when** — place + time elapsed.
- **Function in the act** — one sentence: what this chapter does for
  the larger arc.
- **Plot beats** — 3-6 short bullets, in order.
- **Texture beats** — 2-4 grounding moments (150-400 words each), each
  **typed** with one of the six licensed kinds (see expand-chapter):
  world element unfolded in use, stage built, cost made visible,
  deliberation on the page, re-orientation, secondary humanized. Be
  specific: *unfold* the pitch-boiling the quarter lives off, *stage*
  the mill loft before the chase crosses it, *bill* the drained lamp.
  Generic lingering ("the bells at sundown" with no job) is not a beat.
  These are how the book breathes. **Without grounding beats, chapters
  come out short AND ungrounded.**
- **Subtext beats** — what the POV feels but doesn't say; what the
  reader senses without being told; which lie the character is
  protecting in this scene. Also note which seed envelope items will be
  active, so the writer-of-record sees the plan and the envelope agree.
- **Transition out** — how the chapter ends so the next one feels
  inevitable.

Pacing rules (`references/fantasy-beats.md`):
- Never two action chapters back-to-back. Quiet earns loud.
- Alternate emotional registers.
- Act 1 should feel **inhabited** — dwell on daily life, magic in
  mundane use, world texture. The reader is being placed in the world.
- Sharp midpoint. Something the reader believed gets overturned. Mark
  this clearly in the chapter's function.
- Subplots touch the main plot at ≥3 points and resolve before or
  during the climax.

#### 2f. Fill canon

Walk through the `canon/*.md` files. Promote facts from `setup.md`
into stable canon entries:

- `canon/characters.md` — every principal + named secondaries. Tight
  entries: role, three physical specifics, voice tic, current location,
  current emotional state, current relationships, magic relationship,
  secrets (writer-only).
- `canon/factions.md` — every named faction/caste/order.
- `canon/magic.md` — promote the full system from setup.md. Lock the
  in-world vocabulary here.
- `canon/world.md` — every named place with sensory anchor and
  political stance.
- `canon/timeline.md` — historical events (pre-book) + initial
  book chronology (just ch 1's day for now; the rest grows).

These files will be read in full by the chapter writer. **Keep them
tight.** If a character has a multi-paragraph description, trim to the
load-bearing details.

### 3. Validate before finishing

Run a pass over the plan to check:

- [ ] Every chapter in `outline.md` has plot **and** texture **and**
      subtext beats (no `> TODO:` left in critical fields).
- [ ] Shadow has overview + per-act + at least midpoint and climax
      chapter sections filled.
- [ ] ≥ 8 seeds in `seeds.md`, each with plant/payoff chapters; status
      is `planned` for all.
- [ ] Each principal in `arcs.md` has a decision moment chapter.
- [ ] `canon/magic.md` has source + mechanic + ≥2 costs + ≥3 limits.
- [ ] No `> TODO:` left in `canon/characters.md` for principals.

If anything is missing, **show the user the list** and ask whether to
fill it now or defer.

### 4. Wrap up

Print a short summary:

- Title, chapters, principal characters
- Number of seeds planted across the book
- Midpoint chapter and what overturns there (one line)
- Climax chapter and the decision being made (one line)

Tell the user the next step: run `write-chapter --chapter 1` to begin
writing. Remind them they can edit any plan file at any time — the
writer reads the current file each chapter.

## What this skill does NOT do

- Does not write any prose.
- Does not produce summaries (that's `update-canon` after each chapter).
- Does not modify `setup.md` (use `book-setup` for that).

## Files this skill writes

- `output/<series>/book-NN/plan/outline.md`
- `output/<series>/book-NN/plan/shadow.md`
- `output/<series>/book-NN/plan/seeds.md`
- `output/<series>/book-NN/plan/arcs.md`
- `output/<series>/book-NN/canon/{characters,factions,magic,world,timeline}.md`
