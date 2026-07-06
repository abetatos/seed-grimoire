---
name: revise-chapter
description: Surgical rewrite of specific issues in a written chapter — anti-pattern phrases, weak subtext, missing seed plants, over-long sections. Use this after `critique-chapter` has flagged SHOULD-fix items, or after the user points out specific problems. Modes: `--mode polish` (default), `--mode trim`, `--mode tighten-seeds`.
---

# revise-chapter

You are running the **revise-chapter** skill. The chapter exists. The
critique has named specific issues. Your job is **targeted edits**, not
a rewrite.

## Hard rules

- **Edit in place, surgically.** Use the Edit tool. Do not rewrite
  the whole chapter.
- **Match the surrounding prose exactly.** Voice, rhythm, distance,
  vocabulary. A revision should be invisible.
- **One issue at a time.** Make each Edit address one finding from the
  critique. Don't bundle unrelated fixes into a single Edit.
- **Do not change plot.** The chapter's events do not move. You are
  changing *how* it reads, not *what* happens.
- **Preserve seed plants.** Lines that carry seeds may be lightly
  rephrased but never removed or relocated to a different scene.

## Modes

### Mode: polish (default)
Address all SHOULD-fix items from `notes/critique-chNN.md`. Anti-
pattern phrases get replaced with specific sensory alternatives.
Weak subtext gets a layer added. Telegraphed seeds get rephrased
to embed more naturally. Flat dialogue gets sharpened.

### Mode: trim
The chapter is over target. Cut without losing texture. Look for:
- Repeated sensory beats (kept one, cut the rest)
- Over-explained subtext (cut the explanation, keep the gesture)
- Long monologues — let action carry weight instead
- Adjective stacks ("the dim, cold, silent room")

Goal: bring the chapter within target range while preserving every
plot beat, texture scene, and seed.

### Mode: tighten-seeds
The seed envelope was off — seeds telegraphed, echoes verbatim,
payoff explained. Walk each seed in the envelope and adjust *only*
those lines using `references/seed-craft.md` rules:
- Plants: embed in scene action, no flag words.
- Echoes: oblique, different sensory register.
- Payoffs: trust the reader; remove "she realized" / "it dawned".

## Steps

### 1. Load the critique

Read `notes/critique-chNN.md`. If it doesn't exist, run
`critique-chapter` first or ask the user for an explicit list of
issues.

### 2. Apply edits one-by-one

For each issue (in MUST → SHOULD → CONSIDER order):

1. Find the exact line in the chapter via Read/Grep.
2. Use Edit with the smallest possible `old_string` that uniquely
   identifies the spot.
3. Replace with the targeted fix. Match surrounding voice.
4. Re-read the surrounding paragraph to verify it still flows.

If you cannot find a clean fix without rewriting a paragraph, **skip
the issue and report it** rather than risk damaging the chapter.

### 3. Report

**No word count** — do not count words or compare length to the setup range
in any mode (the pipeline never measures generated length back to the
model). Trim mode is done when every flagged padding finding is cut, not
when a number is reached; a re-critique judges the result.

Print:
- Number of edits made, grouped by tier.
- Any issues skipped (with reason).
- Suggested next step: `critique-chapter <N>` again, or
  `update-canon <N>`.

## What this skill does NOT do

- Does not run `update-canon` (the chapter is locked in only when the
  user agrees).
- Does not modify `plan/`, `canon/`, or `summaries/`.
- Does not invent content. Every replacement must be derivable from
  the existing scene + canon + plan.
