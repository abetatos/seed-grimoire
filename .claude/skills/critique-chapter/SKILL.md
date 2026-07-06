---
name: critique-chapter
description: Hard, structured critique of a written chapter against the book's own contract — beat sheet, canon, shadow, seed envelope, prose anti-patterns, dwelling techniques. Produces a written critique with prioritized issues and concrete fixes. Use this after a chapter is written and before `update-canon` locks it in. Invoke as "critique chapter N".
---

# critique-chapter

You are running the **critique-chapter** skill. Read a chapter against the
bundle that produced it and report where it succeeds and fails. The critique
is **for the user**, not for you to silently fix — the user decides what to
apply.

> **Runs headless.** This critique always audits in a **fresh context** (the
> `book-critic` subagent), never in the conversation that wrote the chapter —
> see step 0. When you ARE the subagent, step 4 "Report to user" means
> **return the verdict + counts + load-bearing findings to the orchestrator** —
> your final message is the report. Still write the `notes/critique-chNN.md`
> file; never edit the chapter.

## Hard rules

- **Be specific and quote the offending line — always.** "The prose is flat"
  is useless; "Paragraph 3 reaches for 'tapestry of mist', a banned cliché —
  replace with a concrete sensory anchor" is useful.
- **MUST fix** — a **verifiable, citable** contract break: contradicts canon,
  omits a seed the envelope says to plant, drops a plot beat, a plot beat that
  doesn't follow causally from the prior chapter, a character action
  inconsistent with the arc waypoint, a motivation that requires off-stage
  information, or a reveal/shadow leak (checks 5-6). Every MUST quotes the
  offending line and names the specific source it breaks (canon line, beat
  sheet bullet, seed id, anti-pattern name). If you cannot cite the source and
  quote the break, it is not a MUST.
- **Tag every MUST with a bracketed issue-type** — `- **[issue-type]** …`. The
  verdict is computed from these tags (step 3). Use the **REJECT-tier** slugs
  (listed in step 3) only for structural breaks a surgical pass can't fix; any
  other MUST (e.g. `[reveal-leak]`, `[shadow-leak]`) is a REVISE-tier fix.
- **Leak severity follows what the page STATES, not what a reader might infer**
  (governs checks 5-6): MUST only when a line states the reserved truth in
  plain language — a sentence a reader could quote as the fact itself. Prose
  that is merely *louder than ideal* (a too-vivid image, "a first-read reader
  could infer X", a volume judgment with no line that *says* it) is SHOULD.
  Either way the anomaly should be whispered here and understood later.
- **SHOULD fix** — anti-pattern phrases, missed grounding opportunities, weak
  subtext, telegraphed seeds, tonal drift, a chapter ending that doesn't earn
  the transition the beat sheet promised.
- **CONSIDER** — taste-level suggestions. The user can ignore.
- **Do not rewrite the chapter.** Quote, name, point. Concrete *direction*
  yes; substitute prose no.
- **Look for story flaws, not just craft flaws.** A chapter can be technically
  clean (all beats hit, all seeds present, prose tidy) and still **wrong**: a
  motivation that doesn't match what the POV knows, a chapter that doesn't
  change the world state, dramatic energy descending when it should ascend.
  Same MUST/SHOULD treatment. Read hard — re-read once before declaring a tier
  clean — but a chapter genuinely **can** pass with zero findings; do not
  manufacture one to avoid an empty verdict. When a finding's severity is in
  doubt, **de-escalate** (uncertain MUST → SHOULD): the verdict must be true,
  not non-empty.

## Steps

### 0. Dispatch the analysis to a fresh subagent (main thread only)

If you can spawn subagents (you have the Agent tool) and you were invoked
standalone (`critique chapter N`, not already inside `book-critic`), **do not
audit in this conversation**. Dispatch steps 1-4 to the `book-critic` subagent
(Agent tool, `subagent_type: book-critic`) with the prompt
`chapter <N> --series-slug <slug> --book-number <M>`. It audits in a **fresh
context** — no leak from this session, and you no longer have to `/clear` to read
the chapter clean. It writes `notes/critique-ch<NN>.md` and returns the verdict +
counts + load-bearing findings. Read that file, then go **straight to step 4**
(report to user) — that is interactive and stays here, in the main thread.

> When the **book-critic subagent itself** runs this skill it has no Agent tool,
> so it cannot dispatch — it simply executes steps 1-4 directly and stops before
> step 4's interactive tail. (That is how recursion is structurally prevented.)
> `write-novel` likewise dispatches this critique itself, so when it chains the
> skill the work is already in the subagent — don't re-dispatch.

### 1. Load the contract

Build the context bundle (idempotent):

```bash
python3 .claude/skills/write-chapter/scripts/build_context.py \
    --series-slug <slug> --book-number <N> --chapter <M> --phase critique
```

`--phase critique` drops the recent-chapters-in-full block (you read the target
chapter directly) but keeps the style guide and craft checklist. It also writes
a **marker-stripped copy** of the chapter to `notes/_chapter-clean-chMM.md`
(the `▼▼▼ EXPAND ▼▼▼` scaffolding removed) and prints the chapter's **sha256**.
Record that hash in your critique file (step 3) as `**Chapter-hash:** <hex>` so
`update-canon` can confirm the prose did not change after this audit.

Then run the deterministic auditor and fold any ERROR into your MUST list:

```bash
python3 scripts/lint_book.py --series-slug <slug> --book-number <N>
```

Each `ERROR` line is a citable contract break (a dropped seed token, a dangling
`Revealed-by`, an out-of-range schedule, a lock-in gap) — add it as a MUST with
the appropriate tag. A clean lint is not a pass on its own; keep reading the
prose.

Read `notes/_context-chMM.md`. Sections relevant to critique: **Setup** (voice,
tense, distance, prose constraints), **Canon** (must not be contradicted),
**Plan / outline** (this chapter's beat sheet), **Shadow timeline** (writer's
truths — implied, never stated), **Seed envelope** (honored exactly), **Style
guide** (this book's `style.md`, incl. anti-cursi calibration), **References**
(anti-patterns checklist, dwelling techniques).

Then read **`notes/voice.md` directly** (the file, not the bundle): its per-POV
voice rules AND its **"Recurring patterns to watch / avoid"** list — *this
book's documented default failure modes* — which you MUST check the chapter
against (step 8d).

Then read the chapter from the **marker-stripped copy**
`notes/_chapter-clean-chMM.md` (not `chapters/MM.md`): same prose, EXPAND
banner lines removed, so the scaffolding can never become a spurious finding.
(The original `chapters/MM.md` is still the file the author edits.)

### 2. Run the structured pass

Go through these checks in order. For each, write a finding (or "clean") to
the critique buffer.

1. **Length is judged structurally — NEVER counted.** Do not count words,
   run `wc`, or compare the chapter's length to the setup range; the
   pipeline deliberately never measures generated length (a visible
   count-vs-target breeds compensation — padding, or "write more
   generously" leaking into the next chapter). Never write a finding whose
   evidence is a number of words. A chapter is *thin* only structurally: a
   missing plot beat (check 2) or fewer than 2 grounding moments (check 3).
   It is *bloated* only structurally: generic lingering that passes no need
   test (check 3), scenes that repeat a job already done, texture stacked on
   texture — tag those `[texture-padding]` **SHOULD** with the quoted lines.
2. **Beat sheet fidelity.** Does the chapter hit every plot beat? Missing beat
   is `MUST fix`.
3. **Grounding beats.** Are there 2-4 grounding moments of the licensed types
   (see `style.md` / expand-chapter's six: world element unfolded in use,
   stage built, cost made visible, deliberation on the page, re-orientation,
   secondary humanized)? List each, named by type and by what it grounds.
   Generic lingering — texture that neither grounds, unfolds, costs, nor
   reasons — does NOT count toward the 2-4 (and may itself be a `SHOULD fix`
   under "Dwelling is rationed"). If under 2 grounding moments, `MUST fix`.
4. **Subtext.** Pick three moments where the chapter could have carried
   subtext. Did it? If multiple are flat, `SHOULD fix`.
4b. **Proactivity & earned wins (sliding scales).** Read the "Sliding scales"
    block at the end of `plan/arcs.md`. Two counts:
    - **The POV chose.** Did the POV make at least one *choice* that changed
      their situation — gained ground, lost it, or took on a new cost?
      Noticing, enduring, hiding well, or being moved by others is not
      choosing. If no such choice: `SHOULD fix [passive-pov]`, naming the
      existing beat where a choice could live. (For Bruno and Olmo this is a
      hard per-chapter rule — see arcs.md.)
    - **Wins are bought.** If the chapter contains a victory, was it paid for
      with failed attempts (this or earlier chapters) that worsened the
      situation or added cost? A free win is `SHOULD fix` — the structural
      twin of an unseeded payoff.
    Diagnostic only: never ask the prose to mention dials or scales.
5. **Seed envelope.**
   - Each `plant` due here: is it planted? Quote the line. Telegraphed (flag
     word, isolated sentence, too prominent) → `SHOULD fix`; missing →
     `MUST fix`.
   - Each `echo`: referenced obliquely? `SHOULD fix` if missing or restated
     verbatim.
   - Each `payoff`: does the truth surface? Is it explained or allowed to
     click? `MUST fix` if missing.
   - **Dose / telegraph by repetition.** For any seed whose `Dose` field
     constrains it (typically a payoff ≤2 chapters from its plant), count the
     chapter's touches and whether it *re-describes* the seed (especially at
     its opening) before paying it off. A near-term payoff re-established in
     full is "seen coming a mile off" — `SHOULD fix`, quoting the redundant
     description and naming the Dose budget it broke.
   - **Trigger fidelity.** For an event payoff: fired from the seed's
     intrinsic `Trigger` (an already-seeded cause), or from a convenient
     invented external actor (a horse, a storm, a stranger arriving just in
     time)? A contrived trigger is `MUST fix` — quote it and point to the
     intrinsic trigger that should fire instead.
   - **No deus ex machina (presence + cause).** Every key character who
     appears must be there for a *motivated, seeded* reason. One who shows up
     exactly when needed with no prior cause ("a mentor passing through", a
     rescuer who happens to be there) is `MUST fix` — quote the unmotivated
     entrance and name the motivated version (a reason tied to the book's
     engine, established before the character matters). Cross-check any
     presence rule in `notes/decisions.md`.
   - **Resolution image.** If a resolution-type seed pays off here, does the
     chapter *invert/transform the exact image planted earlier* (and let it
     click, not explain)? A flat statement instead is `SHOULD fix`.
   - **Reveal-timing leak.** Judge against the seed's payoff chapter or a
     locked decision, with severity per the leak rule in Hard rules (MUST only
     for a plain-language statement, quoted; volume/inference is SHOULD).
6. **Shadow honesty.** Does the narrator state a truth the POV (and the
   reader, at this chapter's reveal level) should not yet hold? Severity per
   the leak rule in Hard rules. Prose that merely *rhymes* with the hidden
   truth — an image, a subtext, an unease — without stating it is correct
   seeding, not a leak; do not flag it.
7. **Canon.** Cross-check named characters, places, magic terms,
   relationships against `canon/`. Quote any contradiction. `MUST fix`. Also
   check the bundle's **Continuity contract** section (the chapter's state
   sheet from plan-chapter): a line that contradicts it — a character in the
   wrong place or state, the POV knowing something the sheet reserves for a
   later chapter, an object that moved with no on-page reason — is
   `MUST fix [canon-contradiction]`.
8. **POV / voice / tense.** Match `setup.md`. Any drift is `SHOULD fix`.
8b. **Style guide.** Hold the prose against this book's `style.md`. Flag
    especially anti-cursi violations: emotional thesis statements, overspent
    physical emotion (tears/trembling more than once or twice), decorative
    beautiful lines that carry no plot/character/sense, and any rule the
    book's own `style.md` declares. Quote each. `SHOULD fix`; `MUST fix` if it
    breaks an explicit book-level style rule.
    First run the deterministic prose auditor — the countable tics (the six
    named caps, explanatory similes, and cross-chapter repetition) are
    **counted for you, not judged by eye**:

    ```bash
    python scripts/lint_prose.py --series-slug <slug> --book-number <n> --chapter <N>
    ```

    Read `notes/_prose-report-chNN.md`: a **tic-count table** (with per-book
    caps from `notes/prose-lint.toml`), the flagged explanatory similes, and a
    **cross-chapter** section (signature words reused across chapters, echoing
    openings, reserved lexicon spent off-plan) — the repetition a fresh
    single-chapter read cannot see. **Do not recount these by hand.** Judge
    each flagged instance: every tic over its cap is a `SHOULD fix` — quote
    the offending line the report lists and say which one to keep; a reserved
    word spent off-plan or a signature word on its 3rd+ chapter is a
    `SHOULD fix` too. The script is a floor on these tics, not the ceiling —
    also read for what its regexes cannot catch (the spun-out "…que Z cuando
    W" simile, the ominous "todavía / ya no").
8c. **Richness & seeding — the add-back check.** Looks for what is *missing*,
    not what is excess: a critique that only subtracts can only make prose
    blander. Two passes:
    - **Sensory mandate.** Does every scene land at least one concrete
      sensation the reader *feels* (temperature, sound, weight, taste, smell),
      not one the narrator merely names? Mark any scene that reads
      grey/abstract. If the book's premise is sensory (colour, sound, scent —
      see `style.md`), hold it harder: a scene that does not make that premise
      felt is a `SHOULD fix` with a concrete suggestion of what to add.
    - **Unseeded payoffs (Chekhov).** List everything that breaks, pays off,
      or turns out to matter in this chapter; check each appeared *earlier* in
      ordinary use (this chapter or a prior one). An object/danger/skill that
      arrives only at the moment it matters is a `SHOULD fix`: name where the
      seed should have been planted. (Check 5 only covers tracked seeds; this
      catches untracked setups — e.g. a structure that collapses must have
      been shown as fragile beforehand.)
8d. **Default-failures sweep (MANDATORY — state it ran, even if clean).**
    Hunt the documented default failures in `notes/voice.md` ("Recurring
    patterns to watch / avoid") explicitly every chapter — they recur across
    drafts. Confirm each is clean, quoting any hit:
    - **(a) Aphoristic narrator** — any universal maxim in timeless present
      that reads like a quote-book line (the one named ban in `style.md`).
      `MUST fix`.
    - **(b) Omniscient flash-forward over a closed POV** — the narrator
      stepping ahead of the POV's present knowledge: "sin saber (todavía)
      que…", "no supo que…", "lo que después / siempre… al recordarlo…", or
      any pre-announcement of a later weight. A flash-forward that spends a
      reserved later beat is `MUST fix`; a vague present-tense unease that
      leaks nothing is fine (not a finding).
    - **(c) Erudite aside that leaks a later reveal** — "X no sabía nada de
      [términos técnicos], que es lo que enseñan en [Y]" (or similar): both a
      POV break AND a reveal-timing leak. `MUST fix`.
    Plus any other entry the book's own `voice.md` list names — treat those as
    this book's known regressions and weight them up, not down. **Sweep at
    most the 7 judgment-only patterns** `voice.md` carries after consolidation
    — the countable ones (a phrase form, a word, an opener shape) have
    graduated to `prose-lint.toml` and are already counted in the step-8b
    report; **cite that report's counts, do not re-hunt them by eye**. This
    cap is deliberate: a sweep longer than ~7 items is one an LLM silently
    stops doing well.
9. **Anti-patterns.** Search the chapter for every entry in
   `references/prose-antipatterns.md` (banned lexicon, fantasy clichés,
   structural tics). Quote each occurrence. `SHOULD fix` for most; `MUST fix`
   if there are >5 instances. Do **not** flag sensory concreteness or typed
   grounding that is not a named anti-pattern — that is the book's texture
   (see 8c). Ornament that carries no plot/character/sense violates the style
   guide's image budget and is flagged under 8b, not here.
10. **Opening / ending.** Non-cliché start (not waking up, not battle, not
    prophecy)? Does it end on the transition out specified in the beat sheet?
11. **Hard-magic laws.** Does magic used here match the capability the reader
    has seen? Are costs visible? `MUST fix` violations.
12. **Dialogue.** Spot-check 3 random lines. Does each reveal character,
    advance plot, or carry subtext (ideally two)? `SHOULD fix` flat lines.

### 3. Write the critique

Write the critique to:

```
output/<series>/book-NN/notes/critique-ch<NN>.md
```

Structure (write the findings; leave the verdict to the script):

```markdown
# Critique — chapter N

**Chapter-hash:** <the sha256 build_context printed for chapter N>
**Verdict:** <filled in below by compute_verdict.py>

## MUST fix
- **[issue-type]** — quoted line / location → concrete direction
- ...

## SHOULD fix
- ...

## CONSIDER
- ...

## What works
- Brief notes on what landed. Important — the writer needs the signal.
```

**Verify your quotes before the verdict is counted.** A finding built on a
line that is not actually in the chapter would be counted like a real one:

```bash
python3 scripts/verify_critique_quotes.py \
    --critique-file output/<series>/book-NN/notes/critique-ch<NN>.md \
    --series-slug <slug> --book-number <N> --chapter <M>
```

Every `ERROR` is a MUST whose quote appears in neither the chapter nor any
source it could legitimately cite — treat it as **presumptively hallucinated**:
re-read the chapter and fix the quote to the real line, or delete the finding.
A MUST with no quotable line at all (`WARN`) must gain one — the format
requires it. Only when this exits clean is the finding set trustworthy enough
to count.

**The verdict is computed, not judged.** After the quotes verify, run:

```bash
python3 scripts/compute_verdict.py \
    --critique-file output/<series>/book-NN/notes/critique-ch<NN>.md \
    --target chapter
```

It counts your MUST/SHOULD/CONSIDER bullets, applies the thresholds below, and
prints `VERDICT: X (MUST=a SHOULD=b CONSIDER=c)`. Write that verdict into the
`**Verdict:**` field — the number that drives the pipeline stays off your
judgment.

Thresholds the script applies (for reference — you do not apply them by hand):

- **PASS** — zero MUST and ≤3 SHOULD. Ready for `update-canon`.
- **REVISE** — any MUST that is *not* a REJECT-tier tag, and/or >3 SHOULD. A
  surgical `revise-chapter` pass resolves these. Most MUSTs land here.
- **REJECT** — a MUST tagged REJECT-tier (`[missing-beat]`,
  `[canon-contradiction]`, `[unseeded-payoff]`, `[contrived-trigger]`,
  `[deus-ex-machina]`): a structural break needing a
  scene rewrite or outline fix.

Severity follows the **tag** you assign each MUST — choose it honestly. When
in doubt between REVISE- and REJECT-tier, pick the REVISE-tier tag.

### 4. Report to user, then ADJUDICATE the findings (main thread only)

Print the verdict, the count of issues by tier, and the critique file path.

Then run the **disposition gate** — this is what stops a chapter looping
through revision forever: critiques audit fresh every pass (no memory of prior
ones, by design), so without a record of what the author already settled, each
fresh read re-flags the same judgment calls under new wording.

For the MUST and SHOULD findings, ask the author (one `AskUserQuestion`, one
finding per question or grouped if many) how to dispose of each:

- **Fix** — hand to `revise-chapter` (surgical edit).
- **Intentional — lock it** — the author judges the flagged choice correct as
  written. Append it to `notes/decisions-ch<NN>.md` under a heading
  `## Critic findings adjudicated as intentional` as a one-line ruling, e.g.
  `- **<finding>** — INTENTIONAL: <author's reason>. Do not re-flag.` A fresh
  critic reads this file and treats the point as closed (see `book-critic.md`
  → "Honor adjudicated decisions"), so the same finding cannot bounce back
  next pass. **CONSIDER items don't need a ruling** — they're taste; skip
  them here.
- **Defer** — the finding belongs to a later chapter (e.g. a payoff not due
  yet). Note it in `notes/open-questions.md`; do not act now.

Then suggest the next step from the verdict:

- PASS → `update-canon <N>` to lock in.
- REVISE → `revise-chapter <N>` for the **Fix**-marked items only.
- REJECT → structural; discuss with the user (scene rewrite or outline fix).

**Loop cap.** Run at most **one** critique → revise → re-critique cycle by
default. After that, re-critique only if a **structural** (REJECT-tier) MUST
remains. Do not re-run a full critique to chase residual SHOULD/taste findings
— lock them as intentional or accept them and move to `update-canon`. The
4-update spiral comes from re-auditing what was already adjudicated.

## What this skill does NOT do

- Does not modify the chapter file.
- Does not modify the plan, canon, or seeds.
- Does not generate replacement prose.
