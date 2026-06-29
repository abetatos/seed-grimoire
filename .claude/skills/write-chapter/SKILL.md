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
- **Aim for the low end of the target range (≥ 8000 words by default),
  not the midpoint.** The range is guidance, **not a strict threshold**:
  do not pad or chase a few percent. **This skill only writes and reports
  the word count — it does not expand or trim.** Growing a short (or at-length)
  chapter is done by the **`expand-chapter` skill**, never by hand-editing the
  prose: it wraps each added zone in visible `EXPAND` markers, caps inserts per
  pass, and stops at 2 passes. Under `write-novel` the orchestrator runs that
  always-once texture pass plus any length-driven second pass for you (step 2c);
  standalone, invoke `expand-chapter` yourself after this skill reports.
- **Three beat types per chapter:** plot, texture, subtext. The chapter
  is not a list of events; it is a lived experience. Budget 2-4
  texture dwellings of 300-500 words each.
- **Seed envelope is law.** Every seed marked `plant`/`echo`/`payoff`
  in the bundle must land exactly as the envelope specifies. When the
  envelope shows a seed's *realized* touches, rhyme with that wording.
- **Never reveal shadow content directly.** The shadow timeline is what
  *you*, the writer, know. The POV knows only what their consciousness lets.
- **Canon is sacred.** Names, places, costs of magic, established
  relationships — immutable. If something feels wrong, *flag it to the
  user* before writing; do not contradict canon silently.
- **Apply the bundle's Craft checklist** (anti-patterns, dwelling, seeds)
  and **Style guide** (§10) — both are in your context already. Do not
  re-derive the rules; obey the ones in the bundle. The full reference
  files (`references/*.md`) are there for on-demand depth only.
- **No invented continuity.** If you need a fact canon lacks (a birth
  town, a river's name), invent it and *flag it* in your output so
  `update-canon` can promote it.

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
    (`notes/decisions-chMM.md`). These OVERRIDE anything below that
    conflicts. Honor them exactly; if a beat seems to contradict a locked
    decision, stop and surface it rather than quietly choosing.
2. Series context (if continuation)
3. Canon (characters, factions, magic, world, timeline)
4. Plan (outline + arcs)
5. Shadow timeline slice for this chapter (writer-only)
6. Seed envelope (exact seeds to plant/echo/payoff)
7. Story so far (hierarchical summaries)
8. Continuity seam — previous chapter's summary + its final scene verbatim
9. **Chapter beat sheet — your specific instruction**
10. Style guide (this book's own `style.md`)
11. Craft references (anti-patterns, dwelling, seed-craft)

Read this file in full. Do not skim. The beat sheet at section 9 is
the contract for this chapter.

### 2. Refuse if the beat sheet is empty

If the chapter's section 9 contains only `> TODO:` lines, **stop**.
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

While drafting, obey the **Craft checklist** in the bundle (anti-patterns,
dwelling, seeds) and the **Style guide** (§10). Open a `references/*.md` file
only when you want deeper craft guidance than the checklist gives.

Word target: aim for the **low end of the range** declared in setup
(e.g., ~8000 if range is 8000-12000) — **not** the midpoint. The range
is guidance, not a quota; do not pad to chase a few percent. A chapter
that comes in **below 80% of the low end** (~6400 for an 8000-floor) is
"too short"; the caller grows it via `expand-chapter` (see step 4). Note
that every chapter gets one `expand-chapter` texture pass regardless, so
landing at the low end here is expected, not a failure.

### 4. Verify word count

After writing, run:

```bash
python3 .claude/skills/write-chapter/scripts/check_wordcount.py \
    --series-slug <slug> \
    --book-number <N> \
    --chapter <M>
```

This exits 0 (in range), 1 (too short), or 2 (too long).

**This skill does not expand or trim — it just reports the result.** The
expand/trim work is the caller's:

- Under **`write-novel`**, the orchestrator's step 2c runs the mandatory
  `expand-chapter` texture pass and decides on any length-driven second pass
  or trim. Just report the count and stop.
- **Standalone**, hand the count to the user and recommend `expand-chapter`
  (never hand-edit the prose — that skips the `EXPAND` markers and the
  per-pass caps). `expand-chapter` runs **at most 2 passes**; if the chapter
  is still a little under the floor after that, accept it. Only flag if it is
  *dramatically* short.

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

## Style guardrails

The **Style guide (bundle §10) is binding** — this book's own `style.md`,
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
