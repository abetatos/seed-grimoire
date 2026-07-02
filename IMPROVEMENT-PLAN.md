# Improvement Plan — The Seed Grimoire

> Implementation plan derived from a full architecture review (2026-07-01).
> Written to be executed by a coding agent with no prior context on this repo.
> Read `CLAUDE.md` first; it is authoritative on conventions. This plan adds
> tasks; it does not override CLAUDE.md.

## Guiding idea

The architecture is sound: state on disk, deterministic context bundles,
critique/lock-in in isolated subagents, surgical mutation of never-compress
files. Its weak point is that **many safety-critical invariants are enforced
by prose in SKILL.md files** (the model must read and obey them) instead of
by scripts (exit codes). The review found the repo already paying for this:
incident-driven "guard paragraphs" accreting in skills, policy duplicated in
3+ files, silent regex failures in `scripts/lib/`, and zero tests over the
code that mutates the book's only non-regenerable source of truth.

**Every task below moves an invariant from prose to code, or removes a
duplication, or adds a deterministic check.** When in doubt, prefer the
smallest change that makes a failure loud.

## Global constraints (apply to every task)

- **Python 3.12, stdlib only.** No third-party runtime deps. Package manager
  is `uv` (`~/.local/bin/uv`); never pip.
- **Never round-trip `plan/seeds.md` or `plan/shadow.md`** through
  load→save. Only surgical text mutation (`seeds.py::update_status_in_text`,
  `append_realized_in_text`, and the shadows equivalents).
- **Do not modify the live book state** under `output/el-vitral/book-01/`
  except where a task explicitly says so. It is a real book in progress and
  doubles as the test fixture — treat it as read-only input.
- Line numbers cited below are anchors from the review date; **re-locate by
  function/section name** before editing, they will have drifted.
- One task per commit. Run the full test suite (`uv run python -m unittest
  discover tests`) before every commit once T3 lands.
- SKILL.md files are English; keep them that way. When editing a SKILL.md,
  make the diff minimal — these files are prompts, and every extra line is
  context cost on every invocation.

---

## Phase 0 — Broken things (fix first, trivial)

### T0. Fix machine-specific paths in `.claude/settings.json`

**Problem.** `.claude/settings.json` carries absolute paths from a previous
machine and a previous project name (`/home/betato/Projects/book-writer/...`).
Consequences on the current machine (macOS, repo at a different path):

- The **Stop hook is dead**: `"command": "bash /home/betato/Projects/book-writer/.claude/hooks/clear-reminder.sh"`
  points nowhere, so the `.clear-pending` sentinel written by `update-canon`
  and `critique-plan` never produces the reminder it exists for.
- Several `permissions.allow` entries and `additionalDirectories` reference
  the stale path and are inert noise.

**Fix.**
1. Rewrite the Stop hook command as
   `bash "$CLAUDE_PROJECT_DIR/.claude/hooks/clear-reminder.sh"`.
2. Delete every `allow` entry and `additionalDirectories` entry containing
   `/home/betato/` (they are one-off Bash approvals from old sessions, not
   policy).
3. Verify `.claude/hooks/clear-reminder.sh` exists, is executable, and reads
   the sentinel path relative to the project dir (not hardcoded).

**Accept when:** manually creating `output/el-vitral/book-01/notes/.clear-pending`
and triggering a Stop produces the reminder; `settings.json` contains no
absolute path from any machine.

---

## Phase 1 — Deterministic guardrails (P0)

### T1. `lint_book.py` — deterministic auditor of book state

**Problem.** About a dozen invariants are currently checked only by the model
reading prose instructions (or not checked at all): seed schedule sanity,
seed↔shadow referential integrity, lock-in completeness. A silent breach
corrupts continuity chapters later.

**Build.** `scripts/lib/lint.py` (logic) + `scripts/lint_book.py` (CLI):

```
uv run python scripts/lint_book.py --series-slug <slug> --book-number <N> [--strict]
```

Checks, each producing findings tagged `ERROR` or `WARN`:

1. **seeds.md integrity** — `load_seeds()` parses; every `Status:` is in
   `VALID_STATUSES`; the file contains no token in `Plant in / Echo in /
   Payoff in` that was silently dropped by parsing (see T4 — lint must
   surface exactly what the parser skipped). Round-trip guard: mutating a
   seed's status to its current value via `update_status_in_text` must return
   the input byte-for-byte.
2. **Schedule sanity** — for every seed: `plant_in` present unless status is
   `planned`-with-no-schedule; `payoff_in > plant_in`; every scheduled
   chapter within `[1, num_chapters]` from `setup.md`; the known **bare-digit
   gotcha**: a `Payoff in:` whose raw text contains extra prose plus a bare
   number (e.g. `libro 2, cap 3`) parses as a same-book chapter — flag any
   parsed payoff chapter whose raw field also contains non-numeric text.
3. **Cross-refs** — every `Revealed-by:` in `plan/shadow.md` names an
   existing seed id; every `Obligatory: §14 <name>` in seeds matches a §14
   row in `output/<series>/grimoire.md` if that file exists.
4. **Lock-in completeness** — for every chapter file `chapters/NN.md`, if
   chapter N < highest written chapter, then `summaries/ch-NN.md` exists and
   contains no `TODO`. `WARN` if `notes/decisions-chNN.md` is missing for a
   written chapter.
5. **Status/prose coherence (cheap version)** — a seed whose status is
   `planted`/`echoed-*` must have ≥1 `Realized:` line; a `paid_off` seed
   whose schedule included echo chapters that never got a Realized line →
   `WARN`.
6. **Stale seam inputs** — `summaries/book-summary.md` exists and its
   `## What just happened` mentions the highest locked chapter number →
   `WARN` if not (detects skipped `update-canon` step 5 / skipped
   `close-act`).

Exit code: 0 = clean or WARN-only; 1 = any ERROR; with `--strict`, 1 on WARN
too. Output: one finding per line, `LEVEL <file>: <message>`, then a one-line
summary. No color, no prose.

**Wire it in** (SKILL.md edits, one or two lines each — do not narrate the
checks inside the skills):

- `resume-act`: run lint right after the state report; surface findings.
- `update-canon` step 1 (i.e. inside the `canon-scribe` path): run lint
  before writing anything; any ERROR becomes a FLAG.
- `critique-chapter` / `critique-plan` step 1: run lint; ERRORs feed the
  MUST list mechanically.

**Accept when:** `lint_book.py` runs clean (or with explainable WARNs) on
`el-vitral/book-01`; unit tests cover each check with synthetic fixtures
(see T3); the three SKILL.md files invoke it.

### T2. PreToolUse hook protecting never-compress files

**Problem.** "Never edit `seeds.md`/`shadow.md` directly" is a prose rule in
CLAUDE.md and two agent definitions. One slip destroys hand-written content
that no script regenerates.

**Build.** `.claude/hooks/protect-never-compress.sh` registered as a
`PreToolUse` hook for `Edit|Write` in `.claude/settings.json`. The hook reads
the tool input JSON from stdin, extracts `file_path`, and **denies** (exit
code 2 with a message on stderr) when the path ends in `plan/seeds.md` or
`plan/shadow.md`. The message must say: "Never-compress file — mutate via
mark_seed.py / mark_truth.py (or edit manually outside the agent)."

Notes:
- Use `$CLAUDE_PROJECT_DIR`-relative logic; no absolute paths (see T0).
- This intentionally does NOT block `Bash` (sed etc.) — the goal is to catch
  the main path (Edit/Write), not to be a security boundary.
- `mark_seed.py`/`mark_truth.py` write via Python open(), not via the Edit
  tool, so they are unaffected.
- The author must still be able to edit these files deliberately: the deny
  message should tell the model to ask the user to make the edit themselves
  or to run a script.

**Accept when:** an Edit attempt on `plan/seeds.md` from a session is denied
with the message; `mark_seed.py` still works; hook has a unit-style smoke
test (invoke the script with a crafted JSON payload, assert exit code).

### T3. Test suite for `scripts/lib/`

**Problem.** Zero tests over the code that mutates the book's source of
truth. The review found real, already-bitten bugs (T4) that a 20-line test
would have caught.

**Build.** `tests/` at repo root, stdlib `unittest`, run via
`uv run python -m unittest discover tests`. Fixtures as small inline strings
or files under `tests/fixtures/` — do NOT point tests at `output/el-vitral`
except one read-only smoke test that runs `load_seeds` + `lint` over it.

Minimum coverage (name the files like this):

- `tests/test_seeds.py`
  - `update_status_in_text` / `append_realized_in_text`: byte-for-byte
    preservation of everything outside the target seed; creates `Realized:`
    block when absent; appends in order; unknown seed id → error.
  - `_parse_chapter_list` edge cases: `"12, 18"`, `"ch 12"`, `"12,"`
    (trailing comma), `"12a"`, `"libro 2, 3"` (the bare-digit gotcha),
    en-dash separators. Lock in the T4 behavior (loud, not silent).
  - `envelope_for_chapter` picks plant/echo/payoff correctly.
- `tests/test_shadows.py` — mirror of the above for truths:
  `update_truth_status_in_text`, `append_surfaced_in_text`, reveal-cap
  refusal, `_truth_chapter_list` edge cases.
- `tests/test_summaries.py`
  - `extract_last_scene`: explicit break `* * *`; break `---` (three
    hyphens — MUST pass after T5); no break → ~900-word paragraph-snapped
    tail; EXPAND banners stripped; short-tail-after-break (<150 words)
    fallback.
  - `plan_context`: window arithmetic at chapters 1, 7, 8 (act boundary).
- `tests/test_context.py`
  - Bundle section order is stable per phase; `plan` drops seam+style+craft;
    `critique` drops full-text chapters but keeps style+craft.
  - `_scope_characters_md`: principal kept whole; secondary scoped out and
    listed; names in `«»` quotes and 2-char names (after T5).
- `tests/test_lint.py` — one fixture book per lint check (T1), asserting the
  exact finding fires.
- `tests/test_wordcount.py` — counts exclude EXPAND marker lines (after T9).

**Accept when:** suite passes; CI-style one-liner documented in CLAUDE.md
(`## Tech stack` section, one line: how to run tests).

### T4. Loud parsing: stop silently dropping schedule tokens

**Problem.** `seeds.py::_parse_chapter_list` (line ~140) and
`shadows.py::_truth_chapter_list` (line ~199) do `tok.strip("ch ")` +
`tok.isdigit()` and **silently skip** anything malformed. This already bit
the project once (the bare-digit payoff gotcha recorded in the author's
notes). A dropped echo chapter means a seed silently never enters any
envelope.

**Fix.** In the shared parser (T7 merges the two copies — do T7 first or
together):

- Accept: bare ints, `ch 12`, `cap 12`, `capítulo 12` (case-insensitive),
  comma/space separated.
- Explicitly recognize and **ignore with intent**: empty tokens from trailing
  commas, and deferral annotations matching `(libro|book)\s*\d+` — these mean
  "not this book" and must NOT contribute a chapter number, even if followed
  by digits. (This is the correct resolution of the bare-digit gotcha:
  `Payoff in: libro 2` must parse as *no payoff this book*.)
- Anything else → collect into a `parse_warnings` list on the returned
  object. `load_seeds()` keeps working (never crash context assembly mid-
  write), but `lint_book.py` (T1 check 1) turns any warning into an ERROR.
- `tok.strip("ch ")` is a char-set strip and mangles asymmetric input;
  replace with a regex.

**Accept when:** T3's edge-case tests pass; lint on a fixture with
`Payoff in: 12a` reports an ERROR naming the seed and the raw token; a seed
with `Payoff in: libro 2` yields `payoff_in = None` and no warning.

---

## Phase 2 — Context economy & single-source policies (P1)

### T5. Regex robustness fixes in `lib/`

Small, mechanical; each needs a test locked in first (T3):

1. `summaries.py::_SCENE_BREAK_RE` (~line 176): add three-hyphen breaks
   `^[ \t]*-{3,}[ \t]*$` and en-dash triplets `– – –`. Keep the current
   forms. (A chapter never starts with `---` frontmatter, so no conflict.)
2. `context.py::_scope_characters_md` (~line 196): name detection currently
   requires 3+ chars and misses `«»`-quoted aliases (~line 201, only
   ASCII double quotes). Widen to 2+ chars and add `«([^»]*)»` alongside
   `"..."`. The scoping bias is INCLUDE, so false positives are safe;
   false negatives (a secondary scoped out while on stage) are not.
3. `context.py` beat-sheet extraction (~line 102) and
   `shadows.py` chapter headers (~line 35): tolerate inline bold in
   headers (`## **Capítulo 3**`) by allowing optional `\*{0,2}` around the
   keyword+number. Do not attempt Roman numerals; not used in this repo.
4. `context.py` empty-file guards (~lines 328, 489): the "is there content"
   checks compare against three different magic strings. Extract one helper
   `_has_content(text: str, placeholders: tuple[str,...]) -> bool` that also
   treats whitespace-only files as empty.

**Accept when:** the corresponding T3 tests flip from red to green and the
full suite stays green.

### T6. `--phase expand` context bundle

**Problem.** `expand-chapter` runs in the main thread on every chapter (the
most expensive session) and its step 1 rebuilds and reads the **full write
bundle** (~15k words and growing) plus the chapter (~8k). For a texture pass
it needs a fraction of that.

**Fix.** In `context.py::build_context`, add phase `expand`:

- **Keep:** precedence header, setup (filtered), decisions (book + chapter),
  canon (with character scoping as in write), seed envelope (so insertions
  don't break seed lines), this chapter's beat sheet (to know which scenes
  are hinges), style guide, voice notes, craft checklist **reduced to the
  dwelling section only**.
- **Drop:** series context, plan/outline neighbors, arcs, shadow slice,
  story-so-far summaries, continuity seam. (Expansion never adds plot or
  reveals; it does not need hidden truth or history. The chapter itself is
  the context.)

Update `expand-chapter/SKILL.md` step 1 to pass `--phase expand`. Measure
before/after bundle word count on `el-vitral` ch 3 and record the number in
the commit message.

**Accept when:** `--phase expand` bundle for el-vitral ch 3 is ≤ ~50% of the
write bundle; T3 context test asserts the expand section set; expand SKILL.md
uses it.

### T7. Merge duplicated parsing into `lib/parsing.py`

**Problem.** `seeds.py::_parse_chapter_list` ≡ `shadows.py::_truth_chapter_list`
and `seeds.py::_parse_realized` ≈ `shadows.py::_parse_surfaced`. Bug fixes
(T4, T5) would otherwise need double edits forever.

**Fix.** New `scripts/lib/parsing.py` with `parse_chapter_list(raw) ->
(list[int], list[str])` (values, warnings) and
`parse_touch_log(block) -> list[str]` (the Realized/Surfaced bullet parser —
accept `-`, `*`, `+` bullets; preserve the line text). Both modules import
from it; behavior governed by T4's spec. Delete the private copies.

**Accept when:** no duplicated implementations remain (grep); suite green.

### T8. Single source per pipeline policy (SKILL.md dedup)

**Problem.** Three policies are fully narrated in multiple SKILL.md files,
and the git history shows each policy change costs multi-file propagation
commits, with drift already visible:

| Policy | Currently narrated in | Canonical owner after this task |
|---|---|---|
| Expand: always 1 texture pass, 2-pass cap, trim rules, marker numbering | `write-novel` 2c, `write-chapter` §Hard rules + step 4, `expand-chapter` 4b/5 | `expand-chapter` |
| Critique loop: 1 revise→re-critique cycle, adjudication, when to re-run | `write-novel` 2d, `critique-chapter` step 4 | `critique-chapter` |
| `/clear` standard + sentinel + exact signal line | `write-novel` 2f, `update-canon` 6, `resume-act`, CLAUDE.md | CLAUDE.md (the rule) + `update-canon` (the signal text) |

**Fix.** In each non-owner file, replace the narration with ≤2 lines: the
trigger ("after write-chapter, always invoke expand-chapter once — policy
and marker rules live in expand-chapter") and the pointer. Keep in the
orchestrator only what the orchestrator itself must *decide* (when to call
what, and on which verdict to stop). Do not change any policy's substance in
this task — pure deduplication, verified by reading the diffs side by side.

Also fix two known drift spots while there:
- `critique-grimoire` lacks the "audit FRESH / overwrite, don't merge" file
  rule that `critique-plan` has (step 3, ~lines 44-49). Add the same two
  lines.
- CLAUDE.md's Architecture section does not mention that `search-corpus`
  dispatches to the built-in `Explore` subagent. One clause fixes it (it
  already mentions it in passing — verify and align).

**Accept when:** each policy's full text exists in exactly one file; a grep
for "EXPAND 1" / "one revise" / "STANDARD: run /clear" shows narration only
at the owners; no behavioral change intended or made.

---

## Phase 3 — Harden the critique loop (P2)

### T9. Critic never sees EXPAND markers + wordcount ignores them

**Problem.** The `▼▼▼ INICIO EXPAND …` scaffolding forces every downstream
consumer to be taught to ignore it — `critique-chapter` carries a 12-line
guard paragraph (~lines 47-58) that exists because a false MUST about
"scaffolding left in the body" once bounced a clean chapter. Solve it
structurally: don't show markers to the critic at all.

**Fix.**
1. Move `_EXPAND_MARKER_RE` from `summaries.py` to `lib/parsing.py` (T7) as
   `strip_expand_markers(text) -> str`; `summaries.py` imports it.
2. `build_context.py --phase critique` additionally writes
   `notes/_chapter-clean-NN.md` = the chapter with marker lines stripped
   (prose between markers kept).
3. `critique-chapter/SKILL.md`: step 1 reads `_chapter-clean-NN.md` instead
   of `chapters/MM.md`; **delete the guard paragraph** (that's the payoff).
   Keep one line: "You are reading a marker-stripped copy; the original is
   chapters/MM.md."
4. `wordcount.py`: strip markers before counting (markers currently inflate
   counts by ~10 words per zone).

**Accept when:** critique bundle flow produces the clean file; guard
paragraph gone; wordcount test (T3) green.

### T10. `strip_expand_markers.py` — make the promised cleanup pass exist

**Problem.** `expand-chapter` 4b calls the markers "a temporary repo
standard… stripped in a later cleanup pass", but no such pass exists in any
skill or script. It's vaporware that the whole convention leans on.

**Fix.** `scripts/strip_expand_markers.py --series-slug S --book-number N
[--chapter M | --all] [--dry-run]`: removes marker lines in place (prose
kept), reports zones removed per chapter. Wire a one-line mention into
`compile-book/SKILL.md` (offer it as an optional pre-compile step, default
OFF — the author currently *wants* markers on the Kindle) and into
`close-act/SKILL.md` as an author-confirmed option at act close.

**Accept when:** dry-run on el-vitral chapters reports the expected zone
counts (ch1: has markers; verify against `grep -c EXPAND`); running on a
fixture chapter leaves prose byte-identical except marker lines.

### T11. Verdicts computed, not judged

**Problem.** The critic both writes findings AND applies threshold rules
("PASS = zero MUST ≤3 SHOULD") by judgment, at the exact step that triggers
actions (revise loop, lock-in, HARD STOP). Threshold discretion is where
severity inflation/deflation leaks in.

**Fix.** `scripts/compute_verdict.py --critique-file <path> --target
chapter|plan|grimoire`:

- Parses the critique file's `## MUST fix` / `## SHOULD fix` / `## CONSIDER`
  sections; counts bullets.
- Detects REJECT-tier structural findings via a machine-readable tag the
  skills already almost have: require finding bullets to start with
  `- **[<type>]**`, and define the REJECT-tier type vocabulary per target
  (chapter: `missing-beat`, `canon-contradiction`, `unseeded-payoff`,
  `contrived-trigger`, `wordcount-under-80`; plan and grimoire: take the
  REJECT lists verbatim from their SKILL.md verdict blocks).
- Applies the thresholds (chapter: PASS = 0 MUST ∧ ≤3 SHOULD; plan/grimoire:
  PASS = 0 MUST ∧ ≤6 SHOULD; REJECT only on a REJECT-tier tag; else REVISE).
- Prints `VERDICT: X (MUST=a SHOULD=b CONSIDER=c)` and exits 0.

SKILL.md changes (all three critique skills + `book-critic.md`): the critic
writes the findings file **without** a verdict line, runs the script, then
writes the returned verdict into the file's `**Verdict:**` field and returns
it. Add the tag vocabulary to each skill's finding-format spec (they already
mandate `**[issue type]**` — this just fixes the vocabulary).

**Accept when:** running the script over the three existing critique files in
`el-vitral/book-01/notes/` reproduces their recorded verdicts (or the
mismatch is explained in the commit message); unit tests cover threshold
boundaries and tag detection.

### T12. Chapter hash ties critique → lock-in

**Problem.** `update-canon` 0a says "confirm nothing changed since the
critique" — impossible to confirm from a fresh session; it's memory-based.

**Fix.**
1. `book-critic` (and the standalone critique path) records at the top of
   `notes/critique-chNN.md`: `**Chapter-hash:** <sha256 of chapters/NN.md>`.
   Provide it mechanically: `prepare`-style helper or one `shasum -a 256`
   Bash line specified in the SKILL.md.
2. `update-canon/scripts/prepare_summary.py`: read the hash line from the
   critique file (if present), hash the current chapter, and on mismatch
   print a loud warning and exit non-zero. The SKILL.md's 0a step becomes:
   "prepare_summary.py verifies the critique hash; on mismatch, re-run the
   consistency pass" — deterministic, no memory required.

**Accept when:** editing one character of a fixture chapter after a mock
critique makes `prepare_summary.py` refuse; matching hash proceeds.

### T13. Cap the forge-grimoire loop

**Problem.** `forge-grimoire` step 5 says "repeat until PASS" with no
iteration bound — an author who keeps rejecting proposals loops forever,
each round spawning a fresh `book-critic`.

**Fix.** SKILL.md edit: max **3** critique iterations per invocation; on the
3rd non-PASS, stop, print the remaining findings and tell the author to
resolve them manually or re-invoke. Two sentences, in the step-5 block.

---

## Phase 4 — Minor hardening (P3, do opportunistically)

### T14. `write-chapter` overwrite guard
Before writing `chapters/NN.md`, if the file exists with >500 words AND has
uncommitted changes (`git status --porcelain -- <file>` non-empty) → STOP and
ask the author (regeneration would destroy unversioned prose). SKILL.md edit
(step 3 preamble) + optionally a `--force`-style note. Keep it to 3 lines.

### T15. `[FIJO]` ↔ `decisions.md` cross-check (lint extension)
Optional lint check (behind `--cross-book`): for each `[FIJO]` line in
`output/<series>/grimoire.md` that names an entity also named in the book's
`notes/decisions.md`, flag pairs whose text conflicts (heuristic: same
entity name, both lines mention chapters/timing; report for human review,
`WARN` only). Low precision is fine — today *nothing* looks at both files.

### T16. Document verdict thresholds rationale
One paragraph in `references/` (or a comment block in `compute_verdict.py`):
why chapter PASS allows ≤3 SHOULD but plan/grimoire allow ≤6 (scope size).
Prevents a future "unify the thresholds" regression.

### T18. Word target: structural budget in the prompt, number only in the check

**Problem.** `write-chapter/SKILL.md` gives the writer a numeric goal ("aim
for ≥8000 words"). An LLM cannot count words while generating; a numeric
anchor doesn't produce the number, it produces a *bias toward padding* —
subordinate-clause filler, repeated emotional beats — exactly what
`style.md` bans. Meanwhile the repo already has the correct mechanism for
length: a **content budget** (N plot beats + 2-4 dwellings of 300-500 words
+ subtext), which an LLM *can* execute, plus a deterministic post-hoc check
(`check_wordcount.py`) that drives expand/trim.

**Fix.**
1. `write-chapter/SKILL.md`: remove the numeric goal from the writer-facing
   instructions (Hard rules bullet ~line 22-29 and step 3's word-target
   paragraph ~line 152-158). Replace with the structural budget: "hit every
   beat in the beat sheet; budget 2-4 texture dwellings of 300-500 words;
   length emerges from the budget — the caller checks the number, you
   don't."
2. Optionally (nice-to-have): `build_context.py` emits a one-line
   `Content budget` in the beat-sheet section — number of beats found +
   dwelling budget — so the budget is per-chapter concrete, not generic.
3. `check_wordcount.py` stays the **sole numeric authority**, unchanged: it
   already triggers the expand/trim decisions in `write-novel` 2c.

**Accept when:** no numeric word goal remains in writer-facing SKILL.md
prose (grep for `8000`/`8 000` in `.claude/skills/write-chapter/`); the
expand/trim flow in write-novel still keys off `check_wordcount.py` exit
codes; chapter length on the next written chapter stays in the expected
band (spot-check, not a hard gate).

### T19. Word-count severity: aesthetic shortfall is not a contract break

**Problem.** `critique-chapter` treats <80% of the word floor as MUST-fix /
REJECT-tier. That makes an aesthetic choice ("a lean chapter is fine",
stated three times across the skills) a contract violation, and pressures
the pipeline toward padding — the opposite of the repo's own style rules.

**Fix.** In `critique-chapter/SKILL.md` (checks + verdict block) and in
`compute_verdict.py`'s tag vocabulary (T11 — do together or after):

- <80% of floor → `SHOULD fix` (was MUST/REJECT-tier).
- <60% of floor → stays REJECT-tier (`wordcount-under-60` replaces
  `wordcount-under-80` in the tag vocabulary): dramatically short means the
  outline under-planned texture beats, which IS structural.
- `check_wordcount.py` thresholds are untouched (it drives expand, not
  verdicts). If its `too_short` boundary is the 80% line, add the 60% line
  to its output so the critic doesn't compute it by hand.

**Accept when:** T11's script and the SKILL.md verdict table agree; a
fixture critique with a 75%-length finding computes REVISE (via SHOULD),
not REJECT.

### T17. Deferred (do NOT do now — recorded so the implementer doesn't)
The TODO.md levers stay deferred by design: canon scoping by roster and
setup filtering activate at act 2+ with real data; trans-book seeds wait for
book 2. Do not implement them as part of this plan.

---

## Phase 5 — Optional architecture step (decide AFTER the base plan works)

### T20. Scene-wise drafting in a writer subagent ("chapter-smith")

Not part of the base plan — recorded so the direction is on paper. Decide
with the author once Phases 0-4 are stable.

**Motivation (two problems, one move):**
- **Quality:** a chapter is ~14-16k output tokens in Spanish. Single-pass
  long generations degrade — strong opening, sagging middle, rushed tail.
  Drafting **scene by scene against the beat sheet** keeps every scene in
  the model's high-quality zone, and length emerges from summed scenes
  instead of a numeric target (completes T18).
- **Tokens:** `write-chapter` + `expand-chapter` run in the main thread and
  carry bundle (~15k words) + chapter (~8k) + expansions. `plan-chapter`
  already persists every decision to disk (`decisions-chNN.md`) precisely so
  writing is regenerable — so the writer no longer *needs* conversation
  state. A `chapter-smith` subagent (constructive, like `canon-scribe`:
  Read/Write/Edit, **no Agent tool**) could draft and expand in isolation
  and return only a report + FLAGS, leaving the main session with
  orchestration and decisions only.

**Sketch:** new `.claude/agents/chapter-smith.md`; `write-chapter` gains a
step-0 self-dispatch like `critique-chapter`/`update-canon` have; the
subagent drafts scene-by-scene from the beat sheet, runs the expand texture
pass internally (or `expand-chapter` keeps its own dispatch), returns
word count + seeds touched + invented-fact FLAGS. Interactive halts (step 2b
consistency findings) return as FLAGS instead of AskUserQuestion, mirroring
`canon-scribe`.

**Risks to weigh:** the author loses mid-draft visibility; FLAGS arrive
after the whole draft instead of before it; voice drift between scenes needs
the seam-within-chapter handled (each scene must see the previous scenes'
tail). Prototype on one chapter and compare against the current flow before
adopting.

---

## Suggested order & dependencies

```
T0 (independent, 15 min)
T3 (test harness first — lock current behavior)
T7 (shared parsing module)  ──►  T4 (loud parsing)  ──►  T1 (lint uses parse warnings)
T5 (regex fixes, tests from T3)
T2 (hook; independent)
T6 (expand phase; independent)
T9 (needs T7 for strip_expand_markers)  ──►  T10
T11, T12, T13 (independent of each other)
T18 (any time)  ──►  T19 (with or after T11 — shares the tag vocabulary)
T8 (SKILL.md dedup — LAST among Phase 2/3, so pointers reference final text)
T14–T16 (any time)
T20 (optional — only after the author signs off on Phases 0-4)
```

## Definition of done (whole plan)

- `uv run python -m unittest discover tests` green; suite covers every lib
  module touched.
- `uv run python scripts/lint_book.py --series-slug el-vitral --book-number 1`
  exits 0 (or all WARNs individually justified in the final report).
- `git diff` over `output/el-vitral/book-01/` is empty (fixture untouched),
  except files a task explicitly modifies (none do).
- Each policy narration exists in exactly one SKILL.md.
- The critique-chapter guard paragraph about EXPAND markers is gone, because
  the critic reads a clean copy.
- Stop hook fires on this machine.
