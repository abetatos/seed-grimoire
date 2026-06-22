#!/usr/bin/env python3
"""Close-act helper — orchestrates the session-end disk sync.

Wraps `prepare_act.py` (chapter summaries → act summary) and additionally:

  - Ensures `notes/voice.md`, `style-rules.md`, `open-questions.md`,
    `session-handoff.md` exist.
  - Resets `session-handoff.md` to a clean skeleton with the act
    number filled in, so the agent's qualitative pass fills it.
  - Reports what's pending for the agent to consolidate.

The qualitative work (voice stabilization, handoff write) is the
agent's job following the SKILL.md.

Usage:
    python close_act.py --series-slug <slug> --book-number <n> --act <a>
    python close_act.py --series-slug <slug> --book-number <n> --act <a> --force
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths, summary_chapter_numbers
from lib import notes_files, summaries as sum_mod


HANDOFF_SKELETON = """# Session handoff — Act {act} closed {date}

> Overwritten at each `close-act`. Read first thing by `resume-act`.
> Captures what the next session needs to continue without loss of
> context. **Agent fills this in following the close-act SKILL.md.**

## Estado al cierre

- Capítulo escrito hasta: ch {last_ch}
- Acto cerrado: {act}
- Próximo: acto {next_act} / capítulo {next_ch}

## Voz consolidada (síntesis de voice.md después del acto {act})

> TODO: el agente sintetiza aquí las observaciones acumuladas en
> voice.md durante este acto en 3-6 reglas estables por POV. Las
> entradas individuales de voice.md siguen estando para consulta;
> esta sección es la versión cocida.

## Hilos abiertos para el acto siguiente

> TODO: agente lista los pendientes de open-questions.md que entran
> a la sesión siguiente, en orden de prioridad.

## Decisiones de esta sesión

> TODO: agente lista decisiones de chat tomadas durante el acto que
> afectan al acto siguiente. Una línea por decisión, con su origen.

## Notas para resume-act

> TODO: lo que la próxima sesión debe leer EN PRIMER LUGAR. Si hay
> algo más importante que cualquier archivo del bundle estándar,
> ponerlo aquí.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--act", type=int, required=True)
    parser.add_argument(
        "--chapters-per-act",
        type=int,
        default=sum_mod.DEFAULT_CHAPTERS_PER_ACT,
    )
    parser.add_argument("--force", action="store_true", help="Re-run even if act summary exists")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.book_root.exists():
        print(f"ERROR: book directory not found: {paths.book_root}", file=sys.stderr)
        return 2

    paths.ensure_dirs()
    notes_files.ensure(paths)

    # Step 1: prepare the act-summary bundle (chapter summaries → act summary).
    prepare_act_path = Path(__file__).resolve().parent / "prepare_act.py"
    if not prepare_act_path.exists():
        print(f"ERROR: prepare_act.py helper not found at {prepare_act_path}", file=sys.stderr)
        return 2

    print("Step 1 — act-summary bundle preparation")
    cmd = [
        "python3", str(prepare_act_path),
        "--series-slug", args.series_slug,
        "--book-number", str(args.book_number),
        "--act", str(args.act),
        "--chapters-per-act", str(args.chapters_per_act),
    ]
    if args.force:
        cmd.append("--force")
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print(f"prepare_act returned {rc}", file=sys.stderr)
        return rc

    # Step 2: reset session-handoff.md to clean skeleton
    lo, hi = sum_mod.act_range(args.act, args.chapters_per_act)
    written = summary_chapter_numbers(paths)
    last_ch = max((n for n in written if n <= hi), default=hi)

    handoff = HANDOFF_SKELETON.format(
        act=args.act,
        date=notes_files.today_stamp(),
        last_ch=last_ch,
        next_act=args.act + 1,
        next_ch=last_ch + 1,
    )
    paths.session_handoff_md.write_text(handoff, encoding="utf-8")

    print()
    print(f"Step 2 — session-handoff.md reset for act {args.act}")
    print(f"  {paths.session_handoff_md}")
    print(f"  Agent must fill the four TODO sections per close-act SKILL.md.")

    # Step 3: report what the agent needs to do
    print()
    print(f"Next: agent runs the qualitative pass per close-act SKILL.md.")
    print(f"  1. Fill summaries/act-{args.act:02d}.md (~1500 words).")
    print(f"  2. Consolidate voice.md observations for act {args.act}.")
    print(f"  3. Write session-handoff.md TODO sections.")
    print(f"  4. Print '✓ Act {args.act} closed. STRONGLY recommended: /clear before act {args.act + 1}.'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
