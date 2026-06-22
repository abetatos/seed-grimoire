---
name: resume-act
description: Single state-aware entry point for a fresh conversation. Reads bible / setup / canon / plan / session handoff / voice rules / style rules / open questions, reports the state, then acts as a DISPATCHER — it detects the lifecycle phase (setup → plan → critique-plan → write → done) and offers the recommended next skill as a confirm menu, delegating to book-setup / plan-book / critique-plan / write-novel. Invoke as `resume-act` or `resume <book>` as the FIRST step of every new session.
---

# resume-act

You are running the **resume-act** skill. This is a **fresh
conversation** — assume nothing was discussed before. Your only state
is the file system. Your job is to read it and report cleanly to the
author so the session can proceed.

This skill is what makes the per-act session pattern work. Every
ephemeral piece of context that would otherwise live in chat memory
has been persisted to disk by the previous session's `update-canon`
+ `close-act`. You re-hydrate from those files in seconds.

## When to invoke

- The author starts a new Claude Code session after a previous
  `/clear`.
- The author returns to the project after a pause.
- The author says "resume" / "continúa donde lo dejamos" /
  "resume-act" / "where are we?"
- **Always run this as the FIRST skill of a fresh session.** Even if
  the author thinks they remember where they left off, the agent
  does not.

## Hard rules

- **Do not assume conversation memory.** A fresh session has none.
  Read disk, report what you find. Don't apologize for not
  remembering — the design says you shouldn't.
- **Do not start writing a chapter inside this skill.** `write-chapter`
  is a separate invocation. Resume-act tells the author where they
  are; the author then says "write" or directs changes.
- **Surface open-questions explicitly.** If there are pendientes in
  `notes/open-questions.md`, they go in your report so the author
  can decide to address them before continuing.
- **Honour the session-handoff verbatim.** If `notes/session-handoff.md`
  has been filled by a prior `close-act`, treat its content as
  authoritative. Print it; do not summarise it.

## Steps

### 1. Run the helper

```bash
python3 .claude/skills/resume-act/scripts/resume_act.py \
    --series-slug <slug> --book-number <N>
```

This:
- Computes where in the book you are (last chapter written, next
  chapter to write, last act closed, next act).
- Prints the latest `session-handoff.md` content (if filled).
- Extracts stable voice rules from `voice.md`.
- Prints active style rules from `style-rules.md`.
- Lists pendientes from `open-questions.md`.
- Snips the "What just happened" section from `book-summary.md`.

The script's output is **already formatted as a report** suitable for
showing the author. You can pass it through to chat with minimal
reframing.

### 2. Sanity-check the disk state

After reading the report, do a quick consistency pass:

- Does the next chapter listed match what the outline expects to
  come next?
- Are there pendientes flagged that should block writing the next
  chapter? (E.g., a gating decision that surfaced in open-questions
  and was never resolved.)
- Is there a handoff but no act-summary for the act it claims to
  close? That suggests `close-act` was interrupted.

If anything looks off, raise it in your report. Otherwise, no action
needed.

### 3. Report state, then dispatch

First show the state, then read the **dispatcher marker** the script
prints on its last line:

```
<!-- DISPATCH phase=<phase> next=<skill> next_chapter=<n> blocked=<0|1> -->
```

`phase` is one of `setup | plan | critique-plan | write | done`. It tells
you which skill to recommend. The lifecycle is **linear**, and the
critiques are **mandatory gates**, never optional:

| phase           | recommended skill | what it does                                  |
|-----------------|-------------------|-----------------------------------------------|
| `setup`         | `book-setup`      | define the book (no usable setup.md yet)      |
| `plan`          | `plan-book`       | regenerate plan/ + initial canon from setup   |
| `critique-plan` | `critique-plan`   | **mandatory** audit before chapter 1          |
| `write`         | `write-novel`     | drive next chapter end-to-end, then `/clear`  |
| `done`          | —                 | book complete                                 |

Format your reply to chat as:

```
Resumed: <book title>, book <N>.

[paste resume_act.py output here]

Quick observations:
- [anything you noticed in the sanity check, or "all consistent"]
```

Then **present the menu with AskUserQuestion** — the recommended option
(from the marker's `next=`) first and labelled "(recommended)", plus the
sensible alternatives for that phase (e.g. in `write`: revise the plan
first; in `plan`: re-run book-setup). This is the "menú + confirmar"
contract: **one confirm**, recommendation surfaced, author stays in control.

### 4. Delegate to the chosen skill

On the author's choice, **invoke that skill** (book-setup / plan-book /
critique-plan / write-novel). Hard rules for delegation:

- **Honour the critique gates.** If phase is `critique-plan`, do not jump
  to writing — `critique-plan` runs first, ALWAYS. `write-novel`'s own
  chain runs `critique-chapter` on every chapter; it is not skippable.
- **Never skip a blocking pendiente.** If the marker has `blocked=1`,
  list the pendientes and resolve them before delegating into `write-novel`.
- **One step per turn.** Dispatch the single recommended step (or the
  author's pick). Do not autopilot across phases or across the `/clear`
  boundary — `write-novel` drives ONE chapter then hands back for `/clear`.
- **`write-novel` runs ONLY in a fresh conversation.** It is the most
  token-heavy step (full bundle + drafting), so it must start with a clean
  context. Therefore:
  - If you reached phase `write` **as the first action of a fresh session**
    (this resume-act is the first thing in the conversation, nothing else
    was run yet), you may delegate to `write-novel` directly.
  - If you reached phase `write` **after running an earlier step this turn**
    (book-setup / plan-book / critique-plan), do **NOT** chain into
    write-novel. STOP and emit the handoff: tell the author to run `/clear`
    and then `resume-act` again — the fresh session will land on `write`
    and drive the chapter cheaply.
- **Fast path.** If the author invoked you as `resume and write` /
  `continue` AND phase is `write` AND `blocked=0` AND this is a fresh
  session, you may skip the menu and delegate straight to `write-novel`.

## What this skill does NOT do

- Does NOT modify any file by itself (it is a pure reader + dispatcher;
  the file writes happen inside the skill it delegates to).
- Does NOT reimplement any skill — it only detects state and routes. The
  real logic stays single-sourced in book-setup / plan-book / critique-plan
  / write-novel.
- Does NOT replace `build_context.py`. The chapter writer still builds
  its own deterministic bundle when it's invoked.
- Does NOT autopilot or call `/clear` — it dispatches one step and the
  per-chapter `/clear` stays a manual user action.
