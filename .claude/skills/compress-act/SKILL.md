---
name: compress-act
description: Fold a finished act's chapter summaries into a single act-level summary so distant chapters drop out of the writer's context window without losing their plot weight. Seeds and shadow are NEVER compressed. Use this when the user says "compress act N" or when the last chapter of an act has been locked in via `update-canon`.
---

# compress-act

> **DEPRECATED — use `close-act` instead.** `close-act` is a strict
> superset of this skill: it folds the act's chapter summaries into an
> act summary (this skill's whole job) **and** consolidates `voice.md`,
> (re)builds `book-summary.md`, and writes `session-handoff.md`. Only use
> `compress-act` if you explicitly want *just* the act-summary fold with
> no other end-of-act bookkeeping. The act-summary structure below is
> still the reference that `close-act` step 2 points to.

You are running the **compress-act** skill. The chapters in an act are
all written and locked into canon. Your job is to merge their summaries
into one act-level summary so they fall out of the recent window
without losing their substance.

## When to invoke

- The user says "compress act N" / "fold the first arc" / equivalent.
- `update-canon` for the last chapter of an act has finished and the
  user agrees to compress.

## Hard rules

- **Never compress `plan/seeds.md`.** It is the source of truth for
  every seed across the book.
- **Never compress `plan/shadow.md`.** It is the writer's truth for
  every future chapter.
- **Never delete chapter summaries.** They stay on disk for search
  and human inspection. Compression only changes which file the
  writer's context bundle reads from.
- **Target ~1500 words for the act summary.** If you can't fit, you
  are retelling instead of compressing.
- **Lose texture; keep facts.** Texture beats live in the chapter
  prose and in the chapter summaries. The act summary records
  events and shifts, not sensory dwellings.

## Steps

### 1. Prepare the bundle

```bash
python3 .claude/skills/compress-act/scripts/prepare_act.py \
    --series-slug <slug> --book-number <N> --act <A>
```

This:
- Bundles all chapter summaries in the act's range into one file
  (`notes/_act-AA-bundle.md`).
- Writes a skeleton `summaries/act-AA.md` for you to fill.
- Prints the chapter range and reminds you that seeds and shadow are
  never compressed.

### 2. Write the act summary

Read the bundle. Fill `summaries/act-AA.md`:

- **What this act did for the book** — 4-6 bullets on its function in
  the larger arc.
- **Plot — sequence of events** — 10-20 short bullets, chronological.
  Decisions, deaths, alliances, geographic moves. **No texture.**
- **Character state changes** — one block per principal, 2-3 lines.
- **Magic / world disclosures** — new rules, costs, places, vocabulary.
- **Seeds activity** — seed ids only (planted / echoed / paid).
  *Reference; the source of truth is still* `plan/seeds.md`.
- **At the end of the act** — 3-5 lines of standing state: locations,
  emotional states, threads.

Keep the total around 1500 words. If you find yourself writing scene
description, you are doing it wrong. Cut.

### 3. Verify

Confirm `summaries/act-AA.md` exists, the chapter summaries
(`summaries/ch-MM.md`) are untouched, and `plan/seeds.md` / `plan/shadow.md`
are untouched. The context builder will now use the act summary for
that range when those chapters fall outside the recent window.

### 4. Report

Print:
- Act number, chapter range, final word count of the act summary.
- A reminder that seeds and shadow remain explicit.
- Suggested next step: `write-chapter <next>`.

## What this skill does NOT do

- Does not touch `plan/seeds.md`, `plan/shadow.md`, `plan/outline.md`.
- Does not delete chapter summaries or chapter prose.
- Does not modify canon.
