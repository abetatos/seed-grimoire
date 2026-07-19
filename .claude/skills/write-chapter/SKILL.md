---
name: write-chapter
description: Write a single chapter of the book in the declared language, writing to the structural budget (every beat in the beat sheet; length is never counted), using the assembled deterministic context (setup + canon + plan + shadow + seed envelope + recent chapters). Use this when the user says "write chapter N", "next chapter", or "continue". Refuses if the chapter's outline beat sheet is empty.
---

# write-chapter

You are running the **write-chapter** skill. Your job is to produce one
chapter of the book, in the declared language, faithful to every input
in the assembled context.

## When to invoke

- "Write chapter N" / "next chapter" / "continue" / "escribe el capítulo N".
- The book has a finished `setup.md` AND a `plan/outline.md` with a
  non-empty beat sheet for the target chapter.

## Hard rules

- **Write in the language declared in `setup.md`.** Default Spanish (`es`).
- **Write to the structural budget, not to a word count.** An LLM cannot
  count words while drafting; a numeric goal doesn't produce the number, it
  produces padding — the filler your `style.md` bans. Hit **every beat in
  the beat sheet** — including its typed grounding beats (2-4 per chapter,
  150-400 words each) — and length emerges from that. **Nobody counts the
  words — ever.**
- **A beat is a PLAYED scene, never a narrated summary.** "Hitting" a beat
  means the reader lives it: the space staged, the action beat by beat, the
  POV reasoning on the page, dialogue where people talk, the turn landed.
  A beat whose events arrive pre-digested ("hubo una fila; a la hija de los
  Robles le quitaron el color") has **collapsed** — it is not covered, it is
  skipped in disguise, and no later pass can fix it (`expand-chapter` inserts
  grounding; it cannot un-summarize a scene — that stretch is the padding
  this pipeline exists to prevent). Generosity lives in THIS pass: unfold
  each beat fully the first time. The windowpane register runs economical by
  default — counter it with more *scene* (another action beat, the cost, the
  reaction), never with more ornament. By design the pipeline never measures generated length or
  shows it back to the model: a visible count-vs-target breeds compensation
  (padding this chapter, or "write more generously" leaking into the next).
  Do not run `wc`, do not estimate your own length, do not report a count.
  Deepening a chapter is the **`expand-chapter` skill**'s job (need tests,
  never length) — never hand-edit for length.
- **Three beat types per chapter:** plot, grounding (the outline's typed
  texture beats), subtext. The chapter is not a list of events; it is a
  lived experience — and the POV chooses at least once.
- **Seed envelope is law.** Every seed marked `plant`/`echo`/`payoff`
  in the bundle must land exactly as the envelope specifies. When the
  envelope shows a seed's *realized* touches, rhyme with that wording.
- **Never reveal shadow content directly.** The shadow timeline is what
  *you*, the writer, know. The POV knows only what their consciousness lets.
- **Canon is sacred.** Names, places, costs of magic, established
  relationships — immutable. If something feels wrong, *flag it to the
  user* before writing; do not contradict canon silently.
- **Apply the bundle's Craft checklist** (anti-patterns, dwelling, seeds)
  and **Style guide** — both are in your context already. Do not
  re-derive the rules; obey the ones in the bundle. The full reference
  files (`references/*.md`) are there for on-demand depth only.
- **No invented continuity.** If you need a fact canon lacks (a birth
  town, a river's name), invent it and *flag it* in your output so
  `update-canon` can promote it.

## Steps

### 0. Dispatch the draft to a fresh subagent (main thread only)

If you can spawn subagents (you have the Agent tool) and you were invoked
standalone (`write chapter N`, not already inside `chapter-smith`), **do not draft
in this conversation**. Dispatch steps 1-4 to the `chapter-smith` subagent (Agent
tool, `subagent_type: chapter-smith`) with the prompt
`chapter <N> --series-slug <slug> --book-number <M>`. It drafts in a **fresh, clean
context** — the ~26k bundle + the growing prose + the between-block re-reads never
enter this conversation, and the draft is written below the attention-degradation
zone, so the voice is truer, not just cheaper (the author's blind-compare confirmed
this — chapter-smith is the default writer, 2026-07-19). Keep it alive
(`run_in_background: true`): the smith is **persistent** and may pause to ask you.

- If it returns **`DRAFTING_PAUSED`** — it hit an irreversible memory gap it can't
  derive from canon — relay its `QUESTIONS` to the author with `AskUserQuestion`
  (its DEFAULT first, labelled recommended), then `SendMessage` the smith
  `RESUME:` + the answers. Loop until it returns the draft-complete hand-off.
- On the **hand-off** (visible plot, PLANTED, INVENTED, ASSUMPTIONS, FLAGS), run
  only the interactive tail — go **straight to step 5** (report): surface any FLAGS
  (HARD STOP) and any ASSUMPTIONS (the reversible gaps it wrote around) to the
  author, and carry PLANTED/INVENTED into the report. (Standalone `write-chapter`
  stops at the draft — the critique's warm fixes are `write-novel`'s loop, not
  this skill's.)

> When the **chapter-smith subagent itself** runs this skill it has no Agent tool,
> so it cannot dispatch — it simply executes steps 1-4 directly and stops before
> step 5's interactive tail. (That is how recursion is structurally prevented.)
> `write-novel` likewise dispatches the draft itself, so when it chains the skill
> the work is already in the subagent — don't re-dispatch.

### 1. Build the context bundle

Run:

```bash
python3 .claude/skills/write-chapter/scripts/build_context.py \
    --series-slug <slug> \
    --book-number <N> \
    --chapter <M>
```

This writes `output/<series>/book-NN/notes/_context-chMM.md`. It is the
**only** input you need — everything is assembled in deterministic
order (sections are named, not numbered — find them by heading):

- **Precedence** — how to resolve conflicts between sections.
- **Setup** (the book's identity).
- **Decisions** — `notes/decisions.md` (book-level binding choices) plus
  this chapter's gate decisions from `plan-chapter` (the `## Decisiones`
  section of `notes/brief-chMM.md`). These OVERRIDE anything below that
  conflicts. Honor them exactly; if a beat seems to contradict a locked
  decision, stop and surface it rather than quietly choosing.
- **Series context** (if continuation).
- **Canon** (characters, factions, magic, world, timeline).
- **Plan** (neighbor beats + arcs).
- **Shadow timeline slice** for this chapter (writer-only).
- **Seed envelope** (exact seeds to plant/echo/payoff).
- **Story so far** (hierarchical summaries).
- **Continuity seam** — previous chapter's summary + its final scene verbatim.
- **Already spent** — images/phrases prior chapters used; reference, don't re-describe.
- **Style guide** (this book's own `style.md` — the reference library).
- **Conversation memory** (consolidated voice rules, author style rules).
- **Craft checklist** (anti-patterns, dwelling, seed-craft, distilled).
- **State sheet** (this chapter's checkable facts, from the brief's `## Estado
  que no se puede contradecir`, when present).
- **Voice exemplars** (only when the book curates them — absent if the
  author runs without exemplars) — imitate the MOVES they make, never their
  images, phrases or content (verbatim reuse is counted by `lint_prose.py`).
- **Chapter N beat sheet — your specific instruction.**
- **Voice spine — read last, write from this** (house core + this book's
  signature + the brakes).

Read this file in full. Do not skim. The *beat sheet* section is the
contract for this chapter.

### 2. Refuse if the beat sheet is empty

If the chapter's beat-sheet section contains only `> TODO:` lines, **stop**.
Tell the user the chapter has no plan and ask them to run `plan-book`
or fill in the beats by hand. Do not write a chapter from imagination.

### 2b. Pre-write consistency check (last cheap gate)

`plan-chapter` already ran the deep gate and locked the forks. This is
the final quick pass before 10 000 words land on top of a problem — keep
the adversarial bias, not the length. Scan the beat sheet once against:

- **Shadow** — does a beat require the POV to know what shadow keeps hidden?
- **Seed envelope** — can each seed actually be planted/echoed/paid given POV,
  location, events?
- **Arcs** — is the POV's arc state compatible with the beats?
- **Canon / grimoire** — any named character, place, magic detail contradicting
  `canon/*` or the grimoire?
- **Motivation** — can the POV *want* each beat with only what they know now?
- **Tone & pacing** — register matches `setup §Prose constraints`; not two same
  -register chapters back to back.

If anything surfaces, **STOP — do not draft.** Quote the exact lines, say why it
matters *dramatically*, offer 2-3 options (including revising the **plan file**,
not just the chapter — the author may change the story at any point), and wait.
If the author overrules a flag, proceed but record it in `notes/decisions.md`.
If clean, say so ("consistency check clean — proceeding to draft") and continue.

### 3. Write the chapter

Open `output/<series>/book-NN/chapters/<NN>.md` for writing.

**Overwrite guard (check ONCE, before block 1).** If the file already exists
with substantial prose (>500 words) AND has uncommitted changes (`git status
--porcelain -- <file>` is non-empty), **STOP and ask the author** before
regenerating — a rewrite would destroy unversioned prose. If the file is
committed (recoverable) or trivial, proceed. The per-block appends below are the
same session extending its own draft, so they do not re-trigger this guard.

Structure:

```markdown
# Capítulo N — <Title>

<prose>
```

Heading uses the language declared in setup (`Capítulo` / `Chapter`).
The chapter is **all prose** after the heading. No subheadings inside
the chapter unless the user has declared a sectioned format.

Drafting plan inside your head before writing:

1. **Decide the opening.** Not "X woke up". Not battle. Start in the
   middle of an action that reveals who the POV is and what they care
   about. Use a non-visual sense (smell, sound, touch, taste) if it
   fits — see `dwelling-techniques.md`.
2. **Plan the grounding beats first.** Where will the 2-4 grounding
   moments sit, and which licensed type is each (world unfolded in use,
   stage built, cost made visible, deliberation, re-orientation,
   secondary humanized)? They should be load-bearing — a labor watched
   working, a room the scene will use, a price felt. Lingering with no
   type is not a beat.
3. **Lay plot beats around the grounding.** A plot beat is a hinge:
   decision, conflict, revelation. Between hinges, the world breathes —
   and the POV *chooses* at least once per chapter (see the sliding
   scales block in `plan/arcs.md`); wins arrive only over paid failures.
4. **Plant subtext.** What does the POV feel but not say? What lie are
   they protecting in this scene? This is where seeds embed naturally.
5. **Bring in the seed envelope.** Plant seeds inside scenes already
   underway. Echo seeds in a different sensory register. Pay off
   without explaining.
6. **End on the transition out** specified in the beat sheet.

**Draft in 2-4 sequential scene blocks, not one pass.** A chapter of 8-12k
words is past the length where a single generation holds quality — the beats
land, the pacing keeps, the voice stays honest at the start and then decays, and
the close (the documented highest-risk zone) gets the tiredest prose. Partition
the beat sheet into blocks of **1-3 beats each** (a block = one scene, or two
tightly-coupled scenes; a long beat sheet is still 2-4 blocks, never one per
beat). Then, for **each block**:

1. **Re-read the last 2-3 paragraphs you just wrote** (the intra-chapter seam)
   so the new block continues the live voice, not a remembered one.
2. **Re-read, in the bundle (`notes/_context-chNN.md`), these named sections:**
   the *Chapter N — beat sheet*, the *State sheet* (if present), and
   the *Voice spine* — in that order, spine LAST: the instruction, not your
   own possibly-drifting prose, must hold the recency slot when you draft.
   This re-read is mandatory between blocks — it resets the instruction
   adherence a long generation erodes. Re-read the sections; do not write
   from memory of them.
3. **Draft the block's beats** plus its share of the outline's typed grounding
   beats, and land the block on a scene turn, not a summary.
3b. **Collapse check (before appending).** Re-read the block against its
   beats: did any beat land as narrated summary instead of a played scene
   (no staged space, no action-by-action, no POV reasoning, events
   pre-digested)? If yes, **replay that beat as a scene now**, in this
   block, before appending — a collapsed beat that reaches the critique
   costs a REVISE, and one that reaches `expand-chapter` gets padding
   stapled over a hole. Zero collapsed beats is the bar, not the average.
4. **Append to `chapters/NN.md`** (Edit tool). Do **not** revise earlier blocks
   while drafting — polish is `revise-chapter`'s job, not this pass's.

After the final block, do **one continuity read of the whole chapter** for seams
between blocks — a repeated description, a dropped object, a time skip — and fix
only those seam defects. (This exact block flow is normally run by the
`chapter-smith` subagent in an isolated clean context — the default writer, per
step 0. These instructions are the drafting spec the smith executes; you reach them
directly only as the smith itself, or via the `--in-session` escape hatch.)

While drafting, obey the **Craft checklist** in the bundle (anti-patterns,
dwelling, seeds) and the **Style guide**. Open a `references/*.md` file
only when you want deeper craft guidance than the checklist gives.

### 4. Hand to the critique — no length check, no grounding pass here

There is deliberately **no word-count verification step** and **no unconditional
grounding pass**. The raw draft goes **straight to the critique**, which is the
sole grounding detector (it runs the six need-tests in fresh context); grounding
is filled *reactively* only where the critique names an unfired need-test:

- Under **`write-novel`**, the raw draft goes to the critique (step 2d); if it
  names an unfired need-test, the orchestrator dispatches `chapter-grounder` to
  fill it. Just stop after writing.
- **Standalone**, recommend `critique-chapter` as the next step. Do not run a
  grounding pass on spec — never hand-edit prose for depth; grounding is the
  critique-driven `expand-chapter` fill (EXPAND markers, 2-pass cap).

### 5. Report

Print to the user:

- Chapter number, title.
- One-sentence summary of what happened (visible plot).
- Seeds planted / echoed / paid off in this chapter (by id).
- Any canon facts you invented while drafting that need promotion
  (e.g., "I named the river *Soral* — promote to canon/world.md").
- Suggested next step:
  - `critique-chapter <N>` for a hard read
  - `update-canon <N>` to fold the chapter into summaries + canon
  - `write-chapter <N+1>` to keep going

### 6. Hand off

Do **not** automatically run `update-canon`. The user decides whether
this chapter is good enough to lock in. They will tell you when to
move on.

## Style guardrails

The bundle's **Style guide section is binding** — this book's own `style.md`,
self-contained. Apply it throughout; do not restate it here. Two things the
skill enforces on top of it: **voice & distance** match `setup.md` (default
close third, past), and **POV is constant within a chapter** unless setup
declares rotation.

## What this skill does NOT do

- Does not modify `plan/`, `canon/`, or `summaries/`. Only writes the
  chapter file and reads the context bundle.
- Does not auto-update seed status. That happens in `update-canon`.
- Does not invent characters, places, or magic rules. It uses what
  canon and plan say, and flags any gap.

## Files this skill writes

- `output/<series>/book-NN/chapters/<NN>.md` — the chapter.
- `output/<series>/book-NN/notes/_context-ch<NN>.md` — the assembled
  context bundle (regeneratable; safe to delete after the chapter is
  accepted).
