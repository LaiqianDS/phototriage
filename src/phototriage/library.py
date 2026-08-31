"""Read-only view of the files on disk."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from .config import IMAGE_EXTS, RAW_EXTS


def ordered(names: list[str]) -> list[str]:
    """Sort case-insensitively, with the exact name breaking ties.

    Without the tie-break, two names differing only in case would keep the
    order the filesystem happened to return, which is not reproducible.
    """
    return sorted(names, key=lambda name: (name.lower(), name))


def walk(folder: Path) -> Iterator[Path]:
    """Every file under `folder`, however deep.

    A folder whose name starts with a dot is left out, like it is in the
    browser. A symbolic link to a folder is not followed, which is what keeps a
    link pointing at one of its own parents from walking for ever, and matches
    `resolve_image` refusing to serve anything a link leads to.

    A subfolder that cannot be read is skipped instead of ending the walk, so
    one unreadable corner of a card does not hide the rest of the shoot.
    """
    try:
        entries = list(folder.iterdir())
    except OSError:
        return
    for entry in entries:
        if entry.is_dir():
            if not entry.is_symlink() and not entry.name.startswith("."):
                yield from walk(entry)
        elif entry.is_file():
            yield entry


def list_images(source: Path, deep: bool = False) -> list[str]:
    """Names of the reviewable images in `source`, in a stable order.

    A name is relative to `source` and always spelled with forward slashes:
    `IMG_1.jpg` for a file in the folder itself, `2024-08-30/IMG_1.jpg` for one
    `deep` reached in a subfolder. A file directly inside the folder is
    therefore named exactly as it was before subfolders were searched, which is
    what lets the decisions in an existing state file keep matching.

    A folder that cannot be listed, because it is missing or unreadable, reads
    as empty. Raising here would turn every later request into a server error,
    because the folder is read again on each one.
    """
    if deep:
        found: Iterator[Path] | list[Path] = walk(source)
    else:
        try:
            found = [entry for entry in source.iterdir() if entry.is_file()]
        except OSError:
            return []
    return ordered(
        [
            entry.relative_to(source).as_posix()
            for entry in found
            if entry.suffix.lower() in IMAGE_EXTS
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


def resolve_image(source: Path, name: str, deep: bool = False) -> Path | None:
    """Path of the image `name` inside `source`.

    Returns None when the file is absent, when it is not a reviewable image, or
    when `name` points outside the source folder. The last check is made after
    resolving, so neither `..` nor a symbolic link can step out of the folder
    and read the rest of the disk.

    `deep` decides how far inside counts: the folder itself, or the whole tree
    under it. It is the same reach `list_images` was given, so an image outside
    the queue can be neither served nor transferred.
    """
    root = source.resolve()
    candidate = (source / name).resolve()
    if candidate.suffix.lower() not in IMAGE_EXTS or not candidate.is_file():
        return None
    inside = candidate.is_relative_to(root) if deep else candidate.parent == root
    return candidate if inside else None


def raw_index(source: Path, deep: bool = False) -> dict[Path, list[Path]]:
    """Map each path without its extension to the RAW files that share it.

    So `/shoot/IMG_1` to `/shoot/IMG_1.CR2`, keyed by the whole path rather than
    by the bare stem: an `IMG_1.CR2` in one subfolder must never be paired with
    the `IMG_1.jpg` of another, and two days of the same card number them alike.

    Built once per plan so that pairing an image with its RAW original stays a
    dictionary lookup instead of a folder scan.
    """
    index: dict[Path, list[Path]] = {}
    if not source.is_dir():
        return index
    for entry in sorted(walk(source) if deep else source.iterdir()):
        if entry.is_file() and entry.suffix.lower() in RAW_EXTS:
            index.setdefault(entry.with_suffix(""), []).append(entry)
    return index
