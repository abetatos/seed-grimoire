"""The book's clock: (día, franja) with ordered franjas and ordinal arithmetic.

Time is not free text and not minutes. It is a day number plus a named part of
the day, drawn from an ordered vocabulary. Arithmetic is ordinal only: a clock
can be compared, and time can only ever advance (monotonic) — a `time` event that
would move the clock backwards is an unrepresentable state, rejected at commit.

`elapsed_bucket` maps a span between two clocks onto the same ordinal cost buckets
the graph uses, so feasibility ("could X travel here in that time?") is a single
ordinal comparison. It is deliberately coarse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .graph import COSTS

# Ordered parts of the day, earliest first.
FRANJAS = ("madrugada", "mañana", "mediodía", "tarde", "noche")
FRANJA_INDEX = {f: i for i, f in enumerate(FRANJAS)}
_FRANJAS_PER_DAY = len(FRANJAS)


class ClockError(ValueError):
    """A malformed clock value or a non-monotonic advance."""


@dataclass(frozen=True)
class Clock:
    day: int
    franja_idx: int

    @classmethod
    def of(cls, day: int, franja: str) -> "Clock":
        if franja not in FRANJA_INDEX:
            raise ClockError(f"unknown franja {franja!r} (expected one of {FRANJAS})")
        if day < 1:
            raise ClockError(f"day must be >= 1, got {day}")
        return cls(day=day, franja_idx=FRANJA_INDEX[franja])

    @property
    def franja(self) -> str:
        return FRANJAS[self.franja_idx]

    def _ord(self) -> int:
        """A single monotonic ordinal for comparison (franja-steps since day 1)."""
        return self.day * _FRANJAS_PER_DAY + self.franja_idx

    # Ordinal comparisons — a clock is a point on a totally ordered timeline.
    def __lt__(self, other: "Clock") -> bool:
        return self._ord() < other._ord()

    def __le__(self, other: "Clock") -> bool:
        return self._ord() <= other._ord()

    def __gt__(self, other: "Clock") -> bool:
        return self._ord() > other._ord()

    def __ge__(self, other: "Clock") -> bool:
        return self._ord() >= other._ord()

    def __str__(self) -> str:
        return f"día {self.day}, {self.franja}"

    def to_dict(self) -> dict:
        return {"day": self.day, "franja": self.franja}

    @classmethod
    def from_dict(cls, d: dict) -> "Clock":
        return cls.of(d["day"], d["franja"])


def elapsed_steps(a: Clock, b: Clock) -> int:
    """Number of franja-steps from a to b (negative if b precedes a)."""
    return b._ord() - a._ord()


def elapsed_bucket(a: Clock, b: Clock) -> str:
    """Coarsely map the span a→b onto a graph cost bucket, for feasibility.

    0 steps → minutos, 1 → horas, within a day → medio-día, ~1 day → día,
    more than a day → días. A span at least this large can absorb a journey of
    the returned bucket or cheaper.
    """
    steps = elapsed_steps(a, b)
    if steps <= 0:
        return COSTS[0]  # minutos
    if steps == 1:
        return "horas"
    if steps < _FRANJAS_PER_DAY:
        return "medio-día"
    if steps < 2 * _FRANJAS_PER_DAY:
        return "día"
    return "días"
