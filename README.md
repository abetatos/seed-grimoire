<div align="center">

# 📖 Pagent

**Write entire fantasy novels with Claude Code — one disciplined chapter at a time.**

Pagent is a skill-driven writing pipeline. The whole book lives on disk as plain
Markdown; Claude plans it, writes it, critiques itself, and locks each chapter
into canon before moving on. No agent graph, no vector database, no API
plumbing — just a deterministic file layout and a set of focused skills.

![Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-7C3AED)
![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB)
![Markdown-native](https://img.shields.io/badge/state-Markdown-000000)
![Dependencies](https://img.shields.io/badge/runtime%20deps-none%20(stdlib)-2EA043)

</div>

---

## Why Pagent

Long fiction breaks LLMs in predictable ways: the model forgets what it
established 20 chapters ago, foreshadowing never pays off, magic does whatever
the plot needs, and chapters drift short. Pagent fixes each of those with a
**contract**, not a vibe:

- 🧱 **Deterministic state.** Every fact lives in a Markdown file you can read,
  edit, and diff. The model never has to "remember" — it re-reads.
- 🌱 **Foreshadowing that survives.** A *seed envelope* tracks every planted
  promise and forces its echo and payoff. Seeds are **never** compressed away.
- 🪄 **Hard magic, honest costs.** Magic is held to the three laws of rules-based
  systems (capability matches what the reader has seen, costs are visible,
  depth beats sprawl).
- 🐢 **Deep-immersion pacing.** Chapters *inhabit* the world before advancing the
  plot — and a word-count contract keeps them from coming in thin.
- 🔁 **Self-critiquing loop.** Each chapter is written, critiqued against the
  book's own rules, revised or expanded, then locked into canon.

## How it works

The book is planned **big to small**: world and characters first
(`setup.md`), then the visible and hidden timelines, then per-chapter beat
sheets. Each chapter starts at a **decision gate** (`plan-chapter`) that puts
the underdetermined creative forks in front of you with a recommendation, then
is written from a deterministic context bundle — setup + canon + plan + the
active seed envelope + the hidden "shadow" slice + rolling summaries + the most
recent chapters in full. Once written, it's critiqued, revised or expanded to
length, and **locked in**. Distant chapters fold into act-level summaries so
context stays flat — but seeds and shadow never do.

```text
book-setup ──▶ plan-book ──▶ ┌─────────────────────────────────────────────┐
                             │  plan-chapter   (decision gate)             │
                             │      ▼                                      │
                             │  write-chapter                              │
                             │      ▼                                      │
                             │  critique-chapter                           │
                             │      ▼                                      │
                             │  expand-chapter / revise-chapter (if needed)│
                             │      ▼                                      │
                             │  update-canon   ──▶  close-act (per act)    │
                             └──────────────────────┬──────────────────────┘
                                                    │ one chapter, then /clear
                                                    ▼
                                              finished book
```

`write-novel` drives that loop for **one chapter**, then stops for a `/clear` —
the next chapter is a fresh session that rebuilds from disk via `resume-act`.

## The skills

Invoke a skill by name or just by describing the intent.

| Skill | What it does |
|-------|--------------|
| `book-setup` | Interactive intake → writes `setup.md`, the single source of truth. |
| `plan-book` | Turns `setup.md` into `plan/*` (outline, shadow, seeds, arcs) + initial `canon/*`. |
| `critique-bible` | Adversarial audit of the **series bible** before any per-book work starts. |
| `critique-plan` | Hard audit of the finished per-book plan before chapter 1. |
| `resume-act` | **First step of every new session.** Reads handoff, voice rules, pendientes — reports state. |
| `plan-chapter` | **Decision gate before writing.** Surfaces the chapter's creative forks with a recommendation and records the choices. |
| `write-chapter` | Writes one chapter to target length from the assembled context. |
| `critique-chapter` | Structured critique against beats, canon, seeds, and prose anti-patterns. |
| `expand-chapter` | Grows an under-length chapter with depth — no new plot. |
| `revise-chapter` | Surgical fixes for flagged issues (`polish` / `trim` / `tighten-seeds`). |
| `update-canon` | Locks a chapter in: summary, seed statuses, new facts → canon. Includes mandatory checkpoint sync. |
| `checkpoint` | Fast manual sync of ephemeral chat state to disk. Run before `/compact`. |
| `close-act` | End-of-act: compresses summaries, stabilises voice rules, writes session handoff. |
| `search-corpus` | Targeted grep across canon → plan → summary → chapter. |
| `compile-book` | Compiles the finished chapters into a Kindle-ready EPUB (and can email it to your Kindle). |
| `write-novel` | Orchestrator: chains the per-chapter loop, halts at act boundaries for /clear. |

## Quickstart

> Requires [Claude Code](https://claude.com/claude-code) and Python 3.12
> (with [`uv`](https://github.com/astral-sh/uv) for the helper scripts).

```bash
git clone https://github.com/abetatos/Pagent.git
cd Pagent
```

Then, inside Claude Code:

```text
new fantasy book          # runs book-setup
plan the book             # runs plan-book
critique the plan         # runs critique-plan
write chapter 1           # runs write-chapter → critique → update-canon
write the book            # runs write-novel for the whole thing
```

Drive a chapter end to end (then `/clear` and resume for the next):

```text
write-novel --from-chapter 1     # plan → write → critique → fix → lock in
```

## Session hygiene (one chapter per session)

Long Claude Code conversations degrade model quality. The pipeline is
designed so each writing session covers **one chapter** and ends with a
`/clear`. Everything you'd want to remember across sessions is persisted
to disk by `update-canon` (per chapter) and `close-act` (at act
boundaries), so the next session rebuilds state in seconds via
`resume-act`.

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

If you need to `/compact` mid-session, run `checkpoint` first — it
syncs ephemeral chat state to disk so nothing important is lost.

Skills cannot trigger `/clear` or `/compact` themselves (those are
user commands). What they do instead: end each canonical step with an
explicit `Safe to /clear` or `STRONGLY recommended: /clear` signal,
so you know exactly when to act.

## Repository layout

```text
.claude/skills/     the skills Claude invokes (SKILL.md + scripts/)
scripts/lib/        deterministic Python helpers (stdlib only)
scripts/build_epub.py    compile chapters → EPUB (via pandoc)
scripts/send_to_kindle.py  email the EPUB to your Kindle
scripts/assets/     reading stylesheet for the EPUB
references/         craft references: beats, hard-magic laws, dwelling,
                    seed-craft, prose anti-patterns, magic checklist
output/             generated books (git-ignored)
```

Each generated book lives under `output/`:

```text
output/<series-slug>/
  series.md            series identity (if it's a series)
  series-state.md      rolling cross-book state
  book-NN/
    setup.md           source of truth for this book
    assets/cover.*     book cover (cover.jpg/.jpeg/.png — auto-embedded in EPUB)
    canon/             characters, factions, magic, world, timeline
    plan/              outline, shadow (writer-only), seeds, arcs
    chapters/NN.md     the prose
    summaries/         ch-NN · act-NN · book-summary (rolling context)
    notes/             decisions, dropped ideas
```

## What survives compression

To keep context flat over a 25+ chapter book, distant material is summarized —
but the load-bearing structure is never lost.

| File | Compressed? |
|------|-------------|
| `plan/seeds.md` | **Never** — source of truth for every foreshadowing seed. |
| `plan/shadow.md` | **Never** — the writer's hidden timeline. |
| `plan/outline.md`, `plan/arcs.md` | Never — they *are* the plan. |
| `canon/*.md` | Edited in place, kept tight by `update-canon`. |
| `summaries/ch-NN.md` | Kept on disk; rolls out of context after the recent window. |
| `summaries/act-NN.md` | Stands in for individual chapter summaries of distant acts. |
| `chapters/NN.md` | Last one kept in full (the continuity seam); older fold into summaries, read in full only via `search-corpus`. |

## Series & trilogy support

For multi-book series, `series.md` holds shared identity and `series-state.md`
tracks open threads after each finished book. Book *N* inherits the previous
book's `summaries/book-summary.md` as context.

## Language

Prose defaults to **Spanish (`es`)**. The skills and references run in English;
the book comes out in whatever language `setup.md` declares — override it per
book in the **Identity** section.

## Reading on Kindle

Once chapters exist, compile them into a single **EPUB** and read the draft
on a real device — the best way to gather your own critiques and notes.

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
embedded automatically — same location for every book, no flags. Use a
portrait JPEG/PNG around 1.6:1 (e.g. 1600×2560), no transparency.

The EPUB contains **only the prose** — chapters in order, a title page and
author from `setup.md`, a navigation TOC, and a reading stylesheet
(`scripts/assets/epub.css`). Canon, plan, shadow, and seeds are never
included (they're spoilers). Conversion is delegated to
[**pandoc**](https://pandoc.org/) — install the static binary into
`~/.local/bin` or `apt install pandoc`.

### Send-to-Kindle setup

Amazon's *Send to Kindle* delivers personal documents to your devices by
email. Two one-time steps on Amazon's side, then config in `.env`:

1. **Find your Kindle address.** *Manage Your Content and Devices →
   Devices →* your Kindle → it ends in `@kindle.com`.
2. **Approve your sender.** *Preferences → Personal Document Settings →
   Approved Personal Document E-mail List →* add the email you'll send
   *from*. Mail from any other address is silently dropped.
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
- The word-count contract is law: chapters under 80% of target trigger
  `expand-chapter`; over 130% trigger `revise-chapter --mode trim`.

---

<div align="center">
<sub>Pagent — a rewrite of an earlier agent-based prototype, traded for
deterministic file orchestration and hard contracts.</sub>
</div>
