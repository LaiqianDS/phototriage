"""Tests for turning the kept decisions into file copies or moves."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from phototriage import transfer
from phototriage.review import Verdict


def names(paths: list[Path]) -> list[str]:
    return [path.name for path in paths]


def test_build_plan_takes_only_the_kept_images(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "keep.png")
    write_image(source / "drop.png")

    plan = transfer.build_plan(source, {"keep.png": Verdict.KEEP, "drop.png": Verdict.DISCARD})

    assert names(plan) == ["keep.png"]


def test_build_plan_adds_the_raw_original(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "IMG_1.png")
    (source / "IMG_1.CR2").write_bytes(b"raw")
    (source / "IMG_2.CR2").write_bytes(b"raw")

    plan = transfer.build_plan(source, {"IMG_1.png": Verdict.KEEP})

    assert names(plan) == ["IMG_1.png", "IMG_1.CR2"]


def test_build_plan_skips_a_decided_file_that_is_gone(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "here.png")

    plan = transfer.build_plan(source, {"gone.png": Verdict.KEEP, "here.png": Verdict.KEEP})

    assert names(plan) == ["here.png"]


def test_build_plan_is_empty_without_decisions(source: Path) -> None:
    assert transfer.build_plan(source, {}) == []


def test_free_name_returns_the_target_when_it_is_free(tmp_path: Path) -> None:
    assert transfer.free_name(tmp_path / "photo.png") == tmp_path / "photo.png"


def test_free_name_numbers_the_variants(tmp_path: Path) -> None:
    (tmp_path / "photo.png").write_bytes(b"")

    first = transfer.free_name(tmp_path / "photo.png")
    first.write_bytes(b"")
    second = transfer.free_name(tmp_path / "photo.png")

    assert first.name == "photo_1.png"
    assert second.name == "photo_2.png"


def test_execute_creates_the_destination_folder(
    source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    plan = [write_image(source / "keep.png")]
    destination = tmp_path / "made" / "on" / "demand"

    transferred = transfer.execute(plan, destination, transfer.Mode.COPY)

    assert transferred == 1
    assert destination.is_dir()


def test_execute_in_copy_mode_leaves_the_source_intact(
    source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "keep.png")
    write_image(source / "drop.png")
    (source / "keep.CR2").write_bytes(b"raw")
    destination = tmp_path / "source_keep"

    plan = transfer.build_plan(source, {"keep.png": Verdict.KEEP, "drop.png": Verdict.DISCARD})
    transferred = transfer.execute(plan, destination, transfer.Mode.COPY)

    assert transferred == 2
    assert sorted(path.name for path in destination.iterdir()) == ["keep.CR2", "keep.png"]
    assert sorted(path.name for path in source.iterdir()) == [
        "drop.png",
        "keep.CR2",
        "keep.png",
    ]


def test_execute_in_move_mode_leaves_only_the_discarded_behind(
    source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "keep.png")
    write_image(source / "drop.png")
    (source / "keep.CR2").write_bytes(b"raw")
    destination = tmp_path / "source_keep"

    plan = transfer.build_plan(source, {"keep.png": Verdict.KEEP, "drop.png": Verdict.DISCARD})
    transferred = transfer.execute(plan, destination, transfer.Mode.MOVE)

    assert transferred == 2
    assert sorted(path.name for path in destination.iterdir()) == ["keep.CR2", "keep.png"]
    assert [path.name for path in source.iterdir()] == ["drop.png"]


def test_execute_never_overwrites_a_taken_name(
    source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "photo.png")
    destination = tmp_path / "source_keep"
    destination.mkdir()
    (destination / "photo.png").write_text("older")

    transfer.execute([source / "photo.png"], destination, transfer.Mode.COPY)

    assert (destination / "photo.png").read_text() == "older"
    assert (destination / "photo_1.png").read_bytes() == (source / "photo.png").read_bytes()


def test_build_plan_takes_a_shared_raw_once(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """Two kept images can share a stem, and therefore the same RAW original."""
    write_image(source / "IMG_1.png")
    write_image(source / "IMG_1.jpg")
    (source / "IMG_1.CR2").write_bytes(b"raw")

    plan = transfer.build_plan(source, {"IMG_1.png": Verdict.KEEP, "IMG_1.jpg": Verdict.KEEP})

    assert names(plan) == ["IMG_1.png", "IMG_1.CR2", "IMG_1.jpg"]


def test_build_plan_leaves_the_raw_behind_when_pairing_is_off(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "IMG_1.png")
    (source / "IMG_1.CR2").write_bytes(b"raw")

    plan = transfer.build_plan(source, {"IMG_1.png": Verdict.KEEP}, pair_raws=False)

    assert names(plan) == ["IMG_1.png"]
