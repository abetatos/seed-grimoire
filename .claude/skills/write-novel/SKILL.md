---
name: write-novel
description: Top-level orchestrator that drives a book from a starting chapter through the end of the book, chaining plan-chapter (decision gate) → write-chapter → expand-chapter (always, texture pass) → critique-chapter → (revise/expand if needed) → update-canon → (close-act at act ends) for ONE chapter, then HARD STOPS for a `/clear` before the next chapter. The project standard is one chapter per session (state lives on disk; the next session rebuilds via resume-act). Use this when the user says "write the next chapter" / "drive chapter N" / "continue the book".
---

# write-novel

You are running the **write-novel** skill. You are the conductor of the
per-chapter pipeline. Each chapter goes through: **plan-chapter (decision
gate)** → write → **expand (always — texture pass)** → critique →
(fix if needed) → update-canon → (optional act compression).

## Design philosophy

Interactive, not autonomous. You are a critical collaborator, not a chapter
shipper. Three operating principles:

- **Halt at any sign of trouble**, not just contract violations — an
  unmotivated beat, a telegraphed seed, an arc inconsistency, a grimoire
  contradiction. Pause and report even if no rule is technically broken.
- **Treat the plan as mutable.** The author may edit `setup.md`, `plan/*`,
  `canon/*` or the grimoire mid-pipeline. After any edit, rebuild context
  (`build_context.py` is idempotent) and re-check before continuing.
- **One chapter per session, then `/clear`.** No cross-chapter autopilot:
  drive one chapter end-to-end, HARD STOP with the `/clear` signal, let the
  next session rebuild from disk via `resume-act`. (`/clear` is a manual user
  action, so unattended multi-chapter runs are impossible by design.)

## When to invoke

- "Write the book." / "Drive chapters 1 to N." / "Keep writing until
  chapter K." / "Continue from chapter X."

## Hard rules

- **One chapter per session, then HARD STOP for `/clear`.** After a
  chapter is locked in (`update-canon`), print the summary and STOP with
  the `/clear` + `resume-act` signal. Do **not** start chapter M+1 in the
  same conversation — `/clear` between chapters is the project standard.
- **One chapter at a time.** Do not parallelize. Each chapter depends
  on the canon update of the previous one.
- **Stop on any rejection.** If `critique-chapter` returns REJECT,
  stop unconditionally and surface it. The user must decide.
- **Stop on contract drift.** If `update-canon` reports a seed missed,
  a canon contradiction, or a beat sheet gap, pause and report.
- **Stop on smell.** If you notice anything that doesn't fit — even
  if no skill flagged it — halt the loop and surface it. The
  adversarial bias is at the orchestrator level too. Over-flag,
  never under-flag.
- **Honor the book length.** Stop at the chapter count declared in
  `setup.md`. Do not invent extra chapters.

## Inputs

- `--series-slug` (required)
- `--book-number` (required)
- `--from-chapter` (default: next unwritten chapter)
- `--through-chapter` (default: last chapter in setup.md)
- `--skip-critique` (flag; default off — only use when iterating fast)

## Steps

### 1. Discover where to start

If `--from-chapter` was not given, run:

```bash
ls output/<series>/book-<NN>/chapters/
```

Take the highest written chapter + 1. If none, start at 1.

If `--through-chapter` was not given, read `num_chapters` from
`setup.md` and use that.

Print the chapter being driven and the standard (one chapter, then /clear).
Even if a range was given, drive only the first unwritten chapter in it,
then stop for /clear.

### 2. Per-chapter loop

For each chapter M in the range, run this pipeline in order. **Stop
the entire loop on any HARD STOP condition.**

#### 2a. Sanity check
- `setup.md` exists.
- `plan/outline.md` has a non-empty beat sheet for chapter M.
  - If empty → HARD STOP. Ask the user to fill the beat sheet
    (or run `plan-book` again).
- Previous chapter is locked into canon (its `summaries/ch-(M-1).md`
  exists and has no TODO).
  - If not → HARD STOP. Ask the user to finish `update-canon` for
    the previous chapter first.

#### 2b'. Decision gate (BEFORE writing)
Invoke the `plan-chapter` skill for chapter M **first**. It builds the
briefing, surfaces the 2-4 underdetermined creative forks (event triggers,
exposure/witnesses, which planted image a payoff resolves) as
`AskUserQuestion` choices with a recommendation each, and writes the answers
to `notes/decisions-chMM.md`. This is the interactive heart of the pipeline —
do not skip it. `write-chapter` (next) reads those decisions as binding.

- If the author defers all forks to "use the recommendation", proceed.
- If a fork exposes a deeper plan problem (a beat that can't be triggered
  intrinsically, a reveal the outline forces too early), HARD STOP and
  surface it — that is a plan bug, not a writing choice.

#### 2b. Write
Invoke the `write-chapter` skill for chapter M. It will:
- Build the context bundle.
- Refuse if the beat sheet is empty (already checked).
- Produce `chapters/MM.md`.
- Run `check_wordcount`.

#### 2c. Texture pass + word count
**Always invoke `expand-chapter` once** for chapter M, regardless of the
word count `write-chapter` reported. This first pass is a deliberate
texture pass: the author wants the added dwellings/sensory paragraphs
even when the chapter is already at length — they give the prose texture.
It marks its zones `EXPAND 1`.

Then re-check `check_wordcount.py` and act on the **post-expand** count:

- If still too short → invoke `expand-chapter` again (pass 2, the cap).
  If it is *still* short after pass 2, accept it and continue — a lean
  chapter is fine; do not pad to force the floor.
- If now too long → invoke `revise-chapter --mode trim` for chapter M.
  Trim connective/hinge prose, not the `EXPAND 1` texture the author
  asked for.
- If on target → continue.

#### 2d. Critique (unless `--skip-critique`)
**Dispatch the critique to the `book-critic` subagent** (Agent tool,
`subagent_type: book-critic`) — do **not** run critique-chapter in this
conversation. The subagent audits in a **fresh context**: it never saw how the
chapter was written, so the critique can't rationalise the prose, and you don't
have to `/clear` to get a clean read. Prompt it with exactly:
`chapter M --series-slug <slug> --book-number <N>`.

It writes `notes/critique-chMM.md` and returns the verdict + issue counts +
load-bearing findings. Act on the **returned verdict**:

- PASS → continue to 2e.
- REVISE → invoke `revise-chapter --mode polish` **in this conversation** (it
  edits prose, so it belongs in the main thread), then **re-dispatch
  book-critic once**. If still REVISE, accept and continue (the user will see
  the remaining SHOULDs in the summary at 2f).
- REJECT → HARD STOP. Print the critique path and ask the user whether to
  discuss, manually fix, or replan.

#### 2e. Lock in
Invoke `update-canon` for chapter M. This now **includes a mandatory
checkpoint sub-step** that persists any ephemeral conversation state
(voice observations, author-declared style rules, open threads) to
disk. After it runs:

- If it reports a seed missed or a canon contradiction → HARD STOP.
- Otherwise it ends with the explicit signal `STANDARD: run /clear now,
  then resume-act before chapter M+1`. Carry that signal through to the
  per-chapter summary in 2f.

#### 2f. HARD STOP for /clear
Print a per-chapter summary:
- Chapter M, title, final word count.
- Verdict from critique.
- Seeds advanced (ids and new statuses).
- Canon files touched.
- One-line carry-forward.
- **Clear signal:** mirror what update-canon said.

Then **STOP unconditionally.** This is the per-chapter `/clear` boundary —
the project standard. Tell the user, as the last lines:

```
STANDARD: run /clear now, then `resume-act` before chapter M+1.
```

Do **not** offer "type continue", and do **not** start chapter M+1 in this
conversation. The next chapter is a fresh session: `/clear` → `resume-act`
→ (which can chain straight into the next `write-chapter`). All state is on
disk, so nothing is lost. If chapter M is the last of an act-window, go to
2g (close-act) *before* the /clear signal.

#### 2g. Close act (at act boundaries)
If chapter M is the last chapter of an act-window (every 7 by default;
match `lib/summaries.py::DEFAULT_CHAPTERS_PER_ACT`), invoke `close-act`
for that act. Besides bundling chapter summaries into an act summary, it
stabilises voice rules into `voice.md`, **(re)builds the full
`book-summary.md` synthesis** (which update-canon no longer does per
chapter), and writes the `session-handoff.md` that the next session
reads first.

After close-act, **STOP** (same per-chapter rule — this is just a heavier
boundary). Tell the user:

```
✓ Act N closed. STANDARD: run /clear now, then `resume-act` for act N+1.
```

### 3. End-of-book handling

When you reach the last chapter (per setup.md):

1. Run the per-chapter pipeline as above.
2. After `update-canon`, refresh the book summary with the final state.
3. If this is part of a series, prompt the user to update
   `series-state.md` with the threads the next book inherits.
4. Print a closing summary: total chapters, total words, total seeds
   planted/paid, any seeds still unpaid (which is a contract bug — the
   user must decide whether to add a payoff scene or drop the seed
   from `plan/seeds.md`).
5. Suggest next: `book-setup` for book N+1 (in a series) or done.

## What this skill does NOT do

- Does not write prose itself — it invokes `write-chapter`.
- Does not modify the plan or shadow.
- Does not skip critique unless explicitly asked.
- Does not parallelize chapter writing — each chapter's canon update
  feeds the next.
