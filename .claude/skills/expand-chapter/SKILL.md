---
name: expand-chapter
description: Add depth where the chapter shows a need — unfold a world element the reader never watched operate, build a passage that lets the reader visualize the space, show the unpaid cost of a spend, put a cold decision's deliberation on the page, re-anchor after a disorienting jump, or give a prop secondary one human beat — without inventing new plot. Runs as a mandatory grounding pass on every chapter, and again (pass 2, the cap) only when the critique names a need test that fired with no insert. Never triggered by word count — the pipeline does not measure generated length. Use this after write-chapter (grounding pass), when critique-chapter flags an under-dwelt spot, or when the user says "I can't picture this scene" / "dwell more in chapter N".
---

# expand-chapter

You are running the **expand-chapter** skill. The chapter exists. This is
the mandatory **grounding pass** the pipeline runs on every chapter — or a
second pass because the critique (or the author) pointed at a concrete
unmet need. Never a length fix: word counts are not measured here. Your job
is **not** generic texture or dwelling — under this book's windowpane style,
lingering for its own sake is a defect. The pass adds only these **six kinds
of insert**, and only **where the chapter shows the need**:

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

## Hard rules

- **Do not invent new plot beats.** If the chapter has 4 plot beats,
  it still has 4 after expansion. Plot is decided in `plan/outline.md`.
- **Do not contradict canon.** If you need a fact that isn't there,
  flag it — don't make it up silently.
- **Do not pad with filler.** "She walked to the door. She opened the
  door. She stepped through." is failure. Expansion means *deeper
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

## Steps

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

### 2. Identify where the need shows

**One read, one verdict.** The tests fire on a first attentive read or
not at all — do not re-read hunting for candidates; a need you must hunt
for is not a need (it is the compliance reflex inventing work).

**Write the candidate list before any prose.** At most 6 lines, each:
the exact quoted line where the need shows + which test + a one-line
insert plan. A candidate that cannot quote its line is invented — drop
it. Then write only the strongest survivors (3 inserts max, as ever);
listing is not committing, and an **empty list is a valid verdict** —
report zero inserts and stop.

The need tests — one per insert kind:

- **World-rush test (→ 1):** a sentence *invokes* a world element (craft,
  magic rule, institution, custom) the reader has never watched operate —
  a noun doing a system's work ("pagó el diezmo del color", "templó el
  hilo"). First time only: an element already unfolded in an earlier
  chapter is NOT a candidate again (trust the reader).
- **Blur test (→ 2):** the reader could not draw the space — scale,
  layout, light, what is underfoot, what stands between the POV and the
  exit — AND the scene *uses* the space (movement, distance, hiding,
  work). A scene that never uses its space needs no stage.
- **Unpaid-bill test (→ 3):** the scene spends magic, effort, a favor, or
  a transgression and moves on with no visible price.
- **Cold-decision test (→ 4):** a choice that matters (it changes the
  POV's situation) is taken with the weighing unseen. Trivial choices
  stay cold — deliberating everything is drift.
- **Lost-reader test (→ 5):** after a time/place cut, a first-time reader
  wouldn't know how long passed, where we are, and what changed.
- **Prop test (→ 6):** a *named* secondary is doing plot work with zero
  specific humanity on the page (max one per chapter, never during a
  hinge).

Constraints on candidates:

- **Hinges stay sharp.** Do not expand inside a decision, conflict, or
  revelation beat; ground *before* the hinge so the hinge can move fast.
- **Transitions almost never qualify.**

### 3. Choose techniques from `dwelling-techniques.md`

Read the techniques reference and pick the ones that serve the insert's
job — techniques are means, the insert kinds are the end:

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

### 4. Apply expansion in-place

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
expansion pass. More than that and the chapter loses shape.

### 4b. Mark each expanded zone (temporary repo standard)

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

- **The number is the expand PASS (this skill invocation), not the
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
- **Cap: at most 2 expand passes per chapter.** Do not invoke the skill
  a third time on the same chapter.

### 5. Second pass — only on demand, never from length

There is **no verification step and no word count**. A second pass (pass 2 —
numbering and the 2-pass hard cap per 4b) happens only when the critique
names a need test that fired with no insert, or the author asks for one.
Never re-invoke the skill on your own initiative, and never count words to
decide anything. If your one attentive read left you suspecting the outline
planned too few texture beats for this chapter, flag that to the user as a
plan observation — do not fix it with inserts.

### 6. Report

- Number of inserts, by need-test type (zero is a valid outcome).
- Which scenes you expanded (one line each).
- Which dwelling techniques you used (named, from the reference).
- Anything you noticed that should be flagged: missing canon facts,
  weak subtext, brittle transitions.

## What this skill does NOT do

- Does not add new plot beats, characters, or settings.
- Does not change the chapter's POV, tense, or voice.
- Does not modify seeds, shadow, or plan files.
- Does not update canon (that's `update-canon`).
