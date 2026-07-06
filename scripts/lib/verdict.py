"""Compute a critique verdict from the findings file, deterministically.

The critic used to both write findings AND apply the PASS/REVISE/REJECT
thresholds by judgment — at the exact step that triggers actions (revise loop,
lock-in, HARD STOP). Threshold discretion is where severity inflation/deflation
leaks in. This module parses the findings a critic already wrote and derives the
verdict by counting, so the number that drives the pipeline is not a judgment.

Findings format the critic writes (per the critique SKILL.md):

    ## MUST fix
    - **[issue-type]** — quoted line → direction
    ## SHOULD fix
    - ...
    ## CONSIDER
    - ...

A REJECT-tier verdict fires only when a MUST finding's ``[issue-type]`` matches
the target's structural vocabulary (below). Everything else with a MUST is
REVISE; zero MUST within the SHOULD cap is PASS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# SHOULD cap for PASS, per target. A chapter is held tighter than a whole plan
# or grimoire, whose larger surface legitimately carries more minor findings.
_SHOULD_CAP = {"chapter": 3, "plan": 6, "grimoire": 6}

# REJECT-tier issue types: a MUST of one of these is a STRUCTURAL break that a
# surgical pass cannot fix (needs a scene rewrite / outline / grimoire change).
# Matched as case-insensitive substrings of the bracketed [issue-type], so the
# critic's slug need only contain the keyword.
_REJECT_TIER = {
    "chapter": (
        "missing-beat", "canon-contradiction", "unseeded-payoff",
        "contrived-trigger", "deus-ex-machina",
    ),
    "plan": (
        "climax-unplanted", "shadow-single-layer", "principal-no-decision",
        "subplot-hermetic", "magic-missing-pillar",
    ),
    "grimoire": (
        "magic-missing-pillar", "no-antagonist-thesis", "climax-passive",
        "no-clock", "system-arc-undeclared", "empty-14-table",
    ),
}

_SECTION_RE = re.compile(r"^##\s+(MUST fix|SHOULD fix|CONSIDER)\b.*$", re.MULTILINE)
_BULLET_RE = re.compile(r"^-\s+(.*)$", re.MULTILINE)          # top-level bullets only
_ISSUE_TYPE_RE = re.compile(r"\*\*\[([^\]]+)\]\*\*")


@dataclass
class Verdict:
    verdict: str          # PASS | REVISE | REJECT
    must: int
    should: int
    consider: int
    reject_tags: list[str]

    def line(self) -> str:
        return (f"VERDICT: {self.verdict} "
                f"(MUST={self.must} SHOULD={self.should} CONSIDER={self.consider})")


def section_bodies(text: str) -> dict[str, str]:
    """Split a critique into its MUST / SHOULD / CONSIDER section bodies.

    Public so quote-verification (lib.quotes) can read the same sections the
    verdict counts, without re-implementing the header parsing.
    """
    out: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        name = m.group(1).split()[0].upper()  # MUST / SHOULD / CONSIDER
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[name] = text[start:end]
    return out


def bullets(body: str) -> list[str]:
    """Top-level ``- `` bullets in a section body (sub-bullets excluded)."""
    return _BULLET_RE.findall(body)


def compute_verdict(text: str, target: str = "chapter") -> Verdict:
    if target not in _SHOULD_CAP:
        raise ValueError(f"unknown target {target!r}")
    bodies = section_bodies(text)
    must_bullets = bullets(bodies.get("MUST", ""))
    should = len(bullets(bodies.get("SHOULD", "")))
    consider = len(bullets(bodies.get("CONSIDER", "")))

    reject_vocab = _REJECT_TIER[target]
    reject_tags: list[str] = []
    for b in must_bullets:
        m = _ISSUE_TYPE_RE.search(b)
        if not m:
            continue
        issue = m.group(1).lower()
        for kw in reject_vocab:
            if kw in issue:
                reject_tags.append(m.group(1))
                break

    must = len(must_bullets)
    if reject_tags:
        v = "REJECT"
    elif must == 0 and should <= _SHOULD_CAP[target]:
        v = "PASS"
    else:
        v = "REVISE"
    return Verdict(v, must, should, consider, reject_tags)
