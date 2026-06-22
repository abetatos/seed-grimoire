---
name: update-canon
description: Lock a finished chapter into the book's state. Writes the chapter summary, updates seed statuses, promotes any new facts from the chapter into canon (characters/factions/magic/world/timeline), and refreshes the rolling book-summary. Use this AFTER `critique-chapter` says PASS (or the user approves). Refuses to run if the chapter file is missing.
---

# update-canon

You are running the **update-canon** skill. The chapter is accepted.
Your job is to fold it into the book's running state so future chapters
have an accurate picture without re-reading prose.

## When to invoke

- The user says "lock in chapter N", "save chapter N to canon",
  "update canon", or equivalent.
- `critique-chapter` has reported PASS (or the user explicitly accepted).

## Hard rules

- **Run only after the chapter is final.** This is the lock-in. If
  the user revises after running update-canon, you must re-run it.
- **Summaries are ~400-500 words. Tight.** They are loaded into every
  future chapter's context until act compression happens.
- **Never modify `plan/shadow.md` or `plan/seeds.md` content here**
  — except seed `Status:` fields, which advance as the book is written.
- **Canon promotion is additive.** Do not delete existing canon entries.
  Append, refine, or update existing fields (current location, current
  emotional state). Names and physical specifics are immutable.
- **Flag every contradiction.** If the chapter contradicted something
  in canon, **stop and tell the user**. Do not silently reconcile.

## Steps

### 0. Pre-lock consistency check (before any write)

Lock-in is **the moment a chapter becomes load-bearing for everything
after it.** Once canon is updated and seeds advance, future chapters
will be written against those facts. So before touching any file,
do an explicit consistency pass:

- **Chapter vs shadow.** Did the chapter accidentally state something
  that shadow.md says should stay hidden? If so, **stop and report** —
  the chapter may need a revision before locking, or shadow.md may
  need updating to acknowledge the leak.
- **Chapter vs canon.** Did the chapter contradict a canon entry
  (name, place, magic rule, relationship)? Quote both. **Stop and ask
  the author** whether to revise the chapter or update canon.
- **Chapter vs seeds.** Were the seeds in this chapter's envelope
  actually planted/echoed/paid in the prose? If a scheduled seed is
  missing from the prose, **stop and report** — locking in would
  break the seed's status chain.
- **Chapter vs bible.** Does the chapter assume something the bible
  declares fixed differently? Bible takes precedence over chapter
  prose. **Stop and ask.**
- **Chapter vs arc waypoints.** Is the POV's state at chapter end
  compatible with their next waypoint? If the chapter took the
  character somewhere the arc didn't plan for, the arc may need
  updating — or the chapter rewrites.

If anything surfaces, do not proceed with the rest of update-canon
until the author decides how to resolve. The cost of locking in a
contradiction is paid in every future chapter.

If everything checks out, say so ("pre-lock consistency check clean
— proceeding to summary and canon promotion") and continue.

### 1. Prepare the skeletons and read what's due

```bash
python3 .claude/skills/update-canon/scripts/prepare_summary.py \
    --series-slug <slug> --book-number <N> --chapter <M>
```

This:
- Writes `summaries/ch-MM.md` skeleton (with the seed envelope embedded)
- Prints the seed envelope for this chapter and current statuses
- Lists the canon files to inspect

If the script warns that the chapter is too short, **stop**. Tell the
user the chapter isn't ready to lock in.

### 2. Write the chapter summary

Open `summaries/ch-MM.md` and fill the TODO sections. Read the chapter
itself (`chapters/MM.md`) for the facts. Fill:

- **POV / Where / When** — one short line each.
- **What happened** — 4-8 bullets, in order. Names, decisions, outcomes.
  Not interpretation. Not subtext. Just events.
- **Texture beats present** — 1-2 lines naming what was dwelt on.
- **Subtext / interior shifts** — what changed underneath. Lies
  reinforced, wounds touched, decisions delayed.
- **Seeds in play** — already auto-listed; verify accuracy against the
  prose.
- **Canon updates required** — the new facts the chapter introduced
  that should be promoted (next step).
- **Carry forward** — 1-3 lines: at chapter end, who is where, in what
  state, what is left hanging into the next chapter.

Word target: 400-500 words for the whole summary. Trim aggressively.

### 3. Advance seed statuses

For each seed in the envelope, advance its status:

- A seed that was `planned` and is planted in this chapter → `planted`
- A seed already `planted` (or `echoed-K`) that is echoed in this
  chapter → `echoed-(K+1)` (or `echoed-1` if first echo).
- A seed that is paid off in this chapter → `paid_off`

Run, once per seed:

```bash
python3 .claude/skills/update-canon/scripts/mark_seed.py \
    --series-slug <slug> --book-number <N> \
    --seed-id <id> --status <new_status>
```

If a seed scheduled for this chapter was **not** present in the prose,
do not advance its status. Tell the user — this is a contract violation
that needs revising the chapter or revising the seeds.md schedule.

### 4. Promote facts to canon

Walk the `Canon updates required` section of the summary you just
wrote. For each item:

- **canon/characters.md** — new minor characters, current emotional
  state changes, current location updates, new relationships.
- **canon/factions.md** — new factions encountered, leadership changes,
  shifts in stance toward principals.
- **canon/magic.md** — new uses observed, new costs witnessed, new
  vocabulary the user accepted.
- **canon/world.md** — new named places, sensory anchors for them,
  political stance.
- **canon/timeline.md** — append a line: `- **Ch M:** <day count>
  — <one-line event>`.

Use the Edit tool. Keep entries tight — these files are read in full
on every chapter, so bloat hurts every future write.

**If you encounter a new fact you cannot promote because canon is
silent on the surrounding structure, ask the user.** Don't invent
canon out of a chapter detail.

### 5. Touch the book summary's "What just happened" only — do NOT rewrite it

Do **not** rewrite the whole `summaries/book-summary.md` here. Within the
current book **nothing reads it**: `lib/context.py` loads only a *prior*
book's book-summary (`_previous_books_context`), and `resume-act` snips
only its `## What just happened` section. The full synthesis (state of
world / principals / threads / reader knowledge) is **rebuilt at act
boundaries by `close-act`** and finalized at book end. Rewriting ~2000
words every chapter is wasted cost (the per-chapter record already lives
in `summaries/ch-NN.md`; the book summary is a *synthesis*, not a log).

So do only the cheap thing:

- If `summaries/book-summary.md` exists, update **only** its
  `## What just happened` section — 2-3 sentences on this chapter, so a
  fresh `resume-act` mid-act re-enters cleanly. Leave every other section
  untouched.
- If it does **not** exist yet (first chapter of the book), create a
  minimal stub: a `# <Title> — running summary` heading and a
  `## What just happened` section only. `close-act` fleshes out the rest
  at the first act close.

### 5b. Mandatory checkpoint (conversation → disk)

This is **not optional**. Once chapter N is locked into canon, the
conversation that wrote it becomes safe to discard — but only if
everything ephemeral has been persisted first. So you run a checkpoint
right here, as part of lock-in.

Follow the `checkpoint` skill's protocol:

```bash
python3 .claude/skills/checkpoint/scripts/checkpoint.py \
    --series-slug <slug> --book-number <N> --report
```

Then look back over the conversation for chapter N (and only this
chapter — earlier chapters are already checkpointed) and add to:

- **`notes/voice.md`** — any new POV / voice observation that came up
  while writing or critiquing this chapter. Date-stamp.
- **`notes/style-rules.md`** — any rule the **author** stated in chat
  during this chapter (not your inferences). Date-stamp.
- **`notes/open-questions.md`** — any thread that was discussed but
  not resolved during this chapter.

If nothing new accumulated, write nothing. Idempotent.

This step transforms the locked chapter into something the conversation
no longer needs to remember.

### 6. Report

Print to the user, in this exact order:

```
✓ Chapter N locked in. Mandatory checkpoint done.

- Summary: notes/summaries/ch-NN.md (X words)
- Seed statuses advanced: seed-id-1 → planted, seed-id-2 → echoed-1, ...
- Canon updated: characters.md, world.md, timeline.md
- Book summary: only "What just happened" touched (full synthesis is close-act's job).
- Checkpoint: M new entries (or "no new state to persist").

STANDARD: run /clear now, then `resume-act` before chapter N+1.
```

**`/clear` after every locked chapter is the project standard.** It keeps
each chapter's session cost flat and the context sharp, and lock-in just
ran the mandatory checkpoint (5b), so nothing is lost. Drop a sentinel so
the project's Stop hook reminds the author:

```bash
touch output/<series>/book-NN/notes/.clear-pending
```

The **last line of your report is the explicit signal** (the `STANDARD:
run /clear …` line). Do not add anything after it.

### 7. Act boundary → close-act

If chapter N is the last of an act-window (every 7 chapters by default,
`DEFAULT_CHAPTERS_PER_ACT` in `lib/summaries.py`), the next step is
**`close-act`** — the superset of the legacy `compress-act`. It folds the
act's chapter summaries into an act summary, consolidates voice,
**(re)builds the full `book-summary.md` synthesis**, and writes the
session handoff. In that case the final signal becomes:

```
✓ Act A complete. Run `close-act` now, then /clear before act A+1.
```

## What this skill does NOT do

- Does not write or modify chapter prose.
- Does not modify the visible outline (`plan/outline.md`) or the
  shadow (`plan/shadow.md`).
- Does not invent canon facts. Every promotion must trace to a line
  in the chapter.
