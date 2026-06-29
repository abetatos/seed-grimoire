#!/usr/bin/env python3
"""Constructive worklist generator for a world grimoire.

This is the **constructive** complement of `audit_grimoire.py`. Where the
audit is adversarial (pass/fail, "is the grimoire ready?"), this scan answers
a different question for the `forge-grimoire` skill: **what is left to build,
in what order, and where is the grimoire under-scoped for a trilogy?**

It does NOT reimplement parsing — it imports the proven helpers from
`audit_grimoire.py` and layers three things on top:

  1. A per-section fill state, including a `partial` state that the binary
     audit cannot express: a section whose header is present and has content,
     but still carries work-pending markers ([POR CONSTRUIR], [EN CURSO],
     [PARCIAL], [POR DECIDIR]) or `___` placeholders.
  2. Trilogy scope checks for §14 (loaded guns), §14b (master mysteries) and
     §9 (cast): row count vs. a breadth target, not just "> 0", and — for the
     cast — fixed-and-surviving arcs vs. a per-book floor, not just full-arc
     bullets. These are the levers for the common failure of seeding/casting a
     trilogy as if it were a standalone.
  3. A single dependency-ordered worklist (MUST -> SHOULD -> CONSIDER) the
     skill walks top to bottom.

Stdlib only (project rule). Usage mirrors the audit:

    python scan_grimoire.py --series-slug <slug>
    python scan_grimoire.py --series-slug <slug> --output <path>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
# Reuse the audit's parsing helpers instead of duplicating them.
sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / "critique-grimoire" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from audit_grimoire import (  # noqa: E402
    SECTION_SPECS,
    _book_tokens,
    _has_real_content,
    check_characters,
    check_loaded_guns,
    check_master_mysteries,
    check_open_decisions,
    find_section_body,
)
from lib.paths import OUTPUT_ROOT  # noqa: E402


# ---- trilogy scope targets ----------------------------------------------
# A trilogy needs breadth here or the per-book plans inherit a thin seed bank
# (the "pocas seeds para la trilogía" failure). Aligned with plan-book's
# "aim for MANY" guidance and critique-grimoire's thresholds.
LOADED_GUN_TARGET = 8     # §14 — at least this many loaded guns for a trilogy
MYSTERY_TARGET = 10       # §14b — protagonist nature + each antagonist agenda +
#                           each institution's real function + each subplot + secret history

# Inline tags that mark a section as still under construction even when it has prose.
PENDING_TAG_RE = re.compile(
    r"\[(POR CONSTRUIR|EN CURSO|PARCIAL|POR DECIDIR|POR AFINAR|POR FIJAR|TODO)\]",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"(?:^|\s)_{3,}(?:\s|$)", re.MULTILINE)

# Human-readable section labels + the dependency walk order. Earlier sections
# constrain later ones, so the skill fills them in this order.
SECTION_ORDER: list[tuple[str, str]] = [
    ("idea_one_sentence", "§1 La idea en una frase"),
    ("two_layers", "§2 La regla de las dos capas"),
    ("magic_how", "§3 La magia — cómo funciona"),
    ("laws", "§4 Las leyes del sistema"),
    ("scaled_or_inverted", "§5 Escalado o invertido"),
    ("limitations", "§6 Limitaciones por personaje"),
    ("factions", "§7 Castas / facciones"),
    ("subplots", "§8 Subtramas"),
    ("characters", "§9 Personajes"),
    ("history", "§10 La historia / cronología"),
    ("geography", "§11 Geografía"),
    ("structure", "§12 Estructura de la trilogía"),
    ("clock", "§13 El reloj — ¿por qué AHORA?"),
    ("mandatory_plantings", "§14 Siembras obligatorias"),
    ("master_mysteries", "§14b Misterios maestros"),
    ("open_decisions", "§15/§16 Decisiones abiertas"),
]
LABELS = dict(SECTION_ORDER)
ANCHORS = dict(SECTION_SPECS)


def _pending_markers(body: str) -> list[str]:
    """Distinct work-pending markers found in a section body."""
    tags = {m.group(1).upper() for m in PENDING_TAG_RE.finditer(body or "")}
    if PLACEHOLDER_RE.search(body or ""):
        tags.add("___ (placeholder)")
    return sorted(tags)


def scan(grimoire_text: str) -> dict:
    """Build a prioritized worklist. Each item: tier, section, reason, hint."""
    must: list[dict] = []
    should: list[dict] = []
    consider: list[dict] = []

    bodies: dict[str, str] = {}
    for key, _label in SECTION_ORDER:
        _head, body = find_section_body(grimoire_text, ANCHORS[key])
        bodies[key] = body or ""

    for key, label in SECTION_ORDER:
        head, body = find_section_body(grimoire_text, ANCHORS[key])
        if head is None:
            must.append({"section": label, "reason": "sección AUSENTE", "hint": "crear desde la plantilla"})
            continue
        if not _has_real_content(body):
            must.append({"section": label, "reason": "cabecera presente pero VACÍA", "hint": "rellenar de cero"})
            continue
        markers = _pending_markers(body)
        if markers:
            should.append({
                "section": label,
                "reason": "marcadores de trabajo pendiente: " + ", ".join(markers),
                "hint": "cerrar lo marcado",
            })

    # §14 — loaded guns: completeness + trilogy breadth.
    lg = check_loaded_guns(bodies["mandatory_plantings"])
    if lg["count"] == 0:
        must.append({"section": "§14 Siembras obligatorias", "reason": "tabla vacía", "hint": "la trama por libro no tendría obligaciones que realizar"})
    else:
        if lg["incomplete"]:
            must.append({"section": "§14 Siembras obligatorias", "reason": f"filas sin libro de siembra/pago: {lg['incomplete']}", "hint": "completar Siembra-en / Paga-en"})
        if lg["not_in_book_i"]:
            should.append({"section": "§14 Siembras obligatorias", "reason": f"siembras que no aparecen en el Libro I: {lg['not_in_book_i']}", "hint": "regla: cada siembra aparece ≥1 vez en el Libro I"})
        if lg["count"] < LOADED_GUN_TARGET:
            should.append({
                "section": "§14 Siembras obligatorias",
                "reason": f"INFRA-ESCALA para trilogía: {lg['count']} siembras (objetivo ≥{LOADED_GUN_TARGET})",
                "hint": "añadir filas con ≥1 pago por libro hasta cubrir la escala",
            })

    # §9 — cast must survive the whole series, not just have full-arc bullets.
    # An arc tagged [PROPUESTA] is a placeholder; one spent in Book I doesn't
    # carry the back half. Floor scales with book count: >= max(2, N-1) fixed
    # arcs surviving into the later books.
    num_books = max(
        len(_book_tokens(bodies["structure"]) |
            _book_tokens(bodies["mandatory_plantings"]) |
            _book_tokens(bodies["master_mysteries"])),
        1,
    )
    rec_arcs = max(2, num_books - 1)
    ch = check_characters(bodies["characters"], bodies["subplots"])
    if ch["proposed_arcs"]:
        should.append({
            "section": "§9 Personajes",
            "reason": f"arcos completos pero SIN FIJAR ([PROPUESTA]/draft): {ch['proposed_arcs']}",
            "hint": "cerrar a [FIJO] el want/need/lie/wound de cada uno (el plan hereda el hueco si no)",
        })
    if ch["surviving_fixed_arcs"] < rec_arcs:
        extra = f"; arcos fijados gastados en el Libro I: {ch['lost_in_book_i']}" if ch["lost_in_book_i"] else ""
        should.append({
            "section": "§9 Personajes",
            "reason": (
                f"solo {ch['surviving_fixed_arcs']} arco(s) fijado(s) sobreviven a la "
                f"primera mitad para una serie de {num_books} libros (suelo ≥{rec_arcs}){extra}"
            ),
            "hint": "fijar/añadir un deuteragonista que cargue los libros II-III; dar arco propio a los pivotes emocionales (no dispositivos de una línea)",
        })

    # §14b — master mysteries: completeness + trilogy breadth.
    mm = check_master_mysteries(bodies["master_mysteries"])
    if mm["count"] == 0:
        must.append({"section": "§14b Misterios maestros", "reason": "tabla vacía", "hint": "critique-plan no podría comprobar la cobertura de shadow"})
    else:
        if mm["incomplete"]:
            must.append({"section": "§14b Misterios maestros", "reason": f"filas sin verdad-real / libro de intro: {mm['incomplete']}", "hint": "completar verdad real e Introducido-en"})
        if mm["count"] < MYSTERY_TARGET:
            should.append({
                "section": "§14b Misterios maestros",
                "reason": f"INFRA-ESCALA para trilogía: {mm['count']} misterios (objetivo ≥{MYSTERY_TARGET})",
                "hint": "cubrir: naturaleza del prota · agenda de CADA antagonista · función real de CADA institución · CADA subtrama · historia secreta",
            })

    # Open decisions — any unresolved gating is MUST.
    od = check_open_decisions(bodies["open_decisions"])
    for d in od["unresolved_gating"]:
        must.append({"section": "§15/§16 Decisiones abiertas", "reason": f"decisión GATING sin resolver: {d}", "hint": "resolver antes de empezar a escribir"})

    return {"must": must, "should": should, "consider": consider, "counts": {"loaded_guns": lg["count"], "mysteries": mm["count"]}}


def render(report: dict) -> str:
    lines = ["# Grimoire forge worklist (constructivo)\n"]
    lines.append(
        f"§14 siembras: **{report['counts']['loaded_guns']}** (objetivo ≥{LOADED_GUN_TARGET}) · "
        f"§14b misterios: **{report['counts']['mysteries']}** (objetivo ≥{MYSTERY_TARGET})\n"
    )

    total = sum(len(report[t]) for t in ("must", "should", "consider"))
    if total == 0:
        lines.append("Sin huecos detectados. El grimorio está listo para `critique-grimoire`.\n")
        return "\n".join(lines)

    for tier, title in (("must", "## MUST — bloquea empezar"), ("should", "## SHOULD — debilita el libro"), ("consider", "## CONSIDER")):
        items = report[tier]
        if not items:
            continue
        lines.append(title + "\n")
        for it in items:
            lines.append(f"- **{it['section']}** — {it['reason']} → _{it['hint']}_")
        lines.append("")

    lines.append("> Recórrelas en este orden (las primeras secciones condicionan a las siguientes).")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--grimoire-path", default=None, help="Override path to grimoire.md")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    grimoire_path = Path(args.grimoire_path) if args.grimoire_path else (OUTPUT_ROOT / args.series_slug / "grimoire.md")
    if not grimoire_path.exists():
        print(f"ERROR: grimoire not found at {grimoire_path}", file=sys.stderr)
        print("Tip: forge-grimoire bootstraps it by copying references/grimoire-template.md to that path.", file=sys.stderr)
        return 2

    report = scan(grimoire_path.read_text(encoding="utf-8"))
    rendered = render(report)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"worklist written to {out_path}")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
