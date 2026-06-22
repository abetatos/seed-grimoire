"""Seeds: parse, filter, update.

Format of seeds.md:

    # Seeds — <book title>

    ## SEED: <id>
    **Detail:** ...
    **Real meaning:** ...
    **Plant in:** 12
    **Echo in:** 18, 24
    **Payoff in:** 31
    **How to plant:** ...
    **How to pay off:** ...
    **Trigger:** the intrinsic, already-seeded cause that fires the payoff
    **Dose:** telegraph budget — how many touches and how loud, given the
        plant->payoff distance (a payoff <=2 chapters from its plant must be
        a single quiet touch, never re-described at the payoff chapter open)
    **Resolution image:** (optional) the plant image the payoff inverts/resolves
    **Realized:**
    - ch1: the AS-WRITTEN concrete image used, not the plan's intention
    - ch5: ...
    **Status:** planned

    `Trigger`, `Dose` and `Resolution image` are optional and may be absent on
    older seeds; they default to empty.

    `Realized` is the touch-log: each time a seed is planted/echoed,
    `update-canon` appends one line recording the image AS WRITTEN (+ chapter).
    Because seeds.md is NEVER compressed, this makes a payoff 20+ chapters later
    rhyme with what actually landed on the page, not with the plan — without
    re-loading the old chapter's prose. Absent on older seeds; defaults to [].

Statuses progress as the book is written:
    planned → planted → echoed-1 → echoed-2 → ... → paid_off

This file is NEVER compressed. It is the source of truth for foreshadowing
across the whole book (and survives act compression).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


SEED_HEADER_RE = re.compile(r"^##\s+SEED:\s*(.+?)\s*$", re.MULTILINE)
# Capture a field's value across wrapped continuation lines: everything up to
# the next field header (`**Key:**` at line start), the next `## ` section, or
# end of the section. Without DOTALL the value would stop at the first newline
# and silently drop wrapped lines.
FIELD_RE = re.compile(
    r"^\*\*(?P<key>[^*]+?):\*\*[ \t]*(?P<value>.*?)(?=\n\*\*[^*\n]+?:\*\*|\n##\s|\Z)",
    re.DOTALL | re.MULTILINE,
)
STATUS_LINE_RE = re.compile(r"^\*\*Status:\*\*[ \t]*.*$", re.MULTILINE)


@dataclass
class Seed:
    id: str
    detail: str = ""
    real_meaning: str = ""
    plant_in: int | None = None
    echo_in: list[int] = field(default_factory=list)
    payoff_in: int | None = None
    how_to_plant: str = ""
    how_to_pay_off: str = ""
    trigger: str = ""
    dose: str = ""
    resolution_image: str = ""
    realized: list[str] = field(default_factory=list)
    status: str = "planned"

    def is_planted(self) -> bool:
        return self.status not in ("planned",)

    def is_paid(self) -> bool:
        return self.status == "paid_off"

    def to_markdown(self) -> str:
        echo_str = ", ".join(str(n) for n in self.echo_in) if self.echo_in else "—"
        out = (
            f"## SEED: {self.id}\n"
            f"**Detail:** {self.detail}\n"
            f"**Real meaning:** {self.real_meaning}\n"
            f"**Plant in:** {self.plant_in if self.plant_in is not None else '—'}\n"
            f"**Echo in:** {echo_str}\n"
            f"**Payoff in:** {self.payoff_in if self.payoff_in is not None else '—'}\n"
            f"**How to plant:** {self.how_to_plant}\n"
            f"**How to pay off:** {self.how_to_pay_off}\n"
        )
        # Optional fields: only emitted when present, so legacy seeds stay clean.
        if self.trigger:
            out += f"**Trigger:** {self.trigger}\n"
        if self.dose:
            out += f"**Dose:** {self.dose}\n"
        if self.resolution_image:
            out += f"**Resolution image:** {self.resolution_image}\n"
        if self.realized:
            out += "**Realized:**\n"
            for line in self.realized:
                out += f"- {line}\n"
        out += f"**Status:** {self.status}\n"
        return out


def _parse_realized(section: str) -> list[str]:
    """Extract the Realized touch-log lines from a seed section.

    Handles both a bulleted block and an inline value. Returns the bullet
    contents without the leading marker; preserves order. The generic FIELD_RE
    would collapse newlines, so Realized is parsed separately to keep one line
    per touch.
    """
    m = re.search(
        r"^\*\*Realized:\*\*[ \t]*(?P<body>.*?)(?=\n\*\*[^*\n]+?:\*\*|\n##\s|\Z)",
        section,
        re.DOTALL | re.MULTILINE,
    )
    if not m:
        return []
    items: list[str] = []
    for line in m.group("body").splitlines():
        line = re.sub(r"^[ \t]*[-*][ \t]*", "", line.strip())
        if line:
            items.append(line)
    return items


def _parse_chapter_list(value: str) -> list[int]:
    if not value or value.strip() in ("—", "-", "none", "None", ""):
        return []
    nums = []
    for tok in re.split(r"[,\s]+", value):
        tok = tok.strip("ch ").strip()
        if tok.isdigit():
            nums.append(int(tok))
    return nums


def _parse_chapter(value: str) -> int | None:
    nums = _parse_chapter_list(value)
    return nums[0] if nums else None


def load_seeds(seeds_path: Path) -> list[Seed]:
    """Parse seeds.md into a list of Seed objects."""
    if not seeds_path.exists():
        return []
    text = seeds_path.read_text(encoding="utf-8")
    seeds: list[Seed] = []

    # Find each SEED section by header position
    headers = list(SEED_HEADER_RE.finditer(text))
    for i, h in enumerate(headers):
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        seed_id = h.group(1).strip()
        fields = {}
        for m in FIELD_RE.finditer(section):
            key = m.group("key").strip().lower().replace(" ", "_")
            # Collapse wrapped continuation lines into one logical value.
            fields[key] = re.sub(r"\s+", " ", m.group("value")).strip()
        seeds.append(
            Seed(
                id=seed_id,
                detail=fields.get("detail", ""),
                real_meaning=fields.get("real_meaning", ""),
                plant_in=_parse_chapter(fields.get("plant_in", "")),
                echo_in=_parse_chapter_list(fields.get("echo_in", "")),
                payoff_in=_parse_chapter(fields.get("payoff_in", "")),
                how_to_plant=fields.get("how_to_plant", ""),
                how_to_pay_off=fields.get("how_to_pay_off", ""),
                trigger=fields.get("trigger", ""),
                dose=fields.get("dose", ""),
                resolution_image=fields.get("resolution_image", ""),
                realized=_parse_realized(section),
                status=fields.get("status", "planned"),
            )
        )
    return seeds


def save_seeds(seeds_path: Path, seeds: list[Seed], book_title: str = "") -> None:
    """Write a list of Seeds back to seeds.md. Preserves ordering."""
    lines = [f"# Seeds — {book_title}\n" if book_title else "# Seeds\n", ""]
    lines.append(
        "These are the foreshadowing seeds for the whole book. Status progresses as\n"
        "chapters are written: `planned → planted → echoed-N → paid_off`.\n\n"
        "**NEVER compress or summarize this file.** It is consulted on every chapter.\n"
    )
    for seed in seeds:
        lines.append("")
        lines.append(seed.to_markdown())
    seeds_path.parent.mkdir(parents=True, exist_ok=True)
    seeds_path.write_text("\n".join(lines), encoding="utf-8")


def envelope_for_chapter(seeds: list[Seed], chapter: int) -> dict:
    """Compute the seed envelope for a chapter:

    Returns dict with keys: plant, echo, payoff. Each is a list of Seeds.
    """
    plant = [s for s in seeds if s.plant_in == chapter]
    echo = [s for s in seeds if chapter in s.echo_in]
    payoff = [s for s in seeds if s.payoff_in == chapter]
    return {"plant": plant, "echo": echo, "payoff": payoff}


def render_envelope(envelope: dict, chapter: int) -> str:
    """Render the seed envelope as a Markdown block for the writer's prompt."""
    if not (envelope["plant"] or envelope["echo"] or envelope["payoff"]):
        return f"## Seeds active in chapter {chapter}\n\nNone scheduled.\n"

    out = [f"## Seeds active in chapter {chapter}\n"]

    if envelope["plant"]:
        out.append("### Plant (introduce for the first time)\n")
        for s in envelope["plant"]:
            out.append(f"- **[{s.id}]** {s.detail}")
            out.append(f"  - *Real meaning (hidden from reader):* {s.real_meaning}")
            out.append(f"  - *How to plant:* {s.how_to_plant}")
            if s.dose:
                out.append(f"  - *Dose (telegraph budget — obey exactly):* {s.dose}")
            if s.resolution_image:
                out.append(f"  - *Resolution image (plant this image now so the payoff can invert it):* {s.resolution_image}")
            out.append("")
    if envelope["echo"]:
        out.append("### Echo (subtle reinforcement of an existing seed)\n")
        for s in envelope["echo"]:
            out.append(f"- **[{s.id}]** {s.detail}")
            out.append(f"  - *Originally planted ch {s.plant_in}. Do not draw attention.*")
            if s.dose:
                out.append(f"  - *Dose (telegraph budget — obey exactly):* {s.dose}")
            _render_realized(out, s)
            out.append("")
    if envelope["payoff"]:
        out.append("### Pay off (this seed comes due)\n")
        for s in envelope["payoff"]:
            out.append(f"- **[{s.id}]** {s.detail}")
            out.append(f"  - *Real meaning:* {s.real_meaning}")
            out.append(f"  - *How to pay off:* {s.how_to_pay_off}")
            if s.trigger:
                out.append(f"  - *Trigger (the intrinsic, already-seeded cause that fires this — do NOT invent a convenient external one):* {s.trigger}")
            if s.dose:
                out.append(f"  - *Dose (telegraph budget — obey exactly):* {s.dose}")
            if s.resolution_image:
                out.append(f"  - *Resolution image (invert/transform the image planted earlier; let it click, do not explain):* {s.resolution_image}")
            _render_realized(out, s)
            out.append("")
    return "\n".join(out)


def _render_realized(out: list[str], s: "Seed") -> None:
    """Append the seed's realized touch-log so an echo/payoff rhymes with what
    actually landed on the page earlier — not with the plan's intention."""
    if not s.realized:
        return
    out.append("  - *As realized earlier (rhyme with THIS wording, not the plan):*")
    for line in s.realized:
        out.append(f"    - {line}")


def mark_status(seeds: list[Seed], seed_id: str, new_status: str) -> bool:
    """Update the status of a seed by id. Returns True if found."""
    for s in seeds:
        if s.id == seed_id:
            s.status = new_status
            return True
    return False


def update_status_in_text(text: str, seed_id: str, new_status: str) -> tuple[str, bool]:
    """Surgically set one seed's ``**Status:**`` line in raw seeds.md text.

    Only the matched seed's status line is rewritten; everything else in the
    file is preserved byte-for-byte. Prefer this over the ``load_seeds`` →
    ``save_seeds`` round-trip for status mutations: ``seeds.md`` is a
    NEVER-compress file with wrapped multi-line fields and a hand-written
    header, and regenerating it would reflow/drop that content. Returns
    ``(new_text, found)``.
    """
    headers = list(SEED_HEADER_RE.finditer(text))
    for i, h in enumerate(headers):
        if h.group(1).strip() != seed_id:
            continue
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        if STATUS_LINE_RE.search(section):
            # lambda replacement avoids backreference issues in new_status
            new_section = STATUS_LINE_RE.sub(
                lambda _m: f"**Status:** {new_status}", section, count=1
            )
        else:
            new_section = section.rstrip("\n") + f"\n**Status:** {new_status}\n"
        return text[:start] + new_section + text[end:], True
    return text, False


def append_realized_in_text(text: str, seed_id: str, realized_line: str) -> tuple[str, bool]:
    """Surgically append one ``Realized:`` touch-log line to a seed.

    Mirrors ``update_status_in_text``: only the matched seed's section is
    touched, everything else preserved byte-for-byte (seeds.md is a
    NEVER-compress file). Creates the ``**Realized:**`` block (just before
    ``**Status:**``) if absent. Returns ``(new_text, found)``.
    """
    bullet = f"- {realized_line.strip()}\n"
    headers = list(SEED_HEADER_RE.finditer(text))
    for i, h in enumerate(headers):
        if h.group(1).strip() != seed_id:
            continue
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        rm = re.search(r"^\*\*Realized:\*\*[ \t]*\n", section, re.MULTILINE)
        if rm:
            # Append after the last contiguous bullet line of the existing block.
            pos = rm.end()
            while True:
                mm = re.match(r"[ \t]*[-*][ \t].*\n", section[pos:])
                if not mm:
                    break
                pos += mm.end()
            new_section = section[:pos] + bullet + section[pos:]
        else:
            insert = f"**Realized:**\n{bullet}"
            sm = STATUS_LINE_RE.search(section)
            if sm:
                new_section = section[:sm.start()] + insert + section[sm.start():]
            else:
                new_section = section.rstrip("\n") + "\n" + insert
        return text[:start] + new_section + text[end:], True
    return text, False
