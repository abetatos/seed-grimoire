

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
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
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


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def build_metadata(title: str, author: str, lang: str, *, show_author: bool) -> str:
    """Pandoc metadata block. `author` is emitted as the visible title-page
    byline ONLY when `show_author` — when a dedication replaces the byline
    the author is supplied out-of-band via --epub-metadata (dc:creator) so
    it stays in the Kindle library without appearing on the title page."""
    lines = ["---", f'title: "{yaml_escape(title)}"']
    if author and show_author:
        lines.append(f'author: "{yaml_escape(author)}"')
    lines.append(f'lang: "{yaml_escape(lang)}"')
    lines.append("---")
    return "\n".join(lines) + "\n"


def front_matter_page(text: str) -> str:
    """Wrap a front-matter file's body so pandoc renders it as its own page,
    unnumbered and OUT of the reading TOC, with no visible heading label
    (the `.frontmatter-hidden` h1 is `display:none` in epub.css). A heading
    is required because --split-level=1 only splits on level-1 headings."""
    return (
        "# Front matter {.unnumbered .unlisted .frontmatter-hidden}\n\n"
        + text.strip()
        + "\n"
    )


def reorder_epub(epub_path: Path, num_front_matter: int) -> None:
    """Post-process the pandoc EPUB so the reading order is
    cover → front matter → nav (índice) → chapters.

    Pandoc emits cover → title page → nav → content. Two fixes:
      * drop the standalone text title page — the cover already carries the
        title, so a near-blank "El cuadrado" page just reads as broken;
      * move the nav (the visible índice) to AFTER the front matter, so the
        reader meets the dedication and synopsis first, then the index.

    Idempotent and defensive: if any of cover/title/nav is absent, whatever
    is present is reordered and the rest is left alone."""
    with zipfile.ZipFile(epub_path) as z:
        infos = z.infolist()
        container = z.read("META-INF/container.xml").decode("utf-8")
        m = re.search(r'full-path="([^"]+\.opf)"', container)
        if not m:
            return
        opf_name = m.group(1)
        opf = z.read(opf_name).decode("utf-8")
        blob = {i.filename: z.read(i.filename) for i in infos}

    spine = re.search(r"(<spine\b[^>]*>)(.*?)(</spine>)", opf, re.S)
    if not spine:
        return
    head, body, tail = spine.group(1), spine.group(2), spine.group(3)
    refs = re.findall(r"<itemref\b[^>]*/>", body)

    def idref(ref: str) -> str:
        mm = re.search(r'idref="([^"]+)"', ref)
        return mm.group(1) if mm else ""

    cover = [r for r in refs if "cover" in idref(r)]
    title = [r for r in refs if "title_page" in idref(r)]
    nav = [r for r in refs if idref(r) == "nav"]
    content = [r for r in refs if r not in cover and r not in title and r not in nav]
    fm = content[:num_front_matter]
    chapters = content[num_front_matter:]

    new_refs = cover + fm + nav + chapters  # title page dropped
    if new_refs == refs:
        return  # nothing to change
    new_body = "\n    " + "\n    ".join(new_refs) + "\n  "
    new_opf = opf[: spine.start()] + head + new_body + tail + opf[spine.end():]

    # Also unlink the dropped title page from the manifest and delete its file,
    # so no orphaned content document is left in the package.
    for ref in title:
        tid = idref(ref)
        item = re.search(rf'<item\b[^>]*id="{re.escape(tid)}"[^>]*/>', new_opf)
        if item:
            href = re.search(r'href="([^"]+)"', item.group(0))
            new_opf = new_opf.replace(item.group(0), "").replace("\n  \n", "\n")
            if href:
                # href is relative to the .opf's directory.
                opf_dir = "/".join(opf_name.split("/")[:-1])
                target = f"{opf_dir}/{href.group(1)}" if opf_dir else href.group(1)
                blob.pop(target, None)

    # Strip the dropped title page from the nav's hidden landmarks list so no
    # reader shortcut points at a deleted file.
    if title:
        navm = re.search(r'<item\b[^>]*properties="[^"]*\bnav\b[^"]*"[^>]*/>', new_opf)
        href = re.search(r'href="([^"]+)"', navm.group(0)) if navm else None
        if href:
            opf_dir = "/".join(opf_name.split("/")[:-1])
            nav_target = f"{opf_dir}/{href.group(1)}" if opf_dir else href.group(1)
            nav_html = blob.get(nav_target)
            if nav_html is not None:
                txt = nav_html.decode("utf-8")
                txt = re.sub(
                    r"\s*<li>\s*<a\b[^>]*epub:type=\"titlepage\"[^>]*>.*?</a>\s*</li>",
                    "", txt, flags=re.S,
                )
                blob[nav_target] = txt.encode("utf-8")

    # Strip the title page navPoint from the NCX (the EPUB2 index Kindle
    # actually reads) — this is the "El cuadrado" index entry that pointed at
    # the now-deleted page.
    if title:
        for name in list(blob):
            if name.endswith(".ncx"):
                txt = blob[name].decode("utf-8")
                txt = re.sub(
                    r"\s*<navPoint\b[^>]*>\s*<navLabel>.*?</navLabel>\s*"
                    r"<content\b[^>]*src=\"[^\"]*title_page\.xhtml\"[^>]*/>\s*</navPoint>",
                    "", txt, flags=re.S,
                )
                blob[name] = txt.encode("utf-8")

    blob[opf_name] = new_opf.encode("utf-8")

    tmp = epub_path.with_suffix(".epub.tmp")
    with zipfile.ZipFile(tmp, "w") as z:
        # mimetype must be first and stored uncompressed.
        if "mimetype" in blob:
            z.writestr(
                zipfile.ZipInfo("mimetype"), blob.pop("mimetype"),
                compress_type=zipfile.ZIP_STORED,
            )
        for name, data in blob.items():
            z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(epub_path)


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

    # Front matter (dedication, epigraph, …) precedes the chapters. A
    # dedication replaces the author byline on the title page: the author
    # then rides in dc:creator metadata (out-of-band) instead of on the page.
    fm_files = P.front_matter_files(bp)
    has_dedication = any(P.is_dedication(f) for f in fm_files)

    tmp_paths: list[Path] = []

    def write_tmp(text: str) -> Path:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            p = Path(f.name)
        tmp_paths.append(p)
        return p

    # Pandoc reads a metadata block first, then front-matter pages, then each
    # chapter file. Each chapter starts with `# Capítulo N — Title`, so
    # split-level=1 yields one EPUB section per chapter with a TOC entry;
    # front-matter pages carry an `.unlisted` heading so they stay out of it.
    meta_path = write_tmp(
        build_metadata(title, author, lang, show_author=not has_dedication)
    )

    # When the byline is suppressed, keep the author in the Kindle library
    # by supplying dc:creator directly.
    epub_meta_path: Path | None = None
    if has_dedication and author:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write(f"<dc:creator>{xml_escape(author)}</dc:creator>\n")
            epub_meta_path = Path(f.name)
        tmp_paths.append(epub_meta_path)

    fm_inputs = [write_tmp(front_matter_page(f.read_text(encoding="utf-8"))) for f in fm_files]

    cmd: list[str] = [
        pandoc,
        # -implicit_figures: a lone image stays an inline <img> (keeps its
        # alt for accessibility) instead of becoming a <figure> whose alt
        # text renders as a visible caption under the photo.
        "--from=markdown+smart-implicit_figures",
        "--to=epub3",
        "--toc",
        "--toc-depth=1",
        "--split-level=1",
        f"--metadata=lang:{lang}",
        # Front-matter/chapter files are staged as temp files in the system
        # tmpdir, so relative image paths (e.g. assets/foo.jpeg) must resolve
        # against the book root, not the tmpdir. Pandoc bundles referenced
        # images into the EPUB from here.
        f"--resource-path={bp.book_root}",
        "-o",
        str(out_path),
        str(meta_path),
    ]
    if epub_meta_path is not None:
        cmd.append(f"--epub-metadata={epub_meta_path}")
    if css.exists():
        cmd.append(f"--css={css}")
    if cover and cover.exists():
        cmd.append(f"--epub-cover-image={cover}")
    cmd += [str(p) for p in fm_inputs]
    cmd += [str(bp.chapter_file(n)) for n in chapters]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        for p in tmp_paths:
            p.unlink(missing_ok=True)

    if proc.returncode != 0:
        print("ERROR: pandoc failed:\n" + proc.stderr, file=sys.stderr)
        return 2

    # Reading order: cover → front matter → índice → chapters (drop the
    # redundant text title page; the cover carries the title).
    reorder_epub(out_path, len(fm_files))

    size_kb = out_path.stat().st_size / 1024
    print(f"Built EPUB: {out_path}  ({size_kb:.0f} KB)")
    print(f"  Title : {title}")
    author_note = " (in metadata; title page shows the dedication)" if has_dedication else ""
    print(f"  Author: {author or '(none — set [author] name in config.toml or pass --author)'}{author_note}")
    print(f"  Lang  : {lang}")
    if fm_files:
        print(f"  Front matter: {', '.join(f.name for f in fm_files)}")
    print(f"  Chapters: {len(chapters)}  ({chapters[0]:02d}–{chapters[-1]:02d})")
    if cover and cover.exists():
        print(f"  Cover : {cover}")
    else:
        print(f"  Cover : (none — drop cover.jpg in {bp.assets_dir}/ or pass --cover)")
    print("\nSend it to your Kindle via the Send-to-Kindle app/email.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
