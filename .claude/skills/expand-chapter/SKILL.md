---
name: expand-chapter
description: Add depth to scenes already on the page — texture, interior, dwelling — without inventing new plot. Runs as a mandatory texture pass on every chapter (the author wants the added paragraphs even at length), and again to grow a chapter that is still under target word count. Use this after write-chapter (texture pass), when `check_wordcount.py` reports `too_short`, or when the user says "this is too short" / "dwell more in chapter N".
---

# expand-chapter

You are running the **expand-chapter** skill. The chapter exists. Either
it came in under word target, or this is the mandatory **texture pass** the
pipeline runs on every chapter even when it is already at length (the author
wants the added dwelling paragraphs — they give the prose texture). Your job
is to **make it breathe**, not to add events.

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
- **Do not force an invented floor.** The word range in `setup.md` is a
  guide, not a law. A chapter that lands a little short because the
  scenes are dense is fine. Better a lean chapter than a padded one;
  never stretch prose to hit a number. Expand only where the scene
  genuinely wants more inhabitation.
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
    --chapter <M>
```

Read both the bundle (`notes/_context-chMM.md`) and the chapter
(`chapters/MM.md`). Note the current word count and the target.

### 2. Identify where to dwell

Scan the chapter and tag scenes as:

- **Hinge** — a plot beat. Decision, conflict, revelation. Do not
  expand these unless the user explicitly asks; hinges should be sharp.
- **Texture** — a daily-life scene, a craft, a meal, a journey. **These
  are where you expand.**
- **Transition** — a connective tissue passage. Almost never the place
  to add.

Aim to move the chapter *toward* the range, distributing a few
dwellings across texture scenes — but do not chase the midpoint as a
quota. Stop when the scenes have the depth they want, even if that
leaves the chapter a little under the floor. A natural short chapter
beats a stretched one.

### 3. Choose techniques from `dwelling-techniques.md`

Read the techniques reference and pick **at least three** to apply.
Common choices for under-length chapters:

- **Sensory anchoring** — replace a visual description with a non-visual
  one (smell, sound, weight). Re-anchor the scene to the body.
- **Texture of labor** — if the POV is doing a craft, slow it down.
  The hands, the resistance of the material, the small failures.
- **Interior in motion** — let the POV's thinking drift sideways
  *during* an action. Memory cuts in, then the action resumes.
- **The room remembered** — let the POV notice an object that has a
  history. One specific over three vague.
- **Time held still** — a paragraph where physical action stops and
  the world is photographed.

### 4. Apply expansion in-place

Use the Edit tool to insert new prose into the chapter file. Each
insertion should:

- Be 200-500 words of continuous prose, not a list of beats.
- Sit *inside* a texture scene the chapter already has.
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

### 5. Verify

```bash
python3 .claude/skills/write-chapter/scripts/check_wordcount.py \
    --series-slug <slug> --book-number <N> --chapter <M>
```

This was pass 1 (its zones are marked `EXPAND 1`). If the chapter is
still under the floor, you may invoke the skill **once** more; that
second invocation is pass 2 and marks its new zones `EXPAND 2` (two
passes is the hard cap). If after two passes the chapter is still a
little short, **that is acceptable** — do not pad to force the floor.
Report the count and move on. Only if the chapter is *dramatically*
short (well under the floor) should you suspect the outline planned too
few texture beats, and flag that to the user.

### 6. Report

- Final word count vs. target.
- Which scenes you expanded (one line each).
- Which dwelling techniques you used (named, from the reference).
- Anything you noticed that should be flagged: missing canon facts,
  weak subtext, brittle transitions.

## What this skill does NOT do

- Does not add new plot beats, characters, or settings.
- Does not change the chapter's POV, tense, or voice.
- Does not modify seeds, shadow, or plan files.
- Does not update canon (that's `update-canon`).
