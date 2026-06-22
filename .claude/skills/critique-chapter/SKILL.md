---
name: critique-chapter
description: Hard, structured critique of a written chapter against the book's own contract — beat sheet, canon, shadow, seed envelope, prose anti-patterns, dwelling techniques, word count. Produces a written critique with prioritized issues and concrete fixes. Use this after a chapter is written and before `update-canon` locks it in. Invoke as "critique chapter N".
---

# critique-chapter

You are running the **critique-chapter** skill. Read a chapter against
the bundle that produced it and report on where it succeeds and fails.

The critique is **for the user**, not for you to silently fix. The
user decides whether to apply revisions.

## Hard rules

- **Be specific.** "The prose is flat" is useless. "Paragraph 3
  reaches for 'tapestry of mist', which is a banned cliché — replace
  with a concrete sensory anchor" is useful.
- **Quote the offending line.** Always.
- **Prioritize ruthlessly.** Group findings into:
  - **MUST fix** — breaks canon, breaks seed envelope, breaks shadow,
    contradicts the beat sheet, falls below 80% word target. Also:
    plot beats that don't follow causally from prior chapter,
    character actions inconsistent with the arc waypoint at this
    chapter, motivations that require off-stage information.
  - **SHOULD fix** — anti-pattern phrases, missed dwelling
    opportunities, weak subtext, telegraphed seeds, tonal drift, a
    chapter ending that doesn't earn the transition the beat sheet
    promised.
  - **CONSIDER** — taste-level suggestions. The user can ignore.
- **Do not rewrite the chapter.** Quote, name, point. Concrete
  *direction* yes; substitute prose no.
- **Do not invent reasons.** Every "MUST fix" must cite a specific
  source: canon line, beat sheet bullet, seed id, anti-pattern name.
- **Look for story flaws, not just craft flaws.** A chapter can be
  technically clean (all beats hit, all seeds present, prose tidy)
  and still **wrong**: the protagonist's motivation in scene 3 doesn't
  match what they know; the chapter doesn't change the world state;
  the dramatic energy descends when it should ascend. These get the
  same MUST/SHOULD treatment as anti-patterns. If a chapter passes
  cleanly with zero findings, you are missing something — re-read.

## Steps

### 1. Load the contract

Build the context bundle (idempotent):

```bash
python3 .claude/skills/write-chapter/scripts/build_context.py \
    --series-slug <slug> --book-number <N> --chapter <M> --phase critique
```

`--phase critique` drops the recent-chapters-in-full block (you read the target
chapter directly from `chapters/MM.md` below — you don't need the other prior
chapters inlined), but keeps the style guide and craft checklist because you
check the prose against them.

Read `notes/_context-chMM.md`. The relevant sections for critique are:

- **Setup** — voice, tense, distance, prose constraints.
- **Canon** — must not be contradicted.
- **Plan / outline** — the beat sheet for this chapter.
- **Shadow timeline** — the writer's truths; check what should be
  *implied* but not stated.
- **Seed envelope** — must be honored exactly.
- **Style guide** — this book's own `style.md` (self-contained voice
  guide). Includes the anti-cursi calibration.
- **References** — anti-patterns checklist, dwelling techniques.

Then read the chapter: `chapters/MM.md`.

### 2. Run the structured pass

Go through these checks in order. For each, write a finding (or
"clean") to the critique buffer.

1. **Word count.** Run check_wordcount. Note actual / target.
2. **Beat sheet fidelity.** Does the chapter hit every plot beat?
   Mark `MUST fix` if a plot beat is missing.
3. **Texture beats.** Are there 2-4 dwelling moments of 300-500 words?
   List each, named by what it dwells on. If under 2, `MUST fix`.
4. **Subtext.** Pick three moments where the chapter could have
   carried subtext. Did it? If multiple are flat, `SHOULD fix`.
5. **Seed envelope.**
   - For each seed marked `plant` in this chapter: is it planted?
     Quote the line. If telegraphed (flag word, isolated sentence,
     too prominent), `SHOULD fix`. If missing, `MUST fix`.
   - For each `echo`: is it referenced obliquely? `SHOULD fix` if
     missing or restated verbatim.
   - For each `payoff`: does the truth surface? Is it explained or
     allowed to click? `MUST fix` if missing.
   - **Dose / telegraph by repetition.** For any seed whose `Dose` field
     constrains it (typically a payoff ≤2 chapters from its plant), count how
     many times the chapter touches it and whether the chapter *re-describes*
     the seed (especially at its opening) before paying it off. A near-term
     payoff that is re-established in full is "seen coming a mile off" —
     `SHOULD fix`, quoting the redundant description and naming the Dose budget
     it broke.
   - **Trigger fidelity.** For an event payoff, does the chapter fire it from
     the seed's intrinsic `Trigger` (an already-seeded cause), or did the
     writer invent a convenient external actor to cause it (a horse, a storm, a
     stranger arriving just in time)? A contrived trigger is `MUST fix` —
     quote it and point to the intrinsic trigger that should fire it instead.
   - **No deus ex machina (presence + cause).** Beyond event triggers, check
     that every key character who appears is there for a *motivated, seeded*
     reason, not a convenience. A character who shows up exactly when needed
     with no prior cause ("a mentor passing through on other business", a
     rescuer who happens to be there) is `MUST fix` — quote the unmotivated
     entrance and name the motivated version (a reason tied to the book's
     engine, established before the character matters). Cross-check against any
     presence rule in `notes/decisions.md`.
   - **Resolution image.** If a resolution-type seed pays off here, does the
     chapter *invert/transform the exact image planted earlier* (and let it
     click, not explain)? If it pays off as a flat statement instead of the
     transformed image, `SHOULD fix`.
   - **Reveal-timing leak.** If this chapter loudly spends an anomaly whose
     real payoff is scheduled for a *later* chapter (per the seed's payoff
     chapter or a locked decision), it is over-spending the reveal — `MUST
     fix`. Quote the over-explained line; the anomaly should be whispered here
     and understood later.
6. **Shadow honesty.** Does the chapter accidentally leak shadow
   content (the writer revealing what the POV shouldn't know)?
   `MUST fix` if so.
7. **Canon.** Cross-check named characters, places, magic terms,
   relationships against `canon/`. Quote any contradiction.
   `MUST fix`.
8. **POV / voice / tense.** Match `setup.md`. Any drift is `SHOULD fix`.
8b. **Style guide.** Hold the prose against the Style guide section
    (this book's `style.md`). Flag violations of the anti-cursi
    calibration especially: emotional thesis statements, overspent
    physical emotion (tears/trembling more than once or twice),
    decorative beautiful lines that carry no plot/character/sense, and
    any rule the book's own `style.md` declares. Quote each. `SHOULD
    fix`; `MUST fix` if it breaks an explicit book-level style rule.
8c. **Richness & seeding — the add-back check.** This check looks for
    what is *missing*, not what is excess: a critique that only
    subtracts can only make prose blander. Two passes:
    - **Sensory mandate.** Does every scene land at least one concrete
      sensation the reader *feels* (temperature, sound, weight, taste,
      smell), not a sensation the narrator merely names? Mark any scene
      that reads grey/abstract. If the book's premise is sensory
      (colour, sound, scent — see `style.md`), hold it harder: a scene
      that does not make that premise felt is a `SHOULD fix` with a
      concrete suggestion of what to add, not just a note.
    - **Unseeded payoffs (Chekhov).** List everything that breaks, pays
      off, or turns out to matter in this chapter, and check each one
      appeared *earlier* in ordinary use (this chapter or a prior one).
      An object/danger/skill that arrives only at the moment it matters
      is a `SHOULD fix`: name where the seed should have been planted.
      (The seed envelope in check 5 only covers tracked seeds; this
      catches the untracked setups too — e.g. a structure that
      collapses must have been shown as fragile beforehand.)
9. **Anti-patterns.** Search the chapter for every entry in
   `references/prose-antipatterns.md` (banned lexicon, fantasy
   clichés, structural tics). Quote each occurrence. `SHOULD fix`
   for most; `MUST fix` if there are >5 instances. Do **not** flag
   richness, lyricism, or sensory density that is not a named
   anti-pattern — that is texture, not a defect (see 8c).
10. **Opening / ending.** Did the chapter start in a non-cliché way
    (not waking up, not battle, not prophecy)? Does it end on the
    transition out specified in the beat sheet?
11. **Hard-magic laws.** Magic used in this chapter — does its
    capability match what the reader has seen? Are costs visible?
    `MUST fix` violations.
12. **Dialogue.** Random spot-check 3 lines of dialogue. Does each
    reveal character, advance plot, or carry subtext (ideally two)?
    `SHOULD fix` flat lines.

### 3. Write the critique

Write the critique to:

```
output/<series>/book-NN/notes/critique-ch<NN>.md
```

Structure:

```markdown
# Critique — chapter N

**Word count:** actual=X target=[lo, hi] (verdict)
**Verdict:** PASS / REVISE / REJECT

## MUST fix
- **[issue type]** — quoted line / location → concrete direction
- ...

## SHOULD fix
- ...

## CONSIDER
- ...

## What works
- Brief notes on what landed. Important — the writer needs the signal.
```

A chapter with **zero MUST and ≤3 SHOULD** is `PASS`.
A chapter with **MUST fix** items is `REJECT`.
Anything in between is `REVISE`.

### 4. Report to user

Print the verdict and the count of issues by tier. Tell the user the
critique file path. Suggest next step:

- PASS → `update-canon <N>` to lock in.
- REVISE → `revise-chapter <N>` (surgical, addresses SHOULD items).
- REJECT → discuss with user; may require rewriting the affected scene
  or revising the outline.

## What this skill does NOT do

- Does not modify the chapter file.
- Does not modify the plan, canon, or seeds.
- Does not generate replacement prose.
