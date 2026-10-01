"""Read-only view of the files on disk."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from .config import IMAGE_EXTS


def ordered(names: list[str]) -> list[str]:
    """Sort case-insensitively, with the exact name breaking ties."""
    return sorted(names, key=lambda name: (name.lower(), name))


def suffix(name: str) -> str:
    """The extension of `name`, lowercased, read exactly the way `Path.suffix` reads it."""
    dot = name.rfind(".")
    return name[dot:].lower() if 0 < dot < len(name) - 1 else ""


def walk(folder: Path, deep: bool = False, skip: Path | None = None) -> Iterator[os.DirEntry[str]]:
    """Every file in `folder` and, when `deep`, however far under it, except under `skip`."""
    skipped = None if skip is None else str(skip)
    try:
        with os.scandir(folder) as scan:
            entries = list(scan)
    except OSError:
        return
    for entry in entries:
        if entry.is_file():
            yield entry
        elif (
            deep
            and entry.is_dir()
            and not entry.is_symlink()
            and not entry.name.startswith(".")
            and entry.path != skipped
        ):
            yield from walk(Path(entry.path), deep, skip)


def list_images(source: Path, deep: bool = False, skip: Path | None = None) -> list[str]:
    """Names of the reviewable images in `source`, in a stable order."""
    # Every entry path starts with the source as it was given, so cutting that off is the relative
    # name.
    root = str(source)
    return ordered(
        [
            entry.path[len(root) :].lstrip(os.sep).replace(os.sep, "/")
            for entry in walk(source, deep, skip)
            if suffix(entry.name) in IMAGE_EXTS
        ]
    )


def is_readable(folder: Path) -> bool:
    """Whether `folder` can be listed at all."""
    try:
        next(folder.iterdir(), None)
    except OSError:
        return False
    return True


def list_folders(source: Path) -> list[str]:
    """Names of the visible subfolders of `source`, in a stable order."""
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
    """Path of the image `name` inside `source`."""
    root = source.resolve()
    candidate = (source / name).resolve()
    if candidate.suffix.lower() not in IMAGE_EXTS or not candidate.is_file():
        return None
    # Checked after resolving, so neither `..` nor a symbolic link can step out of the source.
    inside = candidate.is_relative_to(root) if deep else candidate.parent == root
    if skip is not None and candidate.is_relative_to(skip):
        return None
    return candidate if inside else None


def companion_index(
    source: Path, extensions: frozenset[str], deep: bool = False
) -> dict[Path, list[Path]]:
    """Map each path without its extension to the files of `extensions` beside it."""
    index: dict[Path, list[Path]] = {}
    # Paths here, not names: this runs once per transfer, not once per request.
    for path in sorted(Path(entry.path) for entry in walk(source, deep)):
        if path.suffix.lower() in extensions:
            index.setdefault(path.with_suffix(""), []).append(path)
    return index
