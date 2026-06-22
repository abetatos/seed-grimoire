---
name: close-act
description: End-of-act sync. Closes an act by compressing its chapter summaries into one act summary (replacing compress-act), consolidating voice.md observations into stable rules, and writing session-handoff.md so the next session bootstraps cleanly. Always followed by an explicit `STRONGLY recommended: /clear` signal. Use this when the last chapter of an act has been locked in via update-canon and the user is ready to end the session. Replaces the older `compress-act` skill.
---

# close-act

You are running the **close-act** skill. The act is finished. Your job
is to close the conversation cleanly: compress the act's summaries,
stabilize voice observations, write the handoff document, and tell
the author it's safe (and recommended) to /clear before the next act.

After this skill runs, the next session can rebuild everything from
disk via `resume-act`.

## When to invoke

- The author says "close act N" / "wrap up the session" / "cerramos
  el acto".
- `update-canon` for the last chapter of an act has finished. The
  `update-canon` skill itself prints `Strongly recommended: run
  close-act then /clear` when this condition is met.

## Hard rules

- **Seeds and shadow are NEVER compressed.** They are the source of
  truth for foreshadowing and the writer's hidden timeline. Closing
  the act does not touch them.
- **Voice consolidation is stabilization, not invention.** You can
  only consolidate what voice.md actually says. Do not promote a
  one-time observation to a stable rule unless it appeared multiple
  times during the act.
- **The handoff must be self-contained.** A reader (future you in a
  fresh session) should be able to pick up the next chapter armed
  with bible + plan + canon + handoff alone. No reliance on
  conversation memory.
- **End with the explicit signal.** The last line of your final
  response must be:
  `✓ Act N closed. STANDARD: run /clear now, then resume-act for act N+1.`

## Steps

### 1. Run the helper

```bash
python3 .claude/skills/close-act/scripts/close_act.py \
    --series-slug <slug> --book-number <N> --act <A>
```

This:
- Runs `compress-act/prepare_act.py` (bundles the act's chapter
  summaries into `notes/_act-AA-bundle.md` + writes a skeleton at
  `summaries/act-AA.md` for you to fill).
- Resets `notes/session-handoff.md` to a fresh skeleton dated today,
  with the four TODO sections you'll fill below.

### 2. Fill the act summary

Read the bundle at `notes/_act-AA-bundle.md`. Fill `summaries/act-AA.md`
to about 1500 words. Lose texture; keep facts. Read the existing
`compress-act` SKILL.md for the structure if you need it — close-act
is a strict superset of compress-act.

### 2b. (Re)build the book summary synthesis

`update-canon` no longer rewrites `summaries/book-summary.md` every
chapter (it only touches the `## What just happened` line). The full
synthesis is built **here**, once per act — this is what makes the book
summary effectively *incremental by act* instead of per-chapter.

Open `summaries/book-summary.md` and (re)build it from the act summaries
(`summaries/act-*.md`) plus the current canon state. Target ~2000 words,
ruthless. Structure:

```markdown
# <Book title> — running summary

## State of the world right now
> 4-6 bullets: political, magical, geographic state at the most recent act.

## State of principals right now
> One line per principal: location, emotional state, goal, cost borne.

## Threads in motion
> 3-8 lines: open subplots, unpaid seeds (by id, not content), debts.

## Reader's accumulated knowledge
> 4-6 lines: what the reader now believes (may differ from shadow truth).

## What just happened
> 2-3 sentences on the most recent chapter (carry over / refresh whatever
> update-canon left here).
```

Source of truth is the **act summaries**, not the conversation. If it
grows past ~2500 words, trim the oldest threads. This file is what
becomes the previous-book context for the next book in the trilogy.

### 3. Consolidate voice.md (stabilization)

Open `notes/voice.md`. Walk through the entries added during this act
(date-stamps within the act window). For each POV section:

- Group observations that say similar things.
- Identify the rules that held across ≥ 2 chapters of the act. Those
  are **stable**.
- Identify rules that were stated once and didn't reappear. Those are
  **provisional** — leave them in the per-entry log but do not
  promote.

At the end of each `## POV: <name>` section, add or update a
sub-section:

```markdown
### Stable rules (after act {act})
- (consolidated rule 1)
- (consolidated rule 2)
- ...
```

If a previous act already wrote a `Stable rules` block, **update it
instead of duplicating**. Older rules stay unless contradicted by
new ones — and contradictions go to `open-questions.md` for resolution.

### 4. Write the session handoff

Open `notes/session-handoff.md` (just reset by step 1). Fill the four
TODO sections, in order:

#### 4a. Voz consolidada
The synthesis from step 3. 3-6 stable rules per POV, expressed as
prescriptive sentences ("Bruno habla con frases cortas. Pausa antes
de contestar. Verbos artesanales sobre verbos de pensamiento.").
This becomes the **fast read** for the next session — the
voice.md file is the long form, this is the executive summary.

#### 4b. Hilos abiertos para el acto siguiente
From `notes/open-questions.md` (`## Pendientes` section), copy the
items that the next session must address. Prioritize: anything
blocking the next chapter goes first.

#### 4c. Decisiones de esta sesión
List the decisions taken in chat during this act that affect future
chapters. Be tight: one line each, with origin. Examples:

- "(ch 4) Cambiamos el POV original de Bruno a Vela para que el plant
  de la Lectura no quede telegrafiado."
- "(ch 6) Mentor reformista renombrado: 'Doral'."

Only include decisions not already captured elsewhere (plot decisions
should be in setup.md; name decisions should be in canon).

#### 4d. Notas para resume-act
What does the next session need to read FIRST, before opening the
context bundle? If there's a critical gotcha for chapter N+1
(e.g., "chapter N+1's POV is Yedra, not Bruno — easy to forget"),
put it here. If nothing critical, leave a one-liner: "No special
notes; standard resume-act bundle suffices."

### 5. Verify nothing critical was missed

Before signaling done, check:

- [ ] `summaries/act-NN.md` filled (~1500 words).
- [ ] `summaries/book-summary.md` rebuilt (~2000 words) from the act
      summaries (step 2b).
- [ ] `notes/voice.md` has a `Stable rules (after act N)` block per
      POV that appeared.
- [ ] `notes/session-handoff.md` has all four TODO sections filled.
- [ ] `plan/seeds.md` and `plan/shadow.md` **untouched** (open them to
      verify if unsure).
- [ ] `notes/open-questions.md` reviewed — pending items either
      copied to handoff or explicitly de-prioritized.

### 6. Report and signal

Print:

```
✓ Act N closed.

- summaries/act-NN.md: <word count>
- summaries/book-summary.md: rebuilt (<word count>)
- voice.md: stable rules consolidated for POVs: <list>
- session-handoff.md: <date>, with N pendientes for next session

Next session bootstrap: run `resume-act` (act N+1, chapter <next>).

STANDARD: run /clear now, then resume-act for act N+1.
```

The **last line is the explicit signal**. Do not add anything after it.

## What this skill does NOT do

- Does NOT touch `plan/seeds.md`, `plan/shadow.md`, `plan/outline.md`.
- Does NOT delete chapter summaries (`summaries/ch-NN.md`) or chapter
  prose. They stay on disk for search and inspection.
- Does NOT modify canon (canon is locked by `update-canon` per
  chapter).
- Does NOT run `/clear` — that's a user command. This skill **signals**
  that /clear is safe and recommended; the author executes it.
