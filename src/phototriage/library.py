"""Read-only view of the files on disk."""

from __future__ import annotations

from pathlib import Path

from .config import IMAGE_EXTS, RAW_EXTS


def ordered(names: list[str]) -> list[str]:
    """Sort case-insensitively, with the exact name breaking ties.

    Without the tie-break, two names differing only in case would keep the
    order the filesystem happened to return, which is not reproducible.
    """
    return sorted(names, key=lambda name: (name.lower(), name))


def list_images(source: Path) -> list[str]:
    """Names of the reviewable images in `source`, in a stable order.

    A folder that cannot be listed, because it is missing or unreadable, reads
    as empty. Raising here would turn every later request into a server error,
    because the folder is read again on each one.
    """
    try:
        entries = list(source.iterdir())
    except OSError:
        return []
    return ordered(
        [entry.name for entry in entries if entry.is_file() and entry.suffix.lower() in IMAGE_EXTS]
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


def resolve_image(source: Path, name: str) -> Path | None:
    """Path of the image `name` inside `source`.

    Returns None when the file is absent, when it is not a reviewable image, or
    when `name` points outside the source folder. The last check keeps a
    crafted request from reading the rest of the disk.
    """
    candidate = (source / name).resolve()
    if candidate.suffix.lower() not in IMAGE_EXTS:
        return None
    if not candidate.is_file() or candidate.parent != source.resolve():
        return None
    return candidate


def raw_index(source: Path) -> dict[str, list[Path]]:
    """Map each stem to its RAW files, for example `IMG_1` to `IMG_1.CR2`.

    Built once per plan so that pairing an image with its RAW original stays a
    dictionary lookup instead of a folder scan.
    """
    index: dict[str, list[Path]] = {}
    if not source.is_dir():
        return index
    for entry in sorted(source.iterdir()):
        if entry.is_file() and entry.suffix.lower() in RAW_EXTS:
            index.setdefault(entry.stem, []).append(entry)
    return index
