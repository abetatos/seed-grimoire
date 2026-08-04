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
7b. **World texture — the lived-in world.** Use
    `references/world-texture.md`. This is the design-time catalog that
    makes the world feel *inhabited*, not mapped. Push for: the **economy
    of the magic** (jobs it creates, who profits/pays, the black market); a
    stock of **concrete daily nouns** (food, coin, craft, the working day);
    **culture** (at least one oath/curse, one piece of slang, one
    superstition, one festival/calendar marker); **class markers** the
    reader reads at a glance. Every texture element should have a *job*
    (gate a beat / mark a character / carry a seed) — jobless texture is
    cut. Weight it toward act 1 (inhabitation).
8. **Characters — principals.** Use `references/character-craft.md` — the
   Want/Need/Wound/Lie skeleton is the floor, not the ceiling.
   - **Inherit the §9d slice first (multi-book series).** If the series
     grimoire has a §9d "Arco de serie por personaje", read this book's column
     for each principal (initial state / this-book's turn / whether their Lie
     pays here) and each cross-book hilo that turns or pays in **this** book.
     That slice is the **starting point** for the arcs below — do NOT re-invent
     each principal from zero; extend the series arc into this book's beats. If
     this book genuinely needs to diverge from §9d, say so in the setup notes so
     `plan-book` records it as a series-level flag in `notes/decisions.md`;
     reconciling §9d itself is a deliberate `forge-grimoire` re-run, not an
     automatic step. (Standalone book / no §9d: skip this and design the arcs
     fresh.)

   For each principal: role, age, three physical details, want / need / wound,
   lie they believe, voice, arc, magic relationship, secret, **and the four
   depth levers**:
   - **The contradiction** (§1) — one live contradiction, two true things
     that shouldn't both be true. If you can't name it, it's a function,
     not a person. Required for every principal.
   - **The magic↔lie interlock** (§3) — how *this* character's specific
     relation to the magic dramatizes *their* Lie (and pays a cost where
     their wound already is). Required for **every** principal, not just the
     protagonist.
   - **Antagonist = dark mirror** (§4) — the antagonist shares the
     protagonist's wound and chose the opposite cure; right about the
     diagnosis, wrong about the cure; name **both** the proximate face and
     the systemic antagonist. A stated "thesis" is the floor; the mirror is
     the bar.
   - **The divergence pass** (§6) — for the protagonist's **defining
     flaw**, the antagonist's **thesis**, and any **stock role** the plot
     leans on (mentor, love interest, loyal friend, rival), do NOT accept
     the first idea. Generate **three genuinely different takes** (diverging
     on a load-bearing axis, not cosmetics) and present them as an
     `AskUserQuestion` so the author picks or grafts. This is the guard
     against "recombinación de elementos manidos".
   Don't accept "brave warrior" — push for specifics.
8b. **Relationships as designed dyads.** Use
    `references/relationship-craft.md`. Depth lives *between* people. Don't
    settle for a "relationships matrix" of who-knows-whom — design each
    important pair as a **dyad arc**: what A wants FROM B, what B wants FROM
    A (usually asymmetric — §2), the **misread** each holds of the other,
    the **turn** (the chapter where the dynamic flips), the end-state. Floor
    (§6): protagonist↔antagonist (the master foil), protagonist↔closest
    bond, and **at least one dyad that does NOT involve the protagonist**.
    Name which pairs are **foils** and what thesis each argues.
8c. **The ensemble — 3–6 memorable secondaries.** Use
    `references/character-craft.md` §5. "Faltan personajes" is a thin
    ensemble, not too few principals. Design 3–6 named secondaries who are
    not principals but not props. Each gets **one physical tell**, **one
    micro-want of their own** (a want that predates the protagonist and
    outlasts them — their story, glimpsed), and **one relationship to a
    principal**. Apply the **cut-the-protagonist test**: remove the
    protagonist from the scene — does the secondary still want something? If
    they go inert, they're a prop; give them their own errand or demote them
    to a role ("the ferryman").
9. **Theme.** Force the user to articulate a moral question, not a
   "what's it about" pitch.
10. **Plot.** Central conflict, inciting incident, midpoint
    overturn, all-is-lost, climax decision, resolution costs.
11. **Subplots.** 1-3, each with theme that differs from main.
12. **POV.** Number, default character, distribution.
13. **Slow-immersion specifics.** Sensory anchors that recur. Texture
    beats budget per chapter.
14. **Prose constraints.** Voice, distance, register, allowed/forbidden tics.
14b. **Voice contract → `notes/voice-spine.md`.** Right after prose
    constraints, ask the author THREE questions and write the answers as
    3-4 bullets to `notes/voice-spine.md` (this book's half of the voice
    spine — the write bundle assembles it into the writer's recency slot,
    so this is where the book's *punto especial* lives, not in exemplars):
    1. **The governing sense.** What is the ONE sensory system this book
       runs on (a colour draining, a sound the world makes, a weight)?
       The bullet commits the writer to one concrete non-visual sensation
       per scene in that system.
    2. **The POV's vocabulary.** How does the default POV understand the
       world (a craft, an age, an obsession)? The narration reasons in
       that vocabulary and no other.
    3. **The licensed signature.** What is the ONE stylistic move this
       book — and only this book — has special permission for (e.g. a
       fused sense-image)? Named and rationed here; everything else
       follows the house style.
    Format: a `#` title + `>` provenance blockquote (both stripped at
    assembly) + the bullets. Cap: 4 bullets. Propose a draft of each
    bullet from the setup answers; the author confirms or rewrites.
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

Then run a **depth check** (non-gating, but flag every gap — these are what
`critique-grimoire`/`critique-plan` will otherwise catch later):
- Each principal has a **contradiction** and a **magic↔lie interlock**.
- The antagonist is a **dark mirror** (shared wound, opposite cure), not
  just "has a thesis"; proximate *and* systemic both named.
- ≥ 3 **ensemble secondaries**, each with a tell + a micro-want.
- The dyad floor is met: protag↔antag, protag↔closest bond, and ≥ 1 dyad
  not involving the protagonist.
- World texture: the magic's economy + at least one culture element
  (oath/slang/superstition/festival).

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
- `output/<series>/book-NN/notes/voice-spine.md` (the voice contract, step 14b).
- `output/<series>/series.md` (if new series).
- `output/<series>/series-state.md` (empty placeholder if new series).
