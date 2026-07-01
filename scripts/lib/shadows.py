"""Shadow timeline: the hidden truth behind the visible story.

shadow.md tells the writer what is REALLY happening behind the scenes — the
antagonist's actual moves, the secret connections, the truth of identities.
The writer reads this in full for every chapter, so they can plant seeds
truthfully even when the POV character is ignorant.

Format:

    # Shadow timeline — <book>

    ## Overview
    Free prose. The big-picture hidden truth of the book.

    ## Act 1 (chapters 1-10)
    Operational truth across this act...

    ### Chapter 1
    - Marek (the gardener) is the assassin sent by the Cardinal.
    - Today is his first day on palace grounds in that role.

    ### Chapter 2
    ...

This file, like seeds.md, is NEVER compressed. It is queried by chapter
to extract the relevant slice when context is being built.
"""

from __future__ import annotations

import re
from pathlib import Path


CHAPTER_HEADER_RE = re.compile(r"^###\s+(?:Chapter|Cap|Capítulo)\s+(\d+)", re.MULTILINE | re.IGNORECASE)
ACT_HEADER_RE = re.compile(r"^##\s+(?:Act|Acto)\s+(\d+)", re.MULTILINE | re.IGNORECASE)
# Any H2 header — used to terminate a chapter slice cleanly even when the
# next section is "## Midpoint" / "## Master truths" instead of "## Act N".
ANY_H2_RE = re.compile(r"^##\s+", re.MULTILINE)


def load_shadow(shadow_path: Path) -> str:
    """Return the raw text of shadow.md."""
    if not shadow_path.exists():
        return ""
    return shadow_path.read_text(encoding="utf-8")


_MASTER_TRUTHS_HEADER_RE = re.compile(r"^##\s+Master truths\b", re.MULTILINE | re.IGNORECASE)


def overview_section(shadow_text: str) -> str:
    """Extract the ## Overview prose (everything before the first Act).

    Stops at the ``## Master truths`` heading / first ``## SHADOW-TRUTH`` record
    too, so the structured truths are NOT dumped raw here — they are rendered by
    ``render_truths_panel`` instead (otherwise they'd appear twice).
    """
    if not shadow_text:
        return ""
    cuts = [m.start() for m in (
        ACT_HEADER_RE.search(shadow_text),
        _MASTER_TRUTHS_HEADER_RE.search(shadow_text),
        SHADOW_TRUTH_HEADER_RE.search(shadow_text),
    ) if m]
    if not cuts:
        return shadow_text.strip()
    return shadow_text[: min(cuts)].strip()


def act_containing(shadow_text: str, chapter: int) -> str:
    """Find the act section whose chapter range contains the given chapter.

    Heuristic: act headers may include a range like "Act 1 (chapters 1-10)".
    We parse the range from the header; if absent, return the act based on
    chapter sub-headers within.
    """
    if not shadow_text:
        return ""

    # Slice the text into acts
    act_starts = list(ACT_HEADER_RE.finditer(shadow_text))
    if not act_starts:
        return shadow_text

    for i, m in enumerate(act_starts):
        start = m.start()
        end = act_starts[i + 1].start() if i + 1 < len(act_starts) else len(shadow_text)
        act_text = shadow_text[start:end]

        # Try parsing range from the header line
        header_line = act_text.split("\n", 1)[0]
        range_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", header_line)
        if range_match:
            lo, hi = int(range_match.group(1)), int(range_match.group(2))
            if lo <= chapter <= hi:
                return act_text.strip()
        else:
            # Fall back: check chapter sub-headers in this act
            ch_nums = [int(c.group(1)) for c in CHAPTER_HEADER_RE.finditer(act_text)]
            if ch_nums and min(ch_nums) <= chapter <= max(ch_nums):
                return act_text.strip()

    return ""


def chapter_section(shadow_text: str, chapter: int) -> str:
    """Find the ### Chapter N section text.

    Returns the section (header + body) or empty string if not found.
    """
    if not shadow_text:
        return ""

    headers = list(CHAPTER_HEADER_RE.finditer(shadow_text))
    for i, m in enumerate(headers):
        if int(m.group(1)) == chapter:
            start = m.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(shadow_text)
            # End at the next H2 (any kind: Act / Midpoint / Master truths)
            # if it appears before the next chapter header.
            next_h2 = ANY_H2_RE.search(shadow_text, m.end())
            if next_h2 and next_h2.start() < end:
                end = next_h2.start()
            return shadow_text[start:end].strip()
    return ""


# --------------------------------------------------------------------------- #
# Master-truth reveal tracking
#
# A shadow truth is hidden FROM THE READER at first and is progressively
# revealed as the book runs — once revealed it stops being a shadow. We track
# only the **reader's** knowledge here (a character learning a truth on the page
# is already tracked by the seed that carries it; see seeds.py).
#
# Crucially we do NOT keep a per-truth reveal schedule: that would duplicate the
# carrier seeds' plant/echo/payoff schedule and drift out of sync. Instead each
# truth declares ``Revealed-by:`` (the carrier seed ids) and its ``Status`` is
# DERIVED from those seeds' statuses, then clamped by ``Reveal cap`` (the loudest
# the truth may get in THIS book — the reveal equivalent of a seed's Dose). A
# truth whose payoff is a later book caps below ``confirmed`` and simply stays
# there at book end; that is not a violation.
#
# The reveal ladder names the READER'S interior state, NOT how hard to write:
#
#     hidden → sensed → suspected → confirmed
#
# This is deliberate. Naming a level "hard hint" invites an LLM to state the
# truth plainly; naming it ``suspected`` keeps the target subtle — the reader is
# brought to suspicion by accumulation, never by a line that says it.
# --------------------------------------------------------------------------- #

SHADOW_TRUTH_HEADER_RE = re.compile(r"^##\s+SHADOW-TRUTH:\s*(.+?)\s*$", re.MULTILINE)
TRUTH_FIELD_RE = re.compile(
    r"^\*\*(?P<key>[^*\n:]+?):\*\*[ \t]*(?P<value>.*?)(?=\n\*\*[^*\n]+?:\*\*|\n##\s|\Z)",
    re.DOTALL | re.MULTILINE,
)
TRUTH_STATUS_LINE_RE = re.compile(r"^\*\*Status:\*\*[ \t]*.*$", re.MULTILINE)

# Ordered reveal ladder (reader's interior state).
REVEAL_LEVELS = ["hidden", "sensed", "suspected", "confirmed"]


from dataclasses import dataclass, field as _field


@dataclass
class Truth:
    """A Master truth and its reader-reveal state.

    A truth with a non-empty ``decoy`` is a **misread**: the carrier seeds do
    not bring the reader toward ``truth`` but toward the FALSE belief named in
    ``decoy``. The same reveal ladder is reused, but for a misread it measures
    the reader's conviction in the decoy, and ``confirmed`` means the payoff
    seed has *inverted* the belief (the truth lands, the decoy collapses). See
    ``render_truths_panel`` / ``is_decoy``.
    """

    id: str
    truth: str = ""
    decoy: str = ""  # the FALSE belief the reader is led to; empty = ordinary truth
    mystery: str = ""  # links a §14b master mystery from the grimoire
    revealed_by: list[str] = _field(default_factory=list)
    reveal_cap: str = "confirmed"
    confirm_in: int | None = None  # only for seedless truths (exposition)
    surfaced: list[str] = _field(default_factory=list)
    status: str = "hidden"

    def is_decoy(self) -> bool:
        return bool(self.decoy.strip())


def _truth_chapter_list(value: str) -> list[int]:
    if not value or value.strip() in ("—", "-", "none", "None", ""):
        return []
    nums = []
    for tok in re.split(r"[,\s]+", value):
        tok = tok.strip("ch ").strip()
        if tok.isdigit():
            nums.append(int(tok))
    return nums


def _truth_chapter(value: str) -> int | None:
    nums = _truth_chapter_list(value)
    return nums[0] if nums else None


def _parse_id_list(value: str) -> list[str]:
    if not value or value.strip() in ("—", "-", "none", "None", ""):
        return []
    out = []
    for tok in re.split(r"[,\s]+", value):
        tok = tok.strip().strip("`").strip()
        if tok:
            out.append(tok)
    return out


def _norm_cap(value: str) -> str:
    v = (value or "").strip().lower()
    return v if v in REVEAL_LEVELS else "confirmed"


def _parse_surfaced(section: str) -> list[str]:
    m = re.search(
        r"^\*\*Surfaced:\*\*[ \t]*(?P<body>.*?)(?=\n\*\*[^*\n]+?:\*\*|\n##\s|\Z)",
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


def load_truths(shadow_path: Path) -> list[Truth]:
    """Parse the ## SHADOW-TRUTH records out of shadow.md.

    Returns [] when the file has no structured truths yet (e.g. an older
    free-prose ## Master truths section), so callers degrade gracefully.
    """
    if not shadow_path.exists():
        return []
    return parse_truths(shadow_path.read_text(encoding="utf-8"))


def parse_truths(shadow_text: str) -> list[Truth]:
    truths: list[Truth] = []
    headers = list(SHADOW_TRUTH_HEADER_RE.finditer(shadow_text))
    for i, h in enumerate(headers):
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(shadow_text)
        section = shadow_text[start:end]
        fields = {}
        for m in TRUTH_FIELD_RE.finditer(section):
            key = m.group("key").strip().lower().replace(" ", "_").replace("-", "_")
            fields[key] = re.sub(r"\s+", " ", m.group("value")).strip()
        truths.append(
            Truth(
                id=h.group(1).strip(),
                truth=fields.get("truth", ""),
                decoy=fields.get("decoy", ""),
                mystery=fields.get("mystery", ""),
                revealed_by=_parse_id_list(fields.get("revealed_by", "")),
                reveal_cap=_norm_cap(fields.get("reveal_cap", "")),
                confirm_in=_truth_chapter(fields.get("confirm_in", "")),
                surfaced=_parse_surfaced(section),
                status=fields.get("status", "hidden"),
            )
        )
    return truths


def _level_index(level: str) -> int:
    try:
        return REVEAL_LEVELS.index(level)
    except ValueError:
        return 0


def _seed_contributes(seed_status: str) -> str:
    """Map a carrier seed's status to the reader-reveal level it produces."""
    s = (seed_status or "").strip()
    if s == "paid_off":
        return "confirmed"
    if s.startswith("echoed"):
        try:
            n = int(s.split("-", 1)[1])
        except (IndexError, ValueError):
            n = 1
        return "suspected" if n >= 2 else "sensed"
    if s == "planted":
        return "sensed"
    return "hidden"


def derive_status(truth: "Truth", seed_status_by_id: dict[str, str]) -> str:
    """Derive a truth's reader-reveal status from its carrier seeds, clamped by
    ``reveal_cap``. Seedless truths (exposition) keep their stored status —
    update-canon advances those manually against ``confirm_in``."""
    if not truth.revealed_by:
        return truth.status
    best = "hidden"
    for sid in truth.revealed_by:
        lvl = _seed_contributes(seed_status_by_id.get(sid, ""))
        if _level_index(lvl) > _level_index(best):
            best = lvl
    if _level_index(best) > _level_index(truth.reveal_cap):
        best = truth.reveal_cap
    return best


# A decoy (misread) reuses the reveal ladder, but each rung names the reader's
# conviction in the FALSE belief, and the top rung means the payoff has flipped
# it. The labels exist only for rendering; the stored status stays in
# REVEAL_LEVELS (so mark_truth.py / derive_status are untouched).
_DECOY_LABELS = {
    "hidden": "neutral",
    "sensed": "misled",
    "suspected": "convinced",
    "confirmed": "inverted",
}
# A misread only earns a slot in the per-chapter panel while it is LIVE — the
# reader is mid-belief. Before it starts (hidden) there is nothing to track, and
# once inverted (confirmed) it is done; both drop out so the panel stays lean.
_DECOY_LIVE_STATES = {"sensed", "suspected"}


def render_truths_panel(truths: list[Truth], active_seed_ids: set[str] | None = None) -> str:
    """Render the Master-truths reveal-state panel for the writer's bundle.

    Ordinary truths render at every status. A misread (a truth with a
    ``decoy``) renders only while it is live (see ``_DECOY_LIVE_STATES``) so the
    deceit guidance does not linger in every later chapter's bundle.

    ``active_seed_ids`` (this chapter's seed envelope) gates how much of each
    truth the writer sees. A truth is *approachable* this chapter only when it
    is already being revealed (status past ``hidden``) or one of its carrier
    seeds is active now. A still-``hidden`` truth nobody touches this chapter is
    rendered **dormant** — name + cap only, with its ``Truth:`` text withheld —
    so its wording cannot bleed into prose chapters before its time (the writer
    pulling "el sumidero apex" into chapter 2 was exactly this leak). Passing
    ``None`` keeps the old behaviour (every truth approachable) for callers that
    do not know the envelope.
    """
    active = set(active_seed_ids or [])
    gate = active_seed_ids is not None
    visible = [t for t in truths
               if not t.is_decoy() or t.status in _DECOY_LIVE_STATES]
    if not visible:
        return ""
    out = [
        "## Master truths — reveal state (writer-only; NEVER state these on the page)",
        "",
        "_Levels name the READER'S interior state to reach **by indirection**, not "
        "how loudly to write. `suspected` is still subtle: the reader gets there by "
        "accumulation, never by a line that says it. Never push a truth past its cap._",
        "",
        "_Ladder: hidden → sensed → suspected → confirmed. The schedule lives in the "
        "carrier seeds (see the seed envelope); these truths only track how far the "
        "reader has been brought._",
        "",
        "_Truths marked **dormant** are not in play this chapter: their full text is "
        "withheld so it cannot leak into the prose early. Do not reach for them._",
        "",
    ]
    for t in visible:
        carriers = ", ".join(f"`{c}`" for c in t.revealed_by) if t.revealed_by \
            else "(exposition — no carrier seed)"
        approachable = (
            not gate
            or t.is_decoy()
            or t.status != "hidden"
            or bool(active & set(t.revealed_by))
        )
        if not approachable:
            out.append(
                f"- `{t.id}` — **dormant** (cap: {t.reveal_cap}) · via {carriers} "
                f"— not in play this chapter; full truth withheld, do not approach"
            )
            continue
        if t.is_decoy():
            label = _DECOY_LABELS.get(t.status, t.status)
            out.append(
                f"- `{t.id}` — MISREAD: reader is **{label}** of a FALSE belief "
                f"(cap: {_DECOY_LABELS.get(t.reveal_cap, t.reveal_cap)}) · via {carriers}"
            )
            out.append(f"  - *Reader wrongly believes:* {t.decoy}")
            out.append(f"  - *Real truth (NEVER on the page until the inversion):* {t.truth}")
            out.append("  - *⚠ Deliberate deceit — do NOT 'correct' it as a canon slip; "
                       "sustain it, then let the carrier payoff invert it.*")
        else:
            out.append(f"- `{t.id}` — **{t.status}** (cap: {t.reveal_cap}) · via {carriers}")
        _render_surfaced(out, t)
    return "\n".join(out) + "\n"


def _render_surfaced(out: list[str], t: "Truth") -> None:
    if not t.surfaced:
        return
    out.append("  - *As surfaced earlier (rhyme with THIS wording):*")
    for line in t.surfaced:
        out.append(f"    - {line}")


def update_truth_status_in_text(text: str, truth_id: str, new_status: str) -> tuple[str, bool]:
    """Surgically set one truth's ``**Status:**`` line in raw shadow.md text.

    Mirrors ``seeds.update_status_in_text``: only the matched record's status
    line is rewritten, everything else preserved byte-for-byte (shadow.md is a
    NEVER-compress, hand-authored file). Returns ``(new_text, found)``.
    """
    headers = list(SHADOW_TRUTH_HEADER_RE.finditer(text))
    for i, h in enumerate(headers):
        if h.group(1).strip() != truth_id:
            continue
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        if TRUTH_STATUS_LINE_RE.search(section):
            new_section = TRUTH_STATUS_LINE_RE.sub(
                lambda _m: f"**Status:** {new_status}", section, count=1
            )
        else:
            new_section = section.rstrip("\n") + f"\n**Status:** {new_status}\n"
        return text[:start] + new_section + text[end:], True
    return text, False


def append_surfaced_in_text(text: str, truth_id: str, surfaced_line: str) -> tuple[str, bool]:
    """Surgically append one ``Surfaced:`` touch-log line to a truth.

    Mirrors ``seeds.append_realized_in_text``. Creates the ``**Surfaced:**``
    block (just before ``**Status:**``) if absent. Returns ``(new_text, found)``.
    """
    bullet = f"- {surfaced_line.strip()}\n"
    headers = list(SHADOW_TRUTH_HEADER_RE.finditer(text))
    for i, h in enumerate(headers):
        if h.group(1).strip() != truth_id:
            continue
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        rm = re.search(r"^\*\*Surfaced:\*\*[ \t]*\n", section, re.MULTILINE)
        if rm:
            pos = rm.end()
            while True:
                mm = re.match(r"[ \t]*[-*][ \t].*\n", section[pos:])
                if not mm:
                    break
                pos += mm.end()
            new_section = section[:pos] + bullet + section[pos:]
        else:
            insert = f"**Surfaced:**\n{bullet}"
            sm = TRUTH_STATUS_LINE_RE.search(section)
            if sm:
                new_section = section[:sm.start()] + insert + section[sm.start():]
            else:
                new_section = section.rstrip("\n") + "\n" + insert
        return text[:start] + new_section + text[end:], True
    return text, False


def _act_preamble(act_text: str) -> str:
    """The act-level operational truth (everything before the first ``### Chapter``
    sub-slice). This is the act's *shape* — Superficie/Sombra — without the
    per-chapter beats of future chapters in the act."""
    if not act_text:
        return ""
    m = CHAPTER_HEADER_RE.search(act_text)
    return (act_text[: m.start()] if m else act_text).strip()


def render_shadow_for_chapter(
    shadow_text: str, chapter: int, active_seed_ids: set[str] | None = None
) -> str:
    """Build the shadow block for a chapter's context.

    Includes: the Master-truths panel (gated by ``active_seed_ids``) + overview +
    the act's operational truth (preamble only) + THIS chapter's own slice.

    Deliberately **NOT** the whole act: the sibling ``### Chapter`` sub-slices of
    later chapters in the same act let the writer foreshadow beats several
    chapters ahead (the "se adelanta" leak). The writer gets the act's shape and
    its own chapter; future chapters' hidden moves stay out until their turn.
    """
    if not shadow_text:
        return "## Shadow timeline\n\n(no shadow file yet)\n"

    parts = ["## Shadow timeline (hidden truth — writer-only, never on page)\n"]

    # Master-truths reveal-state panel (status derived from carrier seeds).
    truths = parse_truths(shadow_text)
    if truths:
        panel = render_truths_panel(truths, active_seed_ids)
        if panel:
            parts.append(panel)

    overview = overview_section(shadow_text)
    if overview and "## Overview" in overview:
        # already includes the heading inside
        parts.append(overview)
    elif overview:
        parts.append("### Overview\n" + overview)

    # Act operational truth: preamble only (no future-chapter sub-slices).
    preamble = _act_preamble(act_containing(shadow_text, chapter))
    if preamble:
        parts.append("")
        parts.append(preamble)

    # This chapter's own slice (the only per-chapter shadow the writer sees).
    ch_section = chapter_section(shadow_text, chapter)
    if ch_section:
        parts.append("")
        parts.append(ch_section)

    return "\n".join(parts) + "\n"
