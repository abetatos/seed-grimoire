---
name: checkpoint
description: "The session-CLOSE bookend to The Lodestar (resume-act). Where The Lodestar opens a session by READING disk, checkpoint closes one by WRITING the ephemeral chat state back to disk before the user runs `/clear` or `/compact`. Captures voice/POV observations and author-declared style rules to `notes/voice.md` / `notes/style-rules.md`, and any unresolved carry thread to the in-progress chapter's brief `## Arrastre`. Idempotent. Invoke as `checkpoint` when the user wants to compact or clear mid-chapter, or whenever the chat has accumulated decisions/observations that aren't yet on disk. (update-canon and close-act persist at lock-in / act boundaries; checkpoint covers the mid-chapter gap they don't.)"
---

# checkpoint — the session-close bookend

You are running the **checkpoint** skill — the **write-half bookend** to
`resume-act` (*The Lodestar*): The Lodestar opens a session by reading disk;
checkpoint closes one by writing the chat's **ephemeral knowledge** (things only
in chat, not yet in any file) back to disk before the user runs `/clear` or
`/compact`.

It is **not redundant** with the lock-in skills: `update-canon` persists at a
chapter's lock-in and `close-act` at an act boundary, but a mid-chapter `/clear`
(the author stops partway) falls between them — checkpoint is what saves the
voice observations and carry threads in that gap. Narrow, but the only thing
covering it.

After this skill runs, the conversation is **safe to clear**. Nothing
load-bearing for future chapters is lost when the chat is discarded.

## When to invoke

- The user says "checkpoint" / "sync state" / "save before compact".
- Before the user runs `/compact` (the user can invoke this skill first
  to guarantee no loss).
- Whenever you (the agent) notice the conversation has accumulated
  voice observations, style decisions, or open threads that haven't
  been written down.
- Automatically as a sub-step of `update-canon` (chapter lock-in).

## Hard rules

- **Idempotent.** If nothing new has accumulated since the last
  checkpoint, do not write garbage to the files. Say so and finish.
- **Only persist what's truly ephemeral.** Plot decisions belong in
  `setup.md`. Canon facts belong in `canon/*`. Seeds belong in
  `plan/seeds.md`. This skill captures only:
  - Voice / POV observations (how a character sounds in prose).
  - Style rules the **author** stated (not your inferences).
  - Open discussion threads that didn't resolve.
- **Do not invent observations.** Only persist what was actually said
  or actually noticed. If you didn't make a clear observation about
  Yedra's voice, do not invent one to look thorough.
- **Append, do not overwrite.** Append entries to existing sections,
  do not rewrite the whole file. Date-stamp each new entry.

## Steps

### 1. Ensure files exist and review what's there

```bash
python3 .claude/skills/checkpoint/scripts/checkpoint.py \
    --series-slug <slug> --book-number <N> --report
```

This creates `notes/voice.md` and `notes/style-rules.md` if absent
(idempotent — never overwrites existing content), and prints the current
content of each so you can see what's already captured. The date stamp for new entries is printed
at the end.

### 2. Scan the conversation for ephemeral knowledge

Walk back through what's happened in this conversation. Look for, in
this order:

#### 2a. Voice / POV observations
Any concrete observation about how a POV character sounds in prose
that came up while you were writing. Examples:

- "Bruno tends to use verbs of labor (clavar, doblar) where I'd
  default to thinking verbs."
- "Vela's interior monologue should stay shorter than Bruno's — she's
  not a ruminating character."
- "Avoid the phrase 'a ojos vista' — used twice already, becoming a tic."

If you have these, append them to the appropriate `## POV: <name>`
section of `voice.md` (create the section if absent), or to the
`## Recurring patterns to watch / avoid` section. Date-stamp:
`- (YYYY-MM-DD, ch N) observation text`.

#### 2b. Author-declared style rules
Statements the **author** made in chat that prescribe how prose should
be written. Examples:

- Author said: "menos monólogo interior" → rule.
- Author said: "no describas cosas bonitas porque sí" → rule.
- Author said: "Bruno habla con frases cortas" → rule (also fits voice.md).

Do NOT include your own inferences. Only what the author explicitly
stated. Append to the `## Unfolded` section of `style-rules.md` (the
capture buffer that `close-act` folds into `style.md`). Date-stamp.
Process rules (word count, expand) belong to the skills, not here.

#### 2c. Carry threads / unresolved forks
Things that came up in conversation but weren't resolved and must reach a
later chapter. Examples:

- "Author wanted to revisit the cap 5 transition once cap 4 is done."
- "Question about whether Yedra's lost relative is hermana or hija."

Append to the in-progress chapter's brief `## Arrastre`
(`notes/brief-chNN.md`) with context — plan-chapter for the next chapter
carries it forward and closes it (hard-close rule). A **tooling** bug goes to
`TODO.md` instead, never to the brief. If no brief exists yet (pre-gate), park
it in `session-handoff.md`'s `## Hilos abiertos`.

### 3. If nothing new, say so

If after the scan you have no new entries to add, **do not write to
any file**. Print:

```
✓ Checkpoint complete — no new ephemeral state to persist.
  Safe to /compact or /clear.
```

### 4. If you added entries, summarize what you wrote

Print, in this format:

```
✓ Checkpoint complete.

Added:
- voice.md: 2 entries (POV: Bruno, recurring patterns)
- style-rules.md: 1 entry (General)
- brief-ch04.md: 1 hilo en `## Arrastre`

Safe to /compact or /clear.
```

### 5. Final signal

End the response with the explicit signal:

```
Safe to /compact or /clear.
```

This tells the author the conversation can be discarded without loss.

## What this skill does NOT do

- Does not modify `setup.md`, `canon/*`, `plan/*`, or chapter files.
- Does not extract plot, character, or world facts (those belong in
  canon and setup).
- Does not run `/clear` or `/compact` — those are user-level commands
  that **only the user can execute**. The skill prepares for them;
  the user triggers them.
- Does not consolidate or stabilize the notes files. That's
  `close-act`'s job at the end of each act.
