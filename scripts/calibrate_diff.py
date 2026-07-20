#!/usr/bin/env python3
"""Sentence-aligned before/after diff of a chapter — the raw material for the
``calibrate-style`` skill's POSITIVE model (a style rule distilled from the
author's own hand edits, with no exemplars to photocopy).

The author edits a locked chapter by hand; those edits ARE the voice target,
expressed as a delta rather than a fragment. This aligns the committed version
(``git show HEAD:chapters/NN.md``) against the working tree — sentence by
sentence, difflib — and emits ``notes/_calibration-chNN.md``: the rewritten
pairs (before → after), pure cuts, pure additions, and the measurable deltas
(word count, tic counts) per pair and overall. The skill reads that file and
distills each cluster WITH the author into a named, generalised rule — never
quoting >3 consecutive words of the prose (anti-photocopy).

Usage:
    python scripts/calibrate_diff.py --series-slug S --book-number N --chapter M
    python scripts/calibrate_diff.py --before before.md --after after.md
    # --stdout prints instead of writing notes/_calibration-chNN.md

Exit: 0 on success; 2 = missing book/chapter/file, no HEAD version, or bad args.
"""

from __future__ import annotations

import argparse
import difflib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import prose_lint
from lib.paths import book_paths
from lib.wordcount import count_words, prose_text

# A replace-block pairing floor: a before/after sentence pair below this
# similarity is treated as an unrelated cut + insertion, not a rewrite of the
# same sentence. Low enough to catch heavy rewrites, high enough to avoid
# pairing two sentences that merely share function words.
_PAIR_FLOOR = 0.30


def _git_show_head(rel_path: str) -> str | None:
    """The committed (HEAD) text of a repo-relative path, or None when the path
    is untracked / absent at HEAD (a chapter never committed has no 'before')."""
    try:
        out = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def _sentences(text: str) -> list[str]:
    return prose_lint.split_sentences(prose_text(text))


def align(before: list[str], after: list[str]) -> tuple[
        list[tuple[str, str, float]], list[str], list[str]]:
    """Align two sentence lists into (rewritten pairs, pure cuts, pure adds).

    difflib gives the equal anchors; inside each replace block we greedily pair
    every before-sentence with its best-ratio after-sentence (above the floor),
    so a 1-1 rewrite reads as a pair and a split/merge falls out as cut+add."""
    sm = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    pairs: list[tuple[str, str, float]] = []
    cuts: list[str] = []
    adds: list[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            cuts.extend(before[i1:i2])
        elif tag == "insert":
            adds.extend(after[j1:j2])
        else:  # replace
            b_block = list(before[i1:i2])
            a_block = list(after[j1:j2])
            used: set[int] = set()
            for bs in b_block:
                best_j, best_r = -1, 0.0
                for jj, as_ in enumerate(a_block):
                    if jj in used:
                        continue
                    r = difflib.SequenceMatcher(a=bs, b=as_).ratio()
                    if r > best_r:
                        best_r, best_j = r, jj
                if best_j >= 0 and best_r >= _PAIR_FLOOR:
                    used.add(best_j)
                    pairs.append((bs, a_block[best_j], best_r))
                else:
                    cuts.append(bs)
            for jj, as_ in enumerate(a_block):
                if jj not in used:
                    adds.append(as_)
    return pairs, cuts, adds


def _metrics(text: str) -> dict[str, float]:
    """Small measurable fingerprint of a snippet, so a pair's delta is numbers,
    not vibes: words + the density-lever tics the auditor already counts."""
    words = count_words(text)
    similes = len(prose_lint.find_similes(text))
    como_si, _ = prose_lint.count_como_si(text)
    mente, _, _ = prose_lint.density_per_1000(prose_lint._MENTE_RE, text, words or 1)
    filt, _, _ = prose_lint.density_per_1000(prose_lint._FILTER_VERB_RE, text, words or 1)
    return {"words": words, "similes": similes, "como_si": como_si,
            "mente/1000": round(mente, 1), "filtro/1000": round(filt, 1)}


def _pair_delta(before: str, after: str) -> str:
    mb, ma = _metrics(before), _metrics(after)
    parts = []
    for k in mb:
        if mb[k] != ma[k]:
            parts.append(f"{k} {mb[k]}→{ma[k]}")
    return ", ".join(parts) if parts else "sin cambio medible"


def _overall_tic_table(before_text: str, after_text: str,
                       config: prose_lint.ProseLintConfig) -> list[str]:
    tb = {t.name: t for t in prose_lint.audit_chapter_tics(before_text, config)}
    ta = {t.name: t for t in prose_lint.audit_chapter_tics(after_text, config)}
    rows = ["| tic | antes | después | Δ |", "|-----|-------|---------|---|"]
    for name in tb:
        cb, ca = tb[name].count, ta.get(name, tb[name]).count
        arrow = "→" if cb != ca else "="
        rows.append(f"| {name} | {cb} | {ca} | {cb}{arrow}{ca} |")
    return rows


def render(chapter_label: str, before_text: str, after_text: str,
           config: prose_lint.ProseLintConfig) -> str:
    pairs, cuts, adds = align(_sentences(before_text), _sentences(after_text))
    wb, wa = count_words(before_text), count_words(after_text)
    out = [
        f"# Calibración — {chapter_label}",
        "> Ediciones del autor a mano sobre el capítulo bloqueado: el modelo "
        "POSITIVO de la voz, expresado como delta. Para `calibrate-style`.",
        "> **No copies la prosa**: destila cada cluster en una regla nombrada y "
        "generalizada (nunca cites >3 palabras seguidas).",
        "",
        f"Palabras: {wb} → {wa} ({wa - wb:+d}). "
        f"Reescrituras: {len(pairs)}; cortes: {len(cuts)}; añadidos: {len(adds)}.",
        "",
        "## Conteo de tics (capítulo entero)",
        *_overall_tic_table(before_text, after_text, config),
    ]
    if pairs:
        out += ["", "## Reescrituras (antes → después) — el material de oro"]
        for i, (b, a, r) in enumerate(pairs, start=1):
            out += [
                f"\n**{i}.** (similitud {r:.2f} · {_pair_delta(b, a)})",
                f"- antes: «{b}»",
                f"- después: «{a}»",
            ]
    if cuts:
        out += ["", "## Cortes (el autor eliminó)"]
        out += [f"- «{c}»" for c in cuts]
    if adds:
        out += ["", "## Añadidos (el autor introdujo)"]
        out += [f"- «{a}»" for a in adds]
    if not (pairs or cuts or adds):
        out += ["", "_Sin diferencias de frase entre las dos versiones._"]
    return "\n".join(out) + "\n"


def _default_config() -> prose_lint.ProseLintConfig:
    return prose_lint.ProseLintConfig(
        caps=dict(prose_lint.DEFAULT_CAPS), reserved=[], extra_patterns=[],
        source="defaults")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--series-slug")
    p.add_argument("--book-number", type=int)
    p.add_argument("--chapter", type=int)
    p.add_argument("--before", type=Path, help="Explicit 'before' file (skips git).")
    p.add_argument("--after", type=Path, help="Explicit 'after' file.")
    p.add_argument("--stdout", action="store_true",
                   help="Print the report instead of writing the notes file.")
    args = p.parse_args()

    if args.before or args.after:
        if not (args.before and args.after):
            p.error("pass BOTH --before and --after")
        for f in (args.before, args.after):
            if not f.exists():
                print(f"ERROR: file not found: {f}", file=sys.stderr)
                return 2
        before_text = args.before.read_text(encoding="utf-8")
        after_text = args.after.read_text(encoding="utf-8")
        report = render(f"{args.before.name} → {args.after.name}",
                        before_text, after_text, _default_config())
        print(report, end="")  # arbitrary files have no notes dir → always stdout
        return 0

    if not (args.series_slug and args.book_number and args.chapter):
        p.error("provide --before/--after, or --series-slug --book-number --chapter")
    paths = book_paths(args.series_slug, args.book_number)
    chap_file = paths.chapter_file(args.chapter)
    if not chap_file.exists():
        print(f"ERROR: chapter not found: {chap_file}", file=sys.stderr)
        return 2
    rel = chap_file.resolve().relative_to(REPO_ROOT).as_posix()
    before_text = _git_show_head(rel)
    if before_text is None:
        print(f"ERROR: no committed (HEAD) version of {rel}; nothing to diff "
              f"against. Commit the pre-edit chapter first, or use --before/--after.",
              file=sys.stderr)
        return 2
    after_text = chap_file.read_text(encoding="utf-8")
    try:
        config = prose_lint.load_config(paths)
    except prose_lint.UnsupportedLanguageError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    report = render(f"capítulo {args.chapter}", before_text, after_text, config)
    if args.stdout:
        print(report, end="")
        return 0
    out_path = paths.notes_dir / f"_calibration-ch{args.chapter:02d}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    pairs, cuts, adds = align(_sentences(before_text), _sentences(after_text))
    print(f"calibrate_diff: wrote {out_path.name}; "
          f"{len(pairs)} rewrite(s), {len(cuts)} cut(s), {len(adds)} add(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
