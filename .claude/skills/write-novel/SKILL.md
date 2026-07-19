---
name: write-novel
description: Top-level orchestrator that drives a book from a starting chapter through the end of the book, chaining plan-chapter (decision gate) → write-chapter (persistent chapter-smith subagent, kept alive and driven by SendMessage) → critique-chapter (book-critic, the sole grounding detector) → warm grounding fill / revise by the same live smith (chapter-grounder is the cold fallback) → update-canon → (close-act at act ends) for ONE chapter, then HARD STOPS for a `/clear` before the next chapter. The project standard is one chapter per session (state lives on disk; the next session rebuilds via resume-act). Use this when the user says "write the next chapter" / "drive chapter N" / "continue the book".
---

# write-novel

You are running the **write-novel** skill. You are the conductor of the
per-chapter pipeline. Each chapter goes through: **plan-chapter (decision
gate)** → **write (persistent chapter-smith subagent)** → **critique (book-critic,
sole grounding detector)** → **warm fill / revise by the same live smith** if the
critique calls for it → update-canon → (optional act compression).

You keep **one** `chapter-smith` alive for the whole chapter and drive it with
`SendMessage`: it pauses to ask the author when it hits an irreversible memory gap
(you relay via `AskUserQuestion`), and it applies the critique's fixes in its own
warm voice. It is released at lock-in. The cold `chapter-grounder` is only a
fallback for when there is no live smith (`--in-session`).

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
- **Stop on smell.** If you notice something that genuinely doesn't fit —
  an unmotivated beat, an arc inconsistency, a real contradiction — halt the
  loop and surface it, even if no skill flagged it. But calibrate severity
  honestly: halt on *genuine* trouble, not on taste. Manufacturing problems
  to look thorough is what keeps a chapter looping through revisions without
  converging. Surface real defects; let a clean chapter pass.
- **Honor the book length.** Stop at the chapter count declared in
  `setup.md`. Do not invent extra chapters.

## Inputs

- `--series-slug` (required)
- `--book-number` (required)
- `--from-chapter` (default: next unwritten chapter)
- `--through-chapter` (default: last chapter in setup.md)
- `--skip-critique` (flag; default off — only use when iterating fast)
- `--in-session` (flag; default off) — draft with `write-chapter` in this
  conversation instead of the default `chapter-smith` subagent. Escape hatch only
  (smith unavailable, or turn-by-turn steering); see step 2b.

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
`AskUserQuestion` choices with a recommendation each, and writes them to the
`## Decisiones` section of `notes/brief-chMM.md`. This is the interactive heart
of the pipeline — do not skip it. `write-chapter` (next) reads the brief as binding.

- If the author defers all forks to "use the recommendation", proceed.
- If a fork exposes a deeper plan problem (a beat that can't be triggered
  intrinsically, a reveal the outline forces too early), HARD STOP and
  surface it — that is a plan bug, not a writing choice.

#### 2b. Write

**Dispatch the draft to the `chapter-smith` subagent** (Agent tool,
`subagent_type: chapter-smith`, `run_in_background: true`) — do **not** draft in
this conversation, and **keep it alive**: the smith is a **persistent** agent you
drive across the whole chapter with `SendMessage`, not a one-shot. Do not spawn a
new smith later in the chapter — the same one carries its drafting context through
the critique's warm fixes (2d) and is released only at lock-in (2e). Prompt it with
exactly `chapter M --series-slug <slug> --book-number <N>`. It drafts in a
**fresh, clean context** — the ~26k bundle + the growing prose + the between-block
re-reads never enter this thread, and the draft is written well below the
attention-degradation zone, so the voice is truer, not just cheaper (the author's
blind-compare confirmed the gain, 2026-07-19 — chapter-smith is the default
writer).

It first returns one of two things:

- **`DRAFTING_PAUSED`** — it hit an **irreversible** memory gap it cannot derive
  from canon (a lived-memory detail that will bind later scenes) and needs the
  author. It saved the partial draft and returns a `QUESTIONS` block, each with a
  DEFAULT. **Surface those to the author with `AskUserQuestion`** (main thread,
  cheap — put the smith's DEFAULT first, labelled recommended), then **`SendMessage`
  the same smith `RESUME:` + the answers**. It continues from where it paused with
  its context intact. Loop until it returns the draft-complete hand-off. This is the
  ask-the-author channel a one-shot writer cannot have — it exists *because* the
  smith is persistent. (Reversible gaps never pause; they arrive as ASSUMPTIONS
  below.)
- **Draft-complete hand-off** (visible plot, PLANTED, INVENTED, ASSUMPTIONS,
  FLAGS).

On the hand-off:
- **FLAGS non-empty** (empty beat sheet, a beat unwritable from the plan) → HARD
  STOP and surface it; that is a plan bug, not a writing choice.
- **ASSUMPTIONS non-empty** → surface each to the author (these are the **reversible**
  gaps the smith wrote around — the irreversible ones already became pauses). If
  the author corrects one, `SendMessage` the fix to the live smith as `WARM-FIX:`
  so it applies it in its own voice (no cold `revise` while the smith is alive).
- Carry the PLANTED/INVENTED hand-off into 2f's summary — it is a hint that
  narrows `canon-scribe`'s hunt at lock-in, **not** a substitute for its
  verification.

> **Escape hatch.** If the smith is unavailable (no Agent tool) or the author
> wants to steer a draft turn-by-turn, `--in-session` runs `write-chapter`'s
> steps 1-4 in this conversation instead. It shares the identical SKILL.md, so the
> only difference is the (larger) context it drafts in — expect the voice to drift
> more on late chapters. With no persistent smith in this mode, emergent gaps are
> asked inline (you ARE the main thread) and the critique's fills fall back to the
> cold `chapter-grounder` (2d). Not the default.

#### 2c. Grounding is reactive — no unconditional pass
**Do NOT run a grounding pass here.** The raw draft goes **straight to the
critique** (2d). Grounding is split: **detection is the critique's job** (it
already runs the six need-tests — world unfolded, stage built, cost billed,
deliberation, re-orientation, secondary humanized — in a fresh context, and on
the *raw* draft they fire more often than they would on a pre-grounded one, which
is expected: same depth, moved from a pass that taxed every chapter to a reactive
path that only touches the ones that need it). **Fill is reactive** — only when
the critique names an unfired need-test does the grounder run (2d).

**There is deliberately NO word-count check** — do not count the chapter's
words, run `wc`, or compare its length to the setup range at any point
(a visible count breeds compensation: padding now, or "write more
generously" leaking into the next chapter's decisions). Length is settled
**structurally and only by the critique** (2d). Never self-trigger grounding
from length.

#### 2d. Critique + reactive grounding (unless `--skip-critique`)
**Dispatch the critique to the `book-critic` subagent** (Agent tool,
`subagent_type: book-critic`) — do **not** run critique-chapter in this
conversation. The subagent audits in a **fresh context**: it never saw how the
chapter was written, so the critique can't rationalise the prose, and you don't
have to `/clear` to get a clean read. Prompt it with exactly:
`chapter M --series-slug <slug> --book-number <N>`.

It writes `notes/critique-chMM.md` and returns the verdict + issue counts +
load-bearing findings. **First, act on any grounding the critique names**, then
on the verdict. The **detector is always the fresh `book-critic`** (no curse of
authorship — it never saw the draft written); the **fill is warm**, applied by the
still-alive `chapter-smith` in its own voice:

- **Unfired need-test / uncovered grounding** (the critique names a need-test
  that fired with no insert) → **`SendMessage` the live smith `WARM-FIX:` + the
  named spots** (quote the critic's lines). It fills ONLY those spots, marks its
  zones `EXPAND`, and returns what it inserted, in the same voice it drafted in.
  This is Movement 3's fill made **warm, not cold** — safe because the critic, not
  the smith, did the detecting. Hard cap **2 warm-fill rounds** per chapter. Then
  re-dispatch book-critic once.
  - *Fallback (no live smith — `--in-session`, or the smith already released):*
    **dispatch the cold `chapter-grounder` subagent** (Agent tool,
    `subagent_type: chapter-grounder`, prompt
    `chapter M --series-slug <slug> --book-number <N>`), same 2-pass cap. It fills
    the named spots in a fresh context — correct but colder-voiced than the smith.
- **Collapsed beat** (`[beat-collapsed]`: events narrated as pre-digested summary
  instead of a played scene) → **replay that scene via the live smith**
  (`SendMessage WARM-FIX:` naming the beat to re-play as a scene) — **never a
  grounding insert**: inserts on top of a summary are padding stapled over a hole.
  (Fallback with no live smith: `write-chapter` replay or `revise-chapter` surgery.)
- **Texture that passes no need test** (generic lingering) → `SendMessage` the
  live smith `WARM-FIX:` to trim it (fallback: `revise-chapter --mode trim`) —
  trim the padding, not the grounding the critique asked for.

Then the verdict:

- PASS → continue to 2e.
- REVISE → **`SendMessage` the live smith `WARM-FIX:` + the REVISE findings**
  (it fixes in its warm voice; fallback with no live smith: `revise-chapter
  --mode polish` in this conversation), then **re-dispatch book-critic once**. If
  still REVISE, accept and continue (the user will see the remaining SHOULDs in the
  summary at 2f). If a returned finding is a judgment call the author confirms is
  intentional, lock it into `notes/brief-chMM.md` (a `### Critic findings
  adjudicated as intentional` heading inside `## Decisiones`) before re-dispatching
  — the fresh critic honors that file and won't re-raise it, which is what keeps
  the re-critique from re-litigating settled choices. **Do not exceed this one
  revise→re-critique cycle** chasing residual SHOULD/taste findings.
- REJECT → HARD STOP. Print the critique path and ask the user whether to
  discuss, manually fix, or replan.

#### 2e. Lock in
**Release the smith first.** The chapter's prose is settled once 2d passes, so the
`chapter-smith` has no more work — `SendMessage` it `RELEASE` (or simply stop
messaging it; it dies at lock-in either way). Everything downstream reads the
finished `chapters/MM.md` from disk; the smith's live context is not needed and
must not leak into lock-in.

Then invoke `update-canon` for chapter M. Its **disk-heavy analysis + writes (steps
1-4: chapter summary, seed/truth advances, canon promotion) self-dispatch to the
`canon-scribe` subagent** — just like 2d's critique goes to `book-critic` — so the
≈18k words of chapter prose + canon + seeds + shadow never enter this
conversation. You don't dispatch it yourself; `update-canon`'s step 0 does, then
runs only its cheap main-thread tail here: acting on any subagent FLAGS, and a
**mandatory checkpoint sub-step** that persists ephemeral conversation state
(voice observations, author-declared style rules, open threads) to disk. After it
runs:

- If it reports a seed missed or a canon contradiction → HARD STOP.
- Otherwise it ends with the explicit signal `STANDARD: run /clear now,
  then resume-act before chapter M+1`. Carry that signal through to the
  per-chapter summary in 2f.

#### 2f. HARD STOP for /clear
Capture the Phase-0 baseline first — one line, before the summary:

```bash
python3 scripts/token_report.py
```

It attributes this session's tokens per phase and flags the two fixed
thresholds (main-thread context ceiling, per-chapter output target). Note the
peak-context and total-output figures in the carry-forward so 3-4 chapters of
baseline accumulate for the IMPROVEMENT-PLAN decisions — do **not** act on the
numbers now, just record them.

Print a per-chapter summary:
- Chapter M, title.
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
