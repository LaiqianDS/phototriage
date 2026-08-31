"""Tests for the read-only view of the files on disk."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from phototriage import library


def test_list_images_ignores_case_when_ordering(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    for name in ("b.PNG", "C.png", "a.jpg"):
        write_image(source / name)

    # A plain sort would put the capitals first: ["C.png", "a.jpg", "b.PNG"].
    assert library.list_images(source) == ["a.jpg", "b.PNG", "C.png"]


def test_list_images_repeats_the_same_order(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    for name in ("z.png", "m.png", "a.png"):
        write_image(source / name)

    assert library.list_images(source) == library.list_images(source)


def test_list_images_skips_files_that_are_not_images(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "photo.png")
    (source / "notes.txt").write_text("not an image")
    (source / "photo.CR2").write_bytes(b"raw")

    assert library.list_images(source) == ["photo.png"]


def test_list_images_skips_subfolders(source: Path, write_image: Callable[[Path], Path]) -> None:
    write_image(source / "inner" / "nested.png")

    assert library.list_images(source) == []


def test_list_images_reaches_into_subfolders_when_asked(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "2024-08-31" / "IMG_2.png")
    write_image(source / "2024-08-30" / "IMG_1.png")
    write_image(source / "loose.png")

    assert library.list_images(source, deep=True) == [
        "2024-08-30/IMG_1.png",
        "2024-08-31/IMG_2.png",
        "loose.png",
    ]


def test_list_images_names_a_top_level_file_the_same_way_either_way(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """This is what lets an existing state file keep its decisions.

    Decisions are keyed by the name in this list. If reaching into subfolders
    renamed the files already in the folder itself, every decision taken before
    the switch was turned on would stop matching, and the queue would start
    again from the first photo.
    """
    write_image(source / "IMG_1.png")
    write_image(source / "inner" / "IMG_2.png")

    assert library.list_images(source) == ["IMG_1.png"]
    assert library.list_images(source, deep=True) == ["IMG_1.png", "inner/IMG_2.png"]


def test_list_images_leaves_dot_folders_alone(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """The browser hides them, so the queue does not collect them either."""
    write_image(source / ".cache" / "thumb.png")
    write_image(source / "kept.png")

    assert library.list_images(source, deep=True) == ["kept.png"]


def test_list_images_does_not_follow_a_folder_that_is_a_link(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """A link to a parent of its own would otherwise walk until it ran out.

    It also keeps the queue to files the source folder really holds, which is
    the same rule `resolve_image` applies when it refuses to serve one.
    """
    write_image(source / "real" / "IMG_1.png")
    (source / "loop").symlink_to(source, target_is_directory=True)

    assert library.list_images(source, deep=True) == ["real/IMG_1.png"]


def test_list_images_returns_nothing_for_a_missing_folder(tmp_path: Path) -> None:
    assert library.list_images(tmp_path / "absent") == []


def test_list_folders_ignores_case_and_hides_dot_folders(source: Path) -> None:
    for name in ("Beta", "alpha", ".hidden"):
        (source / name).mkdir()
    (source / "file.txt").write_text("")

    assert library.list_folders(source) == ["alpha", "Beta"]


def test_resolve_image_accepts_a_genuine_image(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    expected = write_image(source / "photo.png")

    assert library.resolve_image(source, "photo.png") == expected


def test_resolve_image_rejects_path_traversal(source: Path) -> None:
    (source.parent / "secret.txt").write_text("private")

    assert library.resolve_image(source, "../secret.txt") is None


def test_resolve_image_rejects_an_image_outside_the_source(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    # The extension passes, so only the folder check can stop this one.
    write_image(source.parent / "outside.png")

    assert library.resolve_image(source, "../outside.png") is None


def test_resolve_image_rejects_an_absolute_path(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    outside = write_image(source.parent / "outside.png")

    assert library.resolve_image(source, str(outside)) is None


def test_resolve_image_rejects_a_subfolder(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "inner" / "nested.png")

    assert library.resolve_image(source, "inner/nested.png") is None


def test_resolve_image_accepts_a_subfolder_when_it_goes_deep(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    expected = write_image(source / "inner" / "nested.png")

    assert library.resolve_image(source, "inner/nested.png", deep=True) == expected


def test_resolve_image_going_deep_still_refuses_to_leave_the_source(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """Reaching further inside must not mean reaching outside.

    Both routes out are closed by resolving first and asking afterwards: `..`
    climbs out of the tree, and a link is followed to wherever it really points.
    """
    write_image(source.parent / "outside.png")
    (source / "inner").mkdir()
    (source / "inner" / "escape.png").symlink_to(source.parent / "outside.png")

    assert library.resolve_image(source, "inner/../../outside.png", deep=True) is None
    assert library.resolve_image(source, "inner/escape.png", deep=True) is None


def test_resolve_image_rejects_a_file_that_is_not_an_image(source: Path) -> None:
    (source / "notes.txt").write_text("not an image")

    assert library.resolve_image(source, "notes.txt") is None


def test_resolve_image_rejects_a_missing_file(source: Path) -> None:
    assert library.resolve_image(source, "absent.png") is None


def test_raw_index_pairs_an_uppercase_raw_with_a_lowercase_image(source: Path) -> None:
    """Lock down the extension comparison.

    An earlier version matched the suffix without lowering it, so a camera that
    writes `IMG_1.CR2` next to `IMG_1.png` lost its RAW original.
    """
    raw = source / "IMG_1.CR2"
    raw.write_bytes(b"raw")

    assert library.raw_index(source) == {source / "IMG_1": [raw]}


def test_raw_index_groups_several_raws_under_one_path(source: Path) -> None:
    for name in ("IMG_1.CR2", "IMG_1.dng"):
        (source / name).write_bytes(b"raw")

    assert sorted(path.name for path in library.raw_index(source)[source / "IMG_1"]) == [
        "IMG_1.CR2",
        "IMG_1.dng",
    ]


def test_raw_index_leaves_out_images_and_other_files(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "IMG_1.png")
    (source / "IMG_1.txt").write_text("")

    assert library.raw_index(source) == {}


def test_raw_index_keeps_every_raw_in_its_own_folder(
    source: Path, write_image: Callable[[Path], Path]
) -> None:
    """Two days of the same card number their files alike.

    Keyed by the bare stem, the RAW of the thirtieth would be handed to the
    image of the thirty first, and a kept photo would travel with the original
    of a different one.
    """
    first = source / "2024-08-30" / "IMG_1.CR2"
    second = source / "2024-08-31" / "IMG_1.CR2"
    for raw in (first, second):
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"raw")

    index = library.raw_index(source, deep=True)

    assert index == {first.with_suffix(""): [first], second.with_suffix(""): [second]}


def test_raw_index_returns_nothing_for_a_missing_folder(tmp_path: Path) -> None:
    assert library.raw_index(tmp_path / "absent") == {}


def test_ordered_breaks_ties_between_names_that_differ_only_in_case() -> None:
    """Case alone must not leave the order up to the filesystem."""
    assert library.ordered(["b.png", "A.png", "a.png"]) == ["A.png", "a.png", "b.png"]
    assert library.ordered(["a.png", "A.png", "b.png"]) == ["A.png", "a.png", "b.png"]


def test_list_images_reads_an_unreadable_folder_as_empty(tmp_path: Path) -> None:
    """Raising would turn every later request into a server error."""
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    try:
        assert library.list_images(locked) == []
        assert library.is_readable(locked) is False
    finally:
        locked.chmod(0o755)
