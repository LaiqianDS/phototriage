"""Read-only view of the files on disk."""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from .config import IMAGE_EXTS


def ordered(names: list[str]) -> list[str]:
    """Sort case-insensitively, with the exact name breaking ties.

    Without the tie-break, two names differing only in case would keep the
    order the filesystem happened to return, which is not reproducible.
    """
    return sorted(names, key=lambda name: (name.lower(), name))


def suffix(name: str) -> str:
    """The extension of `name`, lowercased, read exactly the way `Path.suffix` reads it.

    The listing works on plain names because building a `Path` for every file
    was nearly all of what a request cost on a large folder. `resolve_image`
    still asks `Path.suffix`, and the two must never disagree about a name, so
    this is its rule rather than `os.path.splitext`, which gives `..jpg` none.
    """
    dot = name.rfind(".")
    return name[dot:].lower() if 0 < dot < len(name) - 1 else ""


def walk(folder: Path, skip: Path | None = None) -> Iterator[os.DirEntry[str]]:
    """Every file under `folder`, however deep, except under `skip`.

    A folder whose name starts with a dot is left out, like it is in the
    browser. A symbolic link to a folder is not followed, which is what keeps a
    link pointing at one of its own parents from walking for ever, and matches
    `resolve_image` refusing to serve anything a link leads to.

    A subfolder that cannot be read is skipped instead of ending the walk, so
    one unreadable corner of a card does not hide the rest of the shoot.

    `skip` is a subfolder to leave out whole, which is how a destination inside
    the source stays out of the queue. It is compared as a path, so it has to be
    spelled from the same `folder`, resolved, for the two to meet.

    The walk yields directory entries, not paths. An entry already carries its
    name and its full path as strings, and `os.scandir` has usually learnt
    whether it is a file while listing, so a file costs no `Path` and no extra
    system call. On 4,500 images that took a state read from 86 ms to 4 ms.
    """
    skipped = None if skip is None else str(skip)
    try:
        with os.scandir(folder) as scan:
            entries = list(scan)
    except OSError:
        return
    for entry in entries:
        if entry.is_dir():
            if not entry.is_symlink() and not entry.name.startswith(".") and entry.path != skipped:
                yield from walk(Path(entry.path), skip)
        elif entry.is_file():
            yield entry


def list_images(source: Path, deep: bool = False, skip: Path | None = None) -> list[str]:
    """Names of the reviewable images in `source`, in a stable order.

    A name is relative to `source` and always spelled with forward slashes:
    `IMG_1.jpg` for a file in the folder itself, `2024-08-30/IMG_1.jpg` for one
    `deep` reached in a subfolder. A file directly inside the folder is
    therefore named exactly as it was before subfolders were searched, which is
    what lets the decisions in an existing state file keep matching.

    `skip` is a subfolder that `deep` does not reach into, see `walk`.

    A folder that cannot be listed, because it is missing or unreadable, reads
    as empty. Raising here would turn every later request into a server error,
    because the folder is read again on each one.
    """
    if deep:
        found: Iterable[os.DirEntry[str]] = walk(source, skip)
    else:
        try:
            with os.scandir(source) as scan:
                found = [entry for entry in scan if entry.is_file()]
        except OSError:
            return []
    # Every entry path starts with the source as it was given, so cutting that
    # off is the relative name. The separator after it is stripped rather than
    # counted, because a root such as `/` already ends in one.
    root = str(source)
    return ordered(
        [
            entry.path[len(root) :].lstrip(os.sep).replace(os.sep, "/")
            for entry in found
            if suffix(entry.name) in IMAGE_EXTS
        ]
    )


def is_readable(folder: Path) -> bool:
    """Whether `folder` can be listed at all.

    Asked before a folder is accepted as a source, so that an unreadable one is
    refused instead of being stored and repeated on every restart.
    """
    try:
        next(folder.iterdir(), None)
    except OSError:
        return False
    return True


def list_folders(source: Path) -> list[str]:
    """Names of the visible subfolders of `source`, in a stable order.

    Hidden folders are left out to keep the browser readable.
    """
    return ordered(
        [
            entry.name
            for entry in source.iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        ]
    )


def resolve_image(
    source: Path, name: str, deep: bool = False, skip: Path | None = None
) -> Path | None:
    """Path of the image `name` inside `source`.

    Returns None when the file is absent, when it is not a reviewable image, or
    when `name` points outside the source folder. The last check is made after
    resolving, so neither `..` nor a symbolic link can step out of the folder
    and read the rest of the disk.

    `deep` decides how far inside counts: the folder itself, or the whole tree
    under it, less `skip`. It is the same reach `list_images` was given, so an
    image outside the queue can be neither served nor transferred.
    """
    root = source.resolve()
    candidate = (source / name).resolve()
    if candidate.suffix.lower() not in IMAGE_EXTS or not candidate.is_file():
        return None
    inside = candidate.is_relative_to(root) if deep else candidate.parent == root
    if skip is not None and candidate.is_relative_to(skip):
        return None
    return candidate if inside else None


def companion_index(
    source: Path, extensions: frozenset[str], deep: bool = False
) -> dict[Path, list[Path]]:
    """Map each path without its extension to the files of `extensions` beside it.

    So `/shoot/IMG_1` to `/shoot/IMG_1.CR2`, keyed by the whole path rather than
    by the bare stem: an `IMG_1.CR2` in one subfolder must never be paired with
    the `IMG_1.jpg` of another, and two days of the same card number them alike.

    Built once per plan so that pairing an image with whatever follows it stays
    a dictionary lookup instead of a folder scan.
    """
    index: dict[Path, list[Path]] = {}
    if not source.is_dir():
        return index
    # Paths here, not names: this runs once per transfer, not once per request.
    found = (Path(entry.path) for entry in walk(source)) if deep else source.iterdir()
    for entry in sorted(found):
        if entry.is_file() and entry.suffix.lower() in extensions:
            index.setdefault(entry.with_suffix(""), []).append(entry)
    return index
