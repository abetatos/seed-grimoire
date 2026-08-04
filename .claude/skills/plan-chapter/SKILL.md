---
name: plan-chapter
description: Pre-chapter decision gate. BEFORE write-chapter runs, build a short briefing of the upcoming chapter (its job, the seeds due with their trigger/dose/resolution, the emotional-spine touch, Bruno-or-POV exposure state) and surface the 2-4 creative forks the outline leaves underdetermined as AskUserQuestion choices WITH a recommendation each. Persist the author's answers and the state sheet to a single notes/brief-chNN.md so write-chapter honors them and a regeneration cannot silently overwrite them. Use this as the FIRST step of writing any chapter — invoke as "plan chapter N" / "briefing for chapter N"; write-novel chains it before write-chapter.
---

# plan-chapter

You are running the **plan-chapter** skill. This is the **decision gate
that runs before any prose is written**. Its whole purpose is to put the
underdetermined creative choices of the coming chapter **in front of the
author** — with a recommendation — instead of letting the writer improvise
them silently. (The skill exists because silent improvisation is how a beam
ends up felled by a convenient horse, and how a late reveal gets spent early.)

The output is **decisions on disk**, not prose. You write
`notes/brief-ch<NN>.md` (section `## Decisiones`); `write-chapter` reads it as binding.

## When to invoke

- The user says "plan chapter N", "briefing for chapter N", "what are the
  choices for the next chapter?", or is about to write a chapter.
- `write-novel` chains it automatically before `write-chapter` (step 2b').
- Re-runnable: if the author wants to revisit choices, run it again; it
  overwrites the chapter decisions file.

## Hard rules

- **Decisions, not prose.** Never draft chapter text here. You produce a
  briefing and capture choices.
- **Always recommend.** Every fork you surface must carry your
  recommendation as the first option, with a one-line rationale. The author
  is choosing between *informed* options, not filling a blank.
- **Only surface real forks.** A fork is a place the outline/beat sheet does
  **not** decide and the writer would otherwise invent: the *trigger* of an
  event, *who witnesses and how much they understand* (exposure), *which
  planted image a payoff resolves*, *the order of scenes*, a tone call. Do
  **not** ask about things already fixed by setup, canon, the beat sheet, the
  seed envelope, or `decisions.md`. 2-4 forks is the target; a simple chapter
  may have only 1.
- **Honor what is already locked.** Read `notes/decisions.md` (book-level
  binding law) and the seed envelope first. Never re-ask a settled question;
  never offer an option that violates a locked decision, canon, or the
  shadow's reveal timing.
- **Protect reveal timing.** If a seed's payoff is scheduled for a later
  chapter, the gate's job is to keep this chapter from spending it. Surface
  "how loud is the anomaly here?" as a fork with the quiet option recommended.
- **No deus ex machina — motivate presence and triggers.** Every event's
  *cause* and every key character's *presence* must be intrinsic and seeded,
  never convenient (no stranger "passing by just when", no fortunate rescue).
  When a beat needs a character on the page or an event to fire, surface it as
  a fork and recommend the option where the cause is already on the page and
  the character has their own reason to be there (ideally tied to the book's
  engine). If the outline itself smuggles in a convenience, flag and replace it.
- **The gate writes; write-chapter obeys.** Decisions go to
  `notes/brief-ch<NN>.md` (`## Decisiones`). If a decision is durable (affects more than
  this chapter — a worldbuilding call, a reveal-timing rule, a name), also
  append it to `notes/decisions.md` so it survives a regeneration.

## Steps

### 1. Build / refresh the context bundle

```bash
python3 .claude/skills/write-chapter/scripts/build_context.py \
    --series-slug <slug> --book-number <N> --chapter <M> --phase plan
```

`--phase plan` builds a lighter bundle: it drops the recent chapters in full,
the style guide and the craft checklist (the gate decides forks, it writes no
prose), so prior chapters arrive as summaries. Everything you need to choose —
decisions, canon, neighbor beats, arcs, shadow, the seed envelope and the beat
sheet — is still there.

Read `notes/_context-chMM.md`. Pay special attention to:

- **Decisions** (the new top block) — book-level locked choices + any prior
  chapter decisions. These are binding; do not reopen them.
- **Beat sheet** for chapter M — what is fixed.
- **Seed envelope** — every seed to plant/echo/pay this chapter, now carrying
  `Trigger`, `Dose`, and `Resolution image` where present. A payoff with a
  `Trigger` field tells you the intrinsic cause is already chosen; a payoff
  *without* one is a fork you must surface.
- **Shadow slice** — what must stay hidden and *when* each truth is due.
- **Arcs** — including the **exposure ladder** (how much each POV's secret is
  exposed at this point). The current rung is the baseline for any
  exposure fork.

### 1b. Inherit the L4 layout slice (store-adopted books)

If `plan/layout.md` exists (the book ran the engine layers L1-L5 via
`plan-world`), read **this chapter's slice** — its ordered scenes with the
**computed stage, clock, and cast**. Those were derived from the world-state
store and are already verified feasible (copresence, travel time, reveal caps).

**Do not re-derive what L4 already computed.** The briefing's stage/time and the
state sheet's *Opens at* / *On stage* are **lifted from the layout slice**, not
hand-reconstructed from summaries — hand-deriving them is the duplication that
lets the brief drift from the verified contract. plan-chapter's remaining job
narrows to what L4 does **not** decide: the creative forks (triggers, exposure,
which image pays), the seed doses, the reveal guards, and the carry threads.

If `plan/layout.md` is **absent** (legacy / un-migrated book), derive the
opening state from the previous chapter's summary as before — nothing changes.

### 2. Write the briefing (to the user, in chat)

A short, scannable briefing — not prose. Cover:

- **Chapter job** — the one structural thing this chapter must accomplish.
- **Seeds due** — plant / echo / payoff, each with its dose budget and (for
  payoffs) its trigger and resolution image. Flag any seed whose payoff is
  ≤2 chapters from its plant: "touch once, quietly; do not re-describe."
- **Emotional-spine touch** — which planted felt-image this chapter advances
  or inverts (the "hilado").
- **Exposure state** — the POV's current rung on the exposure ladder, and
  whether this chapter is poised to raise it.
- **Reveal guards** — any later-due truth this chapter could accidentally
  spend; name it.

### 3. Identify the forks and ask

List the 2-4 genuine forks. For each, call `AskUserQuestion` with:

- A clear question naming the stakes.
- 2-4 options. **First option = your recommendation, labelled "(Recomendado)"**,
  with a one-line rationale in the description. Include the cost/benefit of
  each alternative honestly.
- Where useful, a `preview` showing the concrete difference (e.g. an
  intrinsic-trigger beat vs an external-trigger beat).

Typical fork families (use the ones that apply):

- **Trigger of an event** — intrinsic & already-seeded cause vs convenient
  external actor. Recommend intrinsic.
- **Exposure / witnesses** — who sees the POV's anomaly and how much they
  understand; how far the ladder moves. Recommend the option that preserves
  reveal timing unless the outline demands a jump.
- **Which image resolves** — when a felt-image payoff is due, which planted
  image it inverts.
- **Scene order / emphasis** — when the beat sheet lists beats but not their
  sequence or weight.

Batch independent forks into a single `AskUserQuestion` call (multiple
questions) so the author answers them together.

### 4. Write the brief

Write **one** file, `notes/brief-ch<NN>.md` — plan-chapter's single mandatory,
committed hand-off to write-chapter. Three fixed sections, always present, same
shape every chapter. `context.py` splits them to their bundle positions:
`## Decisiones` loads at the top as binding law; the state sheet and `## Arrastre`
load late, next to the beat sheet. Do NOT write separate `decisions-chNN.md` /
`continuity-chNN.md` files — they were merged into the brief (the retired shape).

```markdown
# Brief — chapter N

> plan-chapter's single hand-off to write-chapter. Mandatory, committed.

## Decisiones

- **[fork label]** → chosen: <option>. Rationale: <one line>.
- ...

### Notes for the writer
- Concrete directives that follow from the choices (e.g. "the beam fails from
  the crowd-load + the iron strap finally yielding — both already on the page;
  NO external actor"; "the no-heat anomaly is whispered, not explained — that
  diagnostic belongs to ch24").

## Estado que no se puede contradecir

> The checkable state sheet the writer must not contradict and the critic checks
> the prose against. When `plan/layout.md` exists, lift *Opens at* / *On stage*
> from this chapter's **layout slice** (computed stage/clock/cast — see step 1b);
> otherwise derive from the PREVIOUS chapter's summary carry-forward (in the
> bundle), canon character states, and this chapter's shadow slice. List only
> what is ON STAGE or at risk of being fumbled — 10-20 lines, not a canon dump.

### Opens at
- Place / time: … (delta from ch N-1 end: …)

### On stage
- <name>: physical state, injuries, what they carry / wear

### POV knowledge
- Knows: …
- Does NOT know yet: … (name the chapter each is due, from shadow/seeds)

### Objects in play
- <object>: where it is, last seen state

## Arrastre

- (ninguno)
```

**The `## Arrastre` carry buffer** replaces the retired open-questions.md. Fill
it from the previous chapter's brief `## Arrastre` — carry forward only what is
**still pending for THIS chapter or a later one**, and DELETE any thread the
previous chapter consumed (hard close rule; a thread that never closes is a bug,
not a fixture). Add a new thread only when something must reach a specific later
chapter (e.g. "rima `el-tutor-tiene-agenda` en el cap 4 con la mirada del cap
1"). Tooling bugs do NOT go here — they go to `TODO.md`. If nothing is pending,
leave `- (ninguno)`.

The state sheet lifts the handful of canon facts that govern *this* chapter to a
spot right beside the beat sheet — that is why continuity errors happen: the
facts that govern them otherwise sit in the low-attention middle of a long bundle.

If any decision is **durable** (worldbuilding, reveal-timing rule, a naming
call, an exposure-ladder change), also:

- Append it to `notes/decisions.md` (create the file if absent, using the
  template in that file's header).
- If it changes the exposure ladder, update `plan/arcs.md`'s ladder for that
  POV.

Keep canon/seeds edits out of scope here unless the decision *is* a canon
fact the author just settled — in that case make the minimal edit and note it.

### 5. Report and hand off

Print:
- The decisions captured (one line each) and the brief path.
- Any carry threads placed in `## Arrastre`.
- Any durable decision you propagated to `decisions.md` / `arcs.md`.
- The next step: `write-chapter N` (or, under `write-novel`, it continues
  automatically).

## What this skill does NOT do

- Does not write or modify chapter prose.
- Does not run critique.
- Does not advance seed statuses (update-canon does that).
- Does not invent plot the author hasn't approved — it offers forks and
  records the choice.
