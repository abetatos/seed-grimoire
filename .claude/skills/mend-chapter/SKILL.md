---
name: mend-chapter
description: "Post-critique chapter surgery — the single skill that repairs a drafted chapter where its critique named a need. Two mode-families over one chapter: `--mode ground` adds REACTIVE grounding depth (unfold a world element the reader never watched operate, build a space the reader can't draw, show an unpaid cost, put a cold decision's deliberation on the page, re-anchor a disorienting jump, give a prop-secondary one human beat) — ONLY where critique-chapter named an unfired need-test, never on every chapter, never from word count; `--mode polish|trim|tighten-seeds` does the surgical rewrite of named anti-patterns / over-length / off-envelope seeds. In a write-novel run BOTH are normally applied WARM by the chapter's still-alive chapter-smith (its drafting voice); the cold fresh-context chapter-grounder subagent is the fallback for `ground` when no live smith exists (standalone / --in-session). Hard cap 2 ground passes. Use when critique-chapter flags a fix, or the user says 'I can't picture this scene' / 'trim chapter N' / 'the seeds telegraph'. (Merges the former expand-chapter + revise-chapter.)"
---

# mend-chapter (post-critique chapter surgery)

You are running **mend-chapter**. The chapter exists and its critique has named
specific issues. Your job is **targeted repair against the critique's worklist**,
never a rewrite and never a generic pass. This skill merges the two former
chapter-repair skills into one entry with two mode-families:

- **`--mode ground`** — the **reactive grounding fill** (formerly `expand-chapter`):
  adds *depth* at the spots a critique named an unfired need-test. Six licensed
  insert kinds, no new plot, no length target.
- **`--mode polish` (default) / `--mode trim` / `--mode tighten-seeds`** — the
  **surgical rewrite** (formerly `revise-chapter`): fixes named anti-patterns,
  over-length, weak subtext, off-envelope seeds by editing *how* the prose reads,
  not *what* happens.

Pick the mode from the critique's findings: an **unfired need-test** → `ground`;
a **Fix-marked anti-pattern / weak subtext / telegraphed seed** → `polish`; a
**padding** finding → `trim`; a **seed-envelope** finding → `tighten-seeds`. A
single invocation runs ONE mode.

> **Mechanism names.** `ground` mode reuses the pre-existing bundle phase
> `--phase expand`, the `▼▼▼ EXPAND ▼▼▼` markers, and the cold `chapter-grounder`
> subagent. Those keep their historical "expand" names (the strip script, the
> update-canon hash order, and build_context all key on them); only the
> *skill* you invoke changed from `expand-chapter` to `mend-chapter --mode ground`.

---

# Mode: ground (reactive grounding fill)

This is the **reactive grounding fill** — it runs **only** because the critique
(or the author) pointed at a concrete unmet need; there is **no unconditional
pass on every chapter** (detection is the critique's job, on the raw draft, with
these same six need-tests). Never a length fix: word counts are not measured
here. Your job is **not** generic texture or dwelling — under this book's
windowpane style, lingering for its own sake is a defect. The pass adds only
these **six kinds of insert**, and only **at the spots the critique named**:

1. **The world, unfolded more slowly.** A spot where the chapter *uses* a
   world element — a craft step, a rule of the magic, an institution, a
   custom — but rushes past it, so the reader is told rather than shown.
   Slow it down: one paragraph where the POV *works* the element and the
   reader watches the mechanism operate. Felt, not lectured; show it
   working, never explain the system behind it (the iceberg stays under
   the surface).
2. **A visualization passage.** A scene happening in a space the reader
   cannot draw — no scale, no layout, no light, no sense of what stands
   between the character and the door. Build the stage per `style.md`
   ("Build the stage"): establish the space anchored to the POV's body,
   so every action after it happens somewhere the reader can stand.
3. **The bill (cost made visible).** A spot where the page *spends*
   something — magic, physical effort, a favor, a social transgression —
   and moves on without showing the price. Insert the paragraph where
   the cost is *felt*: the hands that shake, the neighbour who no longer
   returns the look, the material that will not be replaced.
   Limitations are more interesting than powers; a spend with no bill
   is a rule quietly broken.
4. **Deliberation on the page.** A decision the chapter already contains,
   taken cold — the POV acts without the reader seeing the weighing.
   Insert the deliberation *before* the hinge, in the POV's own
   vocabulary: options, fears, the calculus. This is what keeps
   transparent prose warm. The hinge itself stays sharp and fast.
5. **Re-orientation after a jump.** A time or place cut that disorients:
   one short paragraph re-anchoring how long has passed, where we are,
   what changed in the gap. The temporal cousin of building the stage.
6. **A secondary in three dimensions.** A named secondary functioning as
   a prop: one specific beat — a gesture, a worn object, a
   contradiction — that makes them a person. **At most one such insert
   per chapter**, or the cast becomes a catalogue.

If a spot needs none of these, it gets nothing. A chapter that is already
grounded, costed, and reasoned takes zero inserts, whatever its word count.
**Precedence:** the beat sheet outranks every need test — a gap the outline
marks as deferred or reserved is a seed, not a need; the test does not fire.

**REFUSAL — a collapsed beat is not a need.** If what the chapter shows is a
beat rendered as narrated summary (events pre-digested, no staged space, no
action-by-action, no POV reasoning), **do not insert anything there**. An
insert on top of a summary is padding stapled over a hole — stretching the
unstretchable is exactly the failure this pipeline bans. Instead, STOP for
that spot and report it: name the beat, quote the summarizing lines, and
route it back to a scene replay (`write-chapter` re-drafts that scene, or
`mend-chapter --mode polish` if the author prefers surgery). The need tests fix
*under-grounded scenes*; they cannot un-summarize a scene that was never
played.

## Hard rules (ground mode)

- **Do not invent new plot beats.** If the chapter has 4 plot beats,
  it still has 4 after the pass. Plot is decided in `plan/outline.md`.
- **Do not contradict canon.** If you need a fact that isn't there,
  flag it — don't make it up silently.
- **Do not pad with filler.** "She walked to the door. She opened the
  door. She stepped through." is failure. Grounding means *deeper
  attention*, not more sentences.
- **Match the voice already on the page.** Read the chapter first.
  Your additions should be indistinguishable from the existing prose.
  If the POV voice is declared *spare* (short sentences, little
  rumination, no big metaphors — see `setup.md`), expand with
  **concrete texture and sensory detail, not interior monologue**.
  Lyrical, ruminative padding is voice drift, not depth. Prefer the
  hand, the object, the labor over the character's thoughts about them.
- **No word counting — the range in `setup.md` is a planning objective,
  not a check.** Generated length is deliberately never measured back to
  the model (a visible count breeds compensation). Do not count the
  chapter's words before, during, or after the pass: every insert is
  justified by a need test or not at all. Stop when the needs are met.
  Better a lean chapter than a padded one.
- **Do not break seed work.** Existing planted/echoed seeds must stay
  exactly where they are. If you move a seed line, you risk breaking
  the echo or payoff chain.
- **Spanish unless setup says otherwise.**

## Steps (ground mode)

### 0. Dispatch the fill to a fresh subagent (main thread only)

If you can spawn subagents (you have the Agent tool) and you were invoked
standalone (not already inside `chapter-grounder`), **do not fill in this
conversation**. Dispatch the fill to the `chapter-grounder` subagent (Agent tool,
`subagent_type: chapter-grounder`) with the prompt
`chapter <M> --series-slug <slug> --book-number <N>` plus the critique's named
unfired need-tests (or the author's pointed spot). It fills in a **fresh context**
— the chapter prose + the expand bundle never enter this conversation, and the
fill is done by eyes that never wrote the prose (the writer is the worst auditor of
its own gaps). It edits `chapters/MM.md` in place and returns what it inserted.
Then run only the interactive tail — report the inserts and any FLAGS to the user.

> When the **chapter-grounder subagent itself** runs this skill it has no Agent
> tool, so it cannot dispatch — it executes the fill directly and stops before the
> report tail. (That is how recursion is structurally prevented.)
>
> **Cold fallback only.** Inside a `write-novel` run the chapter's own
> `chapter-smith` is still alive, so the critique's fill is applied **warm** by that
> smith (via `SendMessage WARM-FIX:`) — same six need-tests, but in the drafting
> voice. The `chapter-grounder` is the **cold** path: it runs only when there is no
> live smith — this skill invoked **standalone** (author points at a spot after the
> chapter is done and the smith released), or `write-novel --in-session`. The
> detector is always the fresh `book-critic` either way, so filling in warm voice
> is not the writer auditing itself.

### 1. Rebuild the context and read the chapter

```bash
python3 .claude/skills/write-chapter/scripts/build_context.py \
    --series-slug <slug> \
    --book-number <N> \
    --chapter <M> --phase expand
```

`--phase expand` builds a lighter bundle: a grounding pass adds no plot and
reveals nothing, so it drops series context, the shadow slice, plan
neighbors/arcs, the story-so-far summaries and the seam. It keeps what a
grounding pass needs — setup, decisions, canon, the seed envelope (so inserts
don't break seed lines), this chapter's beat sheet, style + voice, the
dwelling checklist, and the voice spine last (insertions are exactly where the
tics creep back in). Read both the bundle (`notes/_context-chMM.md`) and the
chapter (`chapters/MM.md`).

### 2. Confirm each named spot fires its need test

**The worklist is the critique's named unfired need-tests** (or, standalone, the
spot the author pointed at) — **not** an independent re-scan of the chapter.
Detection already happened in fresh context (`book-critic`); your job is to
inhabit each named spot and confirm the need before you fill it. A spot the critic
named that turns out already grounded gets **nothing** — over-marking is the
failure mode this reactive split exists to kill. Never hunt the rest of the
chapter for new gaps the critique did not name.

**One read, one verdict.** The tests fire on a first attentive read or
not at all — do not re-read hunting for candidates; a need you must hunt
for is not a need (it is the compliance reflex inventing work).

**Write the candidate list before any prose.** At most 6 lines, each:
the exact quoted line where the need shows + which test + a one-line
insert plan. A candidate that cannot quote its line is invented — drop
it. Then write only the strongest survivors (3 inserts max, as ever);
listing is not committing, and an **empty list is a valid verdict** —
report zero inserts and stop.

Scan the chapter and collect candidate spots with the six need tests:

- **World-rush test:** does a sentence *invoke* a world element (craft,
  magic rule, institution, custom) that the reader has never watched
  operate? A noun doing a system's work ("pagó el diezmo del color",
  "templó el hilo") is a candidate for an unfolding paragraph — the
  first time. An element already unfolded in an earlier chapter is NOT
  a candidate again (trust the reader).
- **Blur test:** could the reader draw the space this scene happens in —
  scale, layout, light, what is underfoot, what stands between the POV
  and the exit? If not, and the scene *uses* the space (movement,
  distance, hiding, work), it is a candidate for a stage-building
  passage. A scene that never uses its space needs no stage.
- **Unpaid-bill test:** does the scene spend magic, effort, a favor, or
  a transgression and move on with no visible price? Candidate for a
  cost paragraph.
- **Cold-decision test:** does the POV make a choice the reader never
  saw weighed? If the choice matters (it changes his situation), it is
  a candidate for a deliberation paragraph placed *before* the hinge.
  Trivial choices stay cold — deliberating everything is drift.
- **Lost-reader test:** after a time/place cut, would a first-time
  reader know how long passed, where we are, and what changed? If not,
  candidate for a short re-orientation paragraph at the top of the scene.
- **Prop test:** is a *named* secondary doing plot work with zero
  specific humanity on the page? Candidate for one three-dimensions
  beat (max one per chapter, and never during a hinge).

Constraints on candidates:

- **Hinges stay sharp.** Do not expand inside a decision, conflict, or
  revelation beat; ground *before* the hinge so the hinge can move fast.
- **Transitions almost never qualify.**

### 3. Choose techniques from `dwelling-techniques.md`

Read the techniques reference and pick the ones that serve the insert's
job — techniques are means, the six insert kinds are the end:

- For a **world-unfolding paragraph**, the natural fits are **texture of
  labor** (the hands, the resistance of the material, the small
  failures — the mechanism seen through work) and **sensory anchoring**
  (the element known by smell, sound, weight, not by name).
- For a **stage-building passage**, use the "Build the stage" rules in
  `style.md` directly: establish before moving, anchor geometry to the
  body, concrete over generic, re-anchor when the space changes.
  **The room remembered** (one object with a history placed *in* the
  space) can double as furniture and character.
- For a **cost paragraph**, keep it in the body and the world (sensory
  anchoring again): the price is a sensation, an object consumed, a
  changed reaction from someone — never the narrator announcing "it had
  cost him".
- For a **deliberation paragraph**, **interior in motion** is the tool:
  the weighing happens *during* an action, in the POV's vocabulary,
  and ends in the choice the chapter already makes.
- A **re-orientation** or **secondary beat** is short and plain — no
  technique needed beyond one concrete anchor.
- **Time held still** is seasoning, not a basis for an insert on its
  own — under the windowpane style an insert must ground, unfold, cost,
  or reason, not merely linger.

### 4. Apply the fill in-place

Use the Edit tool to insert new prose into the chapter file. Each
insertion should:

- Be sized to its job: 60-150 words for a re-orientation or a secondary
  beat; 150-400 words of continuous prose for an unfolding, stage, cost,
  or deliberation passage. Never a list of beats.
- Sit at a spot that failed a need test in step 2, inside a scene the
  chapter already has.
- Begin with a sensory anchor (smell, sound, touch, taste).
- Carry **at least one subtext layer** — what the POV feels but
  doesn't say.
- Read invisibly *between* its markers: the prose itself should feel
  as if it was always there (the markers below are a temporary
  scaffold, not part of the prose).

Acceptable to insert at multiple points, but **3 insertions max** per
ground pass. More than that and the chapter loses shape.

### 4b. Mark each grounded zone (temporary repo standard)

> **Standard while this repo is early:** every inserted zone is wrapped
> in visible text markers so the author can read the chapter (including
> on Kindle) and tell original prose from added prose, and compare
> options. These markers stay in the file for now; they will be stripped
> in a later cleanup pass once the workflow is trusted.

Wrap each insertion with **numbered** visible markers on their own
lines, blank line above and below:

```
▼▼▼ INICIO EXPAND N (prosa AÑADIDA — no original) ▼▼▼

<inserted prose>

▲▲▲ FIN EXPAND N ▲▲▲
```

- **The number is the ground PASS (this skill invocation), not the
  zone.** Before adding anything, scan the chapter for existing
  `EXPAND` markers:
  - No `EXPAND` markers found → this is **pass 1**: mark *every* zone
    you add in this invocation as `EXPAND 1`.
  - `EXPAND 1` markers already present → this is **pass 2**: mark
    *every* zone you add in this invocation as `EXPAND 2`.
  - All zones added in the *same* invocation share the *same* number,
    however many they are. This way the author sees exactly what each
    call contributed and can compare passes. Full control.
- Use the language of the prose (Spanish by default).
- Plain text markers only — not HTML comments — so they survive the
  EPUB/Kindle export and are visible when reading.
- **Cap: at most 2 ground passes per chapter.** Do not invoke this mode
  a third time on the same chapter.

### 5. Every pass is on demand — never from length

There is **no verification step and no word count**. **Both** passes are reactive
(there is no unconditional pass): each runs only when the critique names a need
test that fired with no insert, or the author asks — with the 2-pass hard cap per
4b. Never re-invoke the mode on your own initiative, and never count words to
decide anything. If, filling a named spot, you suspect the outline planned too few
texture beats for this chapter, flag that to the user as a plan observation — do
not fix it with inserts.

### 6. Report (ground mode)

- Number of inserts, by need-test type (zero is a valid outcome).
- Which scenes you grounded (one line each).
- Which dwelling techniques you used (named, from the reference).
- Anything you noticed that should be flagged: missing canon facts,
  weak subtext, brittle transitions.

---

# Mode: polish / trim / tighten-seeds (surgical rewrite)

The chapter exists. The critique has named specific issues. Your job is
**targeted edits**, not a rewrite.

## Hard rules (surgical modes)

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

## The three surgical modes

### `--mode polish` (default)
Address all Fix / SHOULD-fix items from `notes/critique-chNN.md`. Anti-
pattern phrases get replaced with specific sensory alternatives.
Weak subtext gets a layer added. Telegraphed seeds get rephrased
to embed more naturally. Flat dialogue gets sharpened.

### `--mode trim`
The chapter is over target. Cut without losing texture. Look for:
- Repeated sensory beats (kept one, cut the rest)
- Over-explained subtext (cut the explanation, keep the gesture)
- Long monologues — let action carry weight instead
- Adjective stacks ("the dim, cold, silent room")

Goal: preserve every plot beat, texture scene, and seed while cutting the
padding the critique named. **No word count** — trim is done when every flagged
padding finding is cut, not when a number is reached (the pipeline never
measures generated length back to the model); a re-critique judges the result.

### `--mode tighten-seeds`
The seed envelope was off — seeds telegraphed, echoes verbatim,
payoff explained. Walk each seed in the envelope and adjust *only*
those lines using `references/seed-craft.md` rules:
- Plants: embed in scene action, no flag words.
- Echoes: oblique, different sensory register.
- Payoffs: trust the reader; remove "she realized" / "it dawned".

## Steps (surgical modes)

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

### 3. Report (surgical modes)

**No word count** — do not count words or compare length to the setup range
in any mode. Print:
- Number of edits made, grouped by tier.
- Any issues skipped (with reason).
- Suggested next step: `critique-chapter <N>` again, or `update-canon <N>`.

---

## What this skill does NOT do

- Does not add new plot beats, characters, or settings.
- Does not change the chapter's POV, tense, or voice.
- Does not modify seeds, shadow, or plan files (it only edits the
  chapter prose; seed *status* is `update-canon`'s job).
- Does not update canon or lock the chapter in (that's `update-canon`,
  and only when the author agrees).
- Does not invent content. Every insert/replacement must be derivable
  from the existing scene + canon + plan.