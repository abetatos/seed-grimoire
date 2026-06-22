---
name: critique-plan
description: Hard, structured critique of a finished book plan — setup, outline, shadow, seeds, arcs, canon — against rhythm, plot, foreshadowing, magic system completeness, and worldbuilding economy. Produces a written critique (`notes/critique-plan.md`) with prioritized findings and concrete fixes. Use this after `plan-book` and before `write-chapter 1`. Invoke as "critique the plan" / "audita el planteamiento".
---

# critique-plan

You are running the **critique-plan** skill. The plan is finished (or
the user thinks it is). Your job is to **find what's wrong with it**
before any prose is written.

The user has explicitly asked for this to be **adversarial**, not
validating. Push back. The plan exists to be stress-tested.

## When to invoke

- "Audita el planteamiento" / "critique the plan" / "is this plan
  ready?" / "review the book plan".
- After `plan-book` and before `write-chapter 1` — even on user
  request.
- Also reasonable as a re-check after a major plan revision.

## Hard rules

- **Be specific.** "Structure is weak" is useless. "Act 1 spans 9
  chapters but no character arc shows movement until chapter 7" is
  useful.
- **Quote the offending line / cite the chapter number / name the
  seed id.** Always.
- **Tier ruthlessly:**
  - **MUST fix** — breaks the contract: missing climax decision,
    seeds with no payoff, principals with no decision moment, magic
    with no cost or limits, outline chapters with TODO-only beats.
  - **SHOULD fix** — weakens the book: thin texture-beat plans,
    midpoint that doesn't overturn anything, faction declared but
    never used, action stacking, telegraphed seeds.
  - **CONSIDER** — taste-level. The user can ignore.
- **Do not rewrite the plan.** Quote, name, point. Direction yes;
  substitute prose no.
- **Adversarial bias.** When unsure, escalate the tier. A plan that
  passes critique-plan with zero issues is suspicious; you missed
  something.

## Steps

### 1. Run the deterministic audit

```bash
python3 .claude/skills/critique-plan/scripts/audit_plan.py \
    --series-slug <slug> --book-number <N> \
    --output output/<series>/book-NN/notes/_audit-plan.md
```

The audit checks mechanical truths: gating fields, TODO-only chapters,
seed validity, decision-chapter presence on each arc, canon entries
absent from outline, magic completeness. Read this file — it gives
you the baseline list of MUST-fix items.

### 2. Read the plan in full

Read in this order:

1. `setup.md`
2. `plan/outline.md`
3. `plan/shadow.md`
4. `plan/seeds.md`
5. `plan/arcs.md`
6. `canon/characters.md`, `canon/factions.md`, `canon/magic.md`,
   `canon/world.md`, `canon/timeline.md`
7. References for what "good" looks like:
   - `references/fantasy-beats.md`
   - `references/seed-craft.md`
   - `references/magic-design-checklist.md`
   - `references/hard-magic-laws.md`

### 3. Run the qualitative pass

Go through each of these categories. For every check, produce a
finding (or "clean") for the critique buffer.

#### 3a. Structure
- Act boundaries — does act 1 take enough time to **inhabit** the
  world (slow-immersion), or does it rush?
- Midpoint — does *something the reader believed* get overturned at
  the named midpoint chapter? Quote the chapter's beat sheet to
  prove it.
- All-is-lost — is there a named chapter where everything appears
  beaten? Or does the plan skip from rising action to climax?
- Climax — does the climax decision rest on **something that was
  planted earlier** (a magic capability seen, a relationship built,
  a seed paid)? If the climax depends on a tool that appears in its
  own chapter for the first time, that is `MUST fix`.

#### 3b. Plot / trama
- Causal chain — does each chapter's plot beat follow from the prior
  chapter's outcome, or are there leaps?
- Motivation — at every plot beat, can the POV character plausibly
  *want* this with what they know at that point? Flag any decision
  that requires offstage information.
- Coincidence load — count the moments where chance moves the plot.
  More than 2 in act 2 is a `SHOULD fix`.
- Antagonist competence — does the antagonist have a coherent plan
  in the shadow file? If shadow says "they happen to be there", it
  is `MUST fix`.

#### 3c. Ritmo / pacing
- Chapter function — every chapter must do something for the larger
  arc. Flag chapters whose function is "more of the same".
- Action stacking — two action-heavy chapters back-to-back without
  a quiet chapter between is `SHOULD fix` per
  `references/fantasy-beats.md` pacing rules.
- Texture distribution — count chapters with explicit texture beats
  planned. If many lack texture beats, the book will come out short
  and dry. `SHOULD fix` per chapter.
- Dwelling in act 1 — at least 60% of act 1 chapters should plan a
  texture beat. If under, the book won't feel inhabited.

#### 3d. Magic system
- Source, mechanic, costs (≥2), hard limits (≥3), thematic question,
  three escalation tiers — every one of these must be present and
  specific. `MUST fix` any missing.
- Costs visible in prose — does the outline name **which chapters
  show the cost** in action? If costs are stated in canon but never
  appear in outline texture beats, the magic will feel cheap.
- Apex tier visible only at climax — flag if apex magic appears in
  act 1 or 2. The climax loses its ceiling.
- Thematic question forced at climax — does the climax beat sheet
  put the thematic question in the protagonist's hands? `MUST fix`
  if not.

#### 3e. Characters
- Distinct arcs — read each principal's want/need/lie/decision. If
  two principals have the **same lie** or the same decision shape,
  the book has only one arc. `SHOULD fix`.
- Decision chapter alignment — the protagonist's decision moment
  should sit at the climax. Secondary characters' decisions should
  feed into the climax. Flag misalignments.
- POV economy — is every declared POV needed? A POV with fewer than
  3 chapters of presence is `CONSIDER`. A POV character who never
  carries a plot hinge is `SHOULD fix`.
- Physical specifics — three concrete details per principal, no
  clichés. Vague entries are `SHOULD fix`.

#### 3f. Subplots
- Count subplots. If 0, flag — epic fantasy needs ≥1 subplot to
  breathe outside the protagonist.
- Touchpoints — each subplot must touch the main plot at ≥3 points.
  Quote them. `MUST fix` if a subplot is hermetic.
- Resolution timing — subplots should resolve before or during the
  climax. Any that resolve after are `SHOULD fix` (energy drains).
- Distinct theme — subplot themes must differ from the main theme.
  If both arcs argue the same thing, the subplot is decoration.

#### 3g. Foreshadowing / seeds
- Density — ≥ 8 seeds for an epic fantasy. Fewer is `SHOULD fix`.
- Distribution — plants weighted toward act 1 / early act 2;
  payoffs weighted toward act 2B / act 3. The audit shows per-act
  counts. Flag inversions.
- Telegraphing risk — read each seed's `how_to_plant`. If it sounds
  like the seed *is* the scene's purpose ("a strange old man with
  glowing eyes appears at the door"), it telegraphs. `SHOULD fix`,
  citing `references/seed-craft.md`.
- Echo gaps — if a seed plants in chapter 3 and pays off in chapter
  20 with no echoes between, the reader will have forgotten it.
  `SHOULD fix`.
- Climax-as-payoff — does the climax pay off **at least one major
  seed**? If not, the climax floats. `MUST fix`.
- **Trigger soundness (event payoffs).** For every seed whose payoff is an
  *event* (something breaks, fires, collapses, is discovered), is there a
  `Trigger` field naming an **intrinsic, already-seeded** cause? A payoff with
  no trigger, or a trigger that is a convenient external actor (a horse, a
  storm, a stranger who only shows up to cause it), is `SHOULD fix` — the
  writer will improvise a contrivance at writing time. Cite the seed id and
  the missing/weak trigger.
- **Telegraph by dose & distance.** Flag any seed whose payoff is **≤2
  chapters** from its plant **and** that also carries echoes or a heavy
  `how_to_plant` — it will be "seen coming a mile off". Each such seed needs a
  `Dose` field constraining it to one quiet touch. `SHOULD fix`, citing the
  plant/payoff chapters.
- **Emotional spine present.** Are there ≥2 **resolution-type** seeds (a
  `Resolution image`: a planted felt-image the payoff inverts/transforms), so
  the book *resolves* and not merely *concludes*? Zero is `SHOULD fix` — the
  plot will pay off but the book will feel mechanical, "not woven".

#### 3h. Worldbuilding economy
- Named characters who never appear in the outline — the audit
  flags these. Each is `SHOULD fix` (either use them or cut them).
- Named factions never used in outline — same.
- Named places never used in outline — same.
- Historical events declared but not echoed — historical weight
  exists to reverberate. If no chapter touches a declared past
  event, it is decoration. `CONSIDER`.

#### 3i. Shadow honesty
- Overview — does the shadow overview actually reveal a different
  story than the outline? If shadow restates the outline in code
  words, there is no hidden layer. `MUST fix`.
- Master truths — are there ≥ 5 truths the reader will discover
  *later*? Each must have a chapter pointer.
- Antagonist knowledge — does the shadow describe what the
  antagonist *knows* that the protagonist doesn't? `SHOULD fix` if
  silent.

#### 3j. Consistency
- Cross-check names: do the principals in `arcs.md` match the names
  in `canon/characters.md`? Mismatches = `MUST fix`.
- Cross-check seed plant/payoff chapters against outline: does the
  named chapter exist and have a relevant subtext beat? Mismatches
  = `SHOULD fix`.

### 4. Write the critique

Write to:

```
output/<series>/book-NN/notes/critique-plan.md
```

Structure:

```markdown
# Plan critique — <book title>

**Verdict:** PASS / REVISE / REJECT

**Summary:** one-paragraph diagnosis.

## MUST fix
- **[category — short label]** — concrete finding with a quoted
  line or chapter pointer → suggested direction.
- ...

## SHOULD fix
- ...

## CONSIDER
- ...

## What works
- 3-6 brief notes on what the plan does well. Important — the user
  needs the signal too.
```

Thresholds:
- `MUST fix` count > 0 → **REJECT**.
- `SHOULD fix` count > 6 → **REVISE**.
- Otherwise → **PASS**.

### 5. Report to user

Print:
- Verdict and counts by tier.
- The 3-5 most load-bearing findings (one line each).
- Path to the critique file.

Then go **straight into step 6** — do not just leave the verdict and wait.
The contract is: critique-plan ALWAYS ends by offering possible solutions
as an `AskUserQuestion` menu, not as free prose the author has to parse.

### 6. Offer solutions as an AskUserQuestion menu

After reporting, surface the findings the author must act on as **choices
with concrete solutions** — this is the required closing move of the skill.

- **PASS, zero MUST/SHOULD** → one confirm question: "Plan looks ready —
  proceed to chapter 1?" with options `write chapter 1 (recommended)` /
  `keep polishing CONSIDER items` / `re-audit`.
- **REVISE / REJECT** → take the load-bearing findings (MUST first, then
  SHOULD) and present them as `AskUserQuestion` questions, **up to 4 per
  call** (batch the rest into a second call after). For each finding:
  - `question`: the problem in one line, quoting the offending plan text /
    chapter / seed id.
  - `options`: **2-4 concrete solutions to THAT problem**, the one you
    recommend first and labelled "(recommended)". Each option is an actual
    fix (e.g. "Move the apex-tier reveal from ch7 to the climax (ch28)",
    "Add a Trigger to seed S-04: the dam was already cracked in ch9"), not
    a vague direction. The author can always pick "Other" to dictate their
    own fix.

After the author chooses:
- Apply each chosen solution by editing the specific `plan/*.md` /
  `canon/*.md` / `setup.md` file (you may edit directly once they've
  picked — the choice IS their consent for that fix).
- Re-run `audit_plan.py` to confirm the mechanical issues cleared.

Do **not** re-run the full qualitative pass in this same conversation —
go to step 7. The re-audit happens in a FRESH session (the plan changed
and this context is now heavy; re-auditing here invites failures).

### 7. Drop the /clear sentinel and HARD STOP

critique-plan is a token-heavy step (it loads the whole plan + references).
Once you have either applied fixes or confirmed PASS, **end the session**
the same way locked chapters do: drop a sentinel so the Stop hook reminds
the author to `/clear`, then STOP unconditionally.

Write the sentinel **with a message** (the hook uses the file's content as
the reminder text):

- If the plan was edited this turn (verdict was REVISE/REJECT):
  ```bash
  printf '%s' '🔧 Plan editado. ESTÁNDAR: ejecuta /clear y reentra con resume-act — el dispatcher volverá a critique-plan para re-auditar en limpio (verdict aún no es PASS).' \
    > output/<series>/book-NN/notes/.clear-pending
  ```
- If the verdict is PASS with nothing to fix:
  ```bash
  printf '%s' '✅ Plan PASS. ESTÁNDAR: ejecuta /clear y reentra con resume-act (→ escribir capítulo 1 en sesión fresca).' \
    > output/<series>/book-NN/notes/.clear-pending
  ```

Then print a short closing (verdict, what was edited, path to the critique)
and as the last line tell the author:

```
ESTÁNDAR: ejecuta /clear ahora y reentra con resume-act.
```

Do **not** continue into another critique pass or into writing in this
conversation. The loop is: critique → fix → `/clear` → resume-act (→
critique-plan again until verdict PASS, then → write-novel). Because
`detect_phase` only treats critique-plan as done when the verdict is
**PASS**, this loop terminates correctly on its own.

## What this skill does NOT do

- Does not modify `plan/*.md`, `canon/*.md`, or `setup.md` without
  explicit user direction.
- Does not write prose.
- Does not invent plot or characters.
- Does not "fix" the plan — it diagnoses. The user repairs (with you
  if they ask).
