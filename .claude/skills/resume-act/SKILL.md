---
name: resume-act
description: Bootstrap a fresh conversation at the start of a new act (or at any reentry to a book). Reads bible / setup / canon / plan / session handoff / voice rules / style rules / open questions and reports the state so the agent and author can continue without conversation history. Invoke as `resume-act` or `resume <book>` as the FIRST step of every new session.
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

### 3. Report to the author

Format your reply to chat as:

```
Resumed: <book title>, book <N>.

[paste resume_act.py output here]

Quick observations:
- [anything you noticed in the sanity check, or "all consistent"]

What next?
- **Ready to write chapter <next>.** Reply `write` (or `continue`) and I
  drive it end-to-end (write → critique → revise → update-canon), then
  stop for `/clear`.
- If there are blocking pendientes (open-questions that gate the next
  chapter), I list them first and wait — those take priority.
- If you want to revise the plan before writing, say so and we go
  to the plan files.
```

Because the project standard is **one chapter per session + `/clear`**,
resume-act is the single entry point each session: it bootstraps from
disk and then hands straight to the chapter. Keep it to **one confirm**.

### 4. Standby (or proceed on explicit go)

After reporting, **wait for the author's go**. If they invoked you as
plain `resume-act`, wait for `write`/`continue` before loading the bundle.
If they invoked you as `resume and write` / `continue` (an explicit intent
to proceed) **and** no blocking pendiente is flagged, you may chain
directly into `write-chapter <next>` without a second prompt. Never skip a
blocking open-question to start writing.

## What this skill does NOT do

- Reports state first; only chains into `write-chapter` on an explicit
  `write`/`continue` go and when no blocking pendiente is flagged.
- Does NOT modify any file by itself (it is a pure reader until it hands
  off to `write-chapter`).
- Does NOT replace `build_context.py`. The chapter writer still builds
  its own deterministic bundle when it's invoked.
- Does NOT call `/clear` — by the time you're running this, the
  session is already clean.
