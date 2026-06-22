---
name: write-chapter
description: Write a single chapter of the book in the declared language, hitting the target word range, using the assembled deterministic context (setup + canon + plan + shadow + seed envelope + recent chapters). Use this when the user says "write chapter N", "next chapter", or "continue". Refuses if the chapter's outline beat sheet is empty.
---

# write-chapter

You are running the **write-chapter** skill. Your job is to produce one
chapter of the book, in the declared language, hitting the target word
range, faithful to every input in the assembled context.

## When to invoke

- "Write chapter N" / "next chapter" / "continue" / "escribe el capítulo N".
- The book has a finished `setup.md` AND a `plan/outline.md` with a
  non-empty beat sheet for the target chapter.

## Hard rules

- **Write in the language declared in `setup.md`.** Default Spanish (`es`).
- **You must hit the target word range.** The check_wordcount script
  is the contract. A chapter under 80% of the low target will trigger
  `expand-chapter`. Aim for the midpoint of the range, not the floor.
- **Three beat types per chapter:** plot, texture, subtext. The chapter
  is not a list of events; it is a lived experience. Budget 2-4
  texture dwellings of 300-500 words each.
- **Seed envelope is law.** Every seed marked `plant` must be planted
  in this chapter, `echo` must be referenced obliquely, `payoff` must
  come due — each per `references/seed-craft.md`.
- **Never reveal shadow content directly.** The shadow timeline is
  what *you*, the writer, know. The POV character knows only what
  their consciousness lets them know.
- **Canon is sacred.** Names, places, costs of magic, established
  relationships — all immutable. If something feels wrong, *flag it
  to the user* before writing; do not contradict canon silently.
- **No prose anti-patterns** (see `references/prose-antipatterns.md`):
  no "delve", no "tapestry of", no "ethereal whispers", no chosen-one
  rhetoric, no Y-and-Z lists that flatten. Read the file before
  starting; it is loaded into your context bundle already.
- **No exposition dumps.** Worldbuilding arrives through use — a
  character handling magic in a mundane context teaches the system
  better than a paragraph explaining it.
- **No invented continuity.** If you need a fact that isn't in canon
  (a character's birth town, the name of a river), invent it and
  *flag it* in your output so `update-canon` can promote it.

## Steps

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
order:

1. Setup (the book's identity)
1b. **Decisions** — `notes/decisions.md` (book-level binding choices) plus
    this chapter's gate decisions from `plan-chapter`
    (`notes/_decisions-chMM.md`). These OVERRIDE anything below that
    conflicts. Honor them exactly; if a beat seems to contradict a locked
    decision, stop and surface it rather than quietly choosing.
2. Series context (if continuation)
3. Canon (characters, factions, magic, world, timeline)
4. Plan (outline + arcs)
5. Shadow timeline slice for this chapter (writer-only)
6. Seed envelope (exact seeds to plant/echo/payoff)
7. Story so far (hierarchical summaries)
8. Recent chapters in full (last 2)
9. **Chapter beat sheet — your specific instruction**
10. Style guide (this book's own `style.md`)
11. Craft references (anti-patterns, dwelling, seed-craft)

Read this file in full. Do not skim. The beat sheet at section 9 is
the contract for this chapter.

### 2. Refuse if the beat sheet is empty

If the chapter's section 9 contains only `> TODO:` lines, **stop**.
Tell the user the chapter has no plan and ask them to run `plan-book`
or fill in the beats by hand. Do not write a chapter from imagination.

### 2b. Pre-write consistency check (always — adversarial bias)

The bar for stopping is **not** "contract violation". It is "would the
author want to know about this BEFORE 10 000 words of prose land on
top of it?" Catching a story/logic problem now costs five minutes of
conversation. Catching it after writing costs the rewrite.

Scan for, in order:

- **Shadow vs outline contradiction.** Does this chapter's beat sheet
  require something incompatible with the shadow truth for this
  chapter? (E.g., the POV is supposed to *not know* X, but the beats
  have them act as if they do.)
- **Seed envelope feasibility.** Can each seed in the envelope actually
  be planted / echoed / paid given the POV, location, and events?
  (E.g., a plant requires the POV to witness an object, but the beat
  sheet never puts them in the room.)
- **Arc waypoint alignment.** Is the character's arc state at this
  chapter compatible with the plot beats? (E.g., the chapter demands
  decisive action but `arcs.md` puts them in all-is-lost retreat.)
- **Canon continuity.** Cross-check every named character, place,
  faction, and magic detail used in the beat sheet against `canon/*`.
  Flag any contradiction.
- **Motivation plausibility.** At every plot beat, can the POV
  character *want* this with only what they know at this point in the
  book? Flag any decision that requires off-stage information.
- **Tonal drift.** Do the proposed beats match the declared register
  in `setup.md §Prose constraints`? (Comic moments in a "belleza
  fúnebre" book are SHOULD-flag.)
- **Pacing rhythm.** Was the previous chapter (in the recent-chapters
  bundle) the same emotional register? Two action chapters back to
  back violates the pacing rule in `references/fantasy-beats.md`.
- **Bible alignment.** Does the chapter assume something the bible
  (`output/<series>/bible.md`) declares fixed differently?

If anything surfaces, **STOP. Do not start drafting.**

Report to the author:
1. **What you noticed**, with the exact lines from each source quoted.
2. **Why it matters dramatically** — not just mechanically. (E.g.,
   "the seed `vela-prisma-anillo` schedules a plant in ch 8, but the
   beat sheet for ch 8 has Bruno as POV. Vela doesn't appear. Either
   ch 8 needs Vela's POV, or the plant moves.")
3. **Two or three concrete options** for resolving — including the
   option of revising the **plan file** rather than the chapter. The
   author has the right to modify the story at any point; that is the
   core design principle of this pipeline. Your job is to surface the
   problem cleanly so they can.
4. **Wait** for the author to choose, rewrite, or overrule.

Do **not** advance under "I'll just try my best and we'll see." If the
author tells you to proceed despite a flag, proceed — but record the
override in `notes/decisions.md` so it stays visible later.

If everything checks out, say so explicitly ("consistency check clean
— proceeding to draft") and continue.

### 3. Write the chapter

Open `output/<series>/book-NN/chapters/<NN>.md` for writing.

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
2. **Plan the texture beats first.** Where will the 2-4 dwellings sit?
   They should be load-bearing scenes — a labor performed slowly, a
   meal, a room remembered, a conversation that takes its time.
3. **Lay plot beats around the texture.** A plot beat is a hinge:
   decision, conflict, revelation. Between hinges, the world breathes.
4. **Plant subtext.** What does the POV feel but not say? What lie are
   they protecting in this scene? This is where seeds embed naturally.
5. **Bring in the seed envelope.** Plant seeds inside scenes already
   underway. Echo seeds in a different sensory register. Pay off
   without explaining.
6. **End on the transition out** specified in the beat sheet.

While drafting, lean on:

- **The three laws of hard magic** (`references/hard-magic-laws.md`) — magic
  works for what the rules permit, costs are visible, and the climax
  uses what's been seen.
- **Dwelling techniques** (`references/dwelling-techniques.md`) —
  sensory anchoring, texture of labor, interior in motion. Use at
  least three named techniques across the chapter.
- **Anti-patterns** (`references/prose-antipatterns.md`) — checked
  while drafting, not after.

Word target: aim for the **midpoint of the range** declared in setup
(e.g., target ~10000 if range is 8000-12000). Below 80% of the low
target triggers expand-chapter automatically.

### 4. Verify word count

After writing, run:

```bash
python3 .claude/skills/write-chapter/scripts/check_wordcount.py \
    --series-slug <slug> \
    --book-number <N> \
    --chapter <M>
```

This exits 0 (in range), 1 (too short), or 2 (too long).

- **If too short:** invoke `expand-chapter` — add texture beats and
  dwell longer in scenes already in the chapter. Do not invent new
  events.
- **If too long:** invoke `revise-chapter --mode trim`.
- **If in range:** continue to step 5.

### 5. Report

Print to the user:

- Chapter number, title, final word count vs. target.
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

## Style guardrails (apply throughout)

- **The Style guide section is binding.** Section 10 of the bundle is
  this book's own `style.md` — a self-contained voice guide (copied from
  the house template at book creation, then edited per book). Honor the
  anti-cursi calibration in particular — underplay big feelings, no
  emotional thesis statements, distrust the beautiful line.
- **Voice & distance** match what `setup.md` declares (e.g., close
  third, past tense). If setup is silent, default to close third past.
- **POV is constant within a chapter** unless setup declares
  per-chapter rotation.
- **Dialogue earns its space.** A line of dialogue should reveal
  character, advance plot, or carry subtext — ideally two.
- **One specific over three vague.** "The man" → "the man with the
  copper ring on his thumb". Specificity is how seeds land.
- **No summary prose.** "Days passed and she trained" is a confession
  of failure. Pick one training scene and dwell.
- **No chapter-ending self-talk thesis.** Don't let the POV
  monologue the chapter's theme to themselves at the end.

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
