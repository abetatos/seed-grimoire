---
name: compile-book
description: Compile a book's finished chapters into a single Kindle-ready EPUB and (optionally) email it to your Kindle via Send-to-Kindle. Use this when the user says "compile the book", "export to Kindle", "build the EPUB", "send it to my Kindle", or wants to read the draft on an e-reader to gather notes. Reads only the prose chapters — never canon, plan, or shadow.
---

# compile-book

You are running the **compile-book** skill. Your job is to turn the
written `chapters/NN.md` prose into a clean, navigable **EPUB** the user
can read on a Kindle (or any e-reader) and mark up for revision — and,
if asked, deliver it to their Kindle by email.

## When to invoke

- "Compile the book" / "export to Kindle" / "build the EPUB" /
  "compílame el libro" / "mándalo a mi Kindle".
- The user wants to read the current draft on a real device to gather
  their own critiques and improvements.

## What goes in the EPUB

- **Only the prose.** Chapters in order, each `# Capítulo N — Title`
  heading becoming an EPUB section with a TOC entry.
- A title page and author from `setup.md` (`# Title` + `**Autor:**`);
  when the book declares no author, the project-wide pen name from
  `config.toml` (`[author] name`) is used.
- A reading stylesheet (`scripts/assets/epub.css`): justified prose,
  first-line indents, centered scene breaks.
- **Never** include `canon/`, `plan/`, `shadow.md`, `seeds.md`, or
  summaries — those are spoilers and writer-only.

## Steps

### 1. Build the EPUB

```bash
python3 scripts/build_epub.py --series-slug <slug> --book-number <N>
```

Useful flags:

- `--from 1 --through 10` — compile a chapter range (read a partial draft).
- `--title "…"` / `--author "…"` — override the metadata.
- `--cover path/to/cover.jpg` — override the cover. By default the cover
  is read from the fixed location `assets/cover.{jpg,jpeg,png}` inside the
  book folder, so normally you just drop the file there and never pass
  this flag.
- `--out path.epub` — choose the output path.

Output defaults to `output/<series>/book-NN/build/<title-slug>.epub`.
Requires **pandoc** (static binary in `~/.local/bin`, or `apt install pandoc`).

### 2. (Optional) Send it to Kindle

Only if the user asks to deliver it to their device:

```bash
python3 scripts/send_to_kindle.py --series-slug <slug> --book-number <N>
```

This reads `KINDLE_EMAIL` + SMTP settings from `.env` and emails the
EPUB. The `SMTP_FROM` address must be on Amazon's *Approved Personal
Document E-mail List* (see README → "Reading on Kindle"). If `.env` is
missing SMTP credentials, tell the user to fill it in (copy
`.env.example`) rather than guessing.

### 3. Report

Tell the user the output path, chapter count, and size; if sent, confirm
the destination address and remind them it can take a minute to arrive.

## Cover image

The cover lives at one fixed place per book:

```
output/<series>/book-NN/assets/cover.jpg   # (or cover.jpeg / cover.png)
```

`build_epub.py` picks it up automatically — no flag needed. If the user
gives you a cover image somewhere else, copy it to that path rather than
relying on `--cover`, so every book is laid out the same way. Recommended
image: JPEG/PNG, portrait, ~1.6:1 (e.g. 1600×2560), no transparency.

## What this skill does NOT do

- Does not write, critique, or modify chapters — it only reads them.
- Does not invent a cover or author; it uses `setup.md` / `config.toml` /
  `assets/` / flags.
- Does not store or print SMTP credentials.

## Files this skill writes

- `output/<series>/book-NN/build/<slug>.epub` — the compiled book.
