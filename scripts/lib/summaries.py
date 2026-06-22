"""Hierarchical chapter summaries.

The summary system has three levels:
    Level 1 — per-chapter summary  (400-500 words, structured)
    Level 2 — per-act summary      (1500 words, merged from level 1)
    Level 3 — book summary         (rolling, 2000 words)

When the writer is in chapter N, the context builder picks:
    - act-level summaries for distant chapters (older than the detail window)
    - chapter-level summaries for recent past (last RECENT_DETAIL_WINDOW)
    - the continuity SEAM for chapter N-1: its structured summary (end-state +
      carry-forward) plus only its final scene verbatim — NOT the whole chapter.
      The middle of N-1 is already covered by its summary; the writer only needs
      the exact ending state to open from and the live voice to match. This
      replaces inlining all ~9k words of N-1 (the old heaviest line item).

Compression flow (`close-act` skill):
    Every time an act closes (configurable: every 7 chapters), the chapter
    summaries inside the act are merged into one act-level summary, AND the
    individual chapter summaries are kept (small enough that they cost
    nothing) but excluded from the writer's context window.

Seeds and shadow remain visible always — they live in plan/seeds.md and
plan/shadow.md and are never merged into summaries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .paths import BookPaths, summary_chapter_numbers, act_numbers


# Tunable: how many chapters per act for compression purposes
DEFAULT_CHAPTERS_PER_ACT = 7

# Tunable: how many recent chapters keep their individual summary.
# Lowered from 15 → 6: fifteen ~450-word summaries was ~6.75k words by the
# late book — bigger than a full chapter. Six recent in detail + act summaries
# for everything older keeps signal density roughly constant as the book grows.
RECENT_DETAIL_WINDOW = 6

# Tunable: how many recent chapters feed the continuity SEAM.
# One (just the immediately-prior chapter) is enough: the seam is that chapter's
# summary + its final scene verbatim, not its whole text. Chapter N-2 is served
# by its ~450-word summary. Inlining whole chapters here was the single heaviest
# line item in the bundle (~9k words); the seam cuts it to ~1.2k.
FULL_TEXT_WINDOW = 1

# How many words of the previous chapter's tail to carry verbatim in the seam,
# when the chapter has no explicit scene break to cut on. Snapped to a paragraph
# boundary so the excerpt never starts mid-sentence.
SEAM_TAIL_WORDS = 900


@dataclass
class SummaryPlan:
    """Tells the context builder which files to include for chapter N."""

    full_text_chapters: list[int]
    detail_chapters: list[int]
    act_summaries: list[int]


def act_number_for(chapter: int, chapters_per_act: int = DEFAULT_CHAPTERS_PER_ACT) -> int:
    """1-indexed act number for a chapter."""
    return (chapter - 1) // chapters_per_act + 1


def act_range(act: int, chapters_per_act: int = DEFAULT_CHAPTERS_PER_ACT) -> tuple[int, int]:
    """Inclusive [lo, hi] chapter range for an act."""
    lo = (act - 1) * chapters_per_act + 1
    hi = act * chapters_per_act
    return lo, hi


def plan_context(
    paths: BookPaths,
    current_chapter: int,
    chapters_per_act: int = DEFAULT_CHAPTERS_PER_ACT,
) -> SummaryPlan:
    """Decide which summary files to use for the context of `current_chapter`.

    Strategy:
        - Last FULL_TEXT_WINDOW chapters → continuity seam (summary + final scene)
        - Last RECENT_DETAIL_WINDOW chapters (excluding seam) → individual ch-NN.md
        - Older → act-summary if it exists, else fall back to individual ch-NN.md
    """
    written = [n for n in summary_chapter_numbers(paths) if n < current_chapter]
    # Full-text uses the chapters/ files, not summaries — those are taken from
    # the chapters directory in the context builder. Here we list intended numbers.
    full_text = written[-FULL_TEXT_WINDOW:] if written else []
    full_text_set = set(full_text)

    # Recent detail: chapters in the window that are NOT in full_text
    recent_window = written[-(FULL_TEXT_WINDOW + RECENT_DETAIL_WINDOW):]
    detail = [n for n in recent_window if n not in full_text_set]

    # Distant chapters: anything older than the recent window
    distant = [n for n in written if n < (recent_window[0] if recent_window else current_chapter)]

    # For distant chapters, group by act and use the act summary if it exists.
    available_acts = set(act_numbers(paths))
    distant_acts = set()
    covered_by_act: set[int] = set()
    for n in distant:
        a = act_number_for(n, chapters_per_act)
        if a in available_acts:
            distant_acts.add(a)
            covered_by_act.add(n)

    # Distant chapters NOT covered by an act summary fall back to individual summaries
    fallback_detail = [n for n in distant if n not in covered_by_act]

    return SummaryPlan(
        full_text_chapters=full_text,
        detail_chapters=sorted(set(detail + fallback_detail)),
        act_summaries=sorted(distant_acts),
    )


def load_chapter_summary(paths: BookPaths, n: int) -> str:
    p = paths.chapter_summary(n)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def load_act_summary(paths: BookPaths, a: int) -> str:
    p = paths.act_summary(a)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def load_chapter_text(paths: BookPaths, n: int) -> str:
    p = paths.chapter_file(n)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def render_summaries(paths: BookPaths, plan: SummaryPlan) -> str:
    """Build the 'story so far' block from the chosen summary files."""
    parts: list[str] = ["## Story so far\n"]

    if plan.act_summaries:
        parts.append("### Earlier acts (compressed)\n")
        for a in plan.act_summaries:
            parts.append(load_act_summary(paths, a))
            parts.append("")

    if plan.detail_chapters:
        parts.append("### Recent chapter summaries\n")
        for n in plan.detail_chapters:
            parts.append(load_chapter_summary(paths, n))
            parts.append("")

    if not (plan.act_summaries or plan.detail_chapters):
        parts.append("(This is the first chapter or early enough that no prior summaries exist yet.)\n")

    return "\n".join(parts).rstrip() + "\n"


# Explicit scene separators, if a chapter ever uses them. Current prose does
# not, so the seam falls back to a word-count tail — but if a `* * *` style
# break is present we cut cleanly on the last one.
_SCENE_BREAK_RE = re.compile(
    r"^[ \t]*(?:\*[ \t]*\*[ \t]*\*|\*{3,}|—[ \t]*—[ \t]*—|···|⁂|·[ \t]·[ \t]·)[ \t]*$",
    re.MULTILINE,
)
# expand-chapter wraps inserted prose in visible banner lines; strip the banners
# (keep the prose between them) so the seam reads as clean text.
_EXPAND_MARKER_RE = re.compile(
    r"^.*(?:INICIO EXPAND|FIN EXPAND|▼▼▼|▲▲▲).*$\n?", re.MULTILINE
)
_HEADING_RE = re.compile(r"^#\s.*\n", re.MULTILINE)


def extract_last_scene(text: str, target_words: int = SEAM_TAIL_WORDS) -> str:
    """Return the tail of a chapter to carry verbatim in the seam.

    Strategy, in order:
      1. Drop the chapter heading and any expand-banner lines.
      2. If explicit scene breaks exist, take everything after the last one
         (when that tail is a real scene, not a one-line stub).
      3. Otherwise take the last ``target_words`` words, snapped back to a
         paragraph boundary so the excerpt never begins mid-sentence.
    """
    if not text:
        return ""
    text = _HEADING_RE.sub("", text, count=1)
    text = _EXPAND_MARKER_RE.sub("", text).strip()
    if not text:
        return ""

    breaks = list(_SCENE_BREAK_RE.finditer(text))
    if breaks:
        tail = text[breaks[-1].end():].strip()
        if len(tail.split()) >= 150:
            return tail

    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chosen: list[str] = []
    count = 0
    for p in reversed(paras):
        chosen.insert(0, p)
        count += len(p.split())
        if count >= target_words:
            break
    return "\n\n".join(chosen).strip()


def render_seam(paths: BookPaths, chapter_nums: list[int]) -> str:
    """Build the continuity SEAM for the previous chapter.

    The seam is the previous chapter's structured summary (which already holds
    where/when, what happened, subtext, seeds, and the carry-forward end-state)
    plus only its FINAL SCENE verbatim (for exact opening state + live voice to
    match). This deliberately omits the middle of the chapter — the summary
    already covers it — which is what cuts ~9k words down to ~1.2k.
    """
    if not chapter_nums:
        return "## Continuity seam\n\n(This is the first chapter — no seam.)\n"
    n = chapter_nums[-1]  # the immediately-prior chapter
    parts = [
        f"## Continuity seam — chapter {n}\n",
        f"> Open the new chapter from the END-STATE below; match the VOICE from "
        f"the verbatim final scene. The middle of chapter {n} lives in its "
        f"summary — pull anything else from canon/seeds or `search-corpus`.\n",
    ]
    summary = load_chapter_summary(paths, n).strip()
    if summary:
        parts.append(f"### Chapter {n} — structured summary (end-state + carry-forward)\n")
        parts.append(summary)
        parts.append("")
    scene = extract_last_scene(load_chapter_text(paths, n))
    if scene:
        parts.append(f"### Chapter {n} — final scene, verbatim (voice + exact opening state)\n")
        parts.append(scene)
        parts.append("")
    if not (summary or scene):
        parts.append(f"(Chapter {n} has neither a summary nor prose on disk yet.)\n")
    return "\n".join(parts).rstrip() + "\n"
