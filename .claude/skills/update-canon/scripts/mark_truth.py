#!/usr/bin/env python3
"""Update one shadow truth in plan/shadow.md: its reveal status and/or Surfaced log.

Usage:
    python mark_truth.py --series-slug <slug> --book-number <n> \\
        --truth-id <id> --status <new_status> \\
        [--surfaced "chN [sensed]: how the reader was brought, AS WRITTEN"]

    # author a NEW truth (the L5 shadow-thin path) — appends a well-formed
    # SHADOW-TRUTH block to the Master-truths region (before the first ## Act):
    python mark_truth.py --series-slug <slug> --book-number <n> \\
        --truth-id el-cazador-sabe-que-existe --add \\
        --desc "…" --revealed-by "el-cazador-casi-test" --reveal-cap suspected \\
        [--mystery "…"] [--decoy "…"] [--confirm-in 13]

    # reconcile a stale Reveal cap ceiling (e.g. a decoy the L5 ladder runs to
    # `convinced` while shadow.md still says `sensed`):
    python mark_truth.py --series-slug <slug> --book-number <n> \\
        --truth-id el-portaluz --set-cap suspected

Reveal ladder (the READER'S interior state, never how loudly to write):
    hidden → sensed → suspected → confirmed

The new status is REFUSED if it exceeds the truth's ``Reveal cap`` — the loudest
the truth may get in this book (truths that pay off in a later book cap below
``confirmed``). ``--surfaced`` appends one line to the touch-log of how the
reveal actually landed on the page. Both edits are surgical: only the matched
truth's lines change (shadow.md is a NEVER-compress, hand-authored file).

``--add`` authors a truth that migration never produced (a hunter's interior
certainty, a subplot's buried layer). It writes via Python ``open()`` (not the
Edit tool), so the never-compress hook does not block it, and re-running
``migrate_story`` is NOT needed (which would clobber L1-L4 in the store) — pair
it with ``world_tool.py add-truth`` to land the same truth in the engine store.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths
from lib import shadows as shadows_mod


def _build_truth_block(args) -> str:
    """A well-formed ## SHADOW-TRUTH block from the --add fields, field order
    matching the hand-authored records (Decoy/Mystery optional; Status starts
    hidden; empty Surfaced log ready for update-canon)."""
    lines = [f"## SHADOW-TRUTH: {args.truth_id}", f"**Truth:** {args.desc}"]
    if args.decoy:
        lines.append(f"**Decoy:** {args.decoy}")
    if args.mystery:
        lines.append(f"**Mystery:** {args.mystery}")
    lines.append(f"**Revealed-by:** {args.revealed_by}")
    lines.append(f"**Reveal cap:** {args.reveal_cap}")
    if args.confirm_in is not None:
        lines.append(f"**Confirm in:** {args.confirm_in}")
    lines += ["**Status:** hidden", "**Surfaced:**"]
    return "\n".join(lines)


def _insert_truth_block(text: str, block: str) -> str:
    """Place a new truth block in the Master-truths region — just before the
    first ``## Act`` header (or at end of file if there is none), so it joins the
    structured truths rather than being buried among the per-chapter beats."""
    body = block.rstrip("\n") + "\n\n"
    m = shadows_mod.ACT_HEADER_RE.search(text)
    if m:
        return text[: m.start()] + body + text[m.start():]
    return text.rstrip("\n") + "\n\n" + body


def _add_truth(args, paths, text: str) -> int:
    """Author a NEW truth into shadow.md (the L5 shadow-thin path)."""
    for req in ("desc", "revealed_by", "reveal_cap"):
        if not getattr(args, req):
            print(f"ERROR: --add needs --{req.replace('_', '-')}.", file=sys.stderr)
            return 2
    if args.reveal_cap not in shadows_mod.REVEAL_LEVELS:
        print(f"ERROR: invalid reveal cap '{args.reveal_cap}'. Valid: {shadows_mod.REVEAL_LEVELS}",
              file=sys.stderr)
        return 2
    if any(t.id == args.truth_id for t in shadows_mod.parse_truths(text)):
        print(f"ERROR: truth id '{args.truth_id}' already exists in {paths.shadow_md}",
              file=sys.stderr)
        return 2
    new_text = _insert_truth_block(text, _build_truth_block(args))
    paths.shadow_md.write_text(new_text, encoding="utf-8")
    print(f"truth '{args.truth_id}': added (cap {args.reveal_cap}, via {args.revealed_by})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--truth-id", required=True)
    parser.add_argument("--status", required=False,
                        help=f"one of {shadows_mod.REVEAL_LEVELS}")
    parser.add_argument("--surfaced", required=False,
                        help='append one Surfaced line, e.g. "ch8 [sensed]: ..."')
    parser.add_argument("--add", action="store_true",
                        help="author a NEW SHADOW-TRUTH block (needs --desc/--revealed-by/--reveal-cap)")
    parser.add_argument("--desc", help="(--add) the **Truth:** text")
    parser.add_argument("--mystery", help="(--add) §14b master mystery, if any")
    parser.add_argument("--decoy", help="(--add) the FALSE belief, for a misread truth")
    parser.add_argument("--revealed-by", dest="revealed_by",
                        help="(--add) carrier seed ids, comma-separated")
    parser.add_argument("--reveal-cap", dest="reveal_cap",
                        help=f"(--add) ceiling, one of {shadows_mod.REVEAL_LEVELS}")
    parser.add_argument("--confirm-in", dest="confirm_in", type=int,
                        help="(--add) chapter where a seedless truth is confirmed")
    parser.add_argument("--set-cap", dest="set_cap",
                        help=f"rewrite the truth's Reveal cap ceiling, one of {shadows_mod.REVEAL_LEVELS}")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.shadow_md.exists():
        print(f"ERROR: shadow file not found: {paths.shadow_md}", file=sys.stderr)
        return 3
    text = paths.shadow_md.read_text(encoding="utf-8")

    if args.add:
        return _add_truth(args, paths, text)

    if args.set_cap:
        if args.set_cap not in shadows_mod.REVEAL_LEVELS:
            print(f"ERROR: invalid reveal cap '{args.set_cap}'. Valid: {shadows_mod.REVEAL_LEVELS}",
                  file=sys.stderr)
            return 2
        text, found = shadows_mod.set_reveal_cap_in_text(text, args.truth_id, args.set_cap)
        if not found:
            print(f"ERROR: truth id '{args.truth_id}' not found in {paths.shadow_md}", file=sys.stderr)
            return 3
        paths.shadow_md.write_text(text, encoding="utf-8")
        print(f"truth '{args.truth_id}': reveal cap → {args.set_cap}")
        return 0

    if not args.status and not args.surfaced:
        print("ERROR: pass --status and/or --surfaced (nothing to do).", file=sys.stderr)
        return 2
    if args.status and args.status not in shadows_mod.REVEAL_LEVELS:
        print(f"ERROR: invalid status '{args.status}'. Valid: {shadows_mod.REVEAL_LEVELS}",
              file=sys.stderr)
        return 2

    # Cap guardrail: refuse to push a truth past the loudest it may sound here.
    if args.status:
        truth = next((t for t in shadows_mod.parse_truths(text) if t.id == args.truth_id), None)
        if truth is None:
            print(f"ERROR: truth id '{args.truth_id}' not found in {paths.shadow_md}",
                  file=sys.stderr)
            return 3
        idx = shadows_mod._level_index
        if idx(args.status) > idx(truth.reveal_cap):
            print(
                f"ERROR: '{args.status}' exceeds reveal cap '{truth.reveal_cap}' for "
                f"truth '{args.truth_id}'. This truth must not get louder than its cap "
                f"in this book (it pays off later). Cap it, or change Reveal cap in shadow.md "
                f"on purpose.",
                file=sys.stderr,
            )
            return 2

    done = []
    if args.surfaced:
        text, found = shadows_mod.append_surfaced_in_text(text, args.truth_id, args.surfaced)
        if not found:
            print(f"ERROR: truth id '{args.truth_id}' not found in {paths.shadow_md}",
                  file=sys.stderr)
            return 3
        done.append(f"surfaced += \"{args.surfaced}\"")
    if args.status:
        text, found = shadows_mod.update_truth_status_in_text(text, args.truth_id, args.status)
        if not found:
            print(f"ERROR: truth id '{args.truth_id}' not found in {paths.shadow_md}",
                  file=sys.stderr)
            return 3
        done.append(f"status → {args.status}")

    paths.shadow_md.write_text(text, encoding="utf-8")
    print(f"truth '{args.truth_id}': " + "; ".join(done))
    return 0


if __name__ == "__main__":
    sys.exit(main())
