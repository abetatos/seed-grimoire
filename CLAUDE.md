# CLAUDE.md — The Seed Grimoire

The Seed Grimoire writes entire fantasy novels with Claude Code, **one disciplined chapter
at a time**. The whole book lives on disk as plain Markdown; there is **no agent
graph, no vector DB, no API plumbing** — just a deterministic file layout and a
set of focused skills. Keep it that way: prefer deterministic Markdown + stdlib
over any retrieval/embedding machinery.

## Tech stack

- **Python 3.12, stdlib only** for `scripts/lib/`. No third-party runtime deps.
- Package manager is **`uv`** (`~/.local/bin/uv`). Do **not** use pip/pip3.
- `gh` CLI present, logged in as **abetatos**. (The machine's SSH key is a
  different account, `arec97` — use `gh`/HTTPS for GitHub, not SSH.)
- `sudo` needs an interactive password — install user-level tools without it.

## Architecture

Skills live in `.claude/skills/`. The pipeline per chapter is:
**resume-act** (session bootstrap) → **plan-chapter** (decision gate) →
**write-chapter** → **expand-chapter** (always once — texture pass) →
**critique-chapter** → (**revise-chapter** | a 2nd **expand-chapter** pass)
→ **update-canon** (lock-in) → **close-act** (at act boundaries). **write-novel**
orchestrates one chapter end-to-end, then HARD STOPS for `/clear`.
`expand-chapter` runs **once unconditionally** even when the chapter is already
at length — the author wants the added dwelling/texture paragraphs; word count is
checked *after* that pass and may trigger a second expand (2-pass cap) or a trim.

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
`write-chapter` / `plan-chapter` stay in the main thread (they need conversation
state or are interactive); `update-canon` keeps only its interactive tail there
(see above) and offloads its steps 1-4 to `canon-scribe`.

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
  cleanup pass expand-chapter's markers promise).
- `scripts/lint_prose.py` — counts the named prose tics (explanatory simile,
  "no X, sino Y", "como si", repetition-as-emphasis, anaphora, adverb/gerund
  density) per chapter AND cross-chapter repetition (signature-word reuse,
  echoing openings, reserved lexicon spent off-plan) into
  `notes/_prose-report-chNN.md`, so the critic judges counts instead of tallying
  by eye. Caps + reserved lexicon per book in `notes/prose-lint.toml`
  (stdlib `tomllib`). Run by `critique-chapter` (step 8b).
- `scripts/verify_critique_quotes.py` — checks every quoted line in a chapter
  critique appears in the chapter (or a source it cites) so a hallucinated
  finding can't be counted into the verdict. Run by `critique-chapter` before
  `compute_verdict.py`.
- `.claude/hooks/protect-never-compress.sh` — PreToolUse hook that blocks direct
  Edit/Write of `plan/seeds.md` / `plan/shadow.md` (mutate via `mark_seed.py` /
  `mark_truth.py`).
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
