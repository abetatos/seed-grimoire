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

**forge-grimoire** is the **constructive** counterpart of `critique-grimoire`:
it WRITES the series grimoire section by section (bootstrapping from
`references/grimoire-template.md` if missing), proposing each fill as
author-confirmed `AskUserQuestion` choices, scaling §14 loaded guns / §14b
master mysteries up to trilogy breadth, then auto-running `critique-grimoire`
and re-filling until PASS. Both share `audit_grimoire.py`: critique audits with
it, forge's `scan_grimoire.py` imports its parsing helpers to build the
constructive worklist. forge writes `grimoire.md`; critique never does.
update-canon / write-chapter / plan-chapter stay in the main thread (they need
conversation state or are interactive).

Book state on disk under `output/<series>/book-NN/`:
`setup.md`, `style.md`, `canon/` (characters, factions, magic, world, timeline),
`plan/` (outline, shadow, seeds, arcs), `chapters/`, `summaries/`
(ch-NN, act-NN, book-summary), `notes/` (decisions, decisions-chNN, voice,
style-rules, open-questions, session-handoff).

`scripts/lib/` is the deterministic core: `context.py` (bundle assembly),
`summaries.py` (hierarchical summaries + continuity seam), `seeds.py`
(foreshadowing model), `paths.py`, `shadows.py`, `setup_doc.py`.

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
