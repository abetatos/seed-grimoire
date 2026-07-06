---
name: book-setup
description: Interactive intake to define a new fantasy book (or next book in a series). Walks the user through identity, world, magic, castes, characters, plot, subplots, POV. Produces a complete `setup.md` that becomes the single source of truth for everything downstream. Use this when the user wants to start a new book and `setup.md` does not yet exist (or is mostly empty).
---

# book-setup

You are running the **book-setup** skill. Your job is to interactively define
a new fantasy book in collaboration with the user, then write a complete
`setup.md` file.

## When to invoke

- The user says "new book", "new series", "set up a book", "start a fantasy
  novel", or equivalent.
- There is no `output/<slug>/book-NN/setup.md`, OR there is one and the user
  asks to "redo" it.

## Hard rules

- This project writes **fantasy only**. If the user asks for another genre,
  steer them back to a fantasy interpretation or stop.
- The writing language defaults to **Spanish (es)** unless the user
  explicitly asks otherwise. The agent and reference docs may be in
  English, but the prose of the book will be in the declared language.
- **Do not invent setup details the user has not approved.** You may
  *propose* alternatives, but the user must pick or rewrite.
- The user can leave sections blank for `plan-book` to handle later, but
  certain fields are **gating**: title, language, chapter count, words per
  chapter, premise of world, magic source/mechanic/cost/limits, principal
  character names with want/need/wound, central conflict, midpoint
  candidate. If these are missing, say so before finishing.

## Steps

### 1. Initialize the directory

If the user has not already created the structure:

1. Ask for the **title** (or a working title).
2. Ask whether this is a **standalone** or **book N of a series**.
3. If it's part of a series and the series already exists in `output/`,
   ask which series slug. Otherwise compute the slug from the title.
4. Run:
   ```bash
   python3 .claude/skills/book-setup/scripts/init_book.py \
       --title "<title>" \
       --series-slug "<slug>" \
       --book-number <N>
   ```
   This creates the directory tree and writes a `setup.md` template.

### 2. Walk through `setup.md` interactively

Open `setup.md` and walk the user through each section, in this order
(critical sections first; allow skipping non-critical ones):

1. **Identity** (title, author, subgenre, language, voice, tense). The
   author line is prefilled with the project pen name from `config.toml`
   (`[author] name`); only change it for a book-specific pseudonym.
2. **Length & shape** (chapters, words per chapter, act structure).
3. **Premise of world** (3-5 sentences, era, geography, calendar).
4. **Magic system** — *most important*. Use
   `references/magic-design-checklist.md` as your guide. Push for:
   - A specific source (not "energy").
   - A walkable mechanic.
   - At least two costs visible in prose.
   - At least three hard limits.
   - One thematic question forced by the magic.
   - Three escalation tiers.
5. **Castes / factions / orders.** Aim for 2-4 with stated current
   conflict.
6. **Geography.** 5-10 named places, each with sensory detail.
7. **Historical weight.** 3-5 past events the present reverberates.
8. **Characters — principals.** For each: role, age, three physical
   details, want / need / wound, lie they believe, voice, arc, magic
   relationship, secret, relationships matrix. Don't accept "brave
   warrior" — push for specifics. Use `references/fantasy-beats.md`
   (Character arcs section).
9. **Theme.** Force the user to articulate a moral question, not a
   "what's it about" pitch.
10. **Plot.** Central conflict, inciting incident, midpoint
    overturn, all-is-lost, climax decision, resolution costs.
11. **Subplots.** 1-3, each with theme that differs from main.
12. **POV.** Number, default character, distribution.
13. **Slow-immersion specifics.** Sensory anchors that recur. Texture
    beats budget per chapter.
14. **Prose constraints.** Voice, distance, register, allowed/forbidden tics.
15. **If continuation.** Inherited threads, returning characters,
    unpaid promises.

For each section:
- Read aloud (in the chat) the prompts from the template.
- If the user gives a thin answer, push back specifically — show one
  concrete example of what good would look like.
- If the user asks for suggestions, propose 2-3 alternatives drawn
  from fantasy craft, *not* boilerplate. Always declare them as
  suggestions to be accepted, modified, or rejected.
- Write each section to `setup.md` as soon as the user confirms it.
  Do not batch.

### 3. Validate before finishing

After the walk-through, check the gating fields:
- title, language, num chapters, words per chapter range
- world premise (≥ 3 sentences)
- magic: source + mechanic + ≥2 costs + ≥3 limits + thematic question
- ≥2 principal characters with want/need/wound declared
- central conflict + midpoint + climax decision named

If any are missing, **show the user the list** and ask whether to fill
them now or defer. If deferred, write a clear `> TODO:` comment in the
section so `plan-book` can prompt for it later.

### 4. Wrap up

Confirm the file exists at `output/<series-slug>/book-NN/setup.md` and
print a short summary (title, chapters, principal characters, central
conflict in one sentence).

Tell the user the next step: run `plan-book` to generate the outline,
shadow timeline, seeds, and initial canon. Optionally remind them that
they can edit `setup.md` at any time and re-run `plan-book` to refresh.

## What this skill does NOT do

- Does not generate plot beats or chapter plans (that's `plan-book`).
- Does not write any prose.
- Does not populate `canon/`, `plan/`, or `summaries/`.

## Files this skill writes

- `output/<series>/book-NN/setup.md` (created if absent, then iteratively edited).
- `output/<series>/series.md` (if new series).
- `output/<series>/series-state.md` (empty placeholder if new series).
