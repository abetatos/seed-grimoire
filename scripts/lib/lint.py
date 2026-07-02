"""Deterministic auditor of a book's on-disk state.

A dozen invariants used to be checked only by the model reading SKILL.md prose
(or not at all). A silent breach — a dropped seed token, a dangling
``Revealed-by``, a chapter locked without a summary — corrupts continuity many
chapters later. This module turns those invariants into findings with exit
codes, so ``resume-act`` / ``update-canon`` / the critiques can gate on a script
instead of a careful read.

Findings are ``(level, where, message)`` with level ERROR or WARN. ERROR means a
contract is broken (the pipeline should stop); WARN means "probably wrong, look"
(non-blocking unless ``--strict``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .paths import BookPaths, chapter_numbers, summary_chapter_numbers
from . import seeds as seeds_mod
from . import shadows as shadows_mod
from . import setup_doc


ERROR = "ERROR"
WARN = "WARN"


@dataclass
class Finding:
    level: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.level} {self.where}: {self.message}"


def _num_chapters(paths: BookPaths) -> int | None:
    return setup_doc.num_chapters(setup_doc.load(paths.setup_md))


def check_seeds(paths: BookPaths) -> list[Finding]:
    """Check 1+2+5: parse integrity, status validity, round-trip stability,
    schedule sanity, and status/Realized coherence."""
    out: list[Finding] = []
    if not paths.seeds_md.exists():
        return out
    raw = paths.seeds_md.read_text(encoding="utf-8")
    seeds = seeds_mod.load_seeds(paths.seeds_md)
    n_chapters = _num_chapters(paths)

    for s in seeds:
        where = f"seeds.md[{s.id}]"
        # 1a. Parse warnings from the loud parser → hard error.
        for w in s.parse_warnings:
            out.append(Finding(ERROR, where, f"unparsed schedule token: {w}"))
        # 1b. Status must be on the ladder.
        if not seeds_mod.is_valid_status(s.status):
            out.append(Finding(ERROR, where, f"invalid status {s.status!r}"))
        # 1c. Surgical no-op mutation must be byte-identical (invariant that
        # protects every real mutation the pipeline makes to this file).
        new, found = seeds_mod.update_status_in_text(raw, s.id, s.status)
        if not found:
            out.append(Finding(ERROR, where, "seed id not addressable by surgical mutation"))
        elif new != raw:
            out.append(Finding(ERROR, where, "round-trip status mutation is not byte-stable"))
        # 2. Schedule sanity.
        if s.plant_in is not None and s.payoff_in is not None and s.payoff_in <= s.plant_in:
            out.append(Finding(ERROR, where, f"payoff (ch {s.payoff_in}) not after plant (ch {s.plant_in})"))
        scheduled = ([s.plant_in] if s.plant_in else []) + list(s.echo_in) + ([s.payoff_in] if s.payoff_in else [])
        if n_chapters:
            for ch in scheduled:
                if ch < 1 or ch > n_chapters:
                    out.append(Finding(
                        ERROR, where,
                        f"scheduled chapter {ch} out of book range [1, {n_chapters}] "
                        f"(a cross-book payoff must be written 'Libro N', not a bare number)",
                    ))
        # 5. Status/Realized coherence (WARN — advisory).
        if s.status.startswith(("planted", "echoed")) and not s.realized:
            out.append(Finding(WARN, where, f"status {s.status} but no Realized touch-log line"))
    return out


def check_shadow(paths: BookPaths, seed_ids: set[str]) -> list[Finding]:
    """Check 3: every Revealed-by id resolves to a real seed; parse warnings."""
    out: list[Finding] = []
    if not paths.shadow_md.exists():
        return out
    for t in shadows_mod.load_truths(paths.shadow_md):
        where = f"shadow.md[{t.id}]"
        for w in t.parse_warnings:
            out.append(Finding(ERROR, where, f"unparsed schedule token: {w}"))
        for sid in t.revealed_by:
            if sid not in seed_ids:
                out.append(Finding(ERROR, where, f"Revealed-by names unknown seed {sid!r}"))
    return out


_OBLIGATORY_RE = re.compile(r"§\s*14\b")


def check_grimoire_refs(paths: BookPaths, seeds) -> list[Finding]:
    """Check 3b: every 'Obligatory: §14 <name>' has a matching §14 row in the
    series grimoire (only when the grimoire exists). WARN — the grimoire may
    legitimately not exist yet."""
    out: list[Finding] = []
    if not paths.grimoire_md.exists():
        return out
    grimoire = paths.grimoire_md.read_text(encoding="utf-8")
    for s in seeds:
        if s.obligatory and _OBLIGATORY_RE.search(s.obligatory):
            # crude: the loaded-gun name after "§14" should appear in the grimoire
            name = _OBLIGATORY_RE.sub("", s.obligatory).strip(" -–—:")
            if name and name.lower() not in grimoire.lower():
                out.append(Finding(WARN, f"seeds.md[{s.id}]",
                                   f"Obligatory §14 '{name}' not found in grimoire.md"))
    return out


_TODO_RE = re.compile(r"\bTODO\b|>\s*TODO", re.IGNORECASE)


def check_lockin(paths: BookPaths) -> list[Finding]:
    """Check 4: every chapter below the highest written one is locked in (has a
    TODO-free summary); decisions-chNN.md present (WARN if not)."""
    out: list[Finding] = []
    chapters = chapter_numbers(paths)
    if not chapters:
        return out
    highest = max(chapters)
    for n in chapters:
        if n >= highest:
            continue  # the in-progress chapter need not be locked in yet
        summ = paths.chapter_summary(n)
        if not summ.exists():
            out.append(Finding(ERROR, f"summaries/ch-{n:02d}.md", "missing (chapter not locked in)"))
        elif _TODO_RE.search(summ.read_text(encoding="utf-8")):
            out.append(Finding(ERROR, f"summaries/ch-{n:02d}.md", "still has TODO — lock-in incomplete"))
        if not paths.chapter_decisions_md(n).exists():
            out.append(Finding(WARN, f"notes/decisions-ch{n:02d}.md", "missing (no gate decisions recorded)"))
    return out


def check_book_summary_freshness(paths: BookPaths) -> list[Finding]:
    """Check 6: book-summary's 'What just happened' should mention the highest
    locked chapter (detects a skipped update-canon step 5 / skipped close-act)."""
    out: list[Finding] = []
    summaries = summary_chapter_numbers(paths)
    if not summaries or not paths.book_summary.exists():
        return out
    highest = max(summaries)
    text = paths.book_summary.read_text(encoding="utf-8")
    m = re.search(r"##\s*(?:What just happened|Qué acaba de pasar)(.*?)(?=\n##\s|\Z)",
                  text, re.IGNORECASE | re.DOTALL)
    section = m.group(1) if m else text
    if not re.search(rf"\b{highest}\b", section):
        out.append(Finding(WARN, "summaries/book-summary.md",
                           f"'What just happened' does not mention chapter {highest} "
                           f"(stale? run update-canon step 5 / close-act)"))
    return out


def lint_book(paths: BookPaths) -> list[Finding]:
    """Run every check and return all findings, ERRORs first."""
    seeds = seeds_mod.load_seeds(paths.seeds_md)
    seed_ids = {s.id for s in seeds}
    findings: list[Finding] = []
    findings += check_seeds(paths)
    findings += check_shadow(paths, seed_ids)
    findings += check_grimoire_refs(paths, seeds)
    findings += check_lockin(paths)
    findings += check_book_summary_freshness(paths)
    findings.sort(key=lambda f: 0 if f.level == ERROR else 1)
    return findings


def has_errors(findings: list[Finding]) -> bool:
    return any(f.level == ERROR for f in findings)
