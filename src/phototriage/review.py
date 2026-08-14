"""The decisions taken about one folder of images."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Verdict(str, Enum):
    """What the reviewer decided about one image."""

    KEEP = "keep"
    DISCARD = "discard"


@dataclass(frozen=True)
class Decision:
    """One reviewed image and its verdict."""

    name: str
    verdict: Verdict


@dataclass
class Review:
    """Where the kept images go, and what has been decided so far.

    The decisions are the only state. The cursor position and the keep and
    discard counts are derived from them, so undo cannot leave two copies of
    the state disagreeing. Decisions are keyed by file name rather than by
    position, so adding or removing files in the source folder does not shift
    the pending queue.
    """

    destination: Path
    decisions: list[Decision] = field(default_factory=list)

    @property
    def verdicts(self) -> dict[str, Verdict]:
        """Verdict by file name, in the order the decisions were taken."""
        return {decision.name: decision.verdict for decision in self.decisions}

    def decide(self, name: str, verdict: Verdict) -> None:
        """Record a verdict for `name`."""
        self.decisions.append(Decision(name, verdict))

    def undo(self) -> None:
        """Drop the most recent decision. Does nothing when there is none."""
        if self.decisions:
            self.decisions.pop()
