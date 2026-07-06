---
name: update-canon
description: Lock a finished chapter into the book's state. Writes the chapter summary, updates seed statuses, promotes any new facts from the chapter into canon (characters/factions/magic/world/timeline), and refreshes the rolling book-summary. Use this AFTER `critique-chapter` says PASS (or the user approves). Refuses to run if the chapter file is missing.
---

# update-canon

You are running the **update-canon** skill. The chapter is accepted.
Your job is to fold it into the book's running state so future chapters
have an accurate picture without re-reading prose.

> **The disk-heavy work runs headless.** Steps 1-4 read ≈18k words (chapter
> prose + all canon + `seeds.md` + `shadow.md`) and run in the **`canon-scribe`
> subagent** (a fresh context) so none of those file dumps land in this
> conversation — see step 0 for the dispatch, what stays in the main thread,
> and what to do when you ARE the subagent.

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

### 0. Pre-lock delta check, then dispatch the disk work (main thread only)

This step runs in the main thread. It does the one cheap conversation-aware gate,
then hands the ≈18k words of reads + the deterministic writes to a fresh subagent.

#### 0a. Pre-lock delta check (before any write)

Lock-in makes the chapter load-bearing for everything after it, so it
gets one last gate — but `critique-chapter` just validated the prose
against shadow / canon / seeds / arcs / grimoire. **Do not re-run that whole
pass.** Only check the delta:

- If `critique-chapter` ran and returned PASS (or the author accepted it),
  confirm nothing changed since (no edit to the chapter, canon, or shadow
  after the critique). If untouched, say "pre-lock check clean — proceeding"
  and continue.
- If critique was **skipped** (`--skip-critique`) or the chapter was edited
  after it, run the consistency pass yourself now: chapter vs shadow (no
  leak), vs canon (no contradiction), vs seeds (every scheduled seed actually
  present), vs grimoire, vs arc waypoints.

If anything surfaces, **stop and let the author decide** before writing any
file — the cost of locking in a contradiction is paid in every future chapter.

#### 0b. Dispatch steps 1-4 to the `canon-scribe` subagent

If you can spawn subagents (you have the Agent tool) and you were invoked
standalone (not already inside `canon-scribe`), **do not do the reads or writes of
steps 1-4 in this conversation.** Dispatch them to the `canon-scribe` subagent
(Agent tool, `subagent_type: canon-scribe`) with the prompt exactly:
`chapter <M> --series-slug <slug> --book-number <N>`.

It reads the chapter + canon + seeds + shadow in a **fresh context**, writes
`summaries/ch-MM.md`, advances every **unambiguous** seed/truth status (with its
`Realized` / `surfaced` line), promotes additive canon facts, and returns a compact
delta plus a **FLAGS** block. None of those file dumps enter this conversation.

Then, in the main thread:

1. Read the subagent's return. If `FLAGS: none`, go straight to step 5.
2. If there are FLAGS, each is a HARD STOP the subagent deliberately left unwritten
   — a scheduled seed absent (3a), an unscheduled touch (3b), a truth over its cap
   (3.5), a canon contradiction, or canon silent on a new fact (4). **Surface each
   to the author** and apply their decision. The two outcomes per case are spelled
   out in steps 3a/3b/3.5/4 below; apply the chosen one with the surgical script
   (`mark_seed.py` / `mark_truth.py`) or a single canon Edit — you do **not**
   re-read the whole chapter to do it. Do not silently resolve or silently ignore.
3. Then continue with steps 5, 5b, 6 (all cheap, and 5b needs this conversation).

> When the **`canon-scribe` subagent itself** runs this skill it has no Agent tool,
> so it cannot dispatch — it executes steps 1-4 directly, applies only unambiguous
> advances, collects HARD STOPs as FLAGS, and stops before step 5. `write-novel`
> likewise dispatches this skill itself at lock-in, so when it chains the skill the
> work is already in the subagent — don't re-dispatch. Steps 1-4 below are written
> for whoever executes them (you-as-subagent, or the main thread if no Agent tool).

### 1. Prepare the skeletons and read what's due

First, run the deterministic auditor over current book state:

```bash
python3 scripts/lint_book.py --series-slug <slug> --book-number <N>
```

Any `ERROR` (a dropped seed token, a dangling `Revealed-by`, an out-of-range
schedule, a prior chapter locked without a summary) is a **FLAG** — do not write
anything; collect it for the author (steps 3a/3b/4). Lock-in must not compound an
existing breach.

Then prepare the summary skeleton:

```bash
python3 .claude/skills/update-canon/scripts/prepare_summary.py \
    --series-slug <slug> --book-number <N> --chapter <M>
```

This:
- **Verifies the chapter hash** the critique recorded (T12): if the chapter was
  edited after it was critiqued, it exits non-zero — **stop and re-audit** (or
  re-run the consistency pass) before locking in a chapter no critic has seen.
- Writes `summaries/ch-MM.md` skeleton (with the seed envelope embedded)
- Prints the seed envelope for this chapter and current statuses
- Lists the canon files to inspect

If the script warns that the chapter is too short, **stop**. Tell the
user the chapter isn't ready to lock in. (`--force` overrides the hash check
only when you have deliberately accepted the post-critique edit.)

Once the hash check has passed, strip the expand-chapter banners — this IS the
"later cleanup pass" the EXPAND markers promise, and lock-in is their last
useful moment (the critique already ran against them). It must run AFTER
`prepare_summary.py`: the T12 hash is over the raw file bytes, so stripping
first would trip the check.

```bash
python3 scripts/strip_expand_markers.py \
    --series-slug <slug> --book-number <N> --chapter <M>
```

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
- **Anchor quotes (verbatim)** — copy 2-3 EXACT lines from the chapter into
  «…»: the strongest seed-touch line, the end-state line, one voice-defining
  line. The page's own words, kept so a payoff many chapters later can rhyme
  with what was actually written after the prose has left context. Never
  paraphrase — `lint_book.py` verifies each anchor against the chapter and
  ERRORs a paraphrase.
- **Canon updates required** — the new facts the chapter introduced that
  should be promoted (step 4). Run an explicit **durable-trait sweep** here,
  because prose hides identifying detail inside emotional beats: for every
  **named** character (or named place/object) that appeared, scan the prose
  for any *immutable physical or identifying trait* the chapter committed to
  — build, height, hair/eye, scars, voice, age, gait, a defining mannerism or
  possession. A trait counts even when delivered obliquely (e.g. "the apron
  came down big on him because his father was a narrow man" states the
  father's build). If not already in canon, list it. Skip one-off mood/state
  details (those belong in the summary, not canon); capture only what a
  future chapter could **contradict**.
- **Carry forward** — 1-3 lines: at chapter end, who is where, in what
  state, what is left hanging into the next chapter.

Word target: 400-500 words is the guide, not a gate — a dense chapter may run
longer. Maximum signal per token; don't pad, don't truncate something
load-bearing to hit a number:

- It is a **state delta**, not a recap. Record what *changed* and what carries
  forward — skip blow-by-blow narration the future writer doesn't need.
- **Do not duplicate what other context already carries.** Facts promoted to
  canon, seed touches (in the seed envelope), and hidden-truth movement (shadow)
  are loaded separately — reference them, don't re-narrate them here.
- Prefer terse bullets over prose paragraphs; cut adjectives and scene-setting.

### 3. Advance seed statuses AND log how each seed actually landed

This is the weak link of the pipeline: a seed gets planted/echoed in the
prose but its status never advances or its `Realized` line never gets
written, so a payoff 20 chapters later can't rhyme with what actually
landed. **Do not re-derive loosely from memory.** Work it as a forcing
function — a line-by-line reconciliation of the schedule against the prose,
in **both** directions.

The status ladder: `planned` → `planted` → `echoed-1` → `echoed-2` → … →
`paid_off`. A seed planted this chapter → `planted`; one already
`planted`/`echoed-K` and echoed again → `echoed-(K+1)` (first echo →
`echoed-1`); one paid off → `paid_off`.

#### 3a. Each scheduled seed: confirm against the prose, then mark

The seed envelope printed by `prepare_summary.py` lists every seed whose
`Plant in` / `Echo in` / `Payoff in` equals this chapter. **For each one**,
open `chapters/MM.md` and find the actual sentence that carries it. Two
outcomes only:

- **Present** → quote the line to yourself, then advance status AND write
  the `Realized` touch-log from *that line* — the concrete image **AS
  WRITTEN**, ~12 words, prefixed with the chapter (not a paraphrase of the
  plan's `How to plant`; the page is the source of truth). Payoffs that
  fully discharge a seed need no realized line.
- **Absent** → do **NOT** advance status or log it. This is a contract
  violation. **Stop and tell the user** — the chapter is missing a
  scheduled seed and either the chapter or the `seeds.md` schedule must change.

Run, once per present seed (status and realized in one surgical call):

```bash
python3 .claude/skills/update-canon/scripts/mark_seed.py \
    --series-slug <slug> --book-number <N> \
    --seed-id <id> --status <new_status> \
    --realized "ch<M>: <the concrete image AS WRITTEN, ~12 words>"
```

(`--realized` alone is valid too, if status doesn't change.) The realized
log lives in `plan/seeds.md` (NEVER compressed) and is surfaced in the seed
envelope of every later echo/payoff.

#### 3b. Reverse sweep: seeds touched but NOT scheduled here

The envelope only knows the *plan*. `write-chapter` and `expand-chapter`
routinely echo an emotional through-line (e.g. a recurring physical
sensation) wherever it fits, even in a chapter where `seeds.md` didn't
schedule it — and those touches silently never get logged. So do the
reverse check too: scan `chapters/MM.md` for any seed image **not** in this
chapter's envelope (use the `Detail` / `Resolution image` field of each seed
in `plan/seeds.md` as the lookup; the bundle already lists them). For any
hit:

- **Stop and tell the user**, naming the seed and quoting the line. It is
  either (a) a real, valuable opportunistic echo — then advance its status,
  write the `Realized` line, **and** add this chapter to its `Echo in` in
  `plan/seeds.md` so the schedule matches reality; or (b) an accidental
  re-description that dilutes the dose — then it should be trimmed in the
  prose. **The author decides which.** Do not silently log or silently ignore.

#### 3c. Report what moved

In the step-6 report, list every status change AND every `Realized` line
written, plus any reverse-sweep flag raised. If a scheduled seed was absent
or an unscheduled touch was found, that is a HARD STOP for the author, not a
footnote.

### 3.5. Advance shadow-truth reveal state (reader knowledge)

A shadow truth stops being a shadow as the **reader** is brought toward it.
`plan/shadow.md` carries `## SHADOW-TRUTH` records whose `Status` rides the
ladder **`hidden → sensed → suspected → confirmed`** — the reader's interior
state, *not* how loudly the page states it (`suspected` is still reached by
accumulation, never by a line that says the truth). Each truth's schedule lives
in its **carrier seeds** (`Revealed-by:`), so you do not re-schedule here; you
record how far this chapter actually moved the reader.

For each truth whose `Revealed-by` seed you advanced in step 3:

- Judge, from the prose, how far the chapter brought the **reader** toward that
  truth. `derive_status` gives a mechanical ceiling from the seed statuses, but
  it is only a **ceiling suggestion** — a planted seed does not always make the
  reader *sense* the hidden truth (a bureaucratic signature does not make the
  reader suspect betrayal). Pick the real level by reading the page, never above
  what the chapter earned.
- Advance the status and log how the reveal landed, in one surgical call:

```bash
python3 .claude/skills/update-canon/scripts/mark_truth.py \
    --series-slug <slug> --book-number <N> \
    --truth-id <id> --status <new_status> \
    --surfaced "ch<M> [<level>]: <how the reader was brought, AS WRITTEN, ~12 words>"
```

- The script **refuses any status above the truth's `Reveal cap`** — the loudest
  it may sound in this book (truths paying off in a later book cap below
  `confirmed`). If you hit that wall, do not raise the cap to force it: the
  chapter is over-telegraphing a truth meant to stay quiet. **Stop and tell the
  user.** An over-cap push is a HARD STOP (over-reveal), not a footnote.
- Seedless truths (exposition, no `Revealed-by`) advance against their manual
  `Confirm in:` — same judgment, same cap.

### 4. Promote facts to canon

Walk the `Canon updates required` section of the summary you just
wrote. For each item:

- **canon/characters.md** — new minor characters, current emotional
  state changes, current location updates, new relationships, and any
  **immutable trait** from the durable-trait sweep (step 2), even for
  offstage or dead characters who live only in backstory — a future
  flashback can still contradict them. Record the trait once, tersely,
  next to the character's name.
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
only its `## What just happened` section. The full synthesis is **rebuilt
at act boundaries by `close-act`** and finalized at book end; the
per-chapter record already lives in `summaries/ch-NN.md`. So do only the
cheap thing:

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
everything ephemeral has been persisted first. Follow the `checkpoint`
skill's protocol:

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

### 6. Report

Print to the user, in this exact order:

```
✓ Chapter N locked in. Mandatory checkpoint done.

- Summary: notes/summaries/ch-NN.md (X words)
- Seed statuses advanced: seed-id-1 → planted, seed-id-2 → echoed-1, ...
- Realized logged: seed-id-1 ("ch N: <image as written>"), ...
- Seed flags: <scheduled-but-absent / unscheduled-touch found, or "none">
- Truth reveals: truth-id → sensed, ... (or "none"; flag any over-cap HARD STOP)
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
**`close-act`**. It folds the act's chapter summaries into an act summary,
consolidates voice, **(re)builds the full `book-summary.md` synthesis**, and
writes the session handoff. In that case the final signal becomes:

```
✓ Act A complete. Run `close-act` now, then /clear before act A+1.
```

## What this skill does NOT do

- Does not write or modify chapter prose.
- Does not modify the visible outline (`plan/outline.md`) or the
  shadow (`plan/shadow.md`).
- Does not invent canon facts. Every promotion must trace to a line
  in the chapter.
