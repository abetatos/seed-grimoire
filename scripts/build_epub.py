

#!/usr/bin/env python3
"""Compile a book's chapters into a single Kindle-ready EPUB.

Reads the finished `chapters/NN.md` prose for a book, pulls title /
author / language from `setup.md`, and shells out to **pandoc** to
produce a clean, navigable EPUB you can sideload via Send-to-Kindle.

Markdown → EPUB conversion is delegated to pandoc (it gives us a real
title page, a navigation TOC, and proper chapter splitting on the
`# Capítulo N — …` headings). Everything else here is stdlib: path
resolution, metadata extraction, and assembling the pandoc command.

Usage:
    python3 scripts/build_epub.py \
        --series-slug <slug> \
        --book-number <N> \
        [--author "Name"] \
        [--cover path/to/cover.jpg] \
        [--from 1] [--through 25] \
        [--title "Override Title"] \
        [--out output/.../book.epub]

Exit codes: 0 ok · 1 usage/empty · 2 pandoc missing/failed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Make scripts/lib importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import paths as P  # noqa: E402
from lib import project_config  # noqa: E402
from lib import setup_doc  # noqa: E402
from lib import slugify  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "assets"
DEFAULT_CSS = ASSETS / "epub.css"


def find_pandoc() -> str | None:
    """Locate the pandoc binary (PATH first, then ~/.local/bin)."""
    exe = shutil.which("pandoc")
    if exe:
        return exe
    local = Path.home() / ".local" / "bin" / "pandoc"
    return str(local) if local.exists() else None


def read_author(setup_text: str) -> str:
    for label in ("Autor", "Author", "Escritor", "Writer"):
        val = setup_doc.find_str(setup_text, label)
        if val:
            return val
    return ""


def yaml_escape(value: str) -> str:
    return value.replace('"', '\\"')


def build_metadata(title: str, author: str, lang: str) -> str:
    lines = ["---", f'title: "{yaml_escape(title)}"']
    if author:
        lines.append(f'author: "{yaml_escape(author)}"')
    lines.append(f'lang: "{yaml_escape(lang)}"')
    lines.append("---")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Compile a book to EPUB via pandoc.")
    ap.add_argument("--series-slug", required=True)
    ap.add_argument("--book-number", type=int, required=True)
    ap.add_argument("--author", default=None, help="Override author name.")
    ap.add_argument("--title", default=None, help="Override book title.")
    ap.add_argument("--cover", default=None, help="Cover image path.")
    ap.add_argument("--from", dest="ch_from", type=int, default=None)
    ap.add_argument("--through", dest="ch_through", type=int, default=None)
    ap.add_argument("--css", default=None, help="Override stylesheet path.")
    ap.add_argument("--out", default=None, help="Output .epub path.")
    args = ap.parse_args()

    pandoc = find_pandoc()
    if not pandoc:
        print(
            "ERROR: pandoc not found. Install the static binary to ~/.local/bin "
            "(see scripts/build_epub.py header) or `apt install pandoc`.",
            file=sys.stderr,
        )
        return 2

    bp = P.book_paths(args.series_slug, args.book_number)
    if not bp.book_root.exists():
        print(f"ERROR: book not found: {bp.book_root}", file=sys.stderr)
        return 1

    chapters = P.chapter_numbers(bp)
    if args.ch_from is not None:
        chapters = [n for n in chapters if n >= args.ch_from]
    if args.ch_through is not None:
        chapters = [n for n in chapters if n <= args.ch_through]
    if not chapters:
        print("ERROR: no chapters to compile (none written yet?).", file=sys.stderr)
        return 1

    setup_text = setup_doc.load(bp.setup_md)
    title = args.title or setup_doc.book_title(setup_text) or args.series_slug
    # Author resolution: explicit flag > this book's setup.md > the
    # project-wide pen name in config.toml.
    author = args.author or read_author(setup_text) or project_config.author_name()
    lang = setup_doc.language(setup_text) or "es"

    css = Path(args.css) if args.css else DEFAULT_CSS
    cover = Path(args.cover) if args.cover else bp.cover_path()

    if args.out:
        out_path = Path(args.out)
    else:
        build_dir = bp.book_root / "build"
        build_dir.mkdir(parents=True, exist_ok=True)
        out_path = build_dir / f"{slugify.slugify(title)}.epub"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Pandoc reads a metadata block first, then each chapter file in order.
    # Each chapter starts with `# Capítulo N — Title`, so split-level=1
    # yields one EPUB section per chapter with a proper TOC entry.
    with tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    ) as meta_f:
        meta_f.write(build_metadata(title, author, lang))
        meta_path = Path(meta_f.name)

    cmd: list[str] = [
        pandoc,
        "--from=markdown+smart",
        "--to=epub3",
        "--toc",
        "--toc-depth=1",
        "--split-level=1",
        f"--metadata=lang:{lang}",
        "-o",
        str(out_path),
        str(meta_path),
    ]
    if css.exists():
        cmd.append(f"--css={css}")
    if cover and cover.exists():
        cmd.append(f"--epub-cover-image={cover}")
    cmd += [str(bp.chapter_file(n)) for n in chapters]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        meta_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        print("ERROR: pandoc failed:\n" + proc.stderr, file=sys.stderr)
        return 2

    size_kb = out_path.stat().st_size / 1024
    print(f"Built EPUB: {out_path}  ({size_kb:.0f} KB)")
    print(f"  Title : {title}")
    print(f"  Author: {author or '(none — set [author] name in config.toml or pass --author)'}")
    print(f"  Lang  : {lang}")
    print(f"  Chapters: {len(chapters)}  ({chapters[0]:02d}–{chapters[-1]:02d})")
    if cover and cover.exists():
        print(f"  Cover : {cover}")
    else:
        print(f"  Cover : (none — drop cover.jpg in {bp.assets_dir}/ or pass --cover)")
    print("\nSend it to your Kindle via the Send-to-Kindle app/email.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
