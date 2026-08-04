---
name: plan-world
description: Umbrella conductor that builds the whole engine layer of a book's plan — the spatial-temporal contract L1-L5 — in one guided pass. After plan-book has produced the outline (L0), plan-world migrates the world-state store if needed, then chains plan-space (L1 world graph) → plan-time (L2 clock) → plan-cast (L3 itineraries) → plan-layout (L4 scene list) → plan-knowledge (L5 reveal ladder), stopping at each layer's author gate. Use this after plan-book and before critique-plan, when the user says "build the world layers", "run L1-L5", "plan-world", or resume-act reports phase plan-world. The five layer skills remain individually invocable for surgical re-runs.
---

# plan-world (the engine-layer conductor, L1-L5)

You are running **plan-world**. Its ONLY job is to walk the book through the
five RESTRUCTURE-V2 engine layers **in order**, so the author runs *one* skill
instead of remembering five. It is a **thin conductor**: every layer's real
logic lives in its own skill (`plan-space` / `plan-time` / `plan-cast` /
`plan-layout` / `plan-knowledge`) and stays single-sourced there. plan-world
does not duplicate it — it sequences it, checks the precondition once, and hands
off between gates.

> **Runs in the main thread.** Each layer is an interactive decision gate that
> must talk to the author (like plan-chapter), so plan-world does NOT
> self-dispatch to a subagent. It invokes each layer skill via the Skill tool
> and pauses for the author at each layer's review stop.

## When to invoke

- `resume-act` reports **phase `plan-world`** (plan L0 ready, `plan/layout.md`
  absent).
- The author says "build the world layers", "run L1-L5", "plan-world", "do the
  engine layers".
- After `plan-book`, before `critique-plan`.

## Preconditions

- `plan/outline.md` exists (L0 — from `plan-book`). If not, STOP and send the
  author to `plan-book` first.
- Series slug + book number known (ask or infer from the working context).

## Step 0. Migrate the store if absent

The layers write into the world-state store; L1 needs it migrated first. Check
for `output/<series>/book-NN/state/seeds.json`:

- **Absent** → run the migration (dry-run first, then apply):
  ```bash
  python3 scripts/migrate_story.py --series-slug <slug> --book-number <N> --dry-run
  python3 scripts/migrate_story.py --series-slug <slug> --book-number <N>
  ```
  `migrate_story.py` replay-validates before writing, so an impossible history
  refuses to migrate — surface any failure to the author rather than forcing it.
- **Present** → the store is already migrated; skip to step 1.

## Step 1. Chain the five layers, each an author gate

Invoke the layer skills **in this exact order**, one at a time, via the Skill
tool. Each is interactive: it PROPOSES its layer as readable tables, the author
corrects, then it applies to the store and verifies. **Do not start a layer
until the previous one has completed and the author has confirmed its review
stop** — every layer reads the store the previous one wrote, so order is load-
bearing.

1. **`plan-space`** (L1 — world graph): places, containment, edges with ordinal
   costs, POIs → `state/world.json` + initial entity positions.
2. **`plan-time`** (L2 — the clock): per-chapter opening día/franja; verifies
   every outline displacement is feasible against L1's graph costs.
3. **`plan-cast`** (L3 — itineraries): where every named character stands at
   each chapter opening; verifies with `copresent` that the meetings the
   outline assumes actually have their people in the room.
4. **`plan-layout`** (L4 — scene list): per-chapter ordered scenes with computed
   stage/clock/cast + authored who-speaks / work / tempo → `plan/layout.md`.
5. **`plan-knowledge`** (L5 — reveal ladder): the reader's reveal caps + character
   learn/reveal events; verifies no secret is disclosed past its cap or leaked
   to a character the plan keeps ignorant.

Between layers, print a one-line progress marker (e.g. "L1 ✓ — graph applied;
starting L2 (the clock)") so the author can see how far the pass has gone.

**If the author wants to stop partway**, that is fine — the store persists what
each completed layer wrote. Tell them which layer is next so they (or `resume-act`)
can resume: re-invoking `plan-world` re-checks migration and continues from the
first unbuilt layer, or they can invoke the single layer skill directly.

## Step 2. Hand off to critique-plan

Once L5 completes, the engine layer is built. Print a short closing:

- The five layers landed (and the store passed each layer's verification).
- **Next step: `critique-plan`** — the mandatory audit before chapter 1, which
  now includes the store-backed deep pass (`audit_plan_store.py`) the layers
  make possible.

plan-world does NOT run the critique itself and does NOT write prose. It builds
the contract; `critique-plan` stress-tests it.

## What this skill does NOT do

- Does not duplicate any layer's logic (they stay single-sourced in the five
  layer skills).
- Does not edit `state/*.json` directly (each layer applies via `world_tool.py`).
- Does not write prose, run the plan critique, or touch `setup.md` / `grimoire.md`.

## Files this skill touches

- Triggers `migrate_story.py` (step 0) and the five layer skills, which write
  `state/{world,entities,seeds,shadow}.json`, `state/events/*.jsonl`, and
  `plan/layout.md`. plan-world itself writes nothing.