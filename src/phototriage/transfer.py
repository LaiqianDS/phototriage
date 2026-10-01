"""Turn the kept decisions into file copies or moves."""

from __future__ import annotations

import filecmp
import itertools
import shutil
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from . import library
from .config import RAW_EXTS
from .review import Verdict


class Mode(str, Enum):
    """How to transfer a kept file to the destination."""

    COPY = "copy"
    MOVE = "move"


def build_plan(
    source: Path,
    verdicts: dict[str, Verdict],
    companions: frozenset[str] = RAW_EXTS,
    deep: bool = False,
    skip: Path | None = None,
) -> list[Path]:
    """Files to transfer: every kept image, and what shares its name."""
    beside = library.companion_index(source, companions, deep) if companions else {}
    plan: list[Path] = []
    seen: set[Path] = set()
    for name, verdict in verdicts.items():
        if verdict is not Verdict.KEEP:
            continue
        image = library.resolve_image(source, name, deep, skip)
        if image is None:
            continue
        for path in (image, *beside.get(image.with_suffix(""), [])):
            if path not in seen:
                seen.add(path)
                plan.append(path)
    return plan


@dataclass
class Outcome:
    """What a run did with the files of its plan."""

    transferred: int = 0
    #: Left alone in copy mode, because the destination already held the same bytes.
    already_present: int = 0
    #: The reason each file could not be transferred, by its name in the queue.
    failed: dict[str, str] = field(default_factory=dict)


def execute(
    plan: list[Path],
    source: Path,
    destination: Path,
    mode: Mode,
    on_file: Callable[[int], None] | None = None,
) -> Outcome:
    """Send every file in the plan to `destination` and count what happened."""
    operation = shutil.copy2 if mode is Mode.COPY else shutil.move
    root = source.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    outcome = Outcome()
    for index, path in enumerate(plan):
        if on_file is not None:
            on_file(index)
        relative = path.relative_to(root)
        target = destination / relative
        landing: Path | None = None
        try:
            if mode is Mode.COPY and already_copied(path, target):
                outcome.already_present += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            landing = free_name(target)
            operation(str(path), str(landing))
        except OSError as error:
            # Across two disks a move is a copy and then a removal of the original, so what is left
            # here may also be a whole copy of a file whose original could not be removed.
            if landing is not None and path.exists():
                landing.unlink(missing_ok=True)
            outcome.failed[relative.as_posix()] = error.strerror or str(error)
            continue
        outcome.transferred += 1
    return outcome


def variants(target: Path) -> Iterator[Path]:
    """`target`, then `name_1`, `name_2`... in the order a free name is looked for."""
    yield target
    for suffix in itertools.count(1):
        yield target.with_name(f"{target.stem}_{suffix}{target.suffix}")


def free_name(target: Path) -> Path:
    """`target` itself, or the first `name_1`, `name_2`... variant that is free."""
    return next(candidate for candidate in variants(target) if not candidate.exists())


def already_copied(path: Path, target: Path) -> bool:
    """Whether `target`, or a numbered variant of it, holds the same bytes as `path`."""
    # `filecmp` remembers its answers by size and time, and the server lives for hours.
    filecmp.clear_cache()
    taken = itertools.takewhile(Path.exists, variants(target))
    return any(filecmp.cmp(path, candidate, shallow=False) for candidate in taken)
