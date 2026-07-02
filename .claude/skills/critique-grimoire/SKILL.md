---
name: critique-grimoire
description: Adversarial structural review of `output/<series>/grimoire.md` — the world grimoire. Audits the foundational worldbuilding document BEFORE `book-setup` or `plan-book` run, so that the per-book plan never inherits a flawed foundation. Use this when the user says "audita el grimorio" / "critique the grimoire" / "is the grimoire ready?" Invoke after writing or revising the grimoire, and before running `book-setup` for a new book in the series.
---

# critique-grimoire

You are running the **critique-grimoire** skill. The grimoire is the
foundational worldbuilding document for the whole series. Everything
downstream (`setup.md`, `canon/*`, `plan/*`, chapters) ultimately
quotes from it. If the grimoire has a structural gap, every per-book
plan inherits it — and the writer will discover it mid-prose.

This skill exists so that **the grimoire is bulletproof before any per-book
work starts**. The author has explicitly chosen interactive critical
planning over mid-writing pauses; this is where the criticism lives.

## When to invoke

- The author has finished a draft of `output/<series>/grimoire.md` (or
  revised it after critique).
- Before running `book-setup` for Book I of a series, or for any new
  book that introduces new worldbuilding.
- The author says "audita el grimorio" / "critique the grimoire" / "está
  listo el grimorio para empezar?"

## Hard rules

- **Adversarial bias is total.** A grimoire that passes with zero findings
  is suspicious; re-read. The cost of finding a problem here is one
  conversation. The cost of finding it during Libro II is a rewrite.
- **Be specific.** "Magic is weak" is useless. "§4 declares two costs
  but both are physical — there is no emotional/social cost, so the
  magic has no political traction" is useful.
- **Quote sources.** Every finding cites a line or a missing section.
- **Tier ruthlessly:**
  - **MUST fix** — gaps that break everything downstream: missing
    source/cost/limits in magic, no antagonist with thesis, climax
    declared as passive instead of active, no clock / "why now",
    unresolved gating decisions, system-arc-shape (scaled vs
    inverted) not declared.
  - **SHOULD fix** — gaps that weaken the book: < 5 named places,
    < 3 historical events, subplots without ≥ 3 contact points with
    main, missing distinct theme on a subplot, characters without
    full want/need/lie/wound, missing thematic question on magic.
  - **CONSIDER** — taste-level (e.g., a faction declared but no
    clear conflict with the others; a place with no sensory anchor).
- **Do not rewrite the grimoire.** Quote, name, point. Concrete direction
  yes; substitute text no. The author writes the grimoire.
- **Cross-check, don't assume.** When a deep check looks ambiguous
  (e.g., "subplot has 2 contact points — is the 3rd implied?"),
  surface it as SHOULD with the ambiguity explicit, not as PASS.

## Steps

### 0. Dispatch the analysis to a fresh subagent (main thread only)

If you can spawn subagents (you have the Agent tool), **do not audit in this
conversation**. Dispatch steps 1-4 to the `book-critic` subagent (Agent tool,
`subagent_type: book-critic`) with the prompt `grimoire --series-slug <slug>`. It
audits in a **fresh context** — no leak from this session, no `/clear` needed to
re-audit in clean. It writes `notes/critique-grimoire.md` and returns the verdict +
counts + load-bearing findings. Read that file, then go **straight to step 5**
(report) and step 6 (compose with critique-plan) — those stay here, in the main
thread.

> When the **book-critic subagent itself** runs this skill it has no Agent tool,
> so it cannot dispatch — it simply executes steps 1-4 directly and stops before
> step 5. (That is how recursion is structurally prevented.)

### 1. Run the deterministic audit

```bash
python3 .claude/skills/critique-grimoire/scripts/audit_grimoire.py \
    --series-slug <slug> \
    --output output/<slug>/notes/_audit-grimoire.md
```

The audit checks:
- Section presence and "filled" state (header without content fails).
- Magic depth: source / mechanic / costs ≥ 2 / hard limits ≥ 3 /
  thematic question.
- System arc shape: three escalation tiers OR inverted-system
  explicitly declared.
- Characters: ≥ 2 principals with full arc (want+need+lie+wound),
  antagonist with stated thesis.
- Subplots: count, contact points, distinct theme.
- Historical events: ≥ 3 enumerated.
- Geography: ≥ 5 named places.
- Structure: each book block has a Motor and an active-decision climax.
- Open decisions: any gating decision still unresolved.
- **Series-scoped spine floors** (scale with book count N, read from §12 /
  §14 / §14b): the grimoire only holds the *trans-series* spine, so the
  audit expects **≥ max(6, 3N) loaded guns**, **≥ max(5, 2N) master
  mysteries**, **≥ max(2, N) subplots**, **≥ max(1, N−1) decoys**, and
  **≥ max(1, N−1) trans-book threads** (guns that sow early / pay late)
  plus the same floor of bridging mysteries (intro early / confirm late).
  Shortfalls are SHOULD-fix — the qualitative pass below decides if a thin
  spine is load-bearing enough to block.
- **Decoys**: deliberate misdirection (a false system, a hollow saviour, an
  institution fronting for the real parasite) counted across the gun /
  mystery tables and the factions / characters / two-layer prose. A trilogy
  that lies to the reader should name them on purpose.

If `grimoire.md` does not exist, the audit refuses and tells the user to
start from `references/grimoire-template.md`.

### 2. Read the grimoire in full

Read `output/<series>/grimoire.md` and the audit report. Also read these
craft references for what "good" looks like:

- `references/magic-design-checklist.md`
- `references/seed-craft.md`
- `references/fantasy-beats.md`
- `references/hard-magic-laws.md`

### 3. Run the qualitative pass

The audit catches mechanical gaps. You catch the substance. Go through
each of these categories — every check produces either a finding or an
explicit "clean".

#### 3a. Premise integrity
- Is the one-sentence idea actually unique, or is it a recombination
  of well-worn elements? Push back if generic.
- Do the **two layers** declared in §2 add up to a story with
  retroactive payoff, or do they restate the surface in code words?
- Is the tonal register declared and coherent (gothic / epic /
  romantasy / progression / etc.)?

#### 3b. Magic system as engine
- Source, costs, limits — are they present **and specific** (not
  "energy", not "physical exhaustion")?
- Is the magic system politically integrated — does it stratify the
  world economically and morally?
- Is the thematic question forced by the magic, or is it a separate
  layer pasted on top?
- If the system is **scaled**: are the three tiers visible at the
  right times in the structure (common in act 1, skilled in act 2,
  apex at climax)?
- If the system is **inverted**: is the erosion mechanic concrete
  (what does the protagonist lose, on what schedule)? Is the climax
  the end of their resources, not the peak of their power?

#### 3c. Cast distinctness — *and enough cast to survive the whole series*
A full-arc count alone is a trap: the audit will happily report "2 full
arcs" while one is a `[PROPUESTA]` placeholder and the other is consumed
in Book I. Counting bullets is not the same as having a cast that carries
N books. So check, in this order:
- **Fixed vs proposed.** For every arc-bearing figure (in §9 **and** in
  the subplots section — the de-facto deuteragonist often lives there),
  is the arc **`[FIJO]`** or still **`[PROPUESTA]`/draft**? An arc that
  carries the back half but is tagged proposed is **not a commitment** —
  flag every one by name (SHOULD). The trilogy cannot be audited against
  an un-fixed arc; the per-book plan inherits the gap.
- **Survival into the back half.** Which fixed arcs are *spent* in Book I
  (the figure dies / is lost / is consumed / is grisado)? Subtract them.
  For an N-book series you want **≥ max(2, N−1) fixed arcs that survive
  into the later books.** One living designed arc entering Book II is the
  single most likely mid-Book-II rewrite — call it out explicitly as the
  trilogy's thinnest spine (SHOULD, escalate toward REVISE if it's the
  only finding-cluster).
- **Devices vs people.** Is any back-half emotional pivot (the love
  interest, the bond whose loss is an all-is-lost) a one-line *function*
  with no wound/want/lie of its own? A pivot that carries a climax must
  be a person, not a device — SHOULD give it an arc.
- **Distinctness.** Do their wounds/wants/lies differ? If two figures
  carry the same lie or decision-shape, the book has one arc, not two.
- **Antagonist thesis.** A worldview that, in different light, would be
  correct? If stock evil, that's MUST fix.
- **A second POV/deuteragonist** beyond protagonist and antagonist? Epic
  fantasy without one feels claustrophobic — and a *committed* one (not a
  mere "se permiten otros POV" permission punted to `plan-book`).

#### 3d. Subplots earning their place
- ≥ 1 declared (≥ 2 if total target > 250k).
- Each one with ≥ 3 contact points with the main plot? Quote them.
- Distinct theme from the main? If the subplot argues the same thesis
  as the main, it's decoration.
- Resolution before or during the climax of the main? Subplots that
  resolve after drain energy.

#### 3e. World economy
- ≥ 5 named places, each with a sensory anchor and a function.
- Each named faction has a dramatic function (someone uses them,
  fears them, fights them). Decorative castes / orders / institutions
  are SHOULD-cut.
- Geography supports travel logistics — distances declared or
  derivable?

#### 3f. Historical weight
- ≥ 3 past events that reverberate in the present.
- Each has a stated wound it left. ("Mil años de criba" needs a
  concrete wound: who still bears it?)
- Are mythical accounts paired with **the real truth** (writer-only),
  so the reveal mechanism is honest?

#### 3g. Trilogy / structure rigor
- Each book block declared with a distinct **motor**.
- No diminishing-returns reveals across books (Book II's twist must
  be different in kind from Book I's, not a louder echo).
- Each climax uses an **active-decision verb** (decide / elige /
  rechaza / acepta / niega / entrega). Passive verbs ("abre", "cae",
  "sucede") at the climax are MUST fix — the protagonist must act,
  not be acted upon, at the moment the theme is paid.
- All-is-lost moments named (or at least the dramatic shape sketched)
  for each book.

#### 3h. The clock — "why now?"
- Is the clock explicit? The series happens **in this moment** because
  something causal forces it.
- Does the clock connect to the protagonist's existence (best case —
  protagonist and crisis are the same event) or is it independent?
- Without a clock, the world feels timeless and the urgency is
  vibes-only.

#### 3i. Loaded guns (§14) and master mysteries (§14b)
- Distinct worldbuilding elements declared — rituals (the Lectura),
  pseudo-systems (the Blanco Falso), implicit physical laws (the
  complementario) — are they marked as siembras obligatorias with a
  payoff plan?
- Are there any **declared elements with no payoff plan**? Those are
  decoration. SHOULD cut or SHOULD plant.
- **§14 completeness (the audit checks this):** each loaded gun has a
  sow-book AND a payoff-book, and — by the grimoire's own rule — appears
  at least once in Book I. A row missing a book, or that never lands in
  Book I, is `MUST fix`. An empty §14 table is `MUST fix`: the per-book
  plan would have no concrete obligations to realize.
- **§14b master mysteries:** the grimoire must enumerate, as a table, the
  hidden truths the trilogy reveals, each with a real-truth, an intro-book
  and a confirm-book. These are what `critique-plan` later holds each book's
  `shadow.md` to (every mystery introduced in a book needs a `SHADOW-TRUTH`
  carrying it). An empty/missing §14b table or rows missing intro-book are
  `MUST fix` — without them the plan's shadow coverage cannot be checked.

#### 3j. Open decisions discipline
- Every open decision marked with **Gating: sí / no**?
- All gating decisions resolved? If not, MUST fix.
- Non-gating decisions named so they don't get forgotten?

#### 3k. Cross-book inheritance (trilogy only) — the attrition ledger
A trilogy that kills its tutor in Book I and grises the love interest in
Book II is **spending cast**; if that spend is never costed, the back
half quietly runs out of people. The grimoire (or `series-state.md`)
should carry an explicit ledger — **carries / dies / enters per book**:
- What does the reader **carry** from Book I into Book II that they
  didn't have at the start? Is it stated?
- What **dies** between books (characters, factions, places)? Is it
  named — and is the resulting gap *refilled* (who enters to carry the
  arc the dead figure was carrying)?
- What new figures **enter** in Books II/III, and are their arcs fixed
  by the time they have to bear weight?
- What promises does Book I make that Book III must pay?

If this ledger is absent and the grimoire is killing/consuming
arc-bearing figures across books (check against 3c), that is a **SHOULD
fix**, not a nicety: it's the bookkeeping that proves the cast survives
to the end. Note when `series-state.md` is still the empty template.

### 4. Write the critique

Write to:

```
output/<series>/notes/critique-grimoire.md
```

This audit runs fresh every time: **do not read the previous
`notes/critique-grimoire.md`** before forming your findings, and **overwrite**
it — never merge. The only audit you trust is the one you generate this run.

Structure (write the findings; leave the verdict to the script):

```markdown
# Grimoire critique — <series>

**Verdict:** <filled in below by compute_verdict.py>

**Summary:** one-paragraph diagnosis.

## MUST fix
- **[issue-type]** — concrete finding with quoted text or missing section
  pointer → suggested direction.
- ...

## SHOULD fix
- ...

## CONSIDER
- ...

## What works
- 4-6 brief notes on what the grimoire does well. The author needs the
  signal too, especially since this skill is harsh.

## Cross-references to plan
- If a per-book plan already exists (`book-NN/`), note any
  inconsistencies between grimoire and book setup.
```

Tag each MUST with a bracketed issue-type. Use these **REJECT-tier** slugs for
structural breaks needing the foundation rebuilt: `[magic-missing-pillar]`
(source/cost/limits), `[no-antagonist-thesis]`, `[climax-passive]`,
`[no-clock]`, `[system-arc-undeclared]`, `[empty-14-table]`. Any other MUST (a
§14/§14b row to complete, a gating decision to resolve, a stale cross-ref) is
REVISE-tier.

**The verdict is computed, not judged.** After writing the findings, run:

```bash
python3 scripts/compute_verdict.py \
    --critique-file output/<series>/notes/critique-grimoire.md --target grimoire
```

Write the printed verdict into `**Verdict:**`. Thresholds it applies: **PASS** =
zero MUST and ≤6 SHOULD; **REJECT** = any REJECT-tier MUST; **REVISE** otherwise.
When in doubt between REVISE- and REJECT-tier, pick the REVISE-tier tag.

### 5. Report to user

Print:
- Verdict and counts by tier.
- The 3-5 most load-bearing findings (one line each, citing source).
- Path to the critique file.
- Suggested next step:
  - **REJECT** → revise grimoire, then re-run `critique-grimoire`.
  - **REVISE** → walk through the MUST/SHOULD findings interactively;
    author updates grimoire; re-run.
  - **PASS** → `book-setup` for Book I (or for the next book in
    series), with grimoire as fixed reference.

### 6. Compose with `critique-plan`

If a per-book plan already exists for Book N (`output/<series>/book-NN/`),
`critique-plan` should be re-run AFTER `critique-grimoire` PASS. The
per-book audit can then assume the grimoire is sound and focus on the
book-level plan against the grimoire's contract.

## What this skill does NOT do

- Does not modify `grimoire.md`. The author writes the grimoire.
- Does not generate prose, plan files, or canon entries.
- Does not invent worldbuilding to fill gaps. It surfaces gaps and
  proposes directions; the author decides.
- Does not auto-parse the grimoire into `setup.md` (no `ingest-grimoire` —
  intentional design decision).

## Files this skill writes

- `output/<series>/notes/_audit-grimoire.md` — deterministic audit.
- `output/<series>/notes/critique-grimoire.md` — qualitative critique.
