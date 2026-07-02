"""Word counting + target validation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .parsing import strip_expand_markers


@dataclass
class WordcountReport:
    actual: int
    target_lo: int
    target_hi: int

    @property
    def ratio_to_low(self) -> float:
        if self.target_lo <= 0:
            return 1.0
        return self.actual / self.target_lo

    @property
    def is_too_short(self) -> bool:
        # Trigger expand if below 80% of low target
        return self.target_lo > 0 and self.actual < 0.8 * self.target_lo

    @property
    def is_too_long(self) -> bool:
        # Trigger trim if above 130% of high target
        return self.target_hi > 0 and self.actual > 1.3 * self.target_hi

    @property
    def in_range(self) -> bool:
        return not (self.is_too_short or self.is_too_long)

    def describe(self) -> str:
        return (
            f"actual={self.actual} target=[{self.target_lo}, {self.target_hi}] "
            f"(ratio to low: {self.ratio_to_low:.0%})"
        )


_WORD_RE = re.compile(r"\b[\w'’-]+\b", re.UNICODE)


def prose_text(text: str) -> str:
    """Reduce a chapter to prose only: strip expand-chapter banner lines, fenced
    code blocks and Markdown headers. One helper so word counting and the prose
    auditor (lib.prose_lint) strip the same scaffolding instead of each
    re-deriving it."""
    text = strip_expand_markers(text)
    # Remove fenced code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove headers but keep their text on subsequent line
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    return text


def count_words(text: str) -> int:
    """Count words in prose only (the EXPAND scaffolding otherwise inflates it by
    ~10 words per inserted zone)."""
    return len(_WORD_RE.findall(prose_text(text)))


def report(actual: int, target_lo: int, target_hi: int) -> WordcountReport:
    return WordcountReport(actual=actual, target_lo=target_lo, target_hi=target_hi)
