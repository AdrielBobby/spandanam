"""Kaalam ladder: a tempo readiness ladder over a phrase — pass a step, move to the
next kaalam; fail, retry the same one. Pure functions over an immutable step index,
same style as judge.py's PERFECT/GOOD/MISS grading.

Readiness is read off judge.summary()'s "stars" (0-3), not a separate model call:
stars >= PASS_STARS is the same pass threshold CONTRIBUTING.md already documents for
gemma_game's Repeat-after-Maveli level-up ("stars >= 2 = pass"), reused here for
consistency. Beat timing and hit judging are math in this project and we say so; a
readiness decision derived from that same math belongs with it, not with Gemma.
"""
from __future__ import annotations

from dataclasses import dataclass

PASS_STARS = 2
DEFAULT_SCALES: tuple[float, ...] = (0.6, 0.8, 1.0, 2.0)   # 60% -> 80% -> 100% -> kaalam-doubled


@dataclass(frozen=True)
class Ladder:
    scales: tuple[float, ...] = DEFAULT_SCALES
    phrase: int | None = None      # which sc.phrases[] segment to drill; None = whole score
    step: int = 0

    def __post_init__(self) -> None:
        if not self.scales:
            raise ValueError("Ladder.scales must be non-empty")
        non_positive = [s for s in self.scales if s <= 0]
        if non_positive:
            raise ValueError(f"Ladder.scales must all be > 0, got {non_positive}")
        if not (0 <= self.step < len(self.scales)):
            raise ValueError(f"Ladder.step {self.step} out of range for {len(self.scales)} scales")

    @property
    def bpm_scale(self) -> float:
        return self.scales[self.step]

    @property
    def total_steps(self) -> int:
        return len(self.scales)


@dataclass(frozen=True)
class LadderResult:
    ladder: Ladder | None    # None once the ladder is finished (complete)
    event: str               # "step_up" | "retry" | "complete"


def advance(ladder: Ladder, stars: int) -> LadderResult:
    """Decide the next ladder state from one round's stars. stars >= PASS_STARS moves
    to the next tempo step (or completes if this was the last one); otherwise the
    ladder stays on the current step for a retry."""
    if stars < PASS_STARS:
        return LadderResult(ladder, "retry")
    next_step = ladder.step + 1
    if next_step >= ladder.total_steps:
        return LadderResult(None, "complete")
    return LadderResult(Ladder(ladder.scales, ladder.phrase, next_step), "step_up")
