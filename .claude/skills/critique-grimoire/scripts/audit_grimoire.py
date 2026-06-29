#!/usr/bin/env python3
"""Deterministic structural audit of a world grimoire.

Operates on `output/<series>/grimoire.md`. Returns a Markdown report that
critique-grimoire reads before doing the qualitative adversarial pass.

The bar is intentionally adversarial: the grimoire is the foundation of
everything downstream, so this audit prefers false positives (flag a
gap) over false negatives (miss a gap).

Sections expected (matched flexibly by regex):
  1. Idea en una frase / one-sentence idea
  2. Two layers (anti-confusion)
  3. Magic
  4. Laws / rules
  5. Scaled or inverted system declaration
  6. Limitations
  7. Castes / factions
  8. Subplots
  9. Characters
 10. History / chronology
 11. Geography
 12. Structure (book or trilogy)
 13. Clock — why now
 14. Mandatory plantings (loaded guns)
 15. Open decisions

Plus deep checks:
  - magic: source, costs >= 2, hard limits >= 3, thematic question OR
    inverted-system declared
  - characters: protagonist + antagonist with want/need/lie/wound; arcs are
    classed FIXED vs [PROPUESTA]/draft and (for a fixed arc) surviving vs spent
    in Book I, scanning §9 AND the subplots section (the de-facto deuteragonist
    often lives there) — an N-book series wants >= max(2, N-1) fixed arcs that
    survive into the back half
  - subplots: count, each with >= 3 contact points and distinct theme
  - geography: >= 5 named places
  - history: >= 3 enumerated events
  - structure: each book's clímax uses an active-decision verb
  - trilogy: each book has a distinct motor
  - open decisions: each marked Gating: yes/no; any gating unresolved
    is MUST-fix
  - series scope (floors scale with book count): the grimoire only holds
    the trans-series spine, so for an N-book series the audit expects
    >= max(6, 3N) loaded guns, >= max(5, 2N) master mysteries,
    >= max(2, N) subplots, >= max(1, N-1) decoys, and >= max(1, N-1)
    *trans-book threads* (guns that sow in an early book and pay in a
    later one) + bridging mysteries (intro early / confirm late). These
    are SHOULD-fix floors — the qualitative pass decides if a shortfall
    is load-bearing.
  - decoys: deliberate misdirection (false system, hollow saviour, a
    fronting institution) is counted across the gun/mystery tables and
    the factions/characters/two-layer prose.

Usage:
    python audit_grimoire.py --series-slug <slug>
    python audit_grimoire.py --series-slug <slug> --output <path>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import OUTPUT_ROOT


# ---- section anchors ----------------------------------------------------
# Each section spec: required substring(s) in header (case-insensitive).
SECTION_SPECS: list[tuple[str, list[str]]] = [
    ("idea_one_sentence", ["idea en una frase", "idea en una sola frase", "one-sentence idea", "the idea in one"]),
    ("two_layers", ["dos capas", "two layers", "anti-confusión", "anti-confusion"]),
    ("magic_how", ["la magia", "the magic", "magic system", "sistema mágico", "sistema de magia"]),
    ("laws", ["leyes", "laws", "rules of"]),
    ("scaled_or_inverted", ["sistema escalado", "escalado o invertido", "scaled or inverted", "sistema invertido", "system is inverted", "construido al revés", "construido al reves"]),
    ("limitations", ["limitaciones", "limitations"]),
    ("factions", ["castas", "facciones", "factions", "castes", "orders"]),
    ("subplots", ["subtramas", "subtrama", "subplots"]),
    ("characters", ["personajes", "characters"]),
    ("history", ["historia", "cronología", "cronologia", "history", "chronology"]),
    ("geography", ["geografía", "geografia", "geography"]),
    ("structure", ["estructura", "structure"]),
    ("clock", ["el reloj", "the clock", "why now", "por qué ahora", "porque ahora"]),
    ("mandatory_plantings", ["siembras obligatorias", "loaded guns", "mandatory plantings", "exigencias de siembra"]),
    ("master_mysteries", ["misterios maestros", "master mysteries"]),
    ("open_decisions", ["decisiones aún abiertas", "decisiones abiertas", "open decisions"]),
]


def find_section_body(text: str, anchors: list[str]) -> tuple[str, str] | tuple[None, None]:
    """Find a section by any of the anchor substrings in an H1/H2 header.

    Returns (header_line, body) or (None, None) if not found.
    """
    headers = list(re.finditer(r"^(#{1,3})\s+(.+?)\s*$", text, re.MULTILINE))
    for i, m in enumerate(headers):
        # Drop bracketed status tags ([FIJO], [PARCIAL], [FIJO en estructura …])
        # before anchor matching, so a status word can't masquerade as a
        # section header (e.g. "### Antagonista [FIJO en estructura]" must not
        # capture the "estructura" / structure anchor).
        title = re.sub(r"\[[^\]]*\]", "", m.group(2)).strip().lower()
        if any(a in title for a in anchors):
            start = m.end()
            # End at the next header of same or higher level
            level = len(m.group(1))
            end = len(text)
            for n in headers[i + 1:]:
                if len(n.group(1)) <= level:
                    end = n.start()
                    break
            return m.group(0), text[start:end].strip()
    return None, None


def _content_length(body: str) -> int:
    """Return non-quote, non-bullet content character count."""
    # Strip TODO blockquotes
    body = re.sub(r"^\s*>\s*TODO.*$", "", body, flags=re.MULTILINE)
    # Strip empty markdown
    body = re.sub(r"^\s*[-*]\s*___+\s*$", "", body, flags=re.MULTILINE)  # template placeholders ___
    body = re.sub(r"^\s*___+\s*$", "", body, flags=re.MULTILINE)
    return len(body.strip())


def _has_real_content(body: str) -> bool:
    """A section is 'filled' if it has > 80 chars of non-placeholder text."""
    if not body:
        return False
    return _content_length(body) > 80


# ---- specific deep checks -----------------------------------------------

def check_magic(body: str) -> dict:
    """Source + Mechanic + Costs (>=2) + Hard limits (>=3).

    Tries the template format first (explicit `**Source:**` labels);
    falls back to free-prose detection so an organic grimoire (v4-style)
    still passes when the content is there.
    """
    result = {
        "source_present": False,
        "mechanic_present": False,
        "costs_count": 0,
        "limits_count": 0,
        "thematic_question_present": False,
    }
    if not body:
        return result

    # ---- Source (explicit label OR prose fallback) ----
    m = re.search(r"(?:\*\*)?\s*(?:Source|Fuente|Origen)\s*[:\-]\s*\*?\*?\s*(.+)", body, re.IGNORECASE)
    if m and len(m.group(1).strip()) > 15 and not m.group(1).strip().startswith("("):
        result["source_present"] = True
    else:
        # Prose fallback: section is non-trivial AND mentions a source-like
        # concept (aura, viene de, es luz, comes from, source).
        if len(body) > 200 and re.search(
            r"\baura\b|viene de|es (?:luz|magia)|comes from|source is|nace de|brota de|surge de",
            body, re.IGNORECASE,
        ):
            result["source_present"] = True

    # ---- Mechanic (explicit label OR prose fallback) ----
    if re.search(r"(?:\*\*)?\s*(?:Mechanic|Mecánica|Mecanica|Mechanism)", body, re.IGNORECASE):
        result["mechanic_present"] = True
    else:
        # Prose fallback: section describes HOW the magic operates — either an
        # access verb or the named operations of an organic system (irradiar,
        # heredar, absorber/transferir/re-emitir, the frequency×amplitude bite).
        if re.search(
            r"se accede|se manifiesta|se irradia|se canaliza|step by step|paso a paso|"
            r"c[oó]mo funciona|funciona as[ií]|irradia|se hereda|hereda del|absorbe|"
            r"transfiere|re-?emite|mordida|dos ejes|frecuencia|amplitud|toma(?:r)? (?:el )?aura",
            body, re.IGNORECASE,
        ):
            result["mechanic_present"] = True

    # ---- Costs ----
    cost_section = re.search(
        r"(?:#{2,4}\s*(?:Costes?|Costs?)\s*(?:\([^)]*\))?|(?:\*\*)?(?:Costes?|Costs?)(?:\*\*)?)\s*[:\-]?\s*(.*?)(?=\n#{2,4}|\n\*\*[A-Z]|\Z)",
        body, re.IGNORECASE | re.DOTALL,
    )
    if cost_section:
        bullets = re.findall(r"^\s*[-*]\s+(.+)$", cost_section.group(1), re.MULTILINE)
        real = [b for b in bullets if not b.strip().startswith("(") and len(b.strip()) > 15]
        result["costs_count"] = len(real)

    # Prose fallback: count distinct cost concepts mentioned in prose.
    # Each match counts at most once.
    if result["costs_count"] < 2:
        prose_cost_concepts = {
            "calor": r"\bcalor\b|\bheat\b|fuga térmica|burn out|cocerse",
            "social": r"social\s+cost|coste\s+social|stigma|estigma|marca social",
            "emocional": r"emocional|emotional|grief|paranoia|numbness",
            "identidad": r"identidad|identity|memoria|recuerdo|self",
            "fisico_otro": r"agotamiento|exhaustion|aging|envejec|scarring",
            "material": r"material(?:\s+cost)?|consumed|consume|resource(?:\s+is)?\s+scarce",
        }
        prose_count = sum(
            1 for pat in prose_cost_concepts.values()
            if re.search(pat, body, re.IGNORECASE)
        )
        if prose_count > result["costs_count"]:
            result["costs_count"] = prose_count

    # ---- Hard limits ----
    limits_section = re.search(
        r"(?:#{2,4}\s*(?:Hard limits|Límites duros|Limites duros|Limits)\s*(?:\([^)]*\))?|(?:\*\*)?(?:Hard limits|Límites duros|Limites duros|Limits)(?:\*\*)?)\s*[:\-]?\s*(.*?)(?=\n#{2,4}|\n\*\*[A-Z]|\Z)",
        body, re.IGNORECASE | re.DOTALL,
    )
    if limits_section:
        bullets = re.findall(r"^\s*[-*]\s+(.+)$", limits_section.group(1), re.MULTILINE)
        real = [b for b in bullets if not b.strip().startswith("(") and len(b.strip()) > 15]
        result["limits_count"] = len(real)

    if result["limits_count"] < 3:
        # Prose fallback: count "no puede / cannot / never" patterns + named
        # categories of limit.
        prose_limit_concepts = {
            "no_puede": r"no puede(?:\s+ser)?|cannot|can never|never can|nunca puede",
            "alcance": r"\balcance\b|inverse square|1/r|range falls|distance",
            "tiempo": r"duraci[oó]n|cannot persist|past a duration|duration",
            "transfer": r"cannot be transferred|no se transfiere|cannot share",
            "complementario": r"complementari|cancel|anula|annul",
            "aura_fija": r"aura fija|fixed aura|cannot train|no se entrena|cannot grow|no crece",
            "calor_force": r"calor\b.*\bfuerza|forcing leads to|exceeding.*cooks|fuga térmica",
        }
        prose_count = sum(
            1 for pat in prose_limit_concepts.values()
            if re.search(pat, body, re.IGNORECASE)
        )
        if prose_count > result["limits_count"]:
            result["limits_count"] = prose_count

    # ---- Thematic question ----
    if re.search(r"thematic question|pregunta moral|pregunta temática|pregunta tematica|thematic role|moral question", body, re.IGNORECASE):
        m = re.search(
            r"(?:thematic question|pregunta moral|pregunta temática|pregunta tematica|thematic role|moral question)[^:\n]*[:\-]?\s*(?:\*\*)?\s*(.+)",
            body, re.IGNORECASE,
        )
        if m and len(m.group(1).strip()) > 10 and "___" not in m.group(1):
            result["thematic_question_present"] = True
    elif re.search(r"\?\s*$", body.strip(), re.MULTILINE):
        # Free-prose: section ends with or contains an explicit ethical question.
        if re.search(
            r"¿(?:vale|debe|merece|puede|hay|quién|qué)|\bwho (?:lives|pays)\b|who deserves",
            body, re.IGNORECASE,
        ):
            result["thematic_question_present"] = True

    return result


def check_scaled_or_inverted(body: str) -> dict:
    """At least one of: three tiers declared, or inverted-system declared."""
    if not body:
        return {"scaled_tiers_declared": False, "inverted_system_declared": False}

    body_lower = body.lower()
    has_common = bool(re.search(r"common|común|comun", body_lower))
    has_skilled = bool(re.search(r"skilled|hábil|habil", body_lower))
    has_apex = bool(re.search(r"apex|cumbre|tope", body_lower))
    scaled_tiers = has_common and has_skilled and has_apex

    # Inverted system: any of the keywords in the body is enough — the
    # fact we found the section by its header ("invertido / al revés")
    # tells us the author is declaring the inversion. We just check the
    # body backs it up with the concept of erosion.
    inverted = bool(re.search(r"erosi[oó]n|erosion|desgaste|al rev[eé]s|invertido|inverted", body_lower))

    return {
        "scaled_tiers_declared": scaled_tiers,
        "inverted_system_declared": inverted,
    }


# An arc is "proposed" (not yet fixed) when it carries a draft tag. The whole
# point of the trilogy-cast check: a back-half arc declared [PROPUESTA] is not a
# commitment, it's a placeholder, and the series rests on it.
_PROPOSED_RE = re.compile(
    r"propuesta|propuesto|borrador|\bdraft\b|por\s+fijar|por\s+decidir|proposed|\btbd\b",
    re.IGNORECASE,
)
# A fixed arc that is nonetheless *spent in Book I* does not survive into the
# back half. Heuristic: a loss/death/consumption verb within a short span of a
# "Libro I" mention inside the entity's own section.
_LOST_BOOK_I_RE = re.compile(
    r"(?:pierde|p[ée]rdida|muere|cae\b|consumid\w*|agrisad\w*|sacrificad\w*|"
    r"destruid\w*|se\s+lo\s+lleva)[^.\n]{0,90}\bLibro\s+I\b(?!I)",
    re.IGNORECASE,
)


def _arc_full(sec: str) -> bool:
    """All four arc fields (want+need+lie+wound) present in a block."""
    wnt = bool(re.search(r"\*\*\s*Want|\*Want|\bwant\s*[:\-]", sec, re.IGNORECASE))
    need = bool(re.search(r"\*\*\s*Need|\*Need|\bneed\s*[:\-]|\bnecesidad\s*[:\-]", sec, re.IGNORECASE))
    lie = bool(re.search(r"\*\*\s*Lie|\*Lie|\blie\s*[:\-]|\bmentira\s*[:\-]", sec, re.IGNORECASE))
    wound = bool(re.search(r"\*\*\s*Wound|\*Wound|\bwound\s*[:\-]|\bherida\s*[:\-]", sec, re.IGNORECASE))
    return wnt and need and lie and wound


def _arc_proposed(head: str, sec: str) -> bool:
    """The arc is a draft, not a commitment."""
    # Explicit "arco [PROPUESTA]" / "**Arco [PROPUESTA]:**" anywhere in the block.
    if re.search(r"arco\s*\[?\s*(?:" + _PROPOSED_RE.pattern + r")", head + "\n" + sec, re.IGNORECASE):
        return True
    # The entity's own status tags are all draft (no [FIJO] among them).
    tags = re.findall(r"\[([^\]]+)\]", head)
    if tags and all(_PROPOSED_RE.search(t) and not re.search(r"fijo", t, re.IGNORECASE) for t in tags):
        return True
    return False


def _name_from_head(head: str) -> str:
    # Cut at the first status tag / role separator — handles nested brackets
    # like "[FIJO en función · arco [PROPUESTA] · nombre por fijar]".
    name = re.split(r"\s*[\[—:]|\s+-\s+", head, 1)[0]
    return re.sub(r"\*+", "", name).strip() or "(sin nombre)"


def _subplot_arc_entities(body: str) -> list[tuple[str, str]]:
    """Arc-bearing figures declared inside the subplots section (the de-facto
    deuteragonist often lives here, not in §9). Returns (name, block) pairs.

    Top-level figure bullets are `- **Name:** ...`; their arc sub-bullets are
    indented, so splitting on a non-indented `- **` isolates each figure."""
    if not body:
        return []
    out: list[tuple[str, str]] = []
    for part in re.split(r"^- \*\*", body, flags=re.MULTILINE)[1:]:
        m = re.match(r"(.+?)\*\*", part)
        name = (m.group(1).rstrip(": ").strip() if m else "(sin nombre)")
        out.append((name, part))
    return out


def check_characters(body: str, subplots_body: str = "") -> dict:
    """Count principals with want/need/lie/wound markers, plus antagonist.

    Beyond raw presence, the trilogy cast check distinguishes arcs that are
    *fixed* (a commitment) from *proposed* (a placeholder), and estimates which
    fixed arcs *survive* Book I — a 3-book spine resting on one surviving fixed
    arc is the most likely mid-Book-II rewrite. Arc-bearing figures declared in
    the subplots section (a common home for the deuteragonist) are counted too."""
    if not body and not subplots_body:
        return {
            "principal_count": 0, "with_full_arc": 0, "with_fixed_full_arc": 0,
            "surviving_fixed_arcs": 0, "proposed_arcs": [], "lost_in_book_i": [],
            "has_antagonist_with_thesis": False,
        }

    # (name, head, block) for every arc-bearing entity, from §9 and §8.
    entities: list[tuple[str, str, str]] = []
    for sec in re.split(r"^###\s+", body or "", flags=re.MULTILINE)[1:]:
        head = sec.split("\n", 1)[0]
        if re.search(r"^\s*\(.*\)\s*$", head):  # placeholder "(name)"
            continue
        entities.append((_name_from_head(head), head, sec))
    for name, block in _subplot_arc_entities(subplots_body):
        entities.append((name, block.split("\n", 1)[0], block))

    # principal_count counts §9 sections only (back-compat); subplot figures are
    # extra cast, not "principals" in the §9 sense.
    principal_count = len(re.findall(r"^###\s+(?!\s*\()", body or "", flags=re.MULTILINE))

    with_full_arc = 0
    with_fixed_full_arc = 0
    surviving_fixed_arcs = 0
    proposed_arcs: list[str] = []
    lost_in_book_i: list[str] = []
    has_antagonist_with_thesis = False

    for name, head, sec in entities:
        if _arc_full(sec):
            with_full_arc += 1
            proposed = _arc_proposed(head, sec)
            if proposed:
                proposed_arcs.append(name)
            else:
                with_fixed_full_arc += 1
                if _LOST_BOOK_I_RE.search(sec):
                    lost_in_book_i.append(name)
                else:
                    surviving_fixed_arcs += 1
        if re.search(r"antagonist|antagonista|cara de la orden|inquisidor", head, re.IGNORECASE):
            tesis = re.search(
                r"(?:\*\*?[^*\n]*\bTesis\b[^*\n]*\*?\*?|(?:^|\s)Tesis\b[^:\n]*)[:\-]?\s*(.{20,})",
                sec, re.IGNORECASE | re.MULTILINE,
            )
            if tesis and len(tesis.group(1).strip()) > 15:
                has_antagonist_with_thesis = True

    return {
        "principal_count": principal_count,
        "with_full_arc": with_full_arc,
        "with_fixed_full_arc": with_fixed_full_arc,
        "surviving_fixed_arcs": surviving_fixed_arcs,
        "proposed_arcs": proposed_arcs,
        "lost_in_book_i": lost_in_book_i,
        "has_antagonist_with_thesis": has_antagonist_with_thesis,
    }


def check_subplots(body: str) -> dict:
    """Count subplots and how many have contact points / distinct theme.

    Tries the template H3 format first; falls back to prose detection if
    the grimoire declares subplots inline (e.g., v4 §8 "La subtrama: la
    revolución verde").
    """
    if not body:
        return {"count": 0, "with_contact_points": 0, "with_distinct_theme": 0}

    sections = re.split(r"^###\s+", body, flags=re.MULTILINE)
    count = 0
    with_contact_points = 0
    with_distinct_theme = 0
    for sec in sections[1:]:
        head = sec.split("\n", 1)[0]
        if re.search(r"^\s*\(.*\)\s*$", head):
            continue
        count += 1
        contacts = re.findall(r"punto de contacto|toque \d|touch(?:point)?", sec, re.IGNORECASE)
        if len(contacts) >= 3:
            with_contact_points += 1
        theme = re.search(r"(?:tema|theme)[^:\n]*[:\-]\s*(?:\*\*)?\s*(.+)", sec, re.IGNORECASE)
        if theme and len(theme.group(1).strip()) > 10:
            with_distinct_theme += 1

    # Prose fallback: if no H3 found but the section declares a subtrama
    # inline (e.g. §8 "la revolución verde"), detect it and its touch-points.
    if count == 0:
        # Each "subtrama" / "subplot" mention as a separate concept.
        primary = re.search(
            r"(?:la|una|única|el)\s+subtrama|\bsubtrama\b|primary\s+subplot|"
            r"main\s+subplot|revoluci[oó]n\s+verde",
            body, re.IGNORECASE,
        )
        secondary = re.search(
            r"subtrama\s+secundaria|segunda\s+subtrama|secondary\s+subplot|subplot\s+b\b",
            body, re.IGNORECASE,
        )
        if primary:
            count += 1
        if secondary:
            count += 1
        # Contact points: explicit label (singular OR plural), or an
        # enumerated list keyed to the books ("1. **Libro I:** ...").
        contacts = re.findall(
            r"toque\s*\d|puntos?\s+de\s+contacto|touch\s*\d", body, re.IGNORECASE,
        )
        book_keyed = re.findall(
            r"^\s*\d+\.\s+\*\*\s*(?:Libro|Book)\b", body, re.IGNORECASE | re.MULTILINE,
        )
        if count and (len(contacts) >= 3 or len(book_keyed) >= 3 or
                      re.search(r"≥\s*3\s+puntos?\s+de\s+contacto", body)):
            with_contact_points = 1
        if count and re.search(r"\btema\b|\btheme\b", body, re.IGNORECASE):
            with_distinct_theme = 1

    return {
        "count": count,
        "with_contact_points": with_contact_points,
        "with_distinct_theme": with_distinct_theme,
    }


def check_history(body: str) -> dict:
    """Count enumerated historical events."""
    if not body:
        return {"event_count": 0}
    enumerated = re.findall(r"^\s*\d+\.\s+\*\*", body, re.MULTILINE)
    if not enumerated:
        # Maybe bullets with bold
        enumerated = re.findall(r"^\s*-\s+\*\*[^*]+\*\*", body, re.MULTILINE)
    return {"event_count": len(enumerated)}


def check_geography(body: str) -> dict:
    """Count named places — H3 sub-headers OR bullets with bold lead."""
    if not body:
        return {"places_count": 0}
    h3 = re.findall(r"^###\s+(.+)$", body, re.MULTILINE)
    # Place bullets come two ways: "- **Name:**" (colon inside bold, template)
    # and "- **Name** [tag] — ..." (bold lead, no colon — the organic format).
    bullets = re.findall(r"^\s*-\s+\*\*([^*]+):\*\*", body, re.MULTILINE)
    bullets += re.findall(r"^\s*-\s+\*\*([^*:]+?)\*\*", body, re.MULTILINE)
    names = []
    for h in h3:
        n = h.strip()
        if n.lower() in ("place 1", "place 2", "place 3", "macro political map", "travel", "places"):
            continue
        # Skip placeholder names
        if re.match(r"^(?:Place|Lugar)\s+name", n, re.IGNORECASE):
            continue
        names.append(n)
    for b in bullets:
        n = b.strip()
        # Skip purely structural bullets like "Macro político"
        if n.lower() in ("type", "sensory anchor", "function in plot", "who lives there", "political stance"):
            continue
        # Skip placeholder labels and status-tag bullets ("[POR CONSTRUIR]")
        if re.match(r"^(?:Place|Lugar)\s+\d+", n, re.IGNORECASE):
            continue
        if n.startswith("["):
            continue
        names.append(n)
    return {"places_count": len(set(names))}


def check_structure(body: str) -> dict:
    """For trilogies: each book has a motor + climax. Climax should be active."""
    if not body:
        return {"book_blocks": 0, "passive_climaxes": [], "missing_motor": []}

    # Find every book block — supports both ### Libro I header AND inline
    # **Libro I — title** at the start of a paragraph. The inline pattern
    # tolerates italic spans inside the bold ("**Libro I — *El Apagado*.**").
    h3_books = list(re.finditer(
        r"^###\s+(Libro|Book)\s+([IVX0-9]+)[\s\S]*?(?=\n###\s+(?:Libro|Book)|\Z)",
        body, re.IGNORECASE | re.MULTILINE,
    ))
    inline_books = list(re.finditer(
        r"\*\*\s*(Libro|Book)\s+([IVX0-9]+)[^\n]*?\*\*[\s\S]*?(?=\n\*\*\s*(?:Libro|Book)\s+[IVX0-9]+[^\n]*?\*\*|\Z)",
        body, re.IGNORECASE,
    ))

    matches: list[tuple[str, str]] = []
    for m in h3_books or inline_books:
        book_label = f"Libro {m.group(2)}"
        matches.append((book_label, m.group(0)))

    book_count = len(matches)
    passive_climaxes = []
    missing_motor = []

    # Decision verbs (active climax). Includes the choice-verbs fantasy
    # climaxes actually use (niega/negarse, elige/elección, entrega, vacía-y-
    # devuelve, sacrifica, renuncia, comete-deliberadamente).
    decision_verbs_re = re.compile(
        r"\b(decide|decid[ie]r|elige|elegir|elecci[oó]n|escoge|escoger|rechaza|rechazar|"
        r"acepta|aceptar|niega|negar|niegue|entrega|entregar|abandona|abandonar|renuncia|"
        r"sacrifica|sacrificar|vac[ií]a|vaciar|devuelve|devolver|comete|cometer|deliberad|"
        r"chooses|decides|refuses|accepts|surrenders|gives up)",
        re.IGNORECASE,
    )
    # Author may tag the climax as active explicitly: "Clímax (activo)".
    active_marker_re = re.compile(r"\bactiv[oa]\b|\bactive\b", re.IGNORECASE)

    for label, sec in matches:
        # Motor — explicit field OR keyword in body
        if not (re.search(r"\*\*\s*Motor", sec, re.IGNORECASE) or
                re.search(r"\bmotor\b", sec, re.IGNORECASE)):
            missing_motor.append(label)
        # Climax / cierre — bold OR italic label, else inline. Capture the
        # label itself (group 0) so an explicit "(activo)" tag counts.
        climax_text = ""
        climax_field = re.search(
            r"[*_]{1,2}[^*_\n]*\b(?:Cl[ií]max|Climax|Cierre)\b[^*_\n]*[*_]{1,2}[:\-]?\s*"
            r"(?:.{20,600}?)(?=\n\s*\n|\n[*_]{2}|\Z)",
            sec, re.IGNORECASE | re.DOTALL,
        )
        if climax_field:
            climax_text = climax_field.group(0)
        else:
            climax_inline = re.findall(
                r"(?:cl[ií]max|cierre)[\s\S]{0,400}", sec, re.IGNORECASE,
            )
            if climax_inline:
                climax_text = " ".join(climax_inline)
        if climax_text and not (
            active_marker_re.search(climax_text) or decision_verbs_re.search(climax_text)
        ):
            passive_climaxes.append(label)

    return {
        "book_blocks": book_count,
        "passive_climaxes": passive_climaxes,
        "missing_motor": missing_motor,
    }


def check_open_decisions(body: str) -> dict:
    if not body:
        return {"unresolved_gating": [], "total_items": 0}

    items = re.split(r"\n\s*\d+\.\s+", "\n" + body)
    unresolved_gating: list[str] = []
    total = 0
    for item in items[1:]:
        total += 1
        is_gating = bool(re.search(r"gating:\s*(s[iíy]|yes|true)", item, re.IGNORECASE))
        is_resolved = bool(re.search(r"resuelto|decidido|resolved|decided|\bdecisi[oó]n:", item, re.IGNORECASE))
        if is_gating and not is_resolved:
            first_line = item.split("\n", 1)[0].strip()
            first_line = re.sub(r"\*+\s*$", "", first_line).rstrip(".:").strip()
            unresolved_gating.append(first_line[:120])
    return {"unresolved_gating": unresolved_gating, "total_items": total}


# ---- main ---------------------------------------------------------------

def _md_table(body: str) -> tuple[list[str], list[list[str]]]:
    """Return (header_cells_lowercased, data_rows) of the first markdown table.

    The header is kept so callers can locate a column by name instead of by a
    fixed position — a grimoire table may carry extra columns (a leading row
    number, a trailing category/status) that would otherwise shift the
    sow/payoff/intro/confirm cells the checks read.
    """
    all_rows: list[list[str]] = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        all_rows.append(cells)
    if not all_rows:
        return [], []
    header = [c.lower() for c in all_rows[0]]
    return header, all_rows[1:]


def _col_index(header: list[str], keywords: list[str], default: int | None = None) -> int | None:
    """First header column whose (lowercased) title contains any keyword."""
    for i, h in enumerate(header):
        if any(k in h for k in keywords):
            return i
    return default


_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7}


def _book_tokens(text: str) -> set[int]:
    """Distinct book numbers named as 'Libro N' / 'Book N' in a blob."""
    found: set[int] = set()
    for m in re.finditer(r"\b(?:Libro|Book)\s+([IVX]+|\d+)\b", text or "", re.IGNORECASE):
        tok = m.group(1)
        found.add(int(tok) if tok.isdigit() else _ROMAN.get(tok.lower(), 0))
    found.discard(0)
    return found


def check_loaded_guns(body: str) -> dict:
    """§14: each loaded gun needs a name, a sow-book and a payoff-book, and by
    the grimoire's own rule must appear at least once in Book I.

    Also counts *trans-book* guns (sow-book earlier than payoff-book) — these
    are the threads that stitch the trilogy together; a spine where every gun
    sows and pays inside one book has no inter-book tension."""
    header, rows = _md_table(body)
    # Locate columns by name (tolerates extra leading #/trailing status cols);
    # fall back to the template's positional layout (name, what, sow, pay).
    name_i = _col_index(header, ["siembra", "loaded gun", "gun", "elemento"], 0)
    sow_i = _col_index(header, ["siembra en", "sembrar", "sow"], 2)
    pay_i = _col_index(header, ["paga", "payoff", "pay"], 3)
    incomplete, not_in_book_i, cross_book = [], [], 0
    for r in rows:
        name = re.sub(r"\*\*", "", r[name_i]).strip() if len(r) > name_i else "(empty)"
        if len(r) <= max(sow_i, pay_i) or not r[sow_i].strip() or not r[pay_i].strip():
            incomplete.append(name)
            continue
        sow, pay = _book_tokens(r[sow_i]), _book_tokens(r[pay_i])
        if not re.search(r"\bLibro\s+I\b", r[sow_i]) and 1 not in sow:
            not_in_book_i.append(name)
        if sow and pay and min(pay) > min(sow):
            cross_book += 1
    return {
        "count": len(rows),
        "incomplete": incomplete,
        "not_in_book_i": not_in_book_i,
        "cross_book": cross_book,
    }


def check_master_mysteries(body: str) -> dict:
    """§14b: each master mystery needs a name, a real truth, an intro-book and a
    confirm-book, so the plan can be held to carrying it as a shadow truth.

    Counts *bridging* mysteries (introduced in one book, confirmed in a later
    one) — the slow reveals that reward a reader across the whole series."""
    header, rows = _md_table(body)
    # Columns by name (tolerates a leading # and trailing category column);
    # fall back to the template's layout (name, truth, intro, confirm).
    name_i = _col_index(header, ["misterio", "mystery"], 0)
    truth_i = _col_index(header, ["verdad", "truth", "real"], 1)
    intro_i = _col_index(header, ["introduc", "intro"], 2)
    confirm_i = _col_index(header, ["confirm"], 3)
    incomplete, bridging = [], 0
    for r in rows:
        name = re.sub(r"\*\*", "", r[name_i]).strip() if len(r) > name_i else "(empty)"
        if len(r) <= max(truth_i, intro_i) or not r[truth_i].strip() or not r[intro_i].strip():
            incomplete.append(name)
            continue
        intro = _book_tokens(r[intro_i])
        confirm = _book_tokens(r[confirm_i]) if len(r) > confirm_i else set()
        if intro and confirm and min(confirm) > min(intro):
            bridging += 1
    return {"count": len(rows), "incomplete": incomplete, "bridging": bridging}


# Decoy markers — the elements that lie to the reader on purpose (a false
# system, a hollow saviour, an institution that fronts for the real parasite).
_DECOY_RE = re.compile(
    r"señuelo|se[nñ]uelo|decoy|blanco falso|falso(?:\s+\w+)?|"
    r"mentira central|propaganda|teatro del|fachada|tapadera|"
    r"cartel|m[aá]scara|fingid|aparenta|pantalla\b",
    re.IGNORECASE,
)


def check_decoys(section_bodies: dict) -> dict:
    """Count declared decoys across the loaded-gun / master-mystery tables and
    the factions / characters / two-layer prose. A trilogy that misdirects the
    reader needs them named on purpose, not discovered mid-draft."""
    names: list[str] = []
    for key in ("mandatory_plantings", "master_mysteries"):
        header, rows = _md_table(section_bodies.get(key, ""))
        # Use the element's NAME column, never a leading row-number column.
        name_i = _col_index(header, ["siembra", "misterio", "gun", "mystery", "elemento"], 0)
        for r in rows:
            if len(r) > name_i and _DECOY_RE.search(" ".join(r)):
                names.append(re.sub(r"\*\*", "", r[name_i]).strip())
    for key in ("factions", "characters", "two_layers"):
        for line in section_bodies.get(key, "").splitlines():
            # Only count a prose decoy when it names an element in bold, so a
            # passing mention of "falso"/"propaganda" doesn't inflate the count.
            m = re.search(r"\*\*([^*]+)\*\*", line)
            if m and _DECOY_RE.search(line):
                label = m.group(1).strip().rstrip(".:—- ").strip()
                # Skip prose fragments captured as a bold span (a whole
                # sentence, or a pure row number) — keep proper element names.
                if label and len(label) <= 35 and not label.isdigit():
                    names.append(label)
    uniq = list(dict.fromkeys(n for n in names if n))
    return {"count": len(uniq), "names": uniq[:8]}


def audit(grimoire_text: str) -> dict:
    out: dict = {"sections": {}, "deep": {}}

    section_bodies: dict[str, str] = {}
    for key, anchors in SECTION_SPECS:
        head, body = find_section_body(grimoire_text, anchors)
        present = head is not None
        filled = _has_real_content(body) if present else False
        out["sections"][key] = {"present": present, "filled": filled}
        if present:
            section_bodies[key] = body or ""

    # Magic content can be spread across §Magic + §Laws + §Limitations +
    # §Scaled-or-inverted. Concatenate them all and run check_magic on the
    # combined body so prose-style grimoires get fair credit.
    magic_sources = [
        section_bodies.get(k, "") for k in
        ("magic_how", "laws", "limitations", "scaled_or_inverted")
    ]
    combined_magic = "\n\n".join(s for s in magic_sources if s)
    if combined_magic:
        out["deep"]["magic"] = check_magic(combined_magic)

    if section_bodies.get("scaled_or_inverted"):
        out["deep"]["scaled_or_inverted"] = check_scaled_or_inverted(section_bodies["scaled_or_inverted"])
    else:
        out["deep"]["scaled_or_inverted"] = {"scaled_tiers_declared": False, "inverted_system_declared": False}

    if section_bodies.get("characters"):
        out["deep"]["characters"] = check_characters(
            section_bodies["characters"], section_bodies.get("subplots", "")
        )
    if section_bodies.get("subplots"):
        out["deep"]["subplots"] = check_subplots(section_bodies["subplots"])
    if section_bodies.get("history"):
        out["deep"]["history"] = check_history(section_bodies["history"])
    if section_bodies.get("geography"):
        out["deep"]["geography"] = check_geography(section_bodies["geography"])
    if section_bodies.get("structure"):
        out["deep"]["structure"] = check_structure(section_bodies["structure"])
    if section_bodies.get("open_decisions"):
        out["deep"]["open_decisions"] = check_open_decisions(section_bodies["open_decisions"])
    if section_bodies.get("mandatory_plantings"):
        out["deep"]["loaded_guns"] = check_loaded_guns(section_bodies["mandatory_plantings"])
    if section_bodies.get("master_mysteries"):
        out["deep"]["master_mysteries"] = check_master_mysteries(section_bodies["master_mysteries"])
    out["deep"]["decoys"] = check_decoys(section_bodies)

    # ---- series scope: how big is the spine SUPPOSED to be? --------------
    # The grimoire only carries the trans-series spine (the big guns + master
    # mysteries that cross books), so the floors scale with the number of
    # books, not chapters. num_books is read from the structure block, with a
    # fallback to the distinct "Libro N" tokens named in §12/§14/§14b.
    book_blocks = out["deep"].get("structure", {}).get("book_blocks", 0)
    named_books = (
        _book_tokens(section_bodies.get("structure", ""))
        | _book_tokens(section_bodies.get("mandatory_plantings", ""))
        | _book_tokens(section_bodies.get("master_mysteries", ""))
    )
    num_books = max(book_blocks, len(named_books), 1)
    out["series"] = {
        "num_books": num_books,
        "rec_loaded_guns": max(6, 3 * num_books),
        "rec_master_mysteries": max(5, 2 * num_books),
        "rec_subplots": max(2, num_books),
        "rec_fixed_arcs": max(2, num_books - 1),
        "rec_decoys": max(1, num_books - 1),
        "rec_cross_book_guns": max(1, num_books - 1),
        "rec_bridging_mysteries": max(1, num_books - 1),
    }

    return out


def render(report: dict) -> str:
    lines: list[str] = ["# Grimoire audit (deterministic)\n"]

    sc = report.get("series", {})
    if sc:
        lines.append("## Series scope (spine floors scale with book count)\n")
        lines.append(f"- Books in series: **{sc['num_books']}**")
        lines.append(
            f"- Recommended trans-series spine for this length: "
            f"≥ {sc['rec_loaded_guns']} loaded guns, "
            f"≥ {sc['rec_master_mysteries']} master mysteries, "
            f"≥ {sc['rec_subplots']} subplots, "
            f"≥ {sc['rec_decoys']} decoys, "
            f"≥ {sc['rec_cross_book_guns']} trans-book threads."
        )
        lines.append(
            "- These are floors, not targets: a richer spine is welcome. "
            "Shortfalls below are SHOULD-fix (the qualitative pass decides if "
            "a gap is load-bearing enough to block)."
        )
        lines.append("")

    lines.append("## Sections present\n")
    missing: list[str] = []
    empty: list[str] = []
    for key, info in report["sections"].items():
        label = key.replace("_", " ")
        if not info["present"]:
            lines.append(f"- **MISSING:** {label}")
            missing.append(label)
        elif not info["filled"]:
            lines.append(f"- **EMPTY** (header present, no content): {label}")
            empty.append(label)
        else:
            lines.append(f"- ok: {label}")
    lines.append("")

    if "magic" in report["deep"]:
        m = report["deep"]["magic"]
        lines.append("## Magic system depth\n")
        lines.append(f"- Source declared and filled: **{'yes' if m['source_present'] else 'NO'}**")
        lines.append(f"- Mechanic declared: **{'yes' if m['mechanic_present'] else 'NO'}**")
        lines.append(f"- Costs count: **{m['costs_count']}** (need ≥ 2)")
        lines.append(f"- Hard limits count: **{m['limits_count']}** (need ≥ 3)")
        lines.append(f"- Thematic question declared: **{'yes' if m['thematic_question_present'] else 'NO'}**")
        lines.append("")

    if "scaled_or_inverted" in report["deep"]:
        s = report["deep"]["scaled_or_inverted"]
        lines.append("## System arc shape\n")
        lines.append(f"- Three escalation tiers declared: **{'yes' if s['scaled_tiers_declared'] else 'no'}**")
        lines.append(f"- Inverted system explicitly declared: **{'yes' if s['inverted_system_declared'] else 'no'}**")
        if not (s["scaled_tiers_declared"] or s["inverted_system_declared"]):
            lines.append("- **MUST FIX:** declare one. Otherwise the magic has no climax ceiling and the audit cannot distinguish 'missing apex' from 'deliberate erosion arc'.")
        lines.append("")

    if "characters" in report["deep"]:
        c = report["deep"]["characters"]
        rec_arcs = report.get("series", {}).get("rec_fixed_arcs", 2)
        nb = report.get("series", {}).get("num_books", 1)
        lines.append("## Characters\n")
        lines.append(f"- Principals declared (§9): **{c['principal_count']}**")
        lines.append(
            f"- Arcs with all four bullets (want+need+lie+wound), §9 + subplots: "
            f"**{c['with_full_arc']}**"
        )
        lines.append(
            f"- …of those, **FIXED** (not tagged [PROPUESTA]/draft): "
            f"**{c.get('with_fixed_full_arc', 0)}** "
            f"(floor for a {nb}-book series: ≥ {rec_arcs})"
        )
        lines.append(
            f"- …fixed AND surviving past Book I: **{c.get('surviving_fixed_arcs', 0)}** "
            f"(floor: ≥ {rec_arcs})"
        )
        lines.append(f"- Antagonist with stated thesis: **{'yes' if c['has_antagonist_with_thesis'] else 'NO'}**")
        if c["principal_count"] < 2:
            lines.append("- **MUST FIX:** < 2 principals declared.")
        if c["with_full_arc"] < 2:
            lines.append("- **SHOULD FIX:** < 2 arcs have the four bullets filled at all.")
        if c.get("with_fixed_full_arc", 0) < rec_arcs:
            lines.append(
                f"- **SHOULD FIX:** only {c.get('with_fixed_full_arc', 0)} **fixed** full "
                f"arc(s) for a {nb}-book series (floor ≥ {rec_arcs}). The back half rests on "
                "arcs that are still placeholders — close them to [FIJO] before book-setup."
            )
        if c.get("proposed_arcs"):
            lines.append(
                f"- **SHOULD FIX — arcs present but NOT fixed ([PROPUESTA]/draft):** "
                f"{c['proposed_arcs']}. A trilogy cannot be checked against an un-fixed "
                "deuteragonist/emotional-pivot arc; the plan would inherit the gap."
            )
        if c.get("surviving_fixed_arcs", 0) < rec_arcs:
            extra = (
                f" — fixed arcs spent in Book I: {c['lost_in_book_i']}"
                if c.get("lost_in_book_i") else ""
            )
            lines.append(
                f"- **SHOULD FIX:** only {c.get('surviving_fixed_arcs', 0)} fixed arc(s) "
                f"survive into the back half (floor ≥ {rec_arcs}){extra}. With one living "
                "designed arc entering Book II, the cast is the trilogy's thinnest spine."
            )
        if not c["has_antagonist_with_thesis"]:
            lines.append("- **SHOULD FIX:** antagonist has no stated thesis — risks being stock evil.")
        lines.append("")

    if "subplots" in report["deep"]:
        s = report["deep"]["subplots"]
        lines.append("## Subplots\n")
        lines.append(f"- Subplots declared: **{s['count']}**")
        lines.append(f"- With ≥ 3 contact points with main: **{s['with_contact_points']}**")
        lines.append(f"- With explicit distinct theme: **{s['with_distinct_theme']}**")
        rec_sub = report.get("series", {}).get("rec_subplots", 1)
        if s["count"] < 1:
            lines.append("- **MUST FIX:** at least 1 subplot required for epic fantasy.")
        elif s["count"] < rec_sub:
            lines.append(
                f"- **SHOULD FIX:** {s['count']} subplot(s) for a {report['series']['num_books']}-book "
                f"series — aim for ≥ {rec_sub}, each with a theme distinct from the main and ≥ 3 "
                "contact points. One running subplot across a trilogy reads thin."
            )
        lines.append("")

    if "history" in report["deep"]:
        h = report["deep"]["history"]
        lines.append("## Historical weight\n")
        lines.append(f"- Enumerated past events: **{h['event_count']}** (need ≥ 3)")
        if h["event_count"] < 3:
            lines.append("- **SHOULD FIX:** historical weight is thin.")
        lines.append("")

    if "geography" in report["deep"]:
        g = report["deep"]["geography"]
        lines.append("## Geography\n")
        lines.append(f"- Named places: **{g['places_count']}** (need ≥ 5 for epic)")
        if g["places_count"] < 5:
            lines.append("- **SHOULD FIX:** worldbuilding will feel sparse.")
        lines.append("")

    if "structure" in report["deep"]:
        st = report["deep"]["structure"]
        lines.append("## Structure / trilogy motors\n")
        lines.append(f"- Book blocks declared: **{st['book_blocks']}**")
        if st["missing_motor"]:
            lines.append(f"- **MUST FIX:** books without a Motor: {st['missing_motor']}")
        if st["passive_climaxes"]:
            lines.append(f"- **MUST FIX:** climaxes without an active-decision verb (decide / elige / rechaza / acepta / chooses ...): {st['passive_climaxes']}")
        lines.append("")

    if "open_decisions" in report["deep"]:
        od = report["deep"]["open_decisions"]
        lines.append("## Open decisions\n")
        lines.append(f"- Total decisions tracked: **{od['total_items']}**")
        if od["unresolved_gating"]:
            lines.append("- **MUST FIX — gating decisions still open:**")
            for d in od["unresolved_gating"]:
                lines.append(f"  - {d}")
        else:
            lines.append("- No unresolved gating decisions.")
        lines.append("")

    if "loaded_guns" in report["deep"]:
        lg = report["deep"]["loaded_guns"]
        rec_g = report.get("series", {}).get("rec_loaded_guns", 6)
        rec_x = report.get("series", {}).get("rec_cross_book_guns", 1)
        lines.append("## §14 Loaded guns\n")
        lines.append(f"- Declared: **{lg['count']}** (floor for this series: ≥ {rec_g})")
        lines.append(f"- Trans-book threads (sow earlier than payoff): **{lg['cross_book']}** (floor: ≥ {rec_x})")
        if lg["count"] == 0:
            lines.append("- **MUST FIX:** no loaded guns declared — the per-book plan has nothing concrete to realize.")
        elif lg["count"] < rec_g:
            lines.append(
                f"- **SHOULD FIX:** {lg['count']} loaded guns is thin for a {report['series']['num_books']}-book "
                f"spine — aim for ≥ {rec_g}. Add concrete plantable objects/rituals/props (each with a sow- and "
                "payoff-book) so the writer has guns to fire, not just themes."
            )
        if lg["cross_book"] < rec_x:
            lines.append(
                f"- **SHOULD FIX:** only {lg['cross_book']} gun bridges books — a trilogy wants ≥ {rec_x} that "
                "sow in an early book and pay in a later one, or each book feels self-contained and the series has no pull."
            )
        if lg["incomplete"]:
            lines.append(f"- **MUST FIX — rows missing sow/payoff book:** {lg['incomplete']}")
        if lg["not_in_book_i"]:
            lines.append(f"- **MUST FIX — loaded guns that never appear in Book I** (breaks the §14 rule): {lg['not_in_book_i']}")
        lines.append("")

    if "master_mysteries" in report["deep"]:
        mm = report["deep"]["master_mysteries"]
        rec_m = report.get("series", {}).get("rec_master_mysteries", 5)
        rec_b = report.get("series", {}).get("rec_bridging_mysteries", 1)
        lines.append("## §14b Master mysteries\n")
        lines.append(f"- Declared: **{mm['count']}** (floor for this series: ≥ {rec_m})")
        lines.append(f"- Bridging (intro in one book, confirm in a later one): **{mm.get('bridging', 0)}** (floor: ≥ {rec_b})")
        if mm["count"] == 0:
            lines.append("- **MUST FIX:** no master mysteries declared — `critique-plan` cannot check shadow coverage against the grimoire.")
        elif mm["count"] < rec_m:
            lines.append(
                f"- **SHOULD FIX:** {mm['count']} master mysteries for a {report['series']['num_books']}-book "
                f"series — aim for ≥ {rec_m} (the nature of each protagonist, each antagonist's hidden agenda, each "
                "institution's real function, each subplot's buried truth)."
            )
        if mm.get("bridging", 0) < rec_b:
            lines.append(
                f"- **SHOULD FIX:** only {mm.get('bridging', 0)} mystery spans books — without slow reveals "
                "introduced early and confirmed late, the trilogy has no across-series payoff."
            )
        if mm["incomplete"]:
            lines.append(f"- **MUST FIX — rows missing real-truth / intro book:** {mm['incomplete']}")
        lines.append("")

    if "decoys" in report["deep"]:
        dc = report["deep"]["decoys"]
        rec_d = report.get("series", {}).get("rec_decoys", 1)
        lines.append("## Decoys (deliberate misdirection)\n")
        lines.append(f"- Detected: **{dc['count']}** (floor for this series: ≥ {rec_d})")
        if dc["names"]:
            lines.append(f"- Named: {dc['names']}")
        if dc["count"] < rec_d:
            lines.append(
                f"- **SHOULD FIX:** {dc['count']} decoy(s) detected — a series that misdirects the reader wants "
                f"≥ {rec_d} declared on purpose (a false system, a hollow saviour, an institution fronting for the "
                "real parasite). Mark each so a plant isn't mistaken for a cheat later."
            )
        lines.append("")

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
        print("Tip: copy references/grimoire-template.md to that path and start writing.", file=sys.stderr)
        return 2

    grimoire_text = grimoire_path.read_text(encoding="utf-8")
    report = audit(grimoire_text)
    rendered = render(report)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"audit written to {out_path}")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
