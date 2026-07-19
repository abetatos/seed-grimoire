"""Per-phase token accounting from a session transcript (Phase-0 instrument).

The IMPROVEMENT-PLAN diagnosis rests on ONE hand-analysed transcript. Before any
architecture moves, this turns that analysis into a deterministic, repeatable
measurement so "cheaper" can be told apart from "cheaper and worse" by numbers,
not by n=1.

It reads a Claude Code session ``.jsonl`` and attributes each assistant
message's token usage to the pipeline phase that produced it — via the message's
``attributionSkill`` (``plan-chapter`` / ``write-chapter`` / ``expand-chapter`` /
``critique-chapter`` / ``update-canon`` / …), bucketing the conductor's own
glue under ``(conductor/other)``. It separates **main-thread** work from
isolated **subagent** (``isSidechain``) work, because the plan's whole thesis is
that the main-thread context is the thing to shrink.

Two headline numbers, matching the plan's "fix two explicit thresholds":

- **peak main-thread context** — the largest window the model drafted inside
  during the session (``input + cache_read + cache_creation``). Past
  ``CONTEXT_CEILING`` the draft is written in the attention-degradation zone.
- **total main-thread output tokens** — the per-chapter cost proxy, checked
  against ``OUTPUT_TARGET``.

Pure functions only (``analyze`` takes an iterable of decoded records); the CLI
in ``scripts/token_report.py`` handles file discovery and printing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# ── Phase-0 thresholds (the two the plan says to fix explicitly) ──────────────
# A model drafting past this main-thread context writes worse (attention rot);
# keep late-act canon growth from pushing the writer into the degradation zone.
CONTEXT_CEILING = 80_000
# Per-chapter main-thread output-token target. The measured n=1 baseline was
# ~548k with everything in the main thread; Movement 1 aims well under this.
OUTPUT_TARGET = 250_000

# attributionSkill is absent on the conductor's own turns (write-novel glue,
# interstitial reasoning) — bucket them together rather than dropping them.
CONDUCTOR = "(conductor/other)"


def context_size(usage: dict) -> int:
    """Total context the model processed for one message.

    The window the model actually reasoned over is the sum of freshly sent
    tokens plus everything served from cache — a cache hit is still context the
    model attends to, so it counts toward the degradation-zone ceiling.
    """
    return (usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0))


@dataclass
class PhaseStat:
    phase: str
    messages: int = 0
    output_tokens: int = 0
    peak_context: int = 0


@dataclass
class Report:
    phases: list[PhaseStat]          # main-thread, sorted by output desc
    peak_context: int                # main-thread only
    total_output: int                # main-thread only
    sidechain_output: int            # isolated subagent work in THIS file
    sidechain_messages: int

    @property
    def over_ceiling(self) -> bool:
        return self.peak_context > CONTEXT_CEILING

    @property
    def over_target(self) -> bool:
        return self.total_output > OUTPUT_TARGET


def analyze(records: Iterable[dict]) -> Report:
    """Aggregate per-phase and headline token stats from decoded transcript records.

    ``records`` is any iterable of parsed JSONL objects (one per line). Only
    ``type == "assistant"`` records carry usage; everything else is ignored.
    Sidechain (subagent) messages are counted separately and never fold into the
    main-thread peak or per-phase table.
    """
    stats: dict[str, PhaseStat] = {}
    peak = 0
    total_out = 0
    side_out = 0
    side_msgs = 0

    for rec in records:
        if rec.get("type") != "assistant":
            continue
        usage = (rec.get("message") or {}).get("usage") or {}
        out = usage.get("output_tokens", 0)

        if rec.get("isSidechain"):
            side_out += out
            side_msgs += 1
            continue

        ctx = context_size(usage)
        peak = max(peak, ctx)
        total_out += out

        phase = rec.get("attributionSkill") or CONDUCTOR
        st = stats.get(phase)
        if st is None:
            st = stats[phase] = PhaseStat(phase)
        st.messages += 1
        st.output_tokens += out
        st.peak_context = max(st.peak_context, ctx)

    phases = sorted(stats.values(), key=lambda s: s.output_tokens, reverse=True)
    return Report(phases, peak, total_out, side_out, side_msgs)
