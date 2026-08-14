"""Turn the kept decisions into file copies or moves.

Discarded images are never touched: they simply stay in the source folder.
"""

from __future__ import annotations

import itertools
import shutil
from enum import Enum
from pathlib import Path

from . import library
from .review import Verdict


class Mode(str, Enum):
    """How to transfer a kept file to the destination."""

    COPY = "copy"
    MOVE = "move"


def build_plan(source: Path, verdicts: dict[str, Verdict], pair_raws: bool = True) -> list[Path]:
    """Files to transfer: every kept image, and its RAW originals on request.

    Images that were reviewed but are no longer on disk are skipped, so a plan
    is always executable. Each file appears once, because two kept images can
    share a stem and therefore the same RAW original.
    """
    raws = library.raw_index(source) if pair_raws else {}
    plan: list[Path] = []
    seen: set[Path] = set()
    for name, verdict in verdicts.items():
        if verdict is not Verdict.KEEP:
            continue
        image = library.resolve_image(source, name)
        if image is None:
            continue
        for path in (image, *raws.get(image.stem, [])):
            if path not in seen:
                seen.add(path)
                plan.append(path)
    return plan


def execute(plan: list[Path], destination: Path, mode: Mode) -> int:
    """Send every file in the plan to `destination` and count them."""
    operation = shutil.copy2 if mode is Mode.COPY else shutil.move
    destination.mkdir(parents=True, exist_ok=True)
    for path in plan:
        operation(str(path), str(free_name(destination / path.name)))
    return len(plan)


def free_name(target: Path) -> Path:
    """`target` itself, or the first `name_1`, `name_2`... variant that is free.

    Checked immediately before each transfer, so two sources with the same name
    in one run cannot overwrite each other.
    """
    if not target.exists():
        return target
    for suffix in itertools.count(1):
        candidate = target.with_name(f"{target.stem}_{suffix}{target.suffix}")
        if not candidate.exists():
            return candidate
    raise AssertionError("unreachable")
