"""Fixtures shared by the test suite."""

from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import Path

import pytest

from phototriage.store import Store

# A real 1x1 PNG.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def write_image() -> Callable[[Path], Path]:
    """Return a helper that creates a real image file at a given path."""

    def _write(path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(PNG_BYTES)
        return path

    return _write


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """An empty source folder, one level below `tmp_path`."""
    folder = tmp_path / "source"
    folder.mkdir()
    return folder


@pytest.fixture
def store(tmp_path: Path) -> Store:
    """An empty store whose file does not exist yet."""
    return Store(tmp_path / "state.json")
