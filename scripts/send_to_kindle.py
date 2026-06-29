#!/usr/bin/env python3
"""Email a compiled EPUB to your Kindle via Send-to-Kindle.

Reads SMTP + Kindle config from `.env` (see `.env.example`), attaches the
EPUB, and sends it to your personal `@kindle.com` address. Amazon converts
and delivers it to every registered Kindle/Kindle app.

Prereqs (one-time, on Amazon's side):
  1. Manage Your Content and Devices → Preferences → Personal Document
     Settings → add your SMTP_FROM address to the *Approved Personal
     Document E-mail List*. Mail from any other address is silently dropped.
  2. Note your device's `@kindle.com` address (→ KINDLE_EMAIL in .env).

Usage:
    python3 scripts/send_to_kindle.py path/to/book.epub
    python3 scripts/send_to_kindle.py --series-slug <slug> --book-number <N>

Exit codes: 0 sent · 1 usage/missing file · 2 config/SMTP error.
"""

from __future__ import annotations

import argparse
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import paths as P  # noqa: E402
from lib import setup_doc  # noqa: E402
from lib import slugify  # noqa: E402

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Path) -> dict[str, str]:
    """Minimal .env reader (KEY=VALUE, # comments). No external deps."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def resolve_epub(args, env) -> Path | None:
    if args.epub:
        return Path(args.epub)
    if args.series_slug and args.book_number is not None:
        bp = P.book_paths(args.series_slug, args.book_number)
        title = setup_doc.book_title(setup_doc.load(bp.setup_md)) or args.series_slug
        candidate = bp.book_root / "build" / f"{slugify.slugify(title)}.epub"
        if candidate.exists():
            return candidate
        # Fall back to whatever single .epub sits in build/.
        build = bp.book_root / "build"
        epubs = sorted(build.glob("*.epub")) if build.exists() else []
        return epubs[-1] if epubs else candidate
    return None


def build_subject(args, epub: Path) -> str:
    """Kindle uses the subject as the document title hint. Append the latest
    chapter number so re-sends are distinguishable (Send-to-Kindle never
    replaces, it stacks copies). Falls back to the EPUB filename when unknown."""
    if args.series_slug and args.book_number is not None:
        bp = P.book_paths(args.series_slug, args.book_number)
        title = setup_doc.book_title(setup_doc.load(bp.setup_md)) or args.series_slug
        chapters = P.chapter_numbers(bp)
        if chapters:
            return f"{title} ({chapters[-1]:02d})"
        return title
    return epub.stem


def main() -> int:
    ap = argparse.ArgumentParser(description="Send an EPUB to Kindle by email.")
    ap.add_argument("epub", nargs="?", help="Path to the .epub file.")
    ap.add_argument("--series-slug")
    ap.add_argument("--book-number", type=int)
    ap.add_argument("--to", help="Override KINDLE_EMAIL.")
    args = ap.parse_args()

    env = {**load_env(ENV_PATH), **os.environ}

    epub = resolve_epub(args, env)
    if not epub:
        print("ERROR: give an EPUB path or --series-slug/--book-number.", file=sys.stderr)
        return 1
    if not epub.exists():
        print(f"ERROR: EPUB not found: {epub}\nRun build_epub.py first.", file=sys.stderr)
        return 1

    to_addr = args.to or env.get("KINDLE_EMAIL", "")
    host = env.get("SMTP_HOST", "")
    port = int(env.get("SMTP_PORT", "587") or "587")
    user = env.get("SMTP_USER", "")
    password = env.get("SMTP_PASS", "")
    from_addr = env.get("SMTP_FROM") or user

    missing = [k for k, v in {
        "KINDLE_EMAIL": to_addr, "SMTP_HOST": host,
        "SMTP_USER": user, "SMTP_PASS": password,
    }.items() if not v]
    if missing:
        print(f"ERROR: missing config in .env: {', '.join(missing)}", file=sys.stderr)
        return 2

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = build_subject(args, epub)  # title hint + chapter range.
    msg.set_content("Sent by The Seed Grimoire.")
    msg.add_attachment(
        epub.read_bytes(),
        maintype="application",
        subtype="epub+zip",
        filename=epub.name,
    )

    try:
        with smtplib.SMTP(host, port, timeout=60) as s:
            s.starttls()
            s.login(user, password)
            s.send_message(msg)
    except Exception as exc:  # noqa: BLE001 — surface any SMTP failure plainly.
        print(f"ERROR: send failed: {exc}", file=sys.stderr)
        return 2

    print(f"Sent {epub.name} ({epub.stat().st_size / 1024:.0f} KB) → {to_addr}")
    print("Check your Kindle in a minute (ensure SMTP_FROM is an approved sender).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
