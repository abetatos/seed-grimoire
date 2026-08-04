# WORKFLOW.md — the runbook

**"What do I run next?"** This is the operational source of truth for the
pipeline. (`CLAUDE.md` is the *architecture* — the why; this is the *runbook* —
the what-and-when.) If you are ever lost, the answer is always the same:

> **Run `resume-act`** — *The Lodestar*, the compass every session steers by. It
> reads the book's state, detects the lifecycle phase, and recommends the next
> skill as a confirm menu (leading with a banner box: phase · next step). You do
> not have to remember the two-dozen skills — you remember *one entry point* and
> follow the star.

---

## The mental model: 1 entry point, 5 phases

You never run two dozen skills. You run **`resume-act`** (The Lodestar), and
underneath sits a linear 5-phase spine plus a few utilities. The whole surface
is three tiers — see "The skills, in three tiers" at the bottom:

- **Tier 1 — the 7 you actually invoke:** `resume-act`, `forge-grimoire`,
  `book-setup`, `plan-book`, `plan-world`, `critique-plan`, `write-novel`.
- **Tier 2 — chained for you** (a Tier-1 skill runs them): the L1-L5 engine
  layers, the per-chapter loop, the two constructive critiques.
- **Tier 3 — utilities on demand:** `search-corpus`, `checkpoint`,
  `calibrate-style`, `mend-chapter`, `compile-book`, `close-act`.

| Phase | When | Skills (in order) | Produces |
|---|---|---|---|
| **① WORLD** | once per **series** | `forge-grimoire` → `critique-grimoire` ↺ PASS | `grimoire.md` |
| **② PLAN** | once per **book** | `book-setup` → `plan-book` → **`plan-world`** (L1-L5) → `critique-plan` ↺ PASS | `setup.md`, `plan/`, `canon/`, `state/` |
| **③ CHAPTER** | once per **session** | `write-novel` (chains plan-chapter → write-chapter → critique-chapter → expand/revise → update-canon) | `chapters/NN.md` |
| **④ ACT** | at act boundaries | `close-act` | act summaries, handoff |
| **⑤ SHIP** | book finished | `compile-book` | EPUB |
| *Utilities* | on demand | `resume-act` (The Lodestar), `search-corpus`, `checkpoint`, `calibrate-style`, `mend-chapter` | — |

**The critiques are mandatory gates, not optional.** `critique-grimoire`,
`critique-plan`, and `critique-chapter` each run in a fresh-context subagent
(`book-critic`) and must reach PASS before the phase advances.

---

## The canonical work plan (every book, start to finish)

```
SERIE (once):     forge-grimoire → critique-grimoire ↺ until PASS
──────────────────────────────────────────────────────────────────────
LIBRO (once):     book-setup → plan-book → plan-world (L1→L2→L3→L4→L5)
                  → critique-plan ↺ until PASS
──────────────────────────────────────────────────────────────────────
CAPÍTULO (1/sesión):  resume-act → write-novel → /clear     ← the daily loop
ACTO (boundary):      close-act
LIBRO FIN:            compile-book → update series-state → next book
```

**One chapter per session, then `/clear`.** All state is on disk; the next
session rebuilds via `resume-act`. There is no cross-chapter autopilot —
`write-novel` drives ONE chapter end-to-end then HARD STOPS for `/clear`.

---

## Phase ②: the engine layers (L0-L5), demystified

The single biggest source of "there are too many plan-* skills" is the engine
layer. It is one idea — **the spatial-temporal contract** (where everyone is at
every moment, who can speak or overhear) — built in stages so each is an author
gate. `plan-world` chains L1-L5 for you; the individual skills stay callable for
surgical re-runs.

| Layer | Skill | Fixes | Artifact |
|---|---|---|---|
| **L0** | `plan-book` | *what* happens each chapter (outline) + shadow + seeds + arcs + canon | `plan/outline.md`, … |
| **L1** | `plan-space` | *where* — the world graph (places, edges, costs) | `state/world.json` |
| **L2** | `plan-time` | *when* — the per-chapter clock; feasibility of every move | store clock |
| **L3** | `plan-cast` | *who is where* — every character's itinerary; meetings are copresent | store positions |
| **L4** | `plan-layout` | the per-chapter scene list (stage/clock/cast computed) | `plan/layout.md` |
| **L5** | `plan-knowledge` | the reveal ladder + who-knows-what; no secret leaks past its cap | store knowledge |

Before L1, a book must have its store migrated (`migrate_story.py`) — `plan-world`
does this automatically as its step 0. Integrity lives in the commit: an
impossible event (teleport, backward clock, a leak past a reveal cap) fails to
`replay`, so errors are unrepresentable, not caught by a battery of checks.

---

## Worldbuilding lives in three tiers

Worldbuilding is not missing — it is layered, and this is where each part lives:

1. **Series** → `grimoire.md`: magic system, factions, geography, history,
   master mysteries (§14b), loaded guns (§14). The *trans-book* foundation.
   Built by `forge-grimoire`, audited by `critique-grimoire`.
2. **Book** → `setup.md` + `canon/{world,magic,factions,timeline}.md` + the
   **world texture** (`references/world-texture.md`: economy of the magic,
   daily nouns, culture, class markers). *This book's* world.
3. **Engine** → `state/{world,entities}.json`: the queryable graph of places +
   positions + clock. The *verifiable physical contract*.

---

## The craft references (what "good" looks like)

The canonical homes for craft rules — read on demand, do **not** re-narrate them
inside SKILL.md files:

- **Characters** → `references/character-craft.md` (contradiction, magic↔lie
  interlock per principal, dark-mirror antagonist, the ensemble, the divergence
  pass) — the depth levers past Want/Need/Lie.
- **Relationships** → `references/relationship-craft.md` (the dyad as a designed
  object — the space between people).
- **World texture** → `references/world-texture.md` (the lived-in world at
  design time).
- **Magic** → `references/magic-design-checklist.md`, `references/hard-magic-laws.md`.
- **Structure** → `references/fantasy-beats.md`. **Seeds** →
  `references/seed-craft.md`. **Prose** → `references/prose-antipatterns.md`,
  `references/dwelling-techniques.md`, `references/style.md`.

---

## The skills, in three tiers

The felt "there are too many skills" is a presentation problem: they were listed
flat. They are really three tiers by *who invokes them*. You only ever type
Tier 1.

**Tier 1 — the entry points you actually invoke (7):**
- `resume-act` (The Lodestar — the compass), `forge-grimoire`, `book-setup`,
  `plan-book`, `plan-world`, `critique-plan`, `write-novel`.

**Tier 2 — chained for you (a Tier-1 skill runs these; rarely invoked direct):**
- *Engine layers of `plan-world`:* `plan-space` (L1), `plan-time` (L2),
  `plan-cast` (L3), `plan-layout` (L4), `plan-knowledge` (L5). These are
  **layers, not standalone skills** — think "plan-world," not five names.
- *Chapter loop of `write-novel`:* `plan-chapter`, `write-chapter`,
  `critique-chapter`, `update-canon`.
- *Constructive critique of `forge-grimoire`:* `critique-grimoire`.

**Tier 3 — utilities on demand:**
- `search-corpus` (grep the corpus), `checkpoint` (the session-close bookend to
  The Lodestar), `calibrate-style` (learn voice rules from hand-edits),
  `mend-chapter` (post-critique chapter surgery: `ground` / `polish` / `trim` /
  `tighten-seeds` modes), `close-act` (act boundary), `compile-book` (EPUB).

---

## Golden rules

- **Lost? Run `resume-act` (The Lodestar).** It is the compass — one entry
  point, and it points at the next step.
- **One chapter per session, then `/clear`.**
- **Critiques are gates, never optional** — grimoire, plan, and every chapter.
- **Never hand-edit** `plan/seeds.md`, `plan/shadow.md`, or `state/*.json` —
  a PreToolUse hook blocks it; mutate via the surgical scripts / `world_tool.py`.
- **Length is never counted** back to the model (see the `length invisible`
  rule); pacing is governed by beats + the six need-tests.
