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

VIDEO_EXTS = frozenset({".mov", ".mp4", ".m4v", ".avi", ".mts", ".m2ts"})


def companion_exts(pair_raws: bool, pair_videos: bool) -> frozenset[str]:
    """Extensions that follow a kept image of the same name."""
    return (RAW_EXTS if pair_raws else frozenset()) | (VIDEO_EXTS if pair_videos else frozenset())


DEFAULT_STATE_FILE = Path.home() / ".phototriage" / "state.json"


def default_destination(source: Path) -> Path:
    """Folder for the kept images: a sibling of `source` with a `_keep` suffix."""
    if not source.name:  # a filesystem root has no name to build a sibling from
        return source / "keep"
    return source.parent / f"{source.name}_keep"
