#!/usr/bin/env python3
"""Deterministic audit of a book's planning files.

Reads setup.md, plan/*.md, and canon/*.md and produces a Markdown report of
mechanical findings the agent can layer qualitative critique on top of.

Findings include:
  - Setup: gating fields, chapter count, target words
  - Outline: chapters whose beat sheets are TODO-only or partial
  - Shadow: overview presence, master truths count, gaps
  - Seeds: invalid plant/payoff ordering, orphans, per-act distribution
  - Arcs: missing decision chapter / transformation type per principal
  - Canon: characters/factions/places named in canon but absent from outline,
    magic system completeness (source / cost / limits / thematic question /
    three tiers)

Usage:
    python audit_plan.py --series-slug <slug> --book-number <n>
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.paths import book_paths, BookPaths
from lib import setup_doc, seeds as seeds_mod, shadows as shadows_mod


CHAPTER_HEADER_RE = re.compile(
    r"^##\s+(?:Chapter|Cap|Capítulo)\s+(\d+)\b.*?$", re.IGNORECASE | re.MULTILINE
)
SUBSECTION_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
# Templates use blockquotes only for placeholder/instruction text; real
# planning content goes in bullets or prose. Strip every `>` line.
TODO_LINE_RE = re.compile(r"^\s*>.*$", re.MULTILINE)
PLACEHOLDER_NAME_RE = re.compile(r"^\(.*\)$")


# ----- chapter outline parsing -------------------------------------------

def chapter_sections(outline_text: str) -> dict[int, str]:
    """Return {chapter_num: section_body} for every ## Chapter N section."""
    out: dict[int, str] = {}
    headers = list(CHAPTER_HEADER_RE.finditer(outline_text))
    for i, m in enumerate(headers):
        n = int(m.group(1))
        start = m.end()
        # End at the next ## chapter or end of file
        nxt = headers[i + 1].start() if i + 1 < len(headers) else len(outline_text)
        out[n] = outline_text[start:nxt]
    return out


def subsection_status(section_text: str, subsection_title: str) -> str:
    """Return 'missing' | 'todo' | 'filled' for the named subsection."""
    sub_pattern = re.compile(
        rf"^###\s+{re.escape(subsection_title)}\s*$", re.IGNORECASE | re.MULTILINE
    )
    m = sub_pattern.search(section_text)
    if not m:
        return "missing"
    # Body until next ### or end
    rest = section_text[m.end():]
    nxt = re.search(r"^###\s+", rest, re.MULTILINE)
    body = rest[: nxt.start() if nxt else len(rest)].strip()
    if not body:
        return "missing"
    # Strip blockquote TODO markers
    stripped = TODO_LINE_RE.sub("", body).strip()
    # If after stripping all TODO lines nothing remains, it's TODO-only
    return "todo" if not stripped else "filled"


def outline_findings(outline_text: str, declared_chapters: int) -> dict:
    sections = chapter_sections(outline_text)
    covered = sorted(sections.keys())
    expected = set(range(1, declared_chapters + 1))
    missing_chapters = sorted(expected - set(covered))
    extra_chapters = sorted(set(covered) - expected)

    missing_plot, missing_texture, missing_subtext, missing_function = [], [], [], []
    todo_only_chapters = []
    for n, body in sections.items():
        statuses = {
            "Plot beats": subsection_status(body, "Plot beats"),
            "Texture beats": subsection_status(body, "Texture beats"),
            "Subtext beats": subsection_status(body, "Subtext beats"),
        }
        if statuses["Plot beats"] != "filled":
            missing_plot.append(n)
        if statuses["Texture beats"] != "filled":
            missing_texture.append(n)
        if statuses["Subtext beats"] != "filled":
            missing_subtext.append(n)
        # Function in the act
        if "function in the act" in body.lower():
            # check the bullet line itself: "- **Function in the act:** ..."
            m = re.search(r"function in the act:\*\*\s*(.+)", body, re.IGNORECASE)
            if not m or m.group(1).strip().startswith("> TODO") or "TODO" in m.group(1):
                missing_function.append(n)
        if all(s != "filled" for s in statuses.values()):
            todo_only_chapters.append(n)

    return {
        "chapter_sections_present": covered,
        "missing_chapters": missing_chapters,
        "extra_chapters": extra_chapters,
        "todo_only_chapters": sorted(set(todo_only_chapters)),
        "missing_plot_beats": sorted(set(missing_plot)),
        "missing_texture_beats": sorted(set(missing_texture)),
        "missing_subtext_beats": sorted(set(missing_subtext)),
        "missing_function": sorted(set(missing_function)),
    }


# ----- shadow ------------------------------------------------------------

def shadow_findings(shadow_text: str, declared_chapters: int, seed_ids: set[str] | None = None) -> dict:
    seed_ids = seed_ids or set()
    overview = shadows_mod.overview_section(shadow_text)
    overview_filled = bool(overview) and "TODO" not in overview

    master_truths_present = bool(
        re.search(r"##\s+Master truths", shadow_text, re.IGNORECASE)
    )

    # New structured ## SHADOW-TRUTH records.
    truths = shadows_mod.parse_truths(shadow_text)
    truths = [t for t in truths if t.truth and not t.truth.strip().startswith("<")]

    # Legacy fallback: old "- **Truth N:**" bullets (pre-migration plans).
    legacy = [
        t for t in re.findall(
            r"^\s*-\s+\*\*Truth\s+\d+:\*\*\s*(.+)$", shadow_text,
            re.MULTILINE | re.IGNORECASE,
        )
        if not t.strip().startswith("...")
    ]
    truth_count = len(truths) if truths else len(legacy)

    # Coverage / integrity checks on the structured truths.
    recommended_min = max(8, round(declared_chapters * 0.4))
    thin_coverage = truth_count < recommended_min
    unknown_carriers: list[str] = []
    no_reveal_path: list[str] = []
    for t in truths:
        miss = [c for c in t.revealed_by if seed_ids and c not in seed_ids]
        if miss:
            unknown_carriers.append(f"[{t.id}] unknown carrier seed(s): {miss}")
        if not t.revealed_by and t.confirm_in is None:
            no_reveal_path.append(t.id)

    # Per-chapter shadow sections (`### Chapter N`)
    ch_headers = [int(m.group(1)) for m in shadows_mod.CHAPTER_HEADER_RE.finditer(shadow_text)]
    chapters_with_shadow_section: list[int] = []
    for n in ch_headers:
        body = shadows_mod.chapter_section(shadow_text, n)
        if body:
            inner = re.sub(r"^###.+?\n", "", body, count=1)
            stripped = TODO_LINE_RE.sub("", inner).strip()
            if stripped:
                chapters_with_shadow_section.append(n)

    return {
        "overview_filled": overview_filled,
        "master_truths_section_present": master_truths_present,
        "master_truths_filled_count": truth_count,
        "structured_format": bool(truths),
        "recommended_min_truths": recommended_min,
        "thin_coverage": thin_coverage,
        "unknown_carriers": unknown_carriers,
        "no_reveal_path": no_reveal_path,
        "chapters_with_shadow_detail": sorted(set(chapters_with_shadow_section)),
        "chapter_count": declared_chapters,
    }


# ----- seeds -------------------------------------------------------------

def seeds_findings(seed_list, declared_chapters: int, chapters_per_act: int = 7, max_payoffs_per_chapter: int = 4) -> dict:
    invalid: list[str] = []
    plants_per_act: Counter = Counter()
    payoffs_per_act: Counter = Counter()
    payoffs_per_chapter: Counter = Counter()
    plant_chapters: set[int] = set()
    echo_chapters: set[int] = set()
    payoff_chapters: set[int] = set()

    for s in seed_list:
        if s.plant_in is None:
            invalid.append(f"[{s.id}] missing plant_in")
        if s.payoff_in is None:
            invalid.append(f"[{s.id}] missing payoff_in")
        if s.plant_in is not None and s.payoff_in is not None:
            if s.plant_in >= s.payoff_in:
                invalid.append(f"[{s.id}] plant ({s.plant_in}) is not before payoff ({s.payoff_in})")
            if s.plant_in > declared_chapters or s.payoff_in > declared_chapters:
                invalid.append(f"[{s.id}] plant/payoff outside book range (1..{declared_chapters})")
            for e in s.echo_in:
                if not (s.plant_in < e < s.payoff_in):
                    invalid.append(f"[{s.id}] echo ch {e} not strictly between plant ({s.plant_in}) and payoff ({s.payoff_in})")
        if not s.detail.strip() or not s.real_meaning.strip():
            invalid.append(f"[{s.id}] empty detail or real_meaning")
        if not s.how_to_plant.strip() or not s.how_to_pay_off.strip():
            invalid.append(f"[{s.id}] missing how_to_plant or how_to_pay_off guidance")

        if s.plant_in is not None:
            plant_chapters.add(s.plant_in)
            plants_per_act[((s.plant_in - 1) // chapters_per_act) + 1] += 1
        if s.payoff_in is not None:
            payoff_chapters.add(s.payoff_in)
            payoffs_per_act[((s.payoff_in - 1) // chapters_per_act) + 1] += 1
            payoffs_per_chapter[s.payoff_in] += 1
        for e in s.echo_in:
            echo_chapters.add(e)

    overloaded = sorted(
        [(ch, count) for ch, count in payoffs_per_chapter.items() if count > max_payoffs_per_chapter],
        key=lambda x: -x[1],
    )

    return {
        "total": len(seed_list),
        "invalid": invalid,
        "plant_chapters": sorted(plant_chapters),
        "echo_chapters": sorted(echo_chapters),
        "payoff_chapters": sorted(payoff_chapters),
        "plants_per_act": dict(plants_per_act),
        "payoffs_per_act": dict(payoffs_per_act),
        "payoffs_per_chapter": dict(payoffs_per_chapter),
        "overloaded_payoff_chapters": overloaded,
        "max_payoffs_per_chapter_threshold": max_payoffs_per_chapter,
        "chapters_without_any_seed_activity": [
            n for n in range(1, declared_chapters + 1)
            if n not in plant_chapters and n not in echo_chapters and n not in payoff_chapters
        ],
    }


# ----- arcs --------------------------------------------------------------

def arc_findings(arcs_text: str) -> dict:
    sections: dict[str, str] = {}
    headers = list(H2_RE.finditer(arcs_text))
    for i, m in enumerate(headers):
        name = m.group(1).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(arcs_text)
        sections[name] = arcs_text[start:end]

    principals: list[str] = []
    missing_decision: list[str] = []
    missing_transformation: list[str] = []
    missing_lie: list[str] = []
    missing_need: list[str] = []

    for name, body in sections.items():
        # Skip non-character h2s like "Waypoints" if they sneak in — heuristic:
        # principal sections have a Wound or Want bullet.
        if not re.search(r"\*\*(Wound|Want|Need|Lie)", body, re.IGNORECASE):
            continue
        if PLACEHOLDER_NAME_RE.match(name):
            continue
        # Strip trailing annotation like "Portaluz (secundario, sin arc completo)"
        clean_name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
        principals.append(clean_name)
        # The colon may sit inside the bold close ("**Decision point (which chapter):**")
        # OR after the bold close ("**Decision point** — ch 25"). Accept both.
        def field_filled(key: str) -> bool:
            m = re.search(rf"\*\*{re.escape(key)}[^*]*\*\*\s*[:\-]?\s*(.+)", body, re.IGNORECASE)
            if not m:
                return False
            val = m.group(1).strip()
            return bool(val) and not val.startswith("> TODO") and "TODO" not in val
        if not field_filled("Decision point"):
            missing_decision.append(clean_name)
        if not field_filled("Transformation type"):
            missing_transformation.append(clean_name)
        if not field_filled("Lie they believe"):
            missing_lie.append(clean_name)
        if not field_filled("Need"):
            missing_need.append(clean_name)

    return {
        "principals": principals,
        "missing_decision_chapter": missing_decision,
        "missing_transformation_type": missing_transformation,
        "missing_lie": missing_lie,
        "missing_need": missing_need,
    }


# ----- canon -------------------------------------------------------------

def canon_names(text: str, header_level: int = 2) -> list[str]:
    pat = H2_RE if header_level == 2 else H3_RE
    names: list[str] = []
    for m in pat.finditer(text):
        n = m.group(1).strip()
        # Skip generic headers and placeholder names
        if PLACEHOLDER_NAME_RE.match(n):
            continue
        if n.lower() in {"places", "macro geography", "calendar / time", "languages / scripts"}:
            continue
        names.append(n)
    return names


def canon_findings(paths: BookPaths, outline_text: str, plan_haystack: str) -> dict:
    chars_text = paths.canon_file("characters").read_text(encoding="utf-8") if paths.canon_file("characters").exists() else ""
    facs_text = paths.canon_file("factions").read_text(encoding="utf-8") if paths.canon_file("factions").exists() else ""
    world_text = paths.canon_file("world").read_text(encoding="utf-8") if paths.canon_file("world").exists() else ""
    magic_text = paths.canon_file("magic").read_text(encoding="utf-8") if paths.canon_file("magic").exists() else ""

    character_names = canon_names(chars_text, header_level=2)
    # Strip "(...)" annotations from character names (e.g. "Vela (lectora)")
    character_names = [re.sub(r"\s*\([^)]*\)\s*$", "", n).strip() for n in character_names]
    faction_names = canon_names(facs_text, header_level=2)
    # Strip the parenthetical color/caste suffix from faction names too
    # ("Iglesia (Blanco)" → "Iglesia") so the plan-coverage check finds
    # them by their bare name in shadow/seeds/arcs.
    faction_names = [re.sub(r"\s*\([^)]*\)\s*$", "", n).strip() for n in faction_names]
    # Places are H3 under the Places section in world.md
    place_names: list[str] = []
    places_match = re.search(r"##\s+Places\s*$", world_text, re.IGNORECASE | re.MULTILINE)
    if places_match:
        body = world_text[places_match.end():]
        for m in H3_RE.finditer(body):
            n = m.group(1).strip()
            if n.lower().startswith("place name"):
                continue
            place_names.append(n)
    # Strip parenthetical TODO suffixes ("(TODO: nombrar)")
    place_names = [re.sub(r"\s*\([^)]*\)\s*$", "", n).strip() for n in place_names]

    def absent_from_plan(names: list[str]) -> list[str]:
        out: list[str] = []
        for n in names:
            if not n:
                continue
            if not re.search(rf"\b{re.escape(n)}\b", plan_haystack, re.IGNORECASE):
                out.append(n)
        return out

    # Magic completeness
    def has_section(title: str) -> bool:
        return bool(re.search(rf"^##\s+{re.escape(title)}", magic_text, re.IGNORECASE | re.MULTILINE))

    def section_filled(title: str) -> bool:
        m = re.search(
            rf"^##\s+{re.escape(title)}.*?$([\s\S]*?)(?=^##\s|\Z)",
            magic_text, re.IGNORECASE | re.MULTILINE,
        )
        if not m:
            return False
        body = m.group(1)
        stripped = TODO_LINE_RE.sub("", body).strip()
        return bool(stripped)

    magic = {
        "source_filled": section_filled("Source"),
        "mechanic_filled": section_filled("Mechanic"),
        "costs_filled": section_filled("Costs"),
        "limits_filled": section_filled("Hard limits"),
        "thematic_question_filled": section_filled("Thematic question forced"),
        "tiers_filled": section_filled("Three escalation tiers"),
        "vocabulary_filled": section_filled("Vocabulary"),
    }

    return {
        "characters_named": character_names,
        "characters_absent_from_plan": absent_from_plan(character_names),
        "factions_named": faction_names,
        "factions_absent_from_plan": absent_from_plan(faction_names),
        "places_named": place_names,
        "places_absent_from_plan": absent_from_plan(place_names),
        "magic_completeness": magic,
    }


# ----- setup gating ------------------------------------------------------

def setup_findings(setup_text: str) -> dict:
    title = setup_doc.book_title(setup_text)
    nch = setup_doc.num_chapters(setup_text)
    lang = setup_doc.language(setup_text)
    lo, hi = setup_doc.words_per_chapter_range(setup_text)

    gating = []
    # World premise must be ≥3 sentences. Templates wrap the premise in a
    # `>` blockquote for visual emphasis; we strip the `> ` prefix and any
    # `> TODO ...` lines, then count sentences in what remains.
    world = setup_doc.get_section(setup_text, "premise of world") or setup_doc.get_section(setup_text, "premisa")
    if world:
        clean = re.sub(r"^\s*>\s*TODO.*$", "", world, flags=re.MULTILINE)
        clean = re.sub(r"^\s*>\s?", "", clean, flags=re.MULTILINE)  # strip > prefix
        # Strip bullet markers (they may be metadata like "- Era:" which is
        # not part of the premise itself).
        clean = re.sub(r"^\s*[-*]\s.*$", "", clean, flags=re.MULTILINE)
        sentences = [s.strip() for s in re.split(r"[.!?]+", clean) if s.strip() and len(s.strip()) > 10]
        if len(sentences) < 3:
            gating.append(f"world premise has < 3 sentences (found {len(sentences)})")
    else:
        gating.append("world premise missing")

    # Magic: source + mechanic must be present and non-placeholder. We treat
    # a value as a placeholder only when it is *entirely* parenthesized
    # (e.g. "(where the magic comes from — substance, …)") or empty.
    def _is_placeholder(val: str) -> bool:
        v = val.strip()
        if not v:
            return True
        return v.startswith("(") and v.endswith(")")

    magic_sec = setup_doc.get_section(setup_text, "magic system") or setup_doc.get_section(setup_text, "sistema de magia") or setup_doc.get_section(setup_text, "magia")
    if magic_sec:
        flds = setup_doc.fields(magic_sec)
        if _is_placeholder(flds.get("source", "")):
            gating.append("magic source missing")
        if _is_placeholder(flds.get("mechanic", "")):
            gating.append("magic mechanic missing")
    else:
        gating.append("magic system section missing")

    # Open decisions: parse ## Open decisions and flag any item marked
    # gating that does not show RESUELTO: / DECIDIDO: in its body.
    gating_unresolved: list[str] = []
    decisions_section = setup_doc.get_section(setup_text, "open decisions") or setup_doc.get_section(setup_text, "decisiones abiertas") or setup_doc.get_section(setup_text, "decisiones aún abiertas")
    if decisions_section:
        items = re.split(r"\n\s*\d+\.\s+", "\n" + decisions_section)
        for item in items[1:]:
            is_gating = bool(re.search(r"gating:\s*(s[iíy]|yes|true)", item, re.IGNORECASE))
            is_resolved = bool(re.search(r"resuelto|decidido|resolved|decided|\bdecisión:", item, re.IGNORECASE))
            if is_gating and not is_resolved:
                first_line = item.split("\n", 1)[0].strip()
                # Trim trailing bold/punctuation
                first_line = re.sub(r"\*+\s*$", "", first_line).rstrip(".:").strip()
                gating_unresolved.append(first_line[:120])

    return {
        "title": title,
        "num_chapters": nch,
        "language": lang,
        "words_per_chapter": (lo, hi),
        "gating_issues": gating,
        "gating_decisions_unresolved": gating_unresolved,
    }


# ----- grimoire cross-reference (§14 seeds / §14b mysteries) -------------

_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


def _grimoire_section(text: str, header_re: str) -> str:
    m = re.search(header_re, text, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s", text[start:], re.MULTILINE)
    return text[start: start + nxt.start()] if nxt else text[start:]


def _table_rows(section: str) -> list[list[str]]:
    """Return data rows (cells) of the first markdown table, dropping the
    header row and the `---` separator."""
    rows: list[list[str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):  # separator row
            continue
        rows.append(cells)
    return rows[1:] if rows else []  # drop the column-header row


def _strip_bold(s: str) -> str:
    return re.sub(r"\*\*", "", s).strip()


def _book_in_cell(cell: str, book: int) -> bool:
    roman = _ROMAN.get(book, "")
    return bool(roman) and bool(re.search(rf"\bLibro\s+{roman}\b", cell))


def crossref_findings(grimoire_text: str, book_number: int, seed_list, truths) -> dict:
    """Reconcile the grimoire's obligations against the plan:

    - every §14 loaded gun seeded in THIS book must have a seed tagging it
      (`**Obligatory:** §14 <name>`); and every seed tag must name a real row;
    - every §14b master mystery introduced in THIS book must have a shadow truth
      tagging it (`**Mystery:** <name>`); and every truth tag must be real.
    """
    out = {
        "grimoire_present": bool(grimoire_text),
        "missing_obligatory": [],   # §14 rows for this book with no seed
        "orphan_obligatory": [],    # seed tags naming a non-existent §14 row
        "missing_mysteries": [],    # §14b rows for this book with no truth
        "orphan_mysteries": [],     # truth tags naming a non-existent mystery
    }
    if not grimoire_text:
        return out

    norm = lambda x: _strip_bold(x).lower()

    # §14 loaded guns
    g14 = _table_rows(_grimoire_section(grimoire_text, r"^##\s+14\.\s"))
    gun_names = {norm(r[0]): _strip_bold(r[0]) for r in g14 if r}
    guns_this_book = {
        norm(r[0]) for r in g14 if len(r) >= 3 and _book_in_cell(r[2], book_number)
    }
    seed_tags = {}
    for sd in seed_list:
        if sd.obligatory:
            seed_tags.setdefault(norm(re.sub(r"^§14\s*", "", sd.obligatory)), sd.id)
    out["missing_obligatory"] = sorted(
        gun_names[g] for g in guns_this_book if g not in seed_tags
    )
    out["orphan_obligatory"] = sorted(
        f"{sid} → '{re.sub(r'^§14 ', '', next(s.obligatory for s in seed_list if s.id == sid))}'"
        for g, sid in seed_tags.items() if g not in gun_names
    )

    # §14b master mysteries
    g14b = _table_rows(_grimoire_section(grimoire_text, r"^##\s+14b\.\s"))
    myst_names = {norm(r[0]): _strip_bold(r[0]) for r in g14b if r}
    myst_this_book = {
        norm(r[0]) for r in g14b if len(r) >= 3 and _book_in_cell(r[2], book_number)
    }
    truth_tags = {}
    for t in truths:
        if t.mystery:
            truth_tags.setdefault(norm(t.mystery), t.id)
    out["missing_mysteries"] = sorted(
        myst_names[m] for m in myst_this_book if m not in truth_tags
    )
    out["orphan_mysteries"] = sorted(
        f"{tid} → '{next(t.mystery for t in truths if t.id == tid)}'"
        for m, tid in truth_tags.items() if m not in myst_names
    )
    return out


# ----- series / trilogy coverage -----------------------------------------

_ROMAN_TO_INT = {"VI": 6, "IV": 4, "III": 3, "II": 2, "V": 5, "I": 1}
_ROMAN_RE = r"\bLibro\s+(VI|IV|III|II|V|I)\b"


def _max_book_referenced(*texts: str) -> int:
    found = {1}
    for txt in texts:
        for m in re.finditer(_ROMAN_RE, txt or ""):
            found.add(_ROMAN_TO_INT[m.group(1)])
    return max(found)


def _seed_payoff_book(seeds_raw: str, seed_id: str, this_book: int) -> int:
    """Which book a seed pays off in: a roman 'Libro N' in its Payoff line wins;
    otherwise a numeric chapter means THIS book."""
    m = re.search(
        rf"##\s+SEED:\s*{re.escape(seed_id)}\b.*?\*\*Payoff in:\*\*[ \t]*(?P<v>.+)",
        seeds_raw, re.DOTALL,
    )
    val = m.group("v").splitlines()[0] if m else ""
    rm = re.search(_ROMAN_RE, val)
    return _ROMAN_TO_INT[rm.group(1)] if rm else this_book


def series_findings(grimoire_text, seeds_raw, seed_list, truths, book_number, declared_chapters) -> dict:
    """Trilogy-aware coverage: a series book must seed the books that come after
    it, not just resolve itself. Detects the series span from 'Libro N' mentions,
    then flags later books this plan seeds for thinly or not at all, and raises
    the recommended seed/truth floor by the cross-book burden. Nothing here is a
    fixed count — it scales with chapters and number of later books."""
    max_book = _max_book_referenced(grimoire_text, seeds_raw)
    is_series = max_book > book_number
    out = {"is_series": is_series, "max_book": max_book, "book_number": book_number}
    if not is_series:
        return out

    later = list(range(book_number + 1, max_book + 1))
    into = {L: 0 for L in later}
    for s in seed_list:
        tgt = s.payoff_in if s.payoff_in is not None else _seed_payoff_book(seeds_raw, s.id, book_number)
        if tgt in into:
            into[tgt] += 1

    next_book = book_number + 1
    thin_next_floor = max(2, round(declared_chapters * 0.08))
    # Floor scales with book length AND with how many books still come after.
    rec_seeds = max(8, round(declared_chapters * 0.5)) + 2 * len(later)
    rec_truths = max(8, round(declared_chapters * 0.4)) + len(later)

    out.update({
        "later_books": later,
        "seeds_into": into,
        "unseeded_later": [L for L in later if into[L] == 0],
        "next_book": next_book,
        "seeds_into_next": into.get(next_book, 0),
        "thin_next_floor": thin_next_floor,
        "thin_into_next": into.get(next_book, 0) < thin_next_floor,
        "rec_seeds": rec_seeds,
        "have_seeds": len(seed_list),
        "rec_truths": rec_truths,
        "have_truths": len(truths),
    })
    return out


# ----- rendering ---------------------------------------------------------

def render_report(s: dict, o: dict, sh: dict, sd: dict, ar: dict, c: dict, xr: dict | None = None, se: dict | None = None) -> str:
    lines: list[str] = ["# Plan audit (deterministic)\n"]

    lines.append("## Setup\n")
    lines.append(f"- Title: **{s['title']}**")
    lines.append(f"- Chapters: **{s['num_chapters']}**")
    lines.append(f"- Language: **{s['language']}**")
    lines.append(f"- Target words / chapter: **{s['words_per_chapter'][0]}-{s['words_per_chapter'][1]}**")
    if s["gating_issues"]:
        lines.append("- **Gating issues:**")
        for issue in s["gating_issues"]:
            lines.append(f"  - {issue}")
    else:
        lines.append("- Gating issues: none")
    if s.get("gating_decisions_unresolved"):
        lines.append("- **Open decisions still gating (must resolve before ch 1):**")
        for d in s["gating_decisions_unresolved"]:
            lines.append(f"  - {d}")
    else:
        lines.append("- Open decisions: no unresolved gating")
    lines.append("")

    lines.append("## Outline\n")
    lines.append(f"- Chapter sections present: {len(o['chapter_sections_present'])}")
    if o["missing_chapters"]:
        lines.append(f"- **Missing chapter sections:** {o['missing_chapters']}")
    if o["extra_chapters"]:
        lines.append(f"- **Extra chapter sections beyond declared count:** {o['extra_chapters']}")
    if o["todo_only_chapters"]:
        lines.append(f"- **Chapters whose beat sheet is entirely TODO:** {o['todo_only_chapters']}")
    if o["missing_plot_beats"]:
        lines.append(f"- Missing plot beats: {o['missing_plot_beats']}")
    if o["missing_texture_beats"]:
        lines.append(f"- Missing texture beats: {o['missing_texture_beats']}")
    if o["missing_subtext_beats"]:
        lines.append(f"- Missing subtext beats: {o['missing_subtext_beats']}")
    if o["missing_function"]:
        lines.append(f"- Missing 'function in the act' line: {o['missing_function']}")
    lines.append("")

    lines.append("## Shadow timeline\n")
    lines.append(f"- Overview filled: {'yes' if sh['overview_filled'] else '**no**'}")
    fmt = "structured SHADOW-TRUTH" if sh.get("structured_format") else "**legacy free-prose (migrate to SHADOW-TRUTH)**"
    lines.append(f"- Master truths declared: {sh['master_truths_filled_count']} ({fmt})")
    if sh.get("thin_coverage"):
        lines.append(
            f"- **Thin shadow coverage:** {sh['master_truths_filled_count']} truths for "
            f"{sh['chapter_count']} chapters (want ≥ {sh['recommended_min_truths']}). Add "
            f"truths for each antagonist agenda, institution, and major subplot."
        )
    if sh.get("no_reveal_path"):
        lines.append(
            f"- **Truths with no reveal path** (no `Revealed-by` and no `Confirm in` — "
            f"the reader can never learn them): {sh['no_reveal_path']}"
        )
    if sh.get("unknown_carriers"):
        lines.append("- **Truths citing unknown carrier seeds** (fix the id or add the seed):")
        for u in sh["unknown_carriers"]:
            lines.append(f"  - {u}")
    if sh["chapters_with_shadow_detail"]:
        lines.append(f"- Chapters with shadow detail: {sh['chapters_with_shadow_detail']}")
    else:
        lines.append("- **No per-chapter shadow detail filled.**")
    lines.append("")

    if xr is not None:
        lines.append("## Grimoire coverage (§14 seeds / §14b mysteries)\n")
        if not xr["grimoire_present"]:
            lines.append("- Grimoire not found — cross-reference skipped.")
        else:
            if xr["missing_obligatory"]:
                lines.append(
                    "- **§14 loaded guns seeded in this book with NO seed realizing them** "
                    f"(MUST fix — add the seed): {xr['missing_obligatory']}"
                )
            else:
                lines.append("- §14 loaded guns for this book: all realized by a seed. ✓")
            if xr["orphan_obligatory"]:
                lines.append(f"- **Seeds tagging a non-existent §14 row** (fix the name): {xr['orphan_obligatory']}")
            if xr["missing_mysteries"]:
                lines.append(
                    "- **§14b master mysteries introduced in this book with NO shadow truth** "
                    f"(MUST fix — add the truth): {xr['missing_mysteries']}"
                )
            else:
                lines.append("- §14b mysteries for this book: all carried by a shadow truth. ✓")
            if xr["orphan_mysteries"]:
                lines.append(f"- **Truths tagging a non-existent mystery** (fix the name): {xr['orphan_mysteries']}")
        lines.append("")

    if se is not None and se.get("is_series"):
        lines.append("## Series / trilogy coverage\n")
        lines.append(
            f"- This is book {se['book_number']} of a {se['max_book']}-book series. "
            f"A series book must SEED the books after it, not only resolve itself."
        )
        lines.append(f"- Seeds paying into later books: {se['seeds_into']}")
        if se["unseeded_later"]:
            lines.append(
                f"- **Later books with NO seed planted for them** (the plan leaves them "
                f"to inherit nothing): Libro {se['unseeded_later']}. `SHOULD fix` — plant "
                f"threads now that pay off there."
            )
        if se["thin_into_next"]:
            lines.append(
                f"- **Thin seeding into the very next book (Libro {se['next_book']}):** "
                f"{se['seeds_into_next']} seed(s), want ≥ {se['thin_next_floor']}. The middle "
                f"book needs its payoffs planted here. `SHOULD fix`."
            )
        if se["have_seeds"] < se["rec_seeds"]:
            lines.append(
                f"- **Lean for a trilogy opener:** {se['have_seeds']} seeds, recommended "
                f"≥ {se['rec_seeds']} for a series book of this length (base + cross-book "
                f"burden). Not a hard floor, but reconsider coverage."
            )
        if se["have_truths"] < se["rec_truths"]:
            lines.append(
                f"- Master truths lean for a series book: {se['have_truths']}, recommended "
                f"≥ {se['rec_truths']}."
            )
        lines.append("")

    lines.append("## Seeds\n")
    lines.append(f"- Total: **{sd['total']}**")
    if sd["invalid"]:
        lines.append("- **Invalid entries:**")
        for v in sd["invalid"]:
            lines.append(f"  - {v}")
    lines.append(f"- Plants per act: {sd['plants_per_act']}")
    lines.append(f"- Payoffs per act: {sd['payoffs_per_act']}")
    if sd.get("overloaded_payoff_chapters"):
        threshold = sd["max_payoffs_per_chapter_threshold"]
        lines.append(
            f"- **Overloaded payoff chapters (> {threshold} per chapter):**"
        )
        for ch, count in sd["overloaded_payoff_chapters"]:
            lines.append(f"  - ch {ch}: {count} payoffs")
    if sd["chapters_without_any_seed_activity"]:
        lines.append(f"- Chapters with no plant/echo/payoff: {sd['chapters_without_any_seed_activity']}")
    lines.append("")

    lines.append("## Character arcs\n")
    if not ar["principals"]:
        lines.append("- **No principal arcs found.**")
    else:
        lines.append(f"- Principals: {ar['principals']}")
        if ar["missing_decision_chapter"]:
            lines.append(f"- Missing decision-point chapter: {ar['missing_decision_chapter']}")
        if ar["missing_transformation_type"]:
            lines.append(f"- Missing transformation type: {ar['missing_transformation_type']}")
        if ar["missing_lie"]:
            lines.append(f"- Missing 'lie they believe': {ar['missing_lie']}")
        if ar["missing_need"]:
            lines.append(f"- Missing 'need': {ar['missing_need']}")
    lines.append("")

    lines.append("## Canon\n")
    lines.append(f"- Characters in canon: {c['characters_named']}")
    if c["characters_absent_from_plan"]:
        lines.append(f"- **Characters never mentioned in plan (outline+shadow+arcs+seeds):** {c['characters_absent_from_plan']}")
    lines.append(f"- Factions in canon: {c['factions_named']}")
    if c["factions_absent_from_plan"]:
        lines.append(f"- **Factions never mentioned in plan:** {c['factions_absent_from_plan']}")
    lines.append(f"- Places in canon: {c['places_named']}")
    if c["places_absent_from_plan"]:
        lines.append(f"- **Places never mentioned in plan:** {c['places_absent_from_plan']}")
    m = c["magic_completeness"]
    missing_magic = [k for k, v in m.items() if not v]
    if missing_magic:
        lines.append(f"- **Magic sections empty/missing:** {missing_magic}")
    else:
        lines.append("- Magic sections all present.")
    lines.append("")

    return "\n".join(lines)


# ----- main --------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-slug", required=True)
    parser.add_argument("--book-number", type=int, required=True)
    parser.add_argument("--output", default=None, help="Write report here instead of stdout.")
    args = parser.parse_args()

    paths = book_paths(args.series_slug, args.book_number)
    if not paths.setup_md.exists():
        print(f"ERROR: setup.md not found at {paths.setup_md}", file=sys.stderr)
        return 2
    if not paths.outline_md.exists():
        print(f"ERROR: plan/outline.md not found. Run plan-book first.", file=sys.stderr)
        return 2

    setup_text = setup_doc.load(paths.setup_md)
    outline_text = paths.outline_md.read_text(encoding="utf-8")
    shadow_text = shadows_mod.load_shadow(paths.shadow_md)
    seed_list = seeds_mod.load_seeds(paths.seeds_md)
    arcs_text = paths.arcs_md.read_text(encoding="utf-8") if paths.arcs_md.exists() else ""

    s = setup_findings(setup_text)
    declared = s["num_chapters"] or 0
    o = outline_findings(outline_text, declared)
    sd = seeds_findings(seed_list, declared)
    sh = shadow_findings(shadow_text, declared, {s.id for s in seed_list})
    ar = arc_findings(arcs_text)
    # Combined plan haystack — outline + shadow + arcs + seeds — so the
    # "absent from plan" check doesn't false-positive when the outline is
    # still TODO but the character lives in shadow/seeds/arcs.
    seeds_raw = paths.seeds_md.read_text(encoding="utf-8") if paths.seeds_md.exists() else ""
    plan_haystack = "\n".join([outline_text, shadow_text, arcs_text, seeds_raw])
    c = canon_findings(paths, outline_text, plan_haystack)

    grimoire_text = paths.grimoire_md.read_text(encoding="utf-8") if paths.grimoire_md.exists() else ""
    truths = shadows_mod.parse_truths(shadow_text)
    xr = crossref_findings(grimoire_text, args.book_number, seed_list, truths)
    se = series_findings(grimoire_text, seeds_raw, seed_list, truths, args.book_number, declared)

    report = render_report(s, o, sh, sd, ar, c, xr, se)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"audit written to {args.output}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
