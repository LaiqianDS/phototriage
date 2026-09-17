"""Turn the kept decisions into file copies or moves.

Discarded images are never touched: they simply stay in the source folder.
"""

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
    """Files to transfer: every kept image, and what shares its name.

    `companions` is the set of extensions that follow a kept image, so an empty
    set sends the images alone. Images that were reviewed but are no longer on
    disk are skipped, so a plan is always executable. `deep` is the same reach
    the queue was listed with, so an image left out of the review is left out of
    the transfer as well, even when a decision about it survives in the state
    file from an earlier run. Each file appears once, because two kept images
    can share a name and therefore the same original beside it.

    `skip` narrows that reach like it narrows the queue. The companion index
    needs no such limit: a companion only ever sits beside its own image, so an
    image outside `skip` never pairs with a file inside it.
    """
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
    """Send every file in the plan to `destination` and count what happened.

    A file keeps the subfolder it came from: `2024-08-30/IMG_1.jpg` arrives as
    `2024-08-30/IMG_1.jpg` under the destination. Flattening the tree instead
    would put the `IMG_0042.jpg` of two different days on one name, where the
    second becomes `IMG_0042_1.jpg` and no longer says which day it belongs to.
    In move mode that reading cannot be recovered, because the folder it came
    from is the only place it was written down.

    A source with no subfolders is unaffected: the relative path of a file
    directly inside it is its own name.

    In copy mode a file already copied is not copied again, so a second run
    transfers only what the first one did not. Move mode has no such check: the
    file is still in the source, so it was never moved, and the move goes ahead.

    A file that cannot be transferred is recorded and the run carries on, so
    one unreadable file does not keep the rest of the selection back, and the
    count of what did arrive is never lost. Whatever that file left under its
    new name is removed: the name was free a moment before, so it can only be
    the start of a copy cut short, and a truncated photo under a real name
    reads as a kept one. Only a destination that cannot be created at all
    stops the run, because then nothing can arrive.

    `on_file` is called with the position of each file in the plan just before
    it is handled, whatever then becomes of it, so a caller can tell how far a
    long run has gone. A
    count of transfers alone would stop short of the total whenever a file is
    skipped or fails.
    """
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
            # Across two disks a move is a copy and then a removal of the
            # original, so what is left here may also be a whole copy of a file
            # whose original could not be removed. Taking it away then leaves
            # the file untransferred rather than in two places. The original is
            # checked first: if it is gone, what is here is the only copy left,
            # and it stays, whatever step of the move raised.
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
    """`target` itself, or the first `name_1`, `name_2`... variant that is free.

    Checked immediately before each transfer, so two sources with the same name
    in one run cannot overwrite each other.
    """
    return next(candidate for candidate in variants(target) if not candidate.exists())


def already_copied(path: Path, target: Path) -> bool:
    """Whether `target`, or a numbered variant of it, holds the same bytes as `path`.

    The variants are searched as far as the first free name, because that is
    as far as `free_name` would have gone: a stranger holding `photo.png` sends
    the first copy to `photo_1.png`, and that is where a second run has to look.

    The bytes are compared, not the size and the date. Taking a different file
    for a copy would leave a kept photo out of the destination, with nothing to
    say so. The price is reading both files whenever the sizes match, which on a
    second run costs about what the copy would have, and writes nothing.

    `filecmp` remembers its answers, keyed by the size and the time of both
    files, and the server lives for hours. The memory is dropped first, so a
    copy rewritten in place since an earlier run is read again.
    """
    filecmp.clear_cache()
    taken = itertools.takewhile(Path.exists, variants(target))
    return any(filecmp.cmp(path, candidate, shallow=False) for candidate in taken)
