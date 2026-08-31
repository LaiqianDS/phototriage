"""Tests for turning the kept decisions into file copies or moves."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from phototriage import transfer
from phototriage.config import RAW_EXTS, VIDEO_EXTS, companion_exts
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

    transferred = transfer.execute(plan, source, destination, transfer.Mode.COPY)

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
    transferred = transfer.execute(plan, source, destination, transfer.Mode.COPY)

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
    transferred = transfer.execute(plan, source, destination, transfer.Mode.MOVE)

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

    transfer.execute([source / "photo.png"], source, destination, transfer.Mode.COPY)

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


def test_companion_exts_is_the_union_of_the_two_switches() -> None:
    """The plan is told which extensions follow an image, not which switch is on.

    Two booleans carried all the way down would have to be read together at the
    bottom to answer one question, and a third kind of companion would add a
    third.
    """
    assert companion_exts(pair_raws=False, pair_videos=False) == frozenset()
    assert companion_exts(pair_raws=True, pair_videos=False) == RAW_EXTS
    assert companion_exts(pair_raws=False, pair_videos=True) == VIDEO_EXTS
    assert companion_exts(pair_raws=True, pair_videos=True) == RAW_EXTS | VIDEO_EXTS


def test_build_plan_carries_a_video_that_shares_the_name_of_a_kept_image(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """A phone writes the two halves of a live photo under one name."""
    write_image(source / "IMG_1.png")
    (source / "IMG_1.MOV").write_bytes(b"clip")

    both = companion_exts(pair_raws=True, pair_videos=True)

    assert names(transfer.build_plan(source, {"IMG_1.png": Verdict.KEEP})) == ["IMG_1.png"]
    assert names(transfer.build_plan(source, {"IMG_1.png": Verdict.KEEP}, both)) == [
        "IMG_1.png",
        "IMG_1.MOV",
    ]


def test_build_plan_leaves_a_video_of_its_own_name_behind(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """A clip is never reviewed, so it can only travel as the half of a name.

    `MVI_0042.MOV` with no image beside it is nobody's companion, and the
    switch does not turn it into one.
    """
    write_image(source / "IMG_1.png")
    (source / "MVI_0042.MOV").write_bytes(b"clip")

    plan = transfer.build_plan(
        source, {"IMG_1.png": Verdict.KEEP}, companion_exts(pair_raws=True, pair_videos=True)
    )

    assert names(plan) == ["IMG_1.png"]


def test_build_plan_reaches_into_subfolders_only_when_asked(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """The transfer has the reach the queue had, and no more.

    A decision about `inner/IMG_1.png` can survive in the state file from a run
    with the switch on. With it off that image is not in the queue, so it must
    not be transferred either: what is on screen and what is copied have to be
    the same set.
    """
    write_image(source / "inner" / "IMG_1.png")
    verdicts = {"inner/IMG_1.png": Verdict.KEEP}

    assert transfer.build_plan(source, verdicts) == []
    assert names(transfer.build_plan(source, verdicts, deep=True)) == ["IMG_1.png"]


def test_execute_keeps_the_subfolder_a_photo_came_from(
    source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "2024-08-30" / "IMG_1.png")
    destination = tmp_path / "source_keep"

    plan = transfer.build_plan(source, {"2024-08-30/IMG_1.png": Verdict.KEEP}, deep=True)
    transfer.execute(plan, source, destination, transfer.Mode.COPY)

    assert (destination / "2024-08-30" / "IMG_1.png").is_file()


def test_execute_does_not_put_two_days_of_photos_on_one_name(
    source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    """Flattening would answer this with `IMG_1.png` and `IMG_1_1.png`.

    Both names would be real files and neither would say which day it came
    from, and in move mode the folder that said so is gone.
    """
    for day in ("2024-08-30", "2024-08-31"):
        write_image(source / day / "IMG_1.png")
    destination = tmp_path / "source_keep"
    verdicts = {"2024-08-30/IMG_1.png": Verdict.KEEP, "2024-08-31/IMG_1.png": Verdict.KEEP}

    plan = transfer.build_plan(source, verdicts, deep=True)
    transferred = transfer.execute(plan, source, destination, transfer.Mode.MOVE)

    assert transferred == 2
    assert sorted(path.name for path in destination.rglob("*.png")) == ["IMG_1.png", "IMG_1.png"]
    assert (destination / "2024-08-30" / "IMG_1.png").is_file()
    assert (destination / "2024-08-31" / "IMG_1.png").is_file()


def test_build_plan_leaves_the_raw_behind_when_pairing_is_off(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "IMG_1.png")
    (source / "IMG_1.CR2").write_bytes(b"raw")

    plan = transfer.build_plan(source, {"IMG_1.png": Verdict.KEEP}, companions=frozenset())

    assert names(plan) == ["IMG_1.png"]
