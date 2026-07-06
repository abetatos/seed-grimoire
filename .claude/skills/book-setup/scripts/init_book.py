#!/usr/bin/env python3
"""Initialize a new book's directory structure with an empty setup.md template.

Usage:
    python init_book.py --series-slug <slug> --book-number <n> --title "<title>"

Creates the directory structure and writes a rich setup.md skeleton.
Does NOT overwrite an existing setup.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make scripts/lib importable
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib.project_config import author_name
from lib.slugify import slugify


SETUP_TEMPLATE = """# Book setup — {title}

> This file is the **single source of truth** for this book. Edit it freely.
> Every chapter the writer produces is held against what is declared here.
> Leave sections blank only if you have not yet decided; `plan-book` will
> prompt you to fill the critical gaps before chapter writing begins.

## Identity

- **Title:** {title}
- **Autor:** {author}
- **Subgenre:** (epic / grimdark / sword & sorcery / portal / romantasy / progression / cozy)
- **Series position:** book {book_number} of N — (standalone if N=1)
- **Writing language:** es
- **Narrative voice:** (close third / first / omniscient)
- **Tense:** (past / present)

## Length & shape

- **Chapters:** 25
- **Words per chapter:** 5000-10000 — planning objective ONLY (sizes the
  outline's beats per chapter). Never checked against written prose: the
  pipeline does not count generated words or show counts to the model
  (a visible count-vs-target breeds compensation). Length is governed
  structurally: outline beats + expand-chapter's six need tests.
- **Total target:** ~180k words
- **Act structure:** Act 1 (ch 1-7) · Act 2 (ch 8-18, midpoint ch 13) · Act 3 (ch 19-25)
- **Pace:** slow-immersion first act — dwelling on daily life, world texture, magic in mundane use.

## Premise of world

> Three to five sentences. The pitch. What is unusual about this world that
> a reader would tell a friend?

(Pitch here)

- **Era / tech level:**
- **Climate / geography macro:**
- **Calendar / languages:**

## Magic system

> Read `references/magic-design-checklist.md`. Be specific.

- **Source:** (where the magic comes from — substance, location, relationship, condition)
- **Mechanic:** (how a user accesses it, step by step)
- **Cost:** (what it costs — physical, emotional, social, material; at least two)
- **Hard limits:** (what it can NEVER do — at least three)
- **Who can use:** (access rule — caste, bloodline, ritual, etc.)
- **Social stratification:** (how it splits society)
- **Thematic question forced:** (what moral question the magic puts in characters' hands)
- **Three escalation tiers:**
  - Common:
  - Skilled:
  - Apex (climax-level):

## Castes / factions / orders

> Each major faction with: name, premise, hierarchy, symbol, ritual, relation
> to magic, current conflict with other factions.

### Faction 1
(fill in)

### Faction 2
(fill in)

## Geography

> 5-10 named places. Sensory description, function in plot, who lives there.

- **Place 1:**
- **Place 2:**
- **Place 3:**

**Macro political map:** who controls what
**Travel:** routes, distances, costs

## Historical weight

> The past that the present reverberates. 3-5 events.

- **Event 1:** (what happened, how long ago, who remembers)
- **Event 2:**
- **Event 3:**

**Collective wounds:**
**Myths / prophecies (with their real meaning, not just the believed one):**

## Characters — principals

> One block per principal. Use `references/fantasy-beats.md` (Character
> arcs section) as a guide. Be specific. Three concrete physical details
> per character, no clichés.

### Character 1 — name
- **Role:** (protagonist / antagonist / ally / mentor / rival)
- **Caste / faction:**
- **Age:** · **Physical:** (three specific details)
- **Want (conscious):**
- **Need (real):**
- **Wound (past):**
- **Lie they believe:**
- **Voice / vocabulary / tics:**
- **Arc (transformation by end):**
- **Magic relationship:** (capabilities and personal limits)
- **Secret they hide:**
- **Relationships:**
  - vs (other character): (nature of the bond)
  - vs (other character):

### Character 2 — name
(same fields)

### Character 3 — name
(same fields)

## Characters — secondary

> Quick lines for supporting cast. Name, function, when they appear.

- (name):
- (name):

## Theme

- **Central moral question:** (what does the book argue about — without
  answering on the nose)
- **Sub-themes:** (two or three)
- **Reader promise in chapter 1:** (what the opening promises the reader
  will get by the end)
- **Dominant emotion:** (what the book wants the reader to feel)

## Plot

- **Central conflict (one paragraph):**
- **Inciting incident:**
- **Midpoint — what breaks:**
- **All-is-lost moment:**
- **Climax — the irreversible decision:**
- **Resolution — costs paid, who lands where:**

## Subplots (1-3)

### Subplot A — name
- **Implicated:** (characters)
- **Premise:**
- **Chapter window:** (e.g. introduced ch 3, escalates ch 7-15, resolves ch 18)
- **Resolution:**
- **Theme it carries (different from main):**

### Subplot B
(same fields)

## POV

- **Number of POVs:**
- **Default POV:**
- **Distribution by chapter (rough):**
- **POV switch rule:**

## Slow-immersion specifics

> What world textures will be **dwelt on** in the first act? List the
> oficios, rituals, fauna, foods, places that will recur as anchors.

- **Recurring sensory anchors:** (e.g., the smell of pitch from the
  artisans' quarter; the sound of bells at sundown)
- **Texture beats budget:** in each chapter, plan 2-4 typed grounding
  beats of 150-400 words each (unfold / stage / cost / deliberation /
  re-orient / secondary).

## Prose constraints

- **Voice:** (e.g., close third, past, present-perfect dips for memory)
- **Distance:** (intimate / standard / wide chronicle)
- **Register:** (literary / pulpy / lyrical / spare)
- **Desired tics:** (specific habits to lean into)
- **Forbidden tics:** (additional to the global anti-patterns)

## If continuation (book 2+ of a series)

- **Series resume link:** ../../book-NN/summaries/book-summary.md
- **Threads inherited that this book must address:**
- **Characters returning and their state at the start:**
- **Promises from previous books still unpaid:**
"""


STYLE_MASTER = REPO_ROOT / "references" / "style.md"

STYLE_HEADER = """# Style — {title}

> This book's style guide — the single source of truth for how this book
> reads. It was copied from the house template (`references/style.md`) when
> the book was created; edit it freely. Changes here affect only this book.

"""


def _book_style_from_master(title: str) -> str:
    """Build a book's style.md as a full copy of the master template.

    Everything from the master's first `##` heading onward is duplicated, so
    each book owns a complete, self-contained style file (no global/override
    layering that could contradict itself).
    """
    header = STYLE_HEADER.format(title=title)
    if not STYLE_MASTER.exists():
        return header
    master = STYLE_MASTER.read_text(encoding="utf-8")
    idx = master.find("\n## ")
    body = master[idx + 1:] if idx != -1 else master
    return header + body.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=False, help="Series slug (folder name). If omitted, computed from title.")
    parser.add_argument("--book-number", type=int, default=1)
    parser.add_argument("--title", required=True)
    parser.add_argument("--force", action="store_true", help="Overwrite existing setup.md")
    args = parser.parse_args()

    series_slug = args.series_slug or slugify(args.title)
    paths = book_paths(series_slug, args.book_number)
    paths.ensure_dirs()

    if paths.setup_md.exists() and not args.force:
        print(f"setup.md already exists at {paths.setup_md} — refusing to overwrite (use --force).")
        return 1

    content = SETUP_TEMPLATE.format(
        title=args.title,
        book_number=args.book_number,
        author=author_name() or "(pen name — set [author] name in config.toml)",
    )
    paths.setup_md.write_text(content, encoding="utf-8")

    # Per-book style: a full copy of the master template (self-contained)
    if not paths.style_md.exists():
        paths.style_md.write_text(_book_style_from_master(args.title), encoding="utf-8")

    # Touch empty files we'll need later
    if not paths.series_md.exists():
        paths.series_md.write_text(
            f"# Series — {args.title}\n\n"
            "> Use this file if the series spans multiple books. Edit freely. "
            "Premise, shared themes, tone of voice across the series.\n",
            encoding="utf-8",
        )
    if not paths.series_state.exists():
        paths.series_state.write_text(
            "# Series state\n\n"
            "> Rolling state shared across books in this series. Open threads, "
            "final emotional state of each character at the end of the latest book, "
            "narrative debts still owed.\n",
            encoding="utf-8",
        )

    print(f"Initialized at {paths.book_root}")
    print(f"setup.md created — edit it: {paths.setup_md}")
    print(f"style.md created (optional override; inherits global until filled): {paths.style_md}")
    print(f"Series slug: {series_slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
