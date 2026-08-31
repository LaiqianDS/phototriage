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


def build_plan(
    source: Path,
    verdicts: dict[str, Verdict],
    pair_raws: bool = True,
    deep: bool = False,
) -> list[Path]:
    """Files to transfer: every kept image, and its RAW originals on request.

    Images that were reviewed but are no longer on disk are skipped, so a plan
    is always executable. `deep` is the same reach the queue was listed with, so
    an image left out of the review is left out of the transfer as well, even
    when a decision about it survives in the state file from an earlier run.
    Each file appears once, because two kept images can share a stem and
    therefore the same RAW original.
    """
    raws = library.raw_index(source, deep) if pair_raws else {}
    plan: list[Path] = []
    seen: set[Path] = set()
    for name, verdict in verdicts.items():
        if verdict is not Verdict.KEEP:
            continue
        image = library.resolve_image(source, name, deep)
        if image is None:
            continue
        for path in (image, *raws.get(image.with_suffix(""), [])):
            if path not in seen:
                seen.add(path)
                plan.append(path)
    return plan


def execute(plan: list[Path], source: Path, destination: Path, mode: Mode) -> int:
    """Send every file in the plan to `destination` and count them.

    A file keeps the subfolder it came from: `2024-08-30/IMG_1.jpg` arrives as
    `2024-08-30/IMG_1.jpg` under the destination. Flattening the tree instead
    would put the `IMG_0042.jpg` of two different days on one name, where the
    second becomes `IMG_0042_1.jpg` and no longer says which day it belongs to.
    In move mode that reading cannot be recovered, because the folder it came
    from is the only place it was written down.

    A source with no subfolders is unaffected: the relative path of a file
    directly inside it is its own name.
    """
    operation = shutil.copy2 if mode is Mode.COPY else shutil.move
    root = source.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for path in plan:
        target = destination / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        operation(str(path), str(free_name(target)))
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
