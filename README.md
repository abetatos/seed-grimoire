<div align="center">

<img src="assets/logo.png" alt="The Seed Grimoire" width="280">

# The Seed Grimoire

**Write entire fantasy novels with Claude Code — one disciplined chapter at a time.**

The name says what the project is. A **grimoire** — the world's book of truth,
written and hardened before a single scene exists. And **seeds** — promises
planted in the prose that the book is *contractually obliged* to pay off. Build
those two well and a 25-chapter novel — or a whole **coherent trilogy** — holds
together: foreshadowed, consistent, and worth rereading. The whole book lives on
disk as plain Markdown; Claude plans it,
writes it, critiques itself, and locks each chapter into canon before moving on.
No agent graph, no vector database, no API plumbing — just a deterministic file
layout and a set of focused skills.

![Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-7C3AED)
![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB)
![Markdown-native](https://img.shields.io/badge/state-Markdown-000000)
![Dependencies](https://img.shields.io/badge/runtime%20deps-none%20(stdlib)-2EA043)

</div>

---

## The problem

Long fiction breaks LLMs in predictable ways: the model forgets what it
established 20 chapters ago, foreshadowing is set up and never paid off, magic
does whatever the plot needs this scene, and chapters drift short and thin. You
cannot fix this with a longer prompt — the failure is structural. You fix it
with a **contract** the prose is checked against, and a **plan solid enough to
hold** before any prose is written.

The Seed Grimoire is that contract. Two ideas carry the whole system, and they
are the reason the book holds together:

- 🌱 **Seeds** — every planted promise is tracked, doses are budgeted, and the
  payoff is forced. This is what makes the prose feel *woven*, not episodic.
- 🌑 **The shadow** — a writer-only hidden truth that runs underneath the
  visible story, so the prose can plant honestly without ever leaking.

Everything else — deterministic Markdown state, the per-chapter loop, the
self-critique — exists to serve those two.

---

## The two pillars

### 🌱 Seeds — foreshadowing that *cannot* be forgotten

A seed is a detail planted early so a later revelation feels inevitable in
retrospect. It's the single hardest thing for an LLM to do across a long book,
because the plant and the payoff can be 200,000 words apart. The Seed Grimoire
solves it by refusing to leave seeds to memory: every seed is an explicit entry
in `plan/seeds.md`, the one file that is **never compressed**, and it carries
the machinery to make the touch land on the page:

| Field | What it forces |
|-------|----------------|
| **Plant / Echo / Payoff** | *where* each touch belongs, by chapter. |
| **Trigger** | the *intrinsic, already-seeded cause* that fires an event payoff — no convenient horse that spooks, no sudden storm. The thing that breaks is the thing the reader was told about. |
| **Dose** | a telegraph budget tied to plant→payoff distance, so a seed is never over-planted into "I saw it coming a mile off." |
| **Resolution image** | the emotional through-line — *one image inverted* between plant and climax. The difference between a book that **resolves** and one that merely **concludes**. |
| **Realized** | a touch-log. Every time a seed actually lands, `update-canon` records *how it read on the page*, so a far-later payoff rhymes with the prose, not the plan. |

The craft is plant → echo → payoff, and the rules are unforgiving: embed the
seed inside something the scene was already doing; no flag words ("strangely",
"oddly"); never interpret the seed in the same breath you plant it; echo in a
different sensory register; let the reader make the final connection. The full
discipline lives in [`references/seed-craft.md`](references/seed-craft.md).

The result is **prose with a spine.** Because the seed envelope rides in the
context bundle for every chapter, the writer always knows which promises are due
*now*, which are warming in the background, and which must not be touched yet.

### 🌑 The shadow — the writer's secret

You cannot plant a seed truthfully unless you know what it *really* means — and
the POV character usually must not. That's the shadow: `plan/shadow.md`, a
writer-only hidden timeline of what is actually true beneath the surface the
world believes. It is the other **never-compressed** file.

The shadow is why a planted detail can read as harmless background on the first
pass and as intent on the second. The world believes one thing; the buried
truth is another; the writer holds both and the reader holds only what they've
earned. This two-layer rule starts in the grimoire and propagates all the way
down to the line — it's what protects the book from the most common LLM
foreshadowing failure: **leaking the answer while pretending to hide it.**

Seeds and shadow together are the engine of *continuous, interesting prose*:
the shadow gives every chapter a buried current, the seeds make sure that
current surfaces on schedule, and the Realized log keeps each payoff in
conversation with how the earlier touches actually read.

---

## Planning is the whole game

Most "AI writes a novel" attempts start generating prose immediately and
discover the foundation was cracked around chapter 12. The Seed Grimoire
inverts that: **the hard thinking happens up front, and it is iterative.**
You do not write a plan once and proceed — you write it, attack it
adversarially, fix what breaks, and attack it again, until it passes clean.
There are two such gauntlets, and the book does not advance past either until
it earns a **PASS**.

### 1. The grimoire — the series' book of truth

Before any single book exists, the **grimoire** (`output/<series>/grimoire.md`)
fixes the foundation for the whole series: the one-sentence premise, the
two-layer truth model, the magic system (source, ≥2 costs, ≥3 hard limits, the
moral question it forces), whether the system is *scaled* or *inverted*, the
cast with full want/need/lie/wound, subplots with real contact points, the
historical wounds, the geography, the structure, and **the clock — why this
story, now.** Start from [`references/grimoire-template.md`](references/grimoire-template.md).

`critique-grimoire` then audits it adversarially in a **fresh context** that never
saw it being written. Its bias is total: a grimoire that passes with zero
findings is suspicious. It tiers every gap (MUST / SHOULD / CONSIDER), quotes
its sources, and refuses to rubber-stamp. **Any MUST → REJECT.** You revise the
grimoire and run it again. You iterate here because the cost of finding a
structural hole now is one conversation; the cost of finding it in Book II is a
rewrite.

### 2. The plan — the book a writer can execute

Once the grimoire passes, `book-setup` turns it into one book's `setup.md`, and
`plan-book` expands that into everything a writer executes against:
`plan/outline.md` (visible beats), `plan/shadow.md` (the hidden truth),
`plan/seeds.md` (the foreshadowing catalogue), `plan/arcs.md` (character arcs),
and the initial `canon/`.

Then `critique-plan` runs the **same adversarial loop** on the finished plan —
rhythm, plot logic, foreshadowing coverage, magic completeness, worldbuilding
economy — and writes `notes/critique-plan.md`. You don't write chapter 1 until
the plan passes. Same discipline, same iteration.

```text
grimoire.md ──▶ critique-grimoire ──▶ REJECT? revise grimoire ─┐
     ▲                                                       │
     └───────────────────────────────────────────────────────┘
                          │ PASS
                          ▼
   book-setup ──▶ plan-book ──▶ critique-plan ──▶ REVISE? fix plan ─┐
                     ▲                                               │
                     └─────────────────────────────────────────────┘
                          │ PASS
                          ▼
                   the per-chapter loop  (below)
```

Both critiques run in a **fresh subagent** (`.claude/agents/book-critic.md`)
that audits in an isolated context — it never saw how the work was written, so
it cannot rationalise its own foundation. No `/clear` required to "audit in
clean."

---

## Writing the book — the per-chapter loop

With a passing grimoire and a passing plan, prose is the *easy* part, because
every chapter is written from a deterministic context bundle assembled in a
fixed order: setup + canon + plan + the **active seed envelope** + the relevant
**shadow** slice + rolling summaries + the continuity seam (the previous
chapter's structured summary plus only its final scene, verbatim). The writer
is never guessing what's true or what's due.

Each chapter runs the same loop, then **hard-stops for a `/clear`**:

```text
┌──────────────────────────────────────────────────────────┐
│  plan-chapter    decision gate — you pick the creative forks│
│       ▼                                                     │
│  write-chapter   draft to target length from the bundle    │
│       ▼                                                     │
│  expand-chapter  ALWAYS once — a texture/dwelling pass      │
│       ▼                                                     │
│  critique-chapter  fresh subagent: beats, canon, seeds,    │
│       ▼             prose anti-patterns, word count        │
│  revise-chapter / 2nd expand pass   (only if flagged)      │
│       ▼                                                     │
│  update-canon    lock in: summary, seed statuses, new      │
│       ▼          facts → canon, Realized touch-log         │
│  close-act       (at act boundaries only)                  │
└───────────────────────────┬──────────────────────────────┘
                            │ one chapter, then /clear
                            ▼
                      next fresh session
```

A few deliberate choices:

- **`plan-chapter` is a gate, not a formality.** The outline always leaves a
  few forks underdetermined; the gate puts them in front of you *with a
  recommendation* and records your answers to `notes/decisions-chNN.md`, so a
  regeneration can't silently overwrite them.
- **`expand-chapter` always runs once.** Even when the chapter is already at
  length, the texture pass adds the dwelling/interior paragraphs the author
  wants. Word count is checked *after* — too short triggers a second expand
  (2-pass cap); too long triggers a trim.
- **Critique is adversarial and external.** It runs in the same fresh
  subagent as the planning critiques, so it judges the prose, not its own
  intentions, and writes `notes/critique-*.md` without ever editing the source.

`write-novel` drives that whole loop for **one chapter**, then stops for the
`/clear`. The next chapter is a fresh session that rebuilds from disk via
`resume-act`.

---

## The skills

Invoke a skill by name or just by describing the intent.

| Skill | What it does |
|-------|--------------|
| `critique-grimoire` | Adversarial audit of the **grimoire** (the series-wide world book) before any per-book work. Iterate to PASS. |
| `book-setup` | Interactive intake → writes `setup.md`, the single source of truth for one book. |
| `plan-book` | Turns `setup.md` into `plan/*` (outline, **shadow**, **seeds**, arcs) + initial `canon/*`. |
| `critique-plan` | Hard audit of the finished per-book plan before chapter 1. Iterate to PASS. |
| `resume-act` | **First step of every new session.** Reads handoff, voice/style rules, open questions — reports state and dispatches the next skill. |
| `plan-chapter` | **Decision gate before writing.** Surfaces the chapter's creative forks with a recommendation; records the choices. |
| `write-chapter` | Writes one chapter to target length from the assembled context bundle. |
| `expand-chapter` | Adds depth/texture — no new plot. Runs once on every chapter, again if still under length. |
| `critique-chapter` | Structured critique against beats, canon, **seeds**, and prose anti-patterns. |
| `revise-chapter` | Surgical fixes for flagged issues (`polish` / `trim` / `tighten-seeds`). |
| `update-canon` | Locks a chapter in: summary, **seed statuses + Realized log**, new facts → canon. Includes a mandatory checkpoint. |
| `checkpoint` | Fast manual sync of ephemeral chat state to disk. Run before `/compact`. |
| `close-act` | End-of-act: compresses summaries, stabilises voice rules, writes session handoff. |
| `search-corpus` | Targeted grep across canon → plan → summary → chapter (runs in a subagent). |
| `compile-book` | Compiles the finished chapters into a Kindle-ready EPUB (and can email it). |
| `write-novel` | Orchestrator: chains the per-chapter loop, halts at act boundaries for `/clear`. |

## Quickstart

> Requires [Claude Code](https://claude.com/claude-code) and Python 3.12
> (with [`uv`](https://github.com/astral-sh/uv) for the helper scripts).

```bash
git clone https://github.com/abetatos/seed-grimoire.git
cd seed-grimoire
```

Then, inside Claude Code — note the two iterative critique gates up front:

```text
audita el grimorio        # critique-grimoire → revise the grimoire → repeat until PASS
new fantasy book          # book-setup
plan the book             # plan-book (writes shadow + seeds)
critique the plan         # critique-plan → revise → repeat until PASS
write the book            # write-novel, one chapter at a time
```

Drive a single chapter end to end (then `/clear` and resume for the next):

```text
write-novel --from-chapter 1     # plan → write → expand → critique → fix → lock in
```

## Session hygiene (one chapter per session)

Long Claude Code conversations degrade model quality. The pipeline is designed
so each writing session covers **one chapter** and ends with a `/clear`.
Everything worth remembering across sessions is persisted to disk by
`update-canon` (per chapter) and `close-act` (at act boundaries), so the next
session rebuilds state in seconds via `resume-act`.

```text
Session 1
  resume-act               ← always first; reports state
  plan-chapter 1           ← decision gate: you pick the forks
  write-chapter 1
  update-canon 1           ← includes mandatory checkpoint;
                             signs "Safe to /clear before chapter 2"
  /clear                   ← you trigger

Session 2
  resume-act
  plan-chapter 2
  write-chapter 2
  ...

# At an act boundary, update-canon is followed by close-act before /clear.
```

If you need to `/compact` mid-session, run `checkpoint` first — it syncs
ephemeral chat state to disk so nothing important is lost.

Skills cannot trigger `/clear` or `/compact` themselves (those are user
commands). What they do instead: end each canonical step with an explicit
`Safe to /clear` or `STRONGLY recommended: /clear` signal, so you know exactly
when to act.

## What survives compression

To keep context flat over a 25+ chapter book, distant material is summarized —
but the load-bearing structure is **never** lost. The two pillars are at the
top of the table for a reason.

| File | Compressed? |
|------|-------------|
| `plan/seeds.md` | **Never** — the source of truth for every foreshadowing seed. |
| `plan/shadow.md` | **Never** — the writer's hidden timeline. |
| `plan/outline.md`, `plan/arcs.md` | Never — they *are* the plan. |
| `canon/*.md` | Edited in place, kept tight by `update-canon`. |
| `summaries/ch-NN.md` | Kept on disk; rolls out of context after the recent window. |
| `summaries/act-NN.md` | Stands in for individual chapter summaries of distant acts. |
| `chapters/NN.md` | Last one kept in full (the continuity seam); older fold into summaries, read in full only via `search-corpus`. |

## Repository layout

```text
.claude/skills/     the skills Claude invokes (SKILL.md + scripts/)
.claude/agents/     book-critic — the fresh-context adversarial critic
scripts/lib/        deterministic Python helpers (stdlib only)
scripts/build_epub.py      compile chapters → EPUB (via pandoc)
scripts/send_to_kindle.py  email the EPUB to your Kindle
scripts/assets/     reading stylesheet for the EPUB
references/         craft references: beats, hard-magic laws, dwelling,
                    seed-craft, prose anti-patterns, magic checklist,
                    grimoire template
output/             generated books (git-ignored)
```

Each generated book lives under `output/`:

```text
output/<series-slug>/
  grimoire.md          the grimoire — series-wide book of truth
  series.md            series identity (if it's a series)
  series-state.md      rolling cross-book state
  book-NN/
    setup.md           source of truth for this book
    assets/cover.*     book cover (cover.jpg/.jpeg/.png — auto-embedded in EPUB)
    canon/             characters, factions, magic, world, timeline
    plan/              outline, shadow (writer-only), seeds, arcs
    chapters/NN.md     the prose
    summaries/         ch-NN · act-NN · book-summary (rolling context)
    notes/             decisions, dropped ideas, critiques
```

## Coherent trilogies

A trilogy is not three books in the same setting — it's one argument told in
three movements, and that's exactly what the up-front planning is built to hold.
Coherence across books is a **first-class capability**, enforced where the plan
is hardest to fake:

- **The grimoire spans the whole series.** It declares each book's structure in
  §12 with a **distinct motor per book** (no "louder echo of Book I" in Book
  III) and pairs every myth with its writer-only truth so trilogy-scale reveals
  stay honest.
- **`critique-grimoire` audits cross-book rigor.** It rejects diminishing-returns
  reveals (Book II's twist must differ *in kind* from Book I's), demands an
  active-decision climax for every book, and checks **cross-book inheritance**:
  what the reader carries forward, what dies between books, and which Book-I
  promises Book III must pay. You iterate to PASS before any prose.
- **Seeds and shadow carry across books.** The same never-compressed foreshadowing
  discipline can plant a promise in Book I and pay it off in Book III — the
  Realized touch-log keeps the distant payoff in conversation with how the early
  plant actually read.
- **State persists between books.** `series.md` holds shared identity,
  `series-state.md` tracks open threads after each finished book, and Book *N*
  inherits the previous book's `summaries/book-summary.md` as context.

## Language

Prose defaults to **Spanish (`es`)**. The skills and references run in English;
the book comes out in whatever language `setup.md` declares — override it per
book in the **Identity** section.

## Reading on Kindle

Once chapters exist, compile them into a single **EPUB** and read the draft on a
real device — the best way to gather your own critiques and notes.

```text
compile the book          # runs compile-book → builds the EPUB
export chapters 1-10      # partial draft to read what's done so far
send it to my Kindle      # emails the EPUB to your @kindle.com address
```

Under the hood:

```bash
# Build output/<series>/book-NN/build/<slug>.epub
python3 scripts/build_epub.py --series-slug <slug> --book-number <N>

# Optionally email it to your Kindle
python3 scripts/send_to_kindle.py --series-slug <slug> --book-number <N>
```

**Cover:** drop your cover image at the fixed path
`output/<series>/book-NN/assets/cover.jpg` (or `.jpeg` / `.png`) and it's
embedded automatically — same location for every book, no flags. Use a portrait
JPEG/PNG around 1.6:1 (e.g. 1600×2560), no transparency.

The EPUB contains **only the prose** — chapters in order, a title page and
author from `setup.md`, a navigation TOC, and a reading stylesheet
(`scripts/assets/epub.css`). Canon, plan, shadow, and seeds are never included
(they're spoilers). Conversion is delegated to
[**pandoc**](https://pandoc.org/) — install the static binary into
`~/.local/bin` or `apt install pandoc`.

### Send-to-Kindle setup

Amazon's *Send to Kindle* delivers personal documents to your devices by email.
Two one-time steps on Amazon's side, then config in `.env`:

1. **Find your Kindle address.** *Manage Your Content and Devices → Devices →*
   your Kindle → it ends in `@kindle.com`.
2. **Approve your sender.** *Preferences → Personal Document Settings →
   Approved Personal Document E-mail List →* add the email you'll send *from*.
   Mail from any other address is silently dropped.
3. **Configure `.env`** (copy `.env.example`; it's git-ignored):

   ```ini
   KINDLE_EMAIL=yourname_xxxxxx@kindle.com   # the destination
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=you@example.com                 # an approved sender
   SMTP_PASS=your-app-password               # Gmail: an App Password
   SMTP_FROM=                                # defaults to SMTP_USER
   ```

   For Gmail, generate an **App Password** (*Account → Security → App
   Passwords*) — your normal login won't work over SMTP.

Prefer no email? You can also drag the built `.epub` into the desktop/mobile
**Send to Kindle** app, or upload it at *amazon.com/sendtokindle*.

## Design conventions

- **Stdlib Python only** — zero third-party runtime dependencies.
- Markdown files are human-editable at any time; skills always re-read them.
- **Seeds and shadow are never compressed** — they are the source of truth for
  foreshadowing and the hidden timeline, and they survive every act compression.
- Every chapter gets one `expand-chapter` texture pass regardless of length
  (the author wants the added dwelling paragraphs). The word-count contract is
  then checked: chapters still under 80% of target trigger a second
  `expand-chapter` pass (2-pass cap); over 130% trigger
  `revise-chapter --mode trim`.

---

<div align="center">
<sub>The Seed Grimoire — a rewrite of an earlier agent-based prototype, traded for
deterministic file orchestration and hard contracts. Seeds that survive, a
grimoire that holds.</sub>
</div>
