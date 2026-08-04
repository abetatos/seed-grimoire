#!/usr/bin/env python3
"""Resume-act bootstrap — assembles the start-of-session report.

Runs first thing in a fresh conversation. Reads everything the next
session needs from disk and emits a compact status report. Does NOT
build the full chapter context bundle (that's `build_context.py`
called by write-chapter). It only orients the agent + author so the
session can proceed.

Outputs to stdout:
  - Where in the book we are (next chapter, act).
  - Latest session handoff (verbatim — it's already compact).
  - Stable voice rules (from voice.md `Stable rules` blocks).
  - Active style rules (from style-rules.md).
  - Carry threads from the latest chapter brief (## Arrastre).
  - Quick stats: chapters written / total, acts closed / total, last
    book-summary snippet.

Usage:
    python resume_act.py --series-slug <slug> --book-number <n>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths, chapter_numbers, act_numbers
from lib import brief as brief_mod, notes_files, setup_doc, summaries as sum_mod


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _box(lines: list[str], width: int = 54) -> str:
    """A monospace banner box. The Lodestar's face — the first thing the
    author sees on return, so the phase + next step read at a glance."""
    top = "    ╔" + "═" * (width - 2) + "╗"
    bot = "    ╚" + "═" * (width - 2) + "╝"
    body = []
    for ln in lines:
        # pad to the interior width (account for the two side chars + a lead space)
        body.append("    ║ " + ln.ljust(width - 4) + " ║")
    return "\n".join([top, *body, bot])


def _has_content(p: Path, min_chars: int = 50) -> bool:
    """True if the file exists and holds more than a stub of real content."""
    if not p.exists():
        return False
    return len(p.read_text(encoding="utf-8").strip()) >= min_chars


def detect_phase(paths, last_written: int, next_ch):
    """Where in the lifecycle this book is, as a (phase, next_command) pair.

    Drives the dispatcher menu in the SKILL. The phases are linear and the
    critiques are MANDATORY gates, not optional:

      grimoire      -> forge-grimoire    (brand-new series: no grimoire, no setup)
      setup         -> book-setup        (no usable setup.md yet)
      plan          -> plan-book         (setup ready, plan/canon missing)
      plan-world    -> plan-world         (plan ready, engine layers L1-L5 not built)
      critique-plan -> critique-plan     (plan+layers ready, never audited, ch1 not written)
      write         -> write-novel       (plan audited; drive the next chapter)
      done          -> (none)            (all chapters written)
    """
    plan_ready = all(
        _has_content(p)
        for p in (paths.outline_md, paths.shadow_md, paths.seeds_md, paths.arcs_md)
    ) and _has_content(paths.canon_file("characters"))
    # The engine layers L1-L5 (plan-space/time/cast/layout/knowledge, chained
    # by plan-world) leave plan/layout.md as their last Markdown artifact. Its
    # absence means the spatial-temporal contract has not been built yet.
    layout_ready = _has_content(paths.plan_dir / "layout.md")
    # critique-plan is "done" only when the latest audit verdict is PASS. A
    # REVISE/REJECT verdict keeps us in the critique-plan phase so the
    # /clear → re-audit loop continues until the plan actually passes.
    critique_text = _read(paths.notes_dir / "critique-plan.md")
    plan_critiqued = bool(
        re.search(r"\*\*Verdict:\*\*\s*PASS\b", critique_text, re.IGNORECASE)
    )

    if not _has_content(paths.setup_md):
        # A brand-new series (nothing on disk) starts at the series grimoire,
        # not at the per-book setup. An existing series already has one, so a
        # new book (setup missing, grimoire present) skips straight to setup.
        if not paths.grimoire_md.exists():
            return "grimoire", "forge-grimoire"
        return "setup", "book-setup"
    if not plan_ready:
        return "plan", "plan-book"
    # Engine layers L1-L5 are a gate before the audit, but only before ch1 —
    # once writing has begun the layers are already proven in use, so don't
    # loop back. (A legacy book that never adopted the engine and is already
    # writing is left alone.)
    if not layout_ready and last_written == 0:
        return "plan-world", "plan-world"
    # critique-plan is a hard gate, but only before chapter 1 — once writing
    # has begun the plan is already proven in use, so don't loop back to it.
    if not plan_critiqued and last_written == 0:
        return "critique-plan", "critique-plan"
    if next_ch is not None:
        return "write", "write-novel"
    return "done", None


def _extract_stable_rules(voice_text: str) -> str:
    """Pull every `### Stable rules ...` block out of voice.md."""
    if not voice_text:
        return ""
    pattern = re.compile(
        r"(### Stable rules[^\n]*\n)((?:[ \t]*[-*][^\n]*\n)+)",
        re.MULTILINE,
    )
    blocks = []
    for m in pattern.finditer(voice_text):
        blocks.append(m.group(0).rstrip())
    return "\n\n".join(blocks)


def _latest_arrastre(paths) -> tuple[int, str]:
    """The carry buffer (## Arrastre) from the highest-numbered chapter brief.

    Replaces the retired open-questions.md `## Pendientes` surface: per-chapter
    carry threads now live in each brief's ## Arrastre (IMPROVEMENT-PLAN
    Movement 2). Returns (chapter, body) or (0, "") when nothing is pending.
    """
    briefs = sorted(paths.notes_dir.glob("brief-ch*.md")) if paths.notes_dir.exists() else []
    for p in reversed(briefs):
        m = re.search(r"brief-ch(\d+)\.md$", p.name)
        n = int(m.group(1)) if m else 0
        body = brief_mod.section(brief_mod.split_brief(_read(p)), brief_mod.SEC_ARRASTRE)
        if body and not any(mk.lower() in body.lower() for mk in brief_mod.ARRASTRE_EMPTY):
            return n, body
    return 0, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument(
        "--chapters-per-act",
        type=int,
        default=sum_mod.DEFAULT_CHAPTERS_PER_ACT,
    )
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.book_root.exists():
        print(f"ERROR: book directory not found: {paths.book_root}", file=sys.stderr)
        return 2

    notes_files.ensure(paths)

    # Discovery
    setup_text = setup_doc.load(paths.setup_md)
    title = setup_doc.book_title(setup_text) or "(untitled)"
    total_chapters = setup_doc.num_chapters(setup_text) or 0
    written = chapter_numbers(paths)
    last_written = max(written) if written else 0
    next_ch = last_written + 1 if last_written < total_chapters else None
    acts_closed = act_numbers(paths)
    last_act = max(acts_closed) if acts_closed else 0
    next_act = sum_mod.act_number_for(next_ch, args.chapters_per_act) if next_ch else None

    print("# ✦ THE LODESTAR — resume-act ✦\n")
    print(f"## {title}\n")
    print(f"- Book: {args.book_number}  ·  Series: {args.series_slug}")
    print(f"- Chapters written: **{last_written} / {total_chapters}**")
    print(f"- Acts closed: **{last_act}**")
    if next_ch:
        print(f"- Next: **chapter {next_ch}** (act {next_act})")
    else:
        print(f"- Book complete (all {total_chapters} chapters written).")

    # Latest session handoff (always relevant)
    handoff = _read(paths.session_handoff_md)
    if handoff and "TODO:" not in handoff:
        print("\n---\n## Session handoff (from last close-act)\n")
        print(handoff.strip())
    elif handoff and "TODO:" in handoff:
        print("\n---\n## Session handoff")
        print("\n> ⚠ Handoff has unfilled TODO sections. Either the last act")
        print("> wasn't properly closed, or this is the first act and there")
        print("> is no prior session. Treat as: no prior session-level state.")
    else:
        print("\n---\n## Session handoff")
        print("\n> No prior session handoff. This is a fresh book.")

    # Stable voice rules (consolidated)
    voice = _read(paths.voice_md)
    stable_rules = _extract_stable_rules(voice)
    if stable_rules:
        print("\n---\n## Stable voice rules (from voice.md consolidations)\n")
        print(stable_rules)
    else:
        print("\n---\n## Stable voice rules")
        print("\n> None yet. voice.md exists but has no `Stable rules` blocks —")
        print("> close-act will write them at the end of the act.")

    # Active style rules (full file is short)
    style_rules = _read(paths.style_rules_md)
    if style_rules.strip() and "- (no rules declared yet)" not in style_rules:
        print("\n---\n## Active style rules\n")
        print(style_rules.strip())

    # Carry threads from the latest chapter brief (## Arrastre)
    arr_ch, arrastre = _latest_arrastre(paths)
    if arrastre:
        print(f"\n---\n## Arrastre (hilos pendientes — brief ch{arr_ch:02d})\n")
        print(arrastre)

    # Latest book-summary snippet (if exists)
    book_sum = _read(paths.book_summary)
    if book_sum:
        # Pull the "What just happened" section if present, else last 400 chars
        m = re.search(
            r"##\s+What just happened\s*\n(.*?)(?=\n##\s|\Z)",
            book_sum, re.DOTALL | re.IGNORECASE,
        )
        if m:
            snippet = m.group(1).strip()
            print("\n---\n## What just happened (last update)\n")
            print(snippet)

    # Dispatcher: detect the lifecycle phase and recommend the next skill.
    phase, nxt = detect_phase(paths, last_written, next_ch)
    blocked = bool(arrastre)

    print("\n---\n## Next step (dispatcher)\n")

    # The Lodestar's banner: phase + next step, readable at a glance.
    _PHASE_LABEL = {
        "grimoire": "① WORLD",
        "setup": "② PLAN · setup",
        "plan": "② PLAN · outline",
        "plan-world": "② PLAN · engine L1-L5",
        "critique-plan": "② PLAN · audit",
        "write": f"③ CHAPTER {next_ch or ''}".rstrip(),
        "done": "✓ BOOK COMPLETE",
    }
    _next_arrow = "—" if not nxt else f"▶  {nxt}"
    print(_box([
        "✦ THE LODESTAR ✦",
        f"{title[:44]}  ·  book {args.book_number}",
        f"phase:  {_PHASE_LABEL.get(phase, phase)}",
        f"next:   {_next_arrow}" + ("   ⚠ blocked" if (blocked and phase == 'write') else ""),
    ]))
    print()

    if phase == "grimoire":
        print("**Phase: GRIMOIRE** — brand-new series: no `grimoire.md` and no `setup.md` yet.")
        print("\nRecommended: **forge-grimoire** — build the series worldbuilding "
              "(magic, factions, geography, history, master mysteries), then "
              "**critique-grimoire** until PASS, BEFORE any per-book setup.")
    elif phase == "setup":
        print("**Phase: SETUP** — no usable `setup.md` yet.")
        print("\nRecommended: **book-setup** — interactive intake to define the book.")
    elif phase == "plan":
        print("**Phase: PLAN** — `setup.md` ready, but `plan/` + initial `canon/` are missing.")
        print("\nRecommended: **plan-book** — regenerate the plan and canon from `setup.md`.")
        print("\n> After plan-book comes **plan-world** (engine layers L1-L5), then "
              "**critique-plan runs ALWAYS** before chapter 1.")
    elif phase == "plan-world":
        print("**Phase: PLAN-WORLD** — plan (L0) ready, but the engine layers "
              "L1-L5 (`plan/layout.md` absent) have not been built.")
        print("\nRecommended: **plan-world** — migrates the store if needed, then "
              "chains plan-space → plan-time → plan-cast → plan-layout → "
              "plan-knowledge (the spatial-temporal contract), each an author gate.")
    elif phase == "critique-plan":
        print("**Phase: CRITIQUE-PLAN** — plan exists but has never been audited.")
        print("\nRecommended: **critique-plan** — mandatory gate before writing chapter 1.")
    elif phase == "write":
        print(f"**Phase: WRITE** — plan is ready. Next is **chapter {next_ch}** (act {next_act}).")
        print(f"\nRecommended: **write-novel** — drives chapter {next_ch} end-to-end "
              "(plan-chapter → write → critique [ALWAYS] → update-canon), then stops for `/clear`.")
        print("\n> ⚠ write-novel is the token-heavy step: run it in a FRESH conversation. "
              "If you just ran plan-book/critique-plan here, `/clear` and re-run resume-act first.")
    else:  # done
        print(f"**Phase: DONE** — all {total_chapters} chapters written.")
        print(f"\nRecommended: refresh book-summary, then `book-setup` for book "
              f"{args.book_number + 1} if the series continues.")

    if blocked and phase == "write":
        print("\n> ⚠ Carry threads exist (see Arrastre above). Resolve them BEFORE the next chapter.")

    # Machine-readable marker for the dispatcher menu in SKILL.md.
    nch = next_ch if (phase == "write" and next_ch) else ""
    print(f"\n<!-- DISPATCH phase={phase} next={nxt or 'none'} "
          f"next_chapter={nch} blocked={'1' if blocked else '0'} -->")

    return 0


if __name__ == "__main__":
    sys.exit(main())
