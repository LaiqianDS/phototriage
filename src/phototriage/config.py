"""Recognised file types and naming rules."""

from __future__ import annotations

from pathlib import Path

IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"})

RAW_EXTS = frozenset(
    {
        ".cr2",
        ".cr3",
        ".nef",
        ".arw",
        ".raf",
        ".dng",
        ".rw2",
        ".orf",
        ".srw",
        ".pef",
        ".raw",
    }
)

DEFAULT_STATE_FILE = Path.home() / ".phototriage" / "state.json"

KEEP_SUFFIX = "_keep"


def default_destination(source: Path) -> Path:
    """Folder for the kept images: a sibling of `source` with a `_keep` suffix.

    A sibling keeps the source folder untouched and gives every source its own
    destination, so reviewing several folders never mixes the results.
    """
    if not source.name:  # a filesystem root has no name to build a sibling from
        return source / "keep"
    return source.parent / f"{source.name}{KEEP_SUFFIX}"
