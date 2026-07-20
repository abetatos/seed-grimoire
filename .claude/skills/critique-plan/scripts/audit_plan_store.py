#!/usr/bin/env python3
"""Store-backed deterministic audit of a book's plan (the L1-L5 deep pass).

The complement of ``audit_plan.py``: where that reads the Markdown plan, this
reads the **world-state store** a migrated book carries (``state/*.json`` +
``state/events`` + ``plan/layout.md``) and finds the failures the dense,
engine-native plan can now surface *cheaply, in the plan* — before a word of
prose:

- **replay integrity** — the whole plan is one valid state (a teleport, a
  backward clock, an off-plan touch or a leak past a cap is already
  unrepresentable; if replay raises, the store is impossible).
- **reveal-ladder honesty** — every truth the book surfaces has a reader cap,
  its caps only rise, they stay on ONE ladder (reader vs. decoy), and none is
  set louder than its ``shadow.md`` ``Reveal cap`` ceiling (the check that
  catches what ``set-reveal-cap`` deliberately does NOT enforce).
- **seed carrier coverage** — every in-book scheduled touch (plant/echo/payoff)
  has a scene in ``plan/layout.md`` that actually carries it (the "sin
  huérfanos" verification, made deterministic).
- **graph reachability** — no scene node is stranded with no travel edge.

Store-gated: on a book with no ``state/`` store (an un-migrated legacy book) it
prints a one-line note and exits 0 — there is nothing engine-native to audit.

Usage:
    python audit_plan_store.py --series-slug <slug> --book-number <n> \\
        [--output notes/_audit-plan-store.md]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib import setup_doc, shadows as shadows_mod
from lib.engine import store
from lib.engine.events import IntegrityError
from lib.engine.story import REVEAL_DOSES, DECOY_DOSES

# A finding is (tier, issue_type, message). Tiers mirror audit_plan.py's markers
# so the critic can lift them straight into critique-plan.md.
MUST, SHOULD = "MUST", "SHOULD"

BACKTICK_RE = re.compile(r"`([a-z0-9][a-z0-9-]+)`")
LAYOUT_CH_RE = re.compile(r"^##\s+Cap\s+(\d+)\b", re.MULTILINE)


# ----- reveal-ladder helpers ---------------------------------------------

def _reveal_level_index(dose: str) -> int | None:
    """Map a store dose to its position on the READER'S ladder (0-3), so a decoy
    dose and its reader-equivalent compare against the same shadow.md ceiling:
    misled≈sensed(1), convinced≈suspected(2), inverted≈confirmed(3)."""
    if dose in REVEAL_DOSES:
        return REVEAL_DOSES.index(dose)
    if dose in DECOY_DOSES:
        return DECOY_DOSES.index(dose) + 1
    return None


def _ladder_of(doses: list[str]) -> str | None:
    reader = all(d in REVEAL_DOSES for d in doses)
    decoy = all(d in DECOY_DOSES for d in doses)
    if reader:
        return "reader"
    if decoy:
        return "decoy"
    return None  # mixed / unknown


# ----- layout parsing -----------------------------------------------------

def layout_chapter_seeds(layout_text: str, seed_ids: set[str]) -> dict[int, set[str]]:
    """{chapter -> the seed ids any scene in it carries}, read from the backtick
    tokens in each ``## Cap N`` block, intersected with the real seed ids so
    non-seed backticks (places, POIs) are ignored."""
    out: dict[int, set[str]] = {}
    heads = list(LAYOUT_CH_RE.finditer(layout_text))
    for i, m in enumerate(heads):
        ch = int(m.group(1))
        end = heads[i + 1].start() if i + 1 < len(heads) else len(layout_text)
        body = layout_text[m.end():end]
        out.setdefault(ch, set()).update(
            tok for tok in BACKTICK_RE.findall(body) if tok in seed_ids
        )
    return out


# ----- checks -------------------------------------------------------------

def check_replay(sd: Path) -> list[tuple]:
    try:
        store.replay_book(sd)
    except IntegrityError as exc:
        return [(MUST, "store-replay",
                 f"the store does not replay to a valid state: {exc}. The plan encodes an "
                 f"impossible world; fix the offending event before anything else.")]
    return []


def check_truth_parity(sd: Path, shadow_truth_ids: set[str]) -> list[tuple]:
    store_ids = set(store.load_truths(sd))
    findings = []
    for tid in sorted(store_ids - shadow_truth_ids):
        findings.append((SHOULD, "truth-parity",
                         f"truth `{tid}` is in the store but not in shadow.md — the legacy "
                         f"source the writer reads is missing it (re-run the shadow.md side of add-truth)."))
    for tid in sorted(shadow_truth_ids - store_ids):
        findings.append((SHOULD, "truth-parity",
                         f"truth `{tid}` is in shadow.md but not in the store — L5 caps can't hang "
                         f"on it (add it to the store)."))
    return findings


def check_reveal_ladder(sd: Path, shadow_truths: list) -> list[tuple]:
    findings = []
    store_truths = store.load_truths(sd)
    by_id = {t.id: t for t in shadow_truths}
    for tid, st in store_truths.items():
        caps = st.reveal_caps  # {chapter: dose}
        sh = by_id.get(tid)
        if not caps:
            # Surfaces in-book if any carrier plants/echoes/pays in-book, or a
            # manual confirm_in is set. An uncapped surfacing truth never moves
            # the reader.
            if sh and (sh.revealed_by or sh.confirm_in is not None):
                findings.append((SHOULD, "reveal-uncapped",
                                 f"truth `{tid}` has carriers/confirm-in but NO reveal cap in the "
                                 f"store — the reader is never moved on it. Lay its ladder with set-reveal-cap."))
            continue
        doses = list(caps.values())
        ladder = _ladder_of(doses)
        if ladder is None:
            findings.append((SHOULD, "reveal-ladder-mixed",
                             f"truth `{tid}` mixes reader and decoy doses ({sorted(set(doses))}) — a "
                             f"truth runs ONE ladder. Pick reader (hidden→confirmed) or decoy (misled→inverted)."))
        # non-decreasing across chapters
        by_ch = sorted(caps.items())
        idxs = [(_reveal_level_index(d), ch) for ch, d in by_ch]
        prev = -1
        for lvl, ch in idxs:
            if lvl is not None and lvl < prev:
                findings.append((SHOULD, "reveal-nonmonotonic",
                                 f"truth `{tid}` caps DROP at ch{ch} — a reveal ladder only rises "
                                 f"(a truth does not un-reveal). Fix the cap sequence {by_ch}."))
                break
            if lvl is not None:
                prev = lvl
        # ceiling: never louder than shadow.md's Reveal cap. The reader and decoy
        # ladders reach the TRUTH differently — a reader dose approaches it
        # directly; a decoy dose (misled/convinced) moves the reader DEEPER into
        # the FALSE belief and reveals nothing of the truth until it *inverts*.
        if sh:
            ceiling = shadows_mod.REVEAL_LEVELS.index(sh.reveal_cap) \
                if sh.reveal_cap in shadows_mod.REVEAL_LEVELS else 3
            if ladder == "decoy":
                # Truth is revealed only at `inverted` (the lie collapses); a decoy
                # that stops at misled/convinced approaches the truth by 0.
                truth_approach = 3 if "inverted" in doses else 0
                if truth_approach > ceiling:
                    findings.append((MUST, "reveal-above-cap",
                                     f"decoy truth `{tid}` INVERTS in-book (the lie collapses, revealing "
                                     f"the truth) but shadow.md's Reveal cap is `{sh.reveal_cap}` — a "
                                     f"later-book payoff spent early. Hold the decoy below `inverted`."))
                else:
                    # No early inversion, but a decoy may still run deeper into the
                    # FALSE belief than shadow.md's declared cap (mapped to the decoy
                    # ladder) — a source drift worth one nudge, not a MUST.
                    decoy_ceiling = ceiling - 1  # sensed→misled(0), suspected→convinced(1), confirmed→inverted(2)
                    depth = max(DECOY_DOSES.index(d) for d in doses if d in DECOY_DOSES)
                    if depth > decoy_ceiling:
                        reached = DECOY_DOSES[depth]
                        allowed = DECOY_DOSES[decoy_ceiling] if 0 <= decoy_ceiling < len(DECOY_DOSES) else "neutral"
                        findings.append((SHOULD, "decoy-ceiling",
                                         f"decoy `{tid}` runs to `{reached}` in the store but shadow.md's "
                                         f"Reveal cap (`{sh.reveal_cap}`) maps to `{allowed}` — align shadow.md's "
                                         f"cap with the intended decoy depth (or ease the store cap back)."))
            else:
                top = max((lvl for lvl, _ in idxs if lvl is not None), default=-1)
                if top > ceiling:
                    findings.append((MUST, "reveal-above-cap",
                                     f"truth `{tid}` is capped to reader-level {top} in the store but "
                                     f"shadow.md's Reveal cap is `{sh.reveal_cap}` ({ceiling}) — this book "
                                     f"spends a reveal it must not (it pays off later). Lower the cap."))
    return findings


def check_seed_carriers(sd: Path, declared: int, layout_text: str | None) -> list[tuple]:
    seeds = store.load_seeds(sd)
    if layout_text is None:
        return [(SHOULD, "layout-missing",
                 "plan/layout.md not found — cannot verify seed carrier coverage (run plan-layout).")]
    carried = layout_chapter_seeds(layout_text, set(seeds))
    findings = []
    for sid, seed in sorted(seeds.items()):
        for kind, chapters in seed.schedule.items():
            for ch in chapters:
                if ch > declared:
                    continue  # a later-book touch is correctly out of range
                if sid not in carried.get(ch, set()):
                    findings.append((SHOULD, "seed-no-carrier",
                                     f"seed `{sid}` schedules a **{kind}** in ch{ch} but no scene in "
                                     f"layout.md's ch{ch} carries it — the writer has no placed home for it."))
    return findings


def check_graph_reachable(sd: Path) -> list[tuple]:
    graph = store.load_graph(sd)
    parents = {p.parent for p in graph.places.values() if p.parent}
    edged = {e.a for e in graph.edges} | {e.b for e in graph.edges}
    findings = []
    for pid, place in sorted(graph.places.items()):
        if pid in edged or pid in parents:
            continue
        if place.kind in ("region",):
            continue  # a bare container is reached by containment, not travel
        findings.append((SHOULD, "graph-isolated",
                         f"place `{pid}` ({place.kind}) has no travel edge and no children — a scene "
                         f"there is unreachable by any itinerary. Connect it or remove it."))
    return findings


# ----- render -------------------------------------------------------------

def render(findings: list[tuple]) -> str:
    musts = [f for f in findings if f[0] == MUST]
    shoulds = [f for f in findings if f[0] == SHOULD]
    out = ["# Store-backed plan audit (L1-L5)\n"]
    out.append(f"Deterministic engine-native checks over the world-state store. "
               f"**{len(musts)} MUST · {len(shoulds)} SHOULD.** The critic lifts these "
               f"into critique-plan.md alongside the qualitative pass.\n")
    for tier, label, items in ((MUST, "MUST fix", musts), (SHOULD, "SHOULD fix", shoulds)):
        out.append(f"## {label}\n")
        if not items:
            out.append("- clean\n")
            continue
        for _t, itype, msg in items:
            out.append(f"- **[{itype}]** {msg}")
        out.append("")
    if not musts and not shoulds:
        out.append("_The store replays clean, every surfacing truth has an honest ladder, "
                   "every in-book seed touch has a carrier scene, and no node is stranded._")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--output", default=None, help="Write report here instead of stdout.")
    args = parser.parse_args(argv)

    paths = book_paths(args.series_slug, args.book_number)
    sd = paths.state_dir
    if not sd.exists() or not paths.shadow_json.exists():
        msg = (f"# Store-backed plan audit (L1-L5)\n\n_No world-state store at {sd} — this book "
               f"is not migrated (legacy Markdown path). Nothing engine-native to audit._\n")
        if args.output:
            Path(args.output).write_text(msg, encoding="utf-8")
            print(f"no store; note written to {args.output}")
        else:
            sys.stdout.write(msg)
        return 0

    declared_n = 0
    if paths.setup_md.exists():
        declared_n = setup_doc.num_chapters(setup_doc.load(paths.setup_md)) or 0

    shadow_text = shadows_mod.load_shadow(paths.shadow_md)
    shadow_truths = shadows_mod.parse_truths(shadow_text)
    shadow_ids = {t.id for t in shadow_truths}

    layout_path = paths.plan_dir / "layout.md"
    layout_text = layout_path.read_text(encoding="utf-8") if layout_path.exists() else None

    findings: list[tuple] = []
    findings += check_replay(sd)
    findings += check_truth_parity(sd, shadow_ids)
    findings += check_reveal_ladder(sd, shadow_truths)
    findings += check_seed_carriers(sd, declared_n, layout_text)
    findings += check_graph_reachable(sd)

    report = render(findings)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"store audit written to {args.output}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
