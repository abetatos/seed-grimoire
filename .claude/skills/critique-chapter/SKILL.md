---
name: critique-chapter
description: Hard, structured critique of a written chapter against the book's own contract — beat sheet, canon, shadow, seed envelope, prose anti-patterns, dwelling techniques, word count. Produces a written critique with prioritized issues and concrete fixes. Use this after a chapter is written and before `update-canon` locks it in. Invoke as "critique chapter N".
---

# critique-chapter

You are running the **critique-chapter** skill. Read a chapter against
the bundle that produced it and report on where it succeeds and fails.

The critique is **for the user**, not for you to silently fix. The
user decides whether to apply revisions.

> **Runs headless.** This critique always audits in a **fresh context** (the
> `book-critic` subagent), never in the conversation that wrote the chapter — see
> step 0. `write-novel` dispatches it for you; invoked standalone it
> self-dispatches. When you ARE the subagent, step 4 "Report to user" means
> **return the verdict + counts + load-bearing findings to the orchestrator** —
> your final message is the report. Still write the `notes/critique-chNN.md`
> file; never edit the chapter.

## Hard rules

- **Be specific.** "The prose is flat" is useless. "Paragraph 3
  reaches for 'tapestry of mist', which is a banned cliché — replace
  with a concrete sensory anchor" is useful.
- **Quote the offending line.** Always.
- **Prioritize ruthlessly.** Group findings into:
  - **MUST fix** — a **verifiable, citable** contract break: contradicts
    canon, omits a seed the envelope says to plant, drops a plot beat, a plot
    beat that doesn't follow causally from the prior chapter, a character
    action inconsistent with the arc waypoint, a motivation that requires
    off-stage information, or a line that **states a reserved shadow truth in
    plain language** (see checks 5-6 — a *judgment that the prose is merely too
    loud* is SHOULD, not MUST). Every MUST quotes the offending line and names
    the source it breaks. If you cannot cite the source and quote the break, it
    is not a MUST.
  - **Tag every MUST with a bracketed issue-type** — `- **[issue-type]** …`.
    The verdict is computed from these tags (see step 3), so use the
    **REJECT-tier** slugs for structural breaks a surgical pass can't fix:
    `[missing-beat]`, `[canon-contradiction]`, `[unseeded-payoff]`,
    `[contrived-trigger]`, `[deus-ex-machina]`, `[wordcount-under-60]`. Any
    other MUST (e.g. `[reveal-leak]`, `[shadow-leak]`) is a REVISE-tier fix.
  - **Word count is SHOULD, not MUST** (T19). A chapter below 80% of the floor
    is `[wordcount-short]` **SHOULD** — a lean chapter is a valid choice and
    `expand-chapter` handles growth. Only **below 60%** of the floor is
    structural (`[wordcount-under-60]`, REJECT-tier): that means the outline
    planned too few texture beats.
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
  same MUST/SHOULD treatment as anti-patterns. Read hard — re-read once
  before declaring a tier clean — but a chapter genuinely **can** pass
  with zero findings; do not manufacture one to avoid an empty verdict.
  When a finding's severity is in doubt, **de-escalate** (uncertain MUST
  → SHOULD): the verdict must be true, not non-empty.

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
chapter directly below — you don't need the other prior chapters inlined), but
keeps the style guide and craft checklist because you check the prose against
them. It also writes a **marker-stripped copy** of the chapter to
`notes/_chapter-clean-chMM.md` (the `▼▼▼ EXPAND ▼▼▼` scaffolding removed) and
prints the chapter's **sha256**. Record that hash in your critique file (step 3)
as `**Chapter-hash:** <hex>` so `update-canon` can confirm the prose did not
change after this audit.

Then run the deterministic auditor and fold any ERROR into your MUST list:

```bash
python3 scripts/lint_book.py --series-slug <slug> --book-number <N>
```

Each `ERROR` line is a citable contract break (a dropped seed token, a dangling
`Revealed-by`, an out-of-range schedule, a lock-in gap) — add it as a MUST with
the appropriate tag. A clean lint is not a pass on its own; keep reading the
prose.

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

Then read **`notes/voice.md` directly** (read the file — do not rely on the
bundle): its per-POV voice rules AND its **"Recurring patterns to watch /
avoid"** list, which records *this book's documented default failure modes*
(the ones prior chapters already tripped). You MUST check the chapter against
that list — see step 8d.

Then read the chapter from the **marker-stripped copy**
`notes/_chapter-clean-chMM.md` (not `chapters/MM.md`). It is the same prose with
the EXPAND banner lines removed, so you judge only the writing — the scaffolding
is invisible to you and can never become a spurious finding. (The original
`chapters/MM.md` is still the file the author edits; you just read the clean
view.)

### 2. Run the structured pass

Go through these checks in order. For each, write a finding (or
"clean") to the critique buffer.

1. **Word count.** Run check_wordcount. Note actual / target. Below 80% of the
   floor is `[wordcount-short]` **SHOULD** (a lean chapter is valid — expand
   grows it); only below **60%** is `[wordcount-under-60]` **MUST** (REJECT-tier
   — the outline planned too few texture beats). Never MUST a mere shortfall.
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
   - **Reveal-timing leak.** A reveal leak is `MUST fix` **only when a line
     states the reserved truth in plain language** — a sentence a reader could
     quote as the fact itself, against the seed's payoff chapter or a locked
     decision. Quote that line. If instead the prose is merely *louder than
     ideal* — "a first-read reader could infer X", a too-vivid image, a volume
     judgment with no line that *says* it — that is `SHOULD fix`, not MUST.
     Severity follows what the page **states**, not what a reader **might
     infer**. Either way the anomaly should be whispered here and understood
     later.
6. **Shadow honesty.** Does the chapter leak shadow content — the narrator
   stating a truth the POV (and the reader, at this chapter's reveal level)
   should not yet hold? `MUST fix` **only when a line names the reserved truth
   in plain language** (quote it). Prose that merely *rhymes* with the hidden
   truth — an image, a subtext, an unease — without stating it is correct
   seeding, not a leak; do not flag it.
7. **Canon.** Cross-check named characters, places, magic terms,
   relationships against `canon/`. Quote any contradiction.
   `MUST fix`. Also check the bundle's **Continuity contract** section (the
   chapter's state sheet from plan-chapter): a line that contradicts it — a
   character in the wrong place or state, the POV knowing something the sheet
   reserves for a later chapter, an object that moved with no on-page reason —
   is `MUST fix [canon-contradiction]`.
8. **POV / voice / tense.** Match `setup.md`. Any drift is `SHOULD fix`.
8b. **Style guide.** Hold the prose against the Style guide section
    (this book's `style.md`). Flag violations of the anti-cursi
    calibration especially: emotional thesis statements, overspent
    physical emotion (tears/trembling more than once or twice),
    decorative beautiful lines that carry no plot/character/sense, and
    any rule the book's own `style.md` declares. Quote each. `SHOULD
    fix`; `MUST fix` if it breaks an explicit book-level style rule.
    First run the deterministic prose auditor, then read its report — the
    countable tics (the six named caps, explanatory similes, and cross-chapter
    repetition) are **counted for you, not judged by eye**:

    ```bash
    python scripts/lint_prose.py --series-slug <slug> --book-number <n> --chapter <N>
    ```

    Read `notes/_prose-report-chNN.md`. It carries a **tic-count table** (with
    the per-book caps from `notes/prose-lint.toml`), the flagged explanatory
    similes, and a **cross-chapter** section (signature words the writer has
    reused across chapters, echoing openings, reserved lexicon spent off-plan) —
    the repetition a fresh single-chapter read cannot see. **Do not recount
    these by hand.** Your job is to judge each flagged instance: every tic over
    its cap is a `SHOULD fix` — quote the offending line the report lists and
    say which one to keep; a reserved word spent off-plan or a signature word on
    its 3rd+ chapter is a `SHOULD fix` too. The script is a floor on these tics,
    not the ceiling — also read for what its regexes cannot catch (the spun-out
    "…que Z cuando W" simile, the ominous "todavía / ya no").
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
8d. **Default-failures sweep (MANDATORY — state it ran, even if clean).**
    This book has documented default failures in `notes/voice.md`
    ("Recurring patterns to watch / avoid"); they recur across drafts, so
    hunt them explicitly every chapter rather than hoping the general passes
    catch them. Confirm each is clean, quoting any hit:
    - **(a) Aphoristic narrator** — any universal maxim in timeless present
      that reads like a quote-book line (the one named ban in `style.md`).
      `MUST fix`.
    - **(b) Omniscient flash-forward over a closed POV** — the narrator
      stepping ahead of the POV's present knowledge: "sin saber (todavía)
      que…", "no supo que…", "lo que después / siempre… al recordarlo…", or
      any pre-announcement of a later weight. A flash-forward that spends a
      reserved later beat is `MUST fix`; a vague present-tense unease that
      leaks nothing is fine (not a finding).
    - **(c) Erudite aside that leaks a later reveal** — the construction "X no
      sabía nada de [términos técnicos], que es lo que enseñan en [Y]" (or
      similar). It is **both** a POV break **and** a reveal-timing leak
      (it names, from outside the POV, a truth/term the shadow reserves for a
      later chapter). `MUST fix`.
    Plus any other entry the book's own `voice.md` list names. Whichever
    appear in `voice.md`, treat as this book's known regressions and weight
    them up, not down. **Sweep at most the 7 judgment-only patterns** `voice.md`
    carries after consolidation — the countable ones (a phrase form, a word, an
    opener shape) have graduated to `prose-lint.toml` and are already counted in
    the step-8b report; **cite that report's counts, do not re-hunt them by
    eye**. This cap is deliberate: a sweep longer than ~7 items is one an LLM
    silently stops doing well.
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

Structure (write the findings; leave the verdict to the script):

```markdown
# Critique — chapter N

**Chapter-hash:** <the sha256 build_context printed for chapter N>
**Word count:** actual=X target=[lo, hi]
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

**Verify your quotes before the verdict is counted.** A finding built on a line
that is not actually in the chapter would be counted like a real one. Run:

```bash
python3 scripts/verify_critique_quotes.py \
    --critique-file output/<series>/book-NN/notes/critique-ch<NN>.md \
    --series-slug <slug> --book-number <N> --chapter <M>
```

Every `ERROR` is a MUST finding whose quote appears in neither the chapter nor
any source file (canon/plan/style/decisions) it could legitimately cite — treat
it as **presumptively hallucinated**: re-read the chapter and fix the quote to
the real line, or delete the finding. A MUST with no quotable line at all
(`WARN`) must gain one — the format requires it. Only when this exits clean is
the finding set trustworthy enough to count.

**The verdict is computed, not judged.** After the quotes verify, run:

```bash
python3 scripts/compute_verdict.py \
    --critique-file output/<series>/book-NN/notes/critique-ch<NN>.md \
    --target chapter
```

It counts your MUST/SHOULD/CONSIDER bullets and applies the thresholds below,
then prints `VERDICT: X (MUST=a SHOULD=b CONSIDER=c)`. Write that verdict into
the `**Verdict:**` field. This keeps the number that drives the pipeline off
your judgment at the step that triggers action.

Thresholds the script applies (for reference — you do not apply them by hand):

- **PASS** — zero MUST and ≤3 SHOULD. Ready for `update-canon`.
- **REVISE** — any MUST that is *not* a REJECT-tier tag, and/or >3 SHOULD. A
  surgical `revise-chapter` pass resolves these. Most MUSTs land here.
- **REJECT** — a MUST tagged REJECT-tier (`[missing-beat]`,
  `[canon-contradiction]`, `[unseeded-payoff]`, `[contrived-trigger]`,
  `[deus-ex-machina]`, `[wordcount-under-60]`): a structural break needing a
  scene rewrite or outline fix.

So severity follows the **tag** you assign each MUST — choose it honestly. When
in doubt between REVISE- and REJECT-tier, pick the REVISE-tier tag.

### 4. Report to user, then ADJUDICATE the findings (main thread only)

Print the verdict and the count of issues by tier, and the critique file path.

Then run the **disposition gate** — this is what stops a chapter looping
through revision forever. Critiques audit fresh every pass (no memory of prior
ones, by design), so without a record of what the author already settled, each
fresh read re-flags the same judgment calls under new wording. Close that loop:

For the MUST and SHOULD findings, ask the author (one `AskUserQuestion`,
one finding per question or grouped if many) how to dispose of each:

- **Fix** — hand to `revise-chapter` (surgical edit).
- **Intentional — lock it** — the author judges the flagged choice correct as
  written. Append it to `notes/decisions-ch<NN>.md` under a heading
  `## Critic findings adjudicated as intentional` as a one-line ruling, e.g.
  `- **<finding>** — INTENTIONAL: <author's reason>. Do not re-flag.` A fresh
  critic reads this file and treats the point as closed (see `book-critic.md`
  → "Honor adjudicated decisions"), so the same finding cannot bounce back next
  pass. **CONSIDER items don't need a ruling** — they're taste; skip them here.
- **Defer** — the finding belongs to a later chapter (e.g. a payoff not due
  yet). Note it in `notes/open-questions.md`; do not act now.

Then suggest the next step from the verdict:

- PASS → `update-canon <N>` to lock in.
- REVISE → `revise-chapter <N>` for the **Fix**-marked items only.
- REJECT → structural; discuss with the user (scene rewrite or outline fix).

**Loop cap.** Run at most **one** critique → revise → re-critique cycle by
default. After that one cycle, only re-critique again if a **structural** MUST
(REJECT-tier: missing beat, canon contradiction, unseeded payoff, word count
<80%) remains. Do not re-run a full critique to chase residual SHOULD/taste
findings — lock them as intentional or accept them and move to `update-canon`.
The 4-update spiral comes from re-auditing what was already adjudicated.

## What this skill does NOT do

- Does not modify the chapter file.
- Does not modify the plan, canon, or seeds.
- Does not generate replacement prose.
