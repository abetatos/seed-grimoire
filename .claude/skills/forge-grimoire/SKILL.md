---
name: forge-grimoire
description: Constructive counterpart of `critique-grimoire` — it WRITES the world grimoire. Bootstraps `output/<series>/grimoire.md` from the template if missing, then walks it section by section, detects what is missing or under-scoped (including too-few loaded guns / master mysteries for a trilogy), and fills each gap with the author via `AskUserQuestion` choices. Closes the loop by auto-running `critique-grimoire` and re-filling until PASS. Use when the user says "forja/crea/mejora/completa el grimorio", "el grimorio está flojo", or "faltan siembras/misterios para la trilogía".
---

# forge-grimoire

You are running the **forge-grimoire** skill. This is the **constructive**
counterpart of `critique-grimoire`. Where `critique-grimoire` audits and
deliberately does NOT touch the file, this skill **writes the grimoire** —
section by section, one author-confirmed choice at a time — until it is
complete enough to pass the audit.

The grimoire (`output/<series>/grimoire.md`) is the source of truth for the
whole series' worldbuilding. Everything downstream (`setup.md`, `canon/*`,
`plan/*`, chapters) quotes from it. A thin grimoire — the common failure being
**too few loaded guns / master mysteries for a trilogy** (a seed bank sized for
a standalone) — makes every per-book plan inherit the gap. This skill exists to
fill that gap *before* `book-setup` and `plan-book` run.

## When to invoke

- The author wants to start a grimoire from scratch, or has a half-built one
  (sections marked `[POR CONSTRUIR]` / `[EN CURSO]` / `[PARCIAL]`).
- The author says "forja / crea / mejora / completa el grimorio", "el grimorio
  está flojo", "faltan siembras/misterios para la trilogía".
- Before `critique-grimoire` PASSes and before `book-setup` for Book I.

## Hard rules

- **Never overwrite a `[FIJO]` line without explicit author confirmation.**
  Read the grimoire's own tag legend first (`[FIJO]` = closed, `[PROPUESTA]` =
  coherent suggestion, `[POR CONSTRUIR]` = not designed yet, `[Gating: sí]` =
  blocks writing). New content you propose enters as **`[PROPUESTA]`**; it
  becomes `[FIJO]` only when the author closes it. This is the same guard as
  `plan-book`'s locked decisions: a forge pass must NOT silently rewrite an
  authored choice. If a proposal would contradict a `[FIJO]`, STOP and surface
  the conflict.
- **Propose, don't dump.** Every fill is decided WITH the author via
  `AskUserQuestion`, each question carrying 2-4 concrete options grounded in
  what the grimoire already says, plus a recommendation. The author
  accepts or rewrites. Never invent worldbuilding and write it unasked.
- **Surgical edits, never a full-file rewrite.** Use `Edit` on the target
  section. **Tables (§2, §7, §14, §14b) grow by APPENDING rows** — never
  regenerate the whole table (same discipline as `seeds.md`): a round-trip
  reflow drops content.
- **In-world content in Spanish** (names, factions, magic terms); tags and
  agent-facing metadata stay in their current form.
- **One section per step.** Propose → confirm → write → next. Do not batch a
  dozen questions; the author wants to build it *por pasos*.
- **This skill does not audit.** It builds. The adversarial read is
  `critique-grimoire`, which it calls at the end.

## Steps

### 0. Locate or bootstrap the grimoire

Resolve the series slug (ask if not given). If
`output/<series>/grimoire.md` does **not** exist, bootstrap it by copying the
template and tell the author:

```bash
cp references/grimoire-template.md output/<series>/grimoire.md
```

If it exists, proceed — this is the expansion path.

### 1. Scan for gaps (deterministic worklist)

```bash
python3 .claude/skills/forge-grimoire/scripts/scan_grimoire.py \
    --series-slug <slug> \
    --output output/<slug>/notes/_forge-worklist.md
```

This is the **constructive** complement of `audit_grimoire.py` (it imports its
parsing helpers). It returns a dependency-ordered worklist:
- **MUST** — missing/empty sections, empty §14/§14b tables, unresolved gating.
- **SHOULD** — sections still carrying `[POR CONSTRUIR]`/`[EN CURSO]`/`[PARCIAL]`/
  `___` markers; §14/§14b **under-scoped for a trilogy** (row count below
  `LOADED_GUN_TARGET=8` / `MYSTERY_TARGET=10`); loaded guns missing a sow/payoff
  book or never appearing in Book I.

Read `_forge-worklist.md`. It defines the order of work.

### 2. Read the grimoire and the craft references

Read `output/<series>/grimoire.md` in full so every proposal is coherent with
the `[FIJO]` spine. Read these for what "good" looks like (do not re-narrate
them at the author — pull from them to shape options):

- `references/magic-design-checklist.md`
- `references/seed-craft.md`
- `references/fantasy-beats.md`
- `references/hard-magic-laws.md`

### 3. Walk the worklist, section by section

Fill in this dependency order (earlier sections constrain later ones):

> idea (§1) → dos capas (§2) → magia/leyes/forma del sistema (§3–§6) →
> castas (§7) → subtramas (§8) → personajes (§9) → historia (§10) →
> geografía (§11) → estructura de la trilogía (§12) → reloj (§13) →
> **siembras §14** → **misterios §14b** → decisiones abiertas (§15/§16) →
> tono (transversal).

For each gap:

1. **Build 2-4 concrete options**, each a real proposal anchored in the
   existing `[FIJO]` material (not abstract prompts), each with a one-line
   rationale, and mark your recommendation. Surface them with
   `AskUserQuestion`.
2. **Write the author's choice** into the correct section with `Edit`
   (surgical). Tag it `[PROPUESTA]` unless the author closes it as `[FIJO]`.
3. Move to the next gap. Keep it conversational — one section at a time.

The template (`references/grimoire-template.md`) shows the expected shape and
the minimum bar of each section (e.g. magic needs source + mechanic + ≥2 costs +
≥3 hard limits + thematic question; ≥2 principals with full want/need/lie/wound;
antagonist with a *thesis*, not stock evil; ≥5 named places; ≥3 historical
events; each book block a distinct motor + an active-decision climax verb).

### 4. Scale the trilogy — §14 loaded guns and §14b master mysteries

This is the lever for the author's pain ("creé pocas seeds para la trilogía").
When the scan flags §14 or §14b as under-scoped, drive the count up to the
target by **appending rows**, one at a time, each confirmed via
`AskUserQuestion`:

- **§14 loaded guns (≥ ~8-10):** each worldbuilding element that must appear on
  the page (a ritual, a pseudo-system, an implicit physical law). Each row needs
  a **Siembra-en** and a **Paga-en** book, ≥1 payoff per book across the
  trilogy, and — by the grimoire's own rule — appears at least once in Book I.
  Propose candidates derived from §3-§13 that currently have no payoff plan.
- **§14b master mysteries (≥ ~10-15):** the truths hidden from the *reader*.
  Cover, at minimum, one per category and propose candidates for each from the
  grimoire's own material:
  - the protagonist's hidden nature,
  - **each** antagonist's real agenda,
  - **each** institution's real function,
  - **each** major subplot's buried truth,
  - the secret history.
  Each row needs a **real truth**, an **Introducido-en** book and a
  **Confirmado-en** book. (Note: §14b must be a **table** — prose bullets are
  not counted by the audit and `critique-plan` cannot check shadow coverage
  against them. If the grimoire only has bullets, migrate them into the table.)

### 5. Close the loop — auto-audit until PASS

When the worklist is exhausted, run the adversarial read:

> Invoke `critique-grimoire` for this series. It self-dispatches the analysis to
> the fresh `book-critic` subagent (clean context, no leak), writes
> `notes/critique-grimoire.md`, and returns the verdict.

Read `notes/critique-grimoire.md`:
- **PASS** → go to step 6.
- **REVISE / REJECT** → convert each `MUST fix` / `SHOULD fix` finding into a new
  worklist item and **return to step 3** on exactly those gaps (re-run
  `scan_grimoire.py` to refresh `_forge-worklist.md`). Do not loop silently —
  tell the author which findings you are re-opening.

**Loop cap: at most 3 critique iterations per invocation.** If the grimoire has
not reached PASS after the 3rd audit, **stop** — print the remaining findings
and hand back to the author to resolve them by hand or re-invoke `forge-grimoire`
fresh. An un-converging loop (author keeps rejecting proposals) must not spawn
book-critic indefinitely.

### 6. Report

Print:
- Which sections were filled this session (and whether each landed as
  `[PROPUESTA]` or `[FIJO]`).
- Final §14 / §14b counts vs. target.
- The last audit verdict.
- Next step: `book-setup` for Book I (grimoire as fixed reference).

## What this skill does NOT do

- Does not generate prose, per-book `plan/`, `canon/`, or `setup.md`.
- Does not audit — `critique-grimoire` does (this skill calls it).
- Does not invent and commit worldbuilding unasked, and does not touch `[FIJO]`
  lines without explicit confirmation.

## Files this skill writes

- `output/<series>/grimoire.md` — the grimoire itself (surgical, section by
  section).
- `output/<series>/notes/_forge-worklist.md` — the deterministic worklist
  (regenerated each loop; gitignored-style scratch).
