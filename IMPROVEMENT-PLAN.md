# IMPROVEMENT-PLAN.md — pipeline efficiency & shape

> **Status: PROPOSAL. Do NOT implement mid-generation.** Apply only between
> books / at a clean `/clear` boundary, one movement at a time, re-running the
> test suite after each. `write-chapter/SKILL.md` already dangling-references a
> "chapter-smith … T20" — Movement 1 is that, made real.

> ### Progress (2026-07-19, clean boundary — ch1 being redone)
> - **Movement 4 ✅** placeholder no longer counts as a finding (code +
>   structural lint in `verify_critique_quotes.py` + the SHOULD half + templates
>   of all three critique skills + tests).
> - **Phase 0 ✅** `scripts/token_report.py` (+ `lib/token_report.py`, tests) —
>   per-phase token attribution; two thresholds fixed (`CONTEXT_CEILING=80k`,
>   `OUTPUT_TARGET=250k`); reproduces the n=1 baseline; wired into write-novel's
>   HARD STOP to accrue 3-4 chapters of data.
> - **Movement 2 ✅** merged `brief-chNN.md` (`lib/brief.py`); retired
>   `open-questions.md` (tooling → `TODO.md`, changelog → git); ch1 migrated;
>   context.py splits the brief to its 3 bundle positions; 8 skills rewired.
> - **Movement 1 ✅ (now DEFAULT)** `.claude/agents/chapter-smith.md`
>   (fire-and-forget, opus). **Blind-compare PASSED 2026-07-19** — the author drove
>   ch1 through the smith (isolated, 134k subagent tokens that never touched main;
>   main peak unaffected) and judged the voice a clear improvement, so the
>   in-session draft was not even generated. `write-chapter` now self-dispatches to
>   the smith (step 0, mirroring critique/scribe); `write-novel` dispatches it at
>   the write step; `--in-session` is the escape hatch. That ch1 draft is now
>   `chapters/01.md`. **1c (persistent smith) landed too — see below.**
> - **Movement 3 ✅ (author-directed)** the unconditional expand pass is deleted;
>   grounding is split — detection is the critique (six need-tests on the raw
>   draft, the sole detector), fill is reactive via the new fresh-context
>   `chapter-grounder` agent (opus, a *different* agent from the writer:
>   curse-of-authorship). `write-novel` 2c no longer grounds; 2d routes an unfired
>   need-test to the grounder (2-pass cap). expand-chapter reframed +
>   self-dispatches (step 0).
> - **Movement 1c ✅ (author-directed 2026-07-19)** the smith is now **persistent**,
>   not fire-and-forget. `write-novel` keeps **one** `chapter-smith` alive for the
>   whole chapter (`run_in_background`) and drives it with `SendMessage`: it PAUSES
>   (`DRAFTING_PAUSED` + `QUESTIONS`, each with a DEFAULT) on an **irreversible**
>   memory gap it can't derive from canon → conductor relays via `AskUserQuestion`
>   → `RESUME:` + answers → same smith continues, context intact (reversible gaps
>   still write-around + ASSUMPTION, never pause); after the critique it applies the
>   fills/REVISE **warm** (`WARM-FIX:`, its own voice); it is **released at lock-in**
>   (`RELEASE`). This buys back the ask-the-author channel and warm-voiced fill that
>   fire-and-forget killed. The reconciliation with Movement 3's "different agent"
>   rule: curse-of-authorship binds **detection** (still the fresh `book-critic`),
>   not fill — so warm fill by the writer is safe. The cold `chapter-grounder`
>   demotes to **fallback** (`--in-session` / standalone `expand-chapter`, no live
>   smith). Agent + 4 skills + CLAUDE.md rewired; no Python changed. **Tradeoff
>   accepted knowingly:** the smith stops being a pure function and becomes a
>   long-lived conversational agent (more orchestration, agent lifecycle, a
>   mid-draft round-trip's latency) — the author chose it on the design, ahead of
>   the "voice suffering" evidence the plan had gated it on.
> - **Movement 5 ⏳** no-op until the first act close (act 2+).

The pipeline is the right shape (deterministic Markdown + fresh-context
subagents for the heavy read-only work). The problems are all on the
**generative** side, which still runs in the main thread, plus a layer of
per-chapter note files that grew into ceremony.

**Two goals, not one:** cut **cost** AND stop **quality degradation**. They are
the same lever — see the reframe below.

---

## Diagnosis (grounded in a real run)

Transcript `4cbc0958` (Jul 13, *el-cuadrado* book 1, ch 2, full `write-novel`):
one **2,920-word chapter** drove the main conversation from 48k → **352k tokens
of context (7×)** and **548k output tokens**.

The audits are already well isolated: `book-critic` and `canon-scribe` each
return ~228 tokens — their ~18k-word analyses never enter the main thread. The
leak is entirely generative, and concentrates in two twin sinks:

| phase | what stays in main thread | Δcontext | output |
|---|---|---|---|
| **write-chapter** | write bundle (~26k) + prose + inter-block re-reads | **+98k** | **167k** |
| **update-canon (tail)** | re-reads chapter, ~8 prose Edits, rebuilds summary, checkpoint | **+98k** | **204k** |
| plan-chapter | plan bundle (12.5k) + reasoning | +46k | 31k |
| expand-chapter | bundle + cold chapter re-read + edits | +32k | 76k |

**The memory finding — the writer was NOT re-litigating settled craft.** Its
mid-draft reasoning opened *new* forks plan-chapter could not anticipate,
because they are the author's **lived memories** surfacing only when the
concrete scene demands them (a camping table; the beso at María's house; "this
folklore needs more introduction"). All three were answered with free-text
**"Other"** — the multiple-choice scaffold is bypassed exactly when the decision
is a memory. That single fact drives Movements 1 and 2.

### The reframe — the enemy is context LENGTH, not just tokens

Cost is only half of it. By chapter N the main-thread writer drafts inside 300k+
of context, and **a model at 300k writes worse than at 30k** (attention rot).
So `chapter-smith` is not only cheaper — it produces **better prose** because it
drafts in a clean context. This is what makes Movement 1 a *quality* fix, and
answers "why does 352k hurt?": it hurts because it **degrades the voice**, the
one thing this project cannot spend. The whole sequencing below falls out of it.

---

## Movement 1 — writing becomes a subagent (`chapter-smith`)

**Biggest lever. The missing generative dual of `book-critic` / `canon-scribe`,
and the fix for both cost and voice degradation.**

A fresh-context subagent that:
- Reads the deterministic write bundle + the locked per-chapter brief (Movement
  2) **in its own context**.
- Drafts block-by-block with today's exact inter-block re-read discipline (it is
  mechanical; it moves verbatim into the agent's instructions).
- Returns a **machine-readable hand-off** (not prose): the prose on disk plus a
  structured block of what it planted and invented while writing:

  ```
  PLANTED: las-manos-del-lector @ "de algo que le había comido el color…"
  INVENTED: río Soral → canon/world.md
  ```

  > **RESTRUCTURE-V2 formalizes this hand-off.** Once a book adopts the world-state
  > engine, PLANTED/INVENTED become the smith's **MANIFEST** — the typed event log
  > the page staged (`world_tool.py` vocabulary, seed touches carrying their
  > quote) + DEVIATIONS + the chapter SUMMARY — and `update-canon` collapses from a
  > hunt to a `replay`-validated **commit** of that manifest. Store-gated: an
  > un-migrated book still uses the plain PLANTED/INVENTED hand-off. See
  > `RESTRUCTURE-V2.md` Fase 2b.

**Effect:** the ~34k of bundle + prose + re-reads leaves the main thread; the
352k peak collapses because its largest contributor is gone, and the draft is
written in a clean context (better voice). The conductor (`write-novel`) keeps
only the interactive gate + the returned reports.

### 1c — persistent smith vs fire-and-forget (✅ LANDED 2026-07-19, author-directed — see Progress header)

The version above is **fire-and-forget** and it is enough to bank the cost +
clean-context win — ship it first. But fire-and-forget has two structural holes
the plan elsewhere files under "no clean solution": an **emergent memory fork**
surfacing mid-draft has no way back to the author (the subagent can't talk to
them), and a critique **REVISE** must re-draft in a fresh `revise` agent that
lost the drafting context.

Both close if `chapter-smith` is instead a **persistent agent** the conductor
keeps alive for the whole chapter and drives via `SendMessage` (continues the
subagent with its context intact). One control loop:

- smith drafts; on an **irreversible** memory gap it can't derive from canon it
  returns `DRAFTING_PAUSED` + a `QUESTIONS` block + the partial draft; the
  conductor surfaces them via `AskUserQuestion` (main thread, cheap) and
  `SendMessage`s the answers back — same agent resumes. (Reversible gap → write
  around + flag, never pause. Frontier: `irreversibility × absence-from-canon`.)
- a REVISE / unfilled need-test `SendMessage`s the findings back to the **same**
  smith, which fixes in its own live voice (Movement 3's fill, warm not cold).
- smith dies at lock-in.

This preserves the ask-the-author channel that fire-and-forget kills, and it is
what makes Movement 3's fill match the voice. **Tradeoff:** `chapter-smith` stops
being a pure function and becomes a long-lived conversational agent — more
orchestration in `write-novel`, agent lifecycle to manage, a mid-draft
round-trip's latency. Escalate to it **only if** the Phase-0 blind-compare shows
fire-and-forget's voice suffering on emergent-fork chapters; the plan's
"most-reversible assumption + residual review" is the working fallback until
then. The core plan does not change shape — this adds an option on top.

### 1a — memory forks: harvest BEFORE, don't guess-then-review

Guessing a person's lived memory is where an LLM has zero signal — it invents
plausible fiction, discovered late (after a full draft), costing draft + revise.
Split by predictability:

- **Foreseeable** (the beat sheet already shows "beso scene", "meeting place"):
  `plan-chapter` **harvests them up front**, in the main thread (cheap), into the
  brief. `chapter-smith` writes *against* them instead of guessing. This keeps
  the author in the creative seat where the token is cheap (planning).
- **Emergent** ("this folklore needs more intro" — surfaces only with the
  concrete scene): **no clean fix, by construction.** The writer makes the **most
  reversible** assumption (writes *around* the gap, keeps the scene re-blockable),
  flags it low-confidence, and it goes to a post-draft review the author corrects
  in their own words; a surgical `revise` (subagent) applies the correction.

Keep `plan-chapter`'s `AskUserQuestion` for genuine **craft** forks — those work
(in the real run the author took all 4 recommendations). Stop forcing **memory**
answers into a multiple-choice mould. This is a *when-you-interact* change.

### 1b — slim the `update-canon` tail (no free lunch)

The chapter re-read is **already in `canon-scribe`** (fresh context) — the second
sink is not the re-read, it is the **tail left in main**: ~8 prose Edits + summary
rebuild + checkpoint. Move the writes, not a trust claim:
- The `book-summary` rebuild **moves into `canon-scribe`** (it already holds the
  chapter + canon).
- The prose Edits leave main: marker-stripping is already deterministic
  (`strip_expand_markers.py`); applying corrections is 1a's surgical revise.
- The `PLANTED/INVENTED` hand-off is a **hint that narrows the scribe's hunt, not
  a substitute for verifying** — do not hang a correctness promise on it.
- Leave in main only what needs the live conversation: the checkpoint of
  ephemeral voice/style observations, and acting on FLAGS.

---

## Movement 2 — one fixed-template brief per chapter (do this FIRST)

Land it **before** Movement 1, with the current main-thread writer: it is
low-risk and valuable on its own (the merged brief is the clean hand-off
`chapter-smith` later consumes). Coupling the format migration to the risky
subagent change would drag the migration into any rollback.

Today three per-chapter/rolling note files do three jobs. Collapse to one shape.

### Retire `open-questions.md` — but keep a disciplined carry buffer

In the live book it is **1,866 words** and is not story state — it is a project
diary mixing reset changelogs (git has these), tooling bugs (the name-desync
thread is re-confirmed 6× across 6 dates, never closed), and threads its own
later entries mark STALE. `context.py` loads it into the `plan` + `critique`
bundles ([lib/context.py:626](scripts/lib/context.py#L626)), paying ~2.5k tokens
twice per chapter for a half-dead log.

It failed for lack of **schema and a close rule**, not for existing. Killing it
outright leaves a **cadence gap**: a thread that surfaces *during* ch3 and blocks
ch4 has no mailbox (`session-handoff.md` is per-act; `brief-ch04` does not exist
yet). So:
- tooling bugs → `TODO.md` (or just fix them); changelog → git;
- carry threads → a `## Arrastre` section inside `brief-chNN.md`, which the next
  gate fills from what is pending, with a **hard close rule** (deleted when
  consumed). The old file with a schema and an expiry, not its corpse.

### Merge `continuity-chNN.md` into `brief-chNN.md`

- `decisions-chNN.md`'s content **stays** — the gate's output and the writer's
  binding contract (and, under Movement 1, the hand-off to `chapter-smith`).
- `continuity-chNN.md` is a **derived view, not a source**: ~90% a re-projection
  of canon-state + shadow-slice + seed calendar + prev carry-forward. Its only
  value is compression + late placement near the instruction — placement, not a
  second source of truth.

Collapse to a single **`brief-chNN.md`** with fixed sections: `## Decisiones`
(closed forks) + `## Estado que no se puede contradecir` (state sheet) +
`## Arrastre` (carry buffer). Same shape every chapter. Make it explicitly
**mandatory** — the "optional file that is always written" smell is a mandatory
file in disguise; name it so.

*Considered and rejected — a pre-fill script.* The state sheet is 15 curated
lines the gate writes from context it already holds (seed envelope + shadow slice
are in its bundle). A script projecting canon-state + active seeds produces noise
the gate must prune — not cheaper than writing 15 tight lines, and a new script
to maintain. Do NOT build it.

**Problemática — why Movement 2 is OPTIONAL, not blocking (and why the stated
ordering argument is weak).** Three separate things hide under "merge the notes":

- **It is a format migration, not a new file.** The three sources are written by
  different skills at different times (`plan-chapter` writes two; `update-canon` /
  `close-act` touch `open-questions.md`) and read at specific bundle points by
  `context.py` ([:626](scripts/lib/context.py#L626),
  [:647](scripts/lib/context.py#L647)). Merging rewrites those assembly branches,
  the writers, and the tests, and forces a decision on already-written chapters
  that carry the old files. It crosses `plan-chapter`, `update-canon`,
  `close-act`, `context.py` and tests — not a one-file change.
- **The schema is designed against a consumer that doesn't exist yet.** The plan
  justifies landing it first as "the clean hand-off `chapter-smith` consumes" —
  i.e. the format is shaped for a cold subagent (M1) not yet built, while today's
  real consumer is the main-thread writer with the whole live conversation.
  Design for today's writer and M1 likely finds it thin → **you migrate the
  format twice**; design for tomorrow's subagent and you optimise for something
  not in front of you (YAGNI) that may change when you actually build it.
- **M1 does not need this.** `chapter-smith` can read the three current files
  exactly as they are — merging is **hygiene** (one shape, better placement,
  retiring the half-dead `open-questions.md`), never a prerequisite for moving
  writing into a subagent. So M1 does not depend on M2, and the real reason to do
  M2 first is its **own** value, **not** that M1 needs it — the plan's "it's the
  hand-off M1 needs" does not actually justify the ordering. Land it on its own
  merit; keep it decoupled so it can't drag an M1 rollback.

---

## Movement 3 — split grounding into DETECTION and FILL (replaces the unconditional expand)

The depth is real and a single left-to-right pass cannot reach it by
construction — but an **unconditional** expand step taxes every chapter for an
occasional payoff (near-zero inserts on this short/dense book).

Do **not** fold self-grounding into `chapter-smith`: that reintroduces the
**curse of authorship** (the agent that made the gap is the worst auditor of it),
and auto-auditing inside a context freshly saturated with its own prose is worse,
not better — exactly what fresh contexts exist to avoid. Instead split the
function and put each half where it already lives well:

1. **Detection → fresh eyes.** `critique-chapter` already runs the six need-tests
   in a fresh context. Make it the **only** detector; delete the unconditional
   `expand` pass.
2. **Fill → reactive, proportional to payoff.** When the critique names a
   need-test that fired with no insert, an `expand`/`revise` subagent fills it.
   Short/dense book → the step almost never runs; long book → it fires more
   often, depth preserved. Zero extra per-chapter author burden.

**Grounding is displaced, not deleted — say so.** Today `expand` runs **before**
the critique, so the critic audits an already-grounded chapter. Delete the
unconditional pass and the critic audits the **raw** draft, so its six need-tests
fire **more often** → the reactive fill runs more than "almost never" implies on
a dense book. Not a regression: same depth, the work just moves from a pass that
taxed every chapter to a reactive path that only touches the ones that need it.
But it is a **displacement of where grounding happens**, not a free deletion —
don't sell it as pure savings. And if the persistent smith (1c) is in play, the
fill is `SendMessage`d to that live agent (warm voice); with fire-and-forget it
is a cold `expand` subagent (the residual below).

**Residual (honest):** cold fill matches the voice less well than in-line
writing. Bounded — it only runs on the minority of chapters with a real gap, only
over the inserted paragraphs; the subagent gets the chapter + `voice-spine` +
the insert's neighbours. **Gated by evidence:** if a long book shows cold fill
degrading the voice, reconsider in-line self-grounding. Decide by the Phase-0
data, not up front. `chapter-smith` stays a pure writer.

*Deferred, long-books-only — a coverage check in `critique-plan`.* One audit
question in its existing pass: "does each chapter's typed grounding cover the six
lenses where the beats demand it? Flag the thin ones." Output is a flag, no prose
authored, no over-marking risk. But the reactive fill above already attacks the
same defect, and this short/dense book needed neither. **Ship the core alone; add
this only when a long book shows the fill is patching too much.**

---

## Movement 4 — `verdict.py`: don't count placeholder bullets as findings

**Observed:** a critique left `## MUST fix` empty with a placeholder `- (none)`.
`compute_verdict` counts any top-level `- ` bullet, so `must=1` → a spurious
**REVISE**. The pipeline then self-corrects (inspect `verdict.py`, rewrite the
file, recompute → PASS) — recurring wasted churn from an unenforced convention.

**Fix — a structural filter, not a placeholder denylist.** The template requires
every finding to carry a bracketed issue-type
([critique-chapter/SKILL.md:351](.claude/skills/critique-chapter/SKILL.md#L351)),
and the code already has `_ISSUE_TYPE_RE`. In `compute_verdict`, count a MUST
bullet **only if it carries the `**[issue-type]**` tag**. A `- (none)` / `- —` is
dropped by construction — no locale-fragile word list to maintain (`none`,
`ninguno`, `nada`, `sin hallazgos`… all handled). A real MUST always carries the
tag, so this **cannot drop a genuine finding — zero downside**. Add a test.

**Complete the fix — SHOULD has the same bug, and the plan's premise is
half-true.** The premise "the template requires every finding to carry a
bracketed issue-type" is only enforced-by-example on **MUST**
([SKILL.md:350-355](.claude/skills/critique-chapter/SKILL.md#L350)); SHOULD /
CONSIDER show `- ...` with no tag. So the MUST filter alone leaves the identical
placeholder bug in the **SHOULD** count ([verdict.py:96](scripts/lib/verdict.py#L96)),
which is verdict-bearing via the PASS cap
([verdict.py:114](scripts/lib/verdict.py#L114)) — a `- (none)` under an empty
`## SHOULD fix` can tip a real PASS into REVISE. The complete fix is three coupled
changes, not one:
1. Template: require `**[issue-type]**` on SHOULD too, and state "empty section =
   no bullets, never a placeholder".
2. Code: count MUST **and** SHOULD bullets only when `_ISSUE_TYPE_RE` matches
   (CONSIDER is not counted into the verdict — leave it).
3. A **structural lint** (extend `verify_critique_quotes.py`) that ERRORs on any
   MUST/SHOULD bullet lacking a tag — so a critic that forgets the tag fails
   **loudly** instead of having a real finding silently dropped (the failure mode
   the bare tag-filter would introduce).

The observed bug is the MUST placeholder → that half is NECESARIO. Steps for
SHOULD + the lint close a latent, not-yet-observed bug → OPTIONAL hardening; do
them together since they share the template edit.

Independent of everything else; land it whenever, between generations.

---

## Movement 5 — slim the `critique` bundle (deferred act-2+ lever)

Mapping every `critique-chapter` check to the bundle block it reads: the bundle
is **mostly load-bearing**. **Two blocks are provably dead** for a per-chapter
audit:

- **Series context** (block 2: `series-identity` + `series-state`) — no
  per-chapter critique check reads it. (Series *canon* files load separately in
  the Canon block and STAY.)
- **Act-level summaries** inside story-so-far — a per-chapter audit checks THIS
  chapter's contract. The only cross-chapter checks are **8c** (untracked Chekhov
  setups) and the **world-state-changed?** flaw; both need the *immediate* prior
  state (ch N-1) and the never-compressed seed touch-log — a compressed act
  digest feeds neither.

**The cut:** under `phase == "critique"`, drop block 2 and the act-summary layer
of story-so-far; **keep the recent chapter summaries** (especially N-1) and
everything else. Scope: a `context.py` branch that sets `want_series = False` and
swaps story-so-far for a recent-summaries-only plan.

**No-op until act 2** (no act summaries exist at book start) — same class as the
`TODO.md` Phase-C levers. Land it at the first act close with the measurement
step; verify once by diffing the `critique` bundle with/without the cut. Do NOT
touch mid-generation.

---

## Phase 0 — instrument before deciding (kills the n=1)

The whole plan rests on one transcript. Before touching architecture: a cheap
per-phase token log (a `PostToolUse` hook or a counter in `write-novel`), capture
3-4 chapters, and fix **two explicit thresholds**: (a) a main-thread context
ceiling (e.g. ≤80k, so late acts with large canon stay out of the degradation
zone) and (b) a per-chapter cost target. Without this you cannot tell "cheaper"
from "cheaper and worse." Cheap, reversible, does not touch the generation.

## The quality gate the token tests can't give you

Unit tests **cannot see "the prose got worse."** Before committing Movement 1, at
the next book/act boundary: **write one chapter both ways** (current main-thread
writer vs `chapter-smith`) and have the author **blind-compare**. This is the only
test that separates "cheaper" from "cheaper and worse." If `chapter-smith` matches
or beats the voice (likely, per the clean-context reframe) → proceed; if not, the
problem is localized before you marry it.

---

## What has no clean solution (honest)

1. **Unforeseeable emergent memory forks** — cannot be harvested up front by
   construction. Bounded by "most-reversible assumption + residual review," not
   eliminated.
2. **Voice of cold fill (Movement 3)** — imperfect; bounded to inserted
   paragraphs and gated by evidence. If it hurts, revert to in-line
   self-grounding.
3. **Hand-off vs verification (1b)** — no free lunch; the real saving is moving
   *writes* out of main, not trusting the writer's self-report.

---

## Triaje — NECESARIO / OPCIONAL / OVERKILL

The plan was ~90% right; this only re-buckets it and adds two things (the
persistent smith 1c, the SHOULD half of Movement 4). Sequencing follows from it.

**NECESARIO** — without it the plan misses its goal (cost + voice) or a real bug
survives.
- **Movement 1 core** — writing → subagent. Fire-and-forget is enough for the
  core win.
- **Movement 4 MUST fix** — observed placeholder → spurious REVISE churn.
- **Phase 0** — baseline + blind-compare before marrying M1; the only test that
  separates "cheaper" from "cheaper and worse."

**OPCIONAL** — real improvement, real tradeoff; not required for the plan to work.
- **1c — persistent smith** — *gain:* closes emergent memory forks
  (pause→ask→resume), the revise loop, and warm fill in one move. *cost:*
  long-lived conversational agent, more orchestration + lifecycle + a mid-draft
  round-trip. Escalate only if Phase 0 shows fire-and-forget's voice suffering.
- **Movement 2 — merged brief** — *gain:* one shape, better placement, retires
  the half-dead `open-questions.md`. *cost:* format migration across four skills +
  `context.py` + tests; schema designed against an unbuilt consumer. See the
  problemática under Movement 2 — M1 does NOT need it, so keep it decoupled.
- **Movement 3 — delete unconditional expand** — *gain:* drops the per-chapter
  tax. *cost:* displaces grounding to the reactive path (need-tests fire more at
  critique); reintroduce if a long book needs it often.
- **Movement 4 SHOULD + structural lint** — *gain:* closes the same bug in the
  verdict-bearing SHOULD count and makes a missing tag fail loudly. *cost:*
  template change + critic compliance; bug not yet observed.
- **Movement 5 — slim critique bundle** — *gain:* fewer tokens in the critique
  phase. *cost:* no-op until act 2; verify the diff first.

**OVERKILL** — complexity > payoff; skip unless a long book forces it.
- **Structured PLANTED/INVENTED hand-off** — the scribe re-derives from prose
  anyway; unquantified value. At most, scoped to seed-plant intent.
- **Pre-fill script for the state sheet** — already rejected in Movement 2;
  correct.
- **Coverage check in `critique-plan`** — the reactive fill attacks the same
  defect.
- **Parallelism inside a chapter / across chapters** — fights the sequential
  canon dependency; the hot loop is sped up by removing work from main, not
  parallelising it.
- **Fold self-grounding into the writer** — curse of authorship; rejected
  everywhere.

## Sequencing (impact / cost / risk)

1. **Phase 0 — instrument.** Baseline + thresholds. Do first; blocks nothing.
2. **Movement 4 (verdict.py).** Trivial, independent, zero risk. Land now.
3. **Movement 2 (per-chapter brief).** Low-risk, valuable alone, and the clean
   hand-off Movement 1 needs. **Decoupled and before Movement 1.**
4. **Movement 1 (chapter-smith + 1a/1b).** Biggest saving and the voice fix.
   Gated by the blind-compare above.
5. **Movement 3 (detection/fill split).** Rides with Movement 1 (both concern the
   generative path); deletes the unconditional expand.
6. **Movement 5 (slim critique bundle).** Deferred to the first act close (act
   2+), where it first has any effect. Land with the measurement step.

The two structural changes vs the first draft of this plan: **Movement 2
decouples and moves ahead of Movement 1**, and self-grounding is **not folded**
into the writer (Movement 3 splits detection from fill instead).

---

## Parallelism — narrow by design, and that's correct

The pipeline's power **is** its sequential canon dependency: chapter N+1 needs
N's lock-in. Do not fake parallelism over it.

- **Cross-chapter drafting → NO** (real dependency).
- **Blocks within a chapter → NO** (each block continues the live voice).
- **Act boundaries → YES.** `close-act`'s `naive-reader` and the act critique are
  independent — run them concurrently. Infrequent, zero risk.
- **Inside one deep audit → conditional.** A critique's dimensions are
  independent read-only checks and can fan out — but only worth it in a heavy
  "audit" mode, never the per-chapter default.

The hot loop is sped up by **removing work from the main thread (Movement 1)**,
not by parallelising it.

---

## Loose ends

- Fulfil the dangling `IMPROVEMENT-PLAN.md T20` reference in
  [write-chapter/SKILL.md:214](.claude/skills/write-chapter/SKILL.md#L214) —
  Movement 1 is that plan.
- Close the long-open `build_context.py` name-desync tooling thread (re-confirmed
  6× in `open-questions.md`) as part of retiring that file.
