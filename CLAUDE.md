# CLAUDE.md — The Seed Grimoire

The Seed Grimoire writes entire fantasy novels with Claude Code, **one disciplined chapter
at a time**. The whole book lives on disk as plain deterministic files; there is
**no agent graph, no vector DB, no API plumbing** — just a deterministic file
layout and a set of focused skills. Keep it that way: prefer **deterministic files
(Markdown for prose and narrative canon; JSON state mutated only by scripts) +
stdlib** over any retrieval/embedding machinery, and let the views the LLM reads
be **computed** from that state, not hand-kept.

**The world-state engine (RESTRUCTURE-V2, `scripts/lib/engine/`).** The spatial-
temporal contract — where every character is at every moment, who can speak or
overhear, the geography — lives in a stdlib Python engine over a JSON store
(`state/{world,entities,seeds,shadow}.json` + `state/events/ch-NN.jsonl`), mutated
**only** through `scripts/world_tool.py` (the sole write gate, precedent
`mark_seed.py`). Integrity lives in ONE place — the commit: an impossible event
(teleport, backward clock, off-plan seed touch, leak past a reveal cap) fails to
`replay`, so errors are *unrepresentable states*, not a battery of checks. The LLM
never edits the JSON; it reads **computed** Markdown views (`render_opening_state`,
`render_place`) that cannot drift from the truth. **Adoption is per-book:** a book
with a `state/` store gets the computed World-state bundle block + the lock-in
`replay` check + the manifest→commit lock-in loop; an un-migrated book (el-vitral
today) keeps the full legacy Markdown path unchanged. Landed: Fase 1 (engine),
Fase 2a (context/lint wiring), Fase 2b (skill-layer manifest/commit, store-gated).
Pending: Fase 4 migrates el-vitral (`migrate_story.py` + L1-L5) — see
`RESTRUCTURE-V2.md`. The seed/shadow gotchas below stay live until then.

## Tech stack

- **Python 3.12, stdlib only** for `scripts/lib/`. No third-party runtime deps.
- Package manager is **`uv`** (`~/.local/bin/uv`). Do **not** use pip/pip3.
- `gh` CLI present, logged in as **abetatos**. (The machine's SSH key is a
  different account, `arec97` — use `gh`/HTTPS for GitHub, not SSH.)
- `sudo` needs an interactive password — install user-level tools without it.

## Architecture

Skills live in `.claude/skills/`. The pipeline per chapter is:
**resume-act** (session bootstrap) → **plan-chapter** (decision gate) →
**write-chapter** (drafts via the persistent `chapter-smith` subagent) →
**critique-chapter** (the sole grounding detector) → reactive warm fill / revise
by the **same live smith** (`chapter-grounder` is the cold fallback), only if
the critique calls for it → **update-canon** (lock-in) → **close-act** (at act
boundaries). **write-novel** orchestrates one chapter end-to-end, then HARD STOPS
for `/clear`.
**Grounding is split into detection and fill (no unconditional pass).** The raw
draft goes straight to the critique, which runs the six need-tests in fresh
context — a world element used but never watched operating (unfold it slowly), a
space the reader cannot draw (build the stage), a spend with no visible cost, a
decision taken cold (deliberation before the hinge), a disorienting time/place
jump, or a named secondary functioning as a prop. **Fill is reactive**: only where
the critique names a need-test that fired with no insert is a fill applied, 2-pass
cap, quoting the line where the need shows. **Detection is always fresh
(`book-critic`); the fill is warm — the chapter's still-alive `chapter-smith`
applies it (via `SendMessage WARM-FIX:`) in its own drafting voice** (see the smith
paragraph below). Curse of authorship lands on *detection*, which the smith never
does — so warm fill by the writer is safe. The cold `chapter-grounder` is the
**fallback** when no live smith exists (`expand-chapter` standalone, or
`write-novel --in-session`). On the raw draft the need-tests fire more often than on
a pre-grounded one — same depth, moved from a pass that taxed every chapter to a
reactive path that only touches the ones that need it. A collapsed beat is replayed
(never filled); texture that passes no need test is trimmed. **Generated word
counts are never measured back to the model** — no counter anywhere in the pipeline
(the setup range is a planning-time objective for outline sizing only): a visible
count-vs-target breeds compensation, padding one chapter or "write more
generously" leaking into the next.

Critiques run in a **fresh subagent** (`.claude/agents/book-critic.md`): a
critique audits in an isolated context that never saw how the work was written
(no info leak), so the author no longer has to `/clear` to audit in clean.
All three critique skills self-dispatch (a **step 0**): invoked standalone they
send their **analysis** (their steps 1-4) to the `book-critic` subagent and run
only their interactive tail (the `AskUserQuestion` menu / `/clear` sentinel /
report) in the main thread, because a subagent can't talk to the user.
`write-novel` dispatches `critique-chapter` itself, so when it chains the skill
the analysis is already in the subagent (no re-dispatch). The critic only writes its `notes/critique-*.md` file and returns the
verdict — it never edits source. Recursion is structurally impossible: the
book-critic agent has no Agent tool, so when it runs a critique skill it executes
the analysis directly instead of re-dispatching. `search-corpus` likewise runs in
the built-in `Explore` subagent so file dumps stay out of the main context.

**update-canon** self-dispatches the same way (its **step 0**): lock-in reads
≈18k words (chapter prose + all canon + `seeds.md` + `shadow.md`) and applies the
deterministic writes, so its **steps 1-4 run in the `canon-scribe` subagent** — the
**constructive** dual of `book-critic` (it has Edit; book-critic has none). The
scribe writes the chapter summary, advances every *unambiguous* seed/truth status,
and promotes additive canon; anything that would be a HARD STOP (scheduled seed
absent, unscheduled touch, truth over cap, canon contradiction) it leaves unwritten
and returns as a **FLAG**. Only the cheap conversation-aware tail stays in the main
thread: the pre-lock delta check, acting on FLAGS with the author, the mandatory
checkpoint (needs the live conversation), and the report + `/clear` sentinel.
Recursion is structurally impossible — `canon-scribe` has no Agent tool.

**forge-grimoire** is the **constructive** counterpart of `critique-grimoire`:
it WRITES the series grimoire section by section (bootstrapping from
`references/grimoire-template.md` if missing), proposing each fill as
author-confirmed `AskUserQuestion` choices, scaling §14 loaded guns / §14b
master mysteries up to trilogy breadth, then auto-running `critique-grimoire`
and re-filling until PASS. Both share `audit_grimoire.py`: critique audits with
it, forge's `scan_grimoire.py` imports its parsing helpers to build the
constructive worklist. forge writes `grimoire.md`; critique never does.
`plan-chapter` stays in the main thread (it is the interactive decision gate);
`write-chapter` self-dispatches its draft (steps 1-4) to `chapter-smith` and keeps
only the report tail in main (its **step 0**, mirroring the critique/scribe
pattern); `update-canon` keeps only its interactive tail there (see above) and
offloads its steps 1-4 to `canon-scribe`.

Book state on disk under `output/<series>/book-NN/`:
`setup.md`, `style.md`, `canon/` (characters, factions, magic, world, timeline),
`plan/` (outline, shadow, seeds, arcs), `chapters/`, `summaries/`
(ch-NN, act-NN, book-summary), `notes/` (decisions, decisions-chNN,
continuity-chNN, voice, voice-exemplars, style-rules, open-questions,
session-handoff, prose-lint.toml).

Two more fresh-context agents mirror `book-critic`/`canon-scribe`: `naive-reader`
(Read/Glob only, reads ONLY chapter prose) answers a non-leading questionnaire at
act boundaries so the author can measure telegraphing against `shadow.md` reveal
caps without the curse of knowledge; dispatched by `close-act`.

`chapter-smith` is the **generative** dual — it DRAFTS the chapter. It runs
`write-chapter`'s exact block-by-block flow in an isolated clean context, so the
~26k bundle + prose + inter-block re-reads stay out of the main thread AND the
draft is written below the attention-degradation zone (better voice, not just
cheaper). It is **persistent** (Movement 1c, landed 2026-07-19): the conductor
keeps **one** smith alive for the whole chapter and drives it with `SendMessage`.
It **pauses** — returns `DRAFTING_PAUSED` + a `QUESTIONS` block — when it hits an
**irreversible** memory gap it cannot derive from canon (frontier:
irreversibility × absence-from-canon); the conductor relays via `AskUserQuestion`
and `SendMessage`s `RESUME:` + answers, and the same smith continues with its
context intact. Reversible gaps never pause — write-around + low-confidence
ASSUMPTION. After the critique it applies the fills/REVISE **warm** (`WARM-FIX:`,
its own voice), and it is **released at lock-in** (`RELEASE`). Its draft-complete
hand-off (visible plot, PLANTED/INVENTED, ASSUMPTIONS, FLAGS) narrows
`canon-scribe`'s hunt but never substitutes for its verification. It is the
**default writer** — `write-chapter` self-dispatches to it (step 0) and
`write-novel` dispatches + drives it; the author's blind-compare validated the
voice gain (2026-07-19). `write-novel --in-session` is an escape hatch that drafts
in the main thread (no persistent smith: emergent gaps asked inline, fills fall
back to the cold `chapter-grounder`). See `IMPROVEMENT-PLAN.md` Movements 1 + 1c.

`scripts/lib/` is the deterministic core: `context.py` (bundle assembly),
`summaries.py` (hierarchical summaries + continuity seam), `seeds.py`
(foreshadowing model), `parsing.py` (shared loud parser for the never-compress
files — chapter lists, touch logs, field terminators; used by seeds + shadows),
`paths.py`, `shadows.py`, `setup_doc.py`, `lint.py` (state auditor) and
`verdict.py` (computed critique verdict).

**Deterministic guardrails (invariants live in code, not prose):**
- `scripts/lint_book.py` — audits seed-schedule sanity, seed↔shadow refs,
  lock-in completeness, book-summary freshness. Run by `resume-act`,
  `update-canon`, and the critiques; exit 1 on any ERROR.
- `scripts/compute_verdict.py` — derives PASS/REVISE/REJECT from a critique
  file's tagged findings, so the verdict is counted, not judged.
- `scripts/strip_expand_markers.py` — removes `▼▼▼ EXPAND ▼▼▼` banners (the
  cleanup pass expand-chapter's markers promise). Run by `update-canon` at
  lock-in, AFTER `prepare_summary.py` (its T12 hash is over raw file bytes,
  so stripping first would trip the tamper check).
- `scripts/lint_prose.py` — counts the named prose tics (explanatory simile,
  "no X, sino Y", "como si", repetition-as-emphasis, anaphora, adverb/gerund
  density) per chapter AND cross-chapter repetition (verbatim motif phrases,
  re-described images ≥3 uses in ≥2 chapters, signature-word reuse, echoing
  openings, reserved lexicon spent off-plan) into `notes/_prose-report-chNN.md`,
  so the critic judges counts instead of tallying by eye. The same counts feed
  the write/expand bundle's "Already spent" section (`overuse_summary`), which
  fires from chapter 2 on — the summaries + seam showcase chapter N-1's best
  images, so the writer needs the counterweight. Caps + reserved lexicon per
  book in `notes/prose-lint.toml` (stdlib `tomllib`). Run by `critique-chapter`
  (step 8b). The lexical layer is per-language (es only today): a book whose
  setup declares another language raises `UnsupportedLanguageError` instead of
  counting wrong and reporting clean — see `SUPPORTED_LANGUAGES` in
  `lib/prose_lint.py`.
- `scripts/verify_critique_quotes.py` — checks every quoted line in a chapter
  critique appears in the chapter (or a source it cites) so a hallucinated
  finding can't be counted into the verdict. Run by `critique-chapter` before
  `compute_verdict.py`.
- `.claude/hooks/protect-never-compress.sh` — PreToolUse hook that blocks direct
  Edit/Write of `plan/seeds.md` / `plan/shadow.md` (mutate via `mark_seed.py` /
  `mark_truth.py`) and of the world-state store `state/*.json` +
  `state/events/*.jsonl` (mutate via `world_tool.py` / `migrate_story.py`, which
  replay-validate before writing). The surgical scripts write via Python
  `open()`, not the Edit tool, so they are unaffected.
- `.claude/models.toml` + `scripts/sync_models.py` — project-level source of
  truth for which model each subagent runs on (`[agents]` → agent frontmatter,
  `[dispatch]` → search-corpus's Explore dispatch token). Edit the TOML, then
  `uv run python scripts/sync_models.py` (`--check` to detect drift). Do NOT
  hand-edit `model:` in `.claude/agents/*.md` — it gets overwritten. Prose
  skills carry no `model` field on purpose (a skill override bleeds into the
  rest of the turn when write-novel chains skills).
- Tests: `uv run python -m unittest discover -t . -s tests` (stdlib only).

## How context is assembled (`build_context.py` → `lib/context.py`)

One Markdown bundle per chapter, in a fixed precedence order. `--phase` tailors it:

- `write` — full bundle (the only phase that drafts prose).
- `plan` — for plan-chapter's gate; drops the seam, style guide and craft
  checklist (prior chapters arrive as summaries).
- `critique` — drops the seam; keeps style + craft.

**The continuity seam** (not the whole previous chapter): chapter N-1's
structured summary (end-state + carry-forward) + only its **final scene
verbatim**. Tunables in `summaries.py`: `FULL_TEXT_WINDOW=1`,
`RECENT_DETAIL_WINDOW=6`, `SEAM_TAIL_WORDS=900`,
`DEFAULT_CHAPTERS_PER_ACT=7`.

## Conventions

- **Prose defaults to Spanish (`es`)**; skills and `references/` are in English.
- **Author / pen name** lives in root `config.toml` (`[author] name`, read by
  `lib/project_config.py`) — the project-wide default for EPUB metadata and
  new `setup.md` scaffolds. A book overrides it via its `**Autor:**` line in
  `setup.md`; `build_epub.py` resolves `--author` > setup > config.
- **Seeds and shadow are NEVER compressed** — they survive act compression and
  are the source of truth for foreshadowing and the hidden timeline.
- **Seeds carry a `Realized:` touch-log.** Every plant/echo, `update-canon`
  appends how the seed *actually landed on the page* (via
  `mark_seed.py --realized`), so a far-later payoff rhymes with the prose, not
  the plan.
- **`decisions.md`** = book-level binding choices; **`decisions-chNN.md`** =
  per-chapter gate decisions (from plan-chapter). Both authoritative and
  committed — note the **no underscore prefix** (the `_context-chNN.md` bundles
  are the regeneratable, gitignored ones).
- **One chapter per session, then `/clear`.** All state is on disk; the next
  session rebuilds via `resume-act`. No cross-chapter autopilot.
- Craft rules have **one canonical in-context home**: the bundle's Craft
  checklist + the book's `style.md`. The full `references/*.md` files are for
  on-demand depth — do not re-narrate them inside SKILL.md files.

## Gotchas

- **Do NOT name Sanderson** (copyright caution). Use the extracted craft terms:
  `references/hard-magic-laws.md`, "slow-immersion" pacing, "hard-magic laws".
- **`seeds.md` is a NEVER-compress file** with wrapped multi-line fields and a
  hand-written header. Mutate it **surgically** (`seeds.py::update_status_in_text`
  / `append_realized_in_text`), never via a `load_seeds`→`save_seeds` round-trip,
  which would reflow/drop content.
- `main` is the single working branch.

## Pending work

See `TODO.md` — notably the deferred Phase-C token-growth levers (canon scoping,
setup filter) to apply once canon is large (act 2+), and trans-book seeds.
