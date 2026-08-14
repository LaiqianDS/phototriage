"""Tests for what the app remembers between runs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phototriage.config import default_destination
from phototriage.review import Verdict
from phototriage.store import SCHEMA_VERSION, Store


def test_save_and_load_round_trip(tmp_path: Path, source: Path) -> None:
    store = Store(tmp_path / "state.json")
    review = store.open(source, tmp_path / "elsewhere")
    review.decide("b.png", Verdict.KEEP)
    review.decide("a.png", Verdict.DISCARD)
    store.save()

    reloaded = Store.load(tmp_path / "state.json")
    resumed = reloaded.open(source)

    assert reloaded.last == source
    assert resumed.destination == tmp_path / "elsewhere"
    assert list(resumed.verdicts) == ["b.png", "a.png"]
    assert resumed.verdicts["b.png"] is Verdict.KEEP


def test_save_creates_the_folder_of_the_state_file(tmp_path: Path, source: Path) -> None:
    path = tmp_path / "nested" / "deeper" / "state.json"
    store = Store(path)
    store.open(source)

    store.save()

    assert path.is_file()


def test_load_of_a_missing_file_starts_empty(tmp_path: Path) -> None:
    store = Store.load(tmp_path / "absent.json")

    assert store.last is None


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("{not json at all", id="corrupt"),
        pytest.param('{"version": 4, "last": null, "reviews": {', id="truncated"),
        pytest.param("", id="empty"),
    ],
)
def test_load_of_an_unreadable_file_starts_empty(tmp_path: Path, text: str) -> None:
    path = tmp_path / "state.json"
    path.write_text(text, encoding="utf-8")

    store = Store.load(path)

    assert store.last is None


def test_load_of_an_unknown_version_starts_empty(tmp_path: Path, source: Path) -> None:
    path = tmp_path / "state.json"
    payload = {
        "version": SCHEMA_VERSION + 1,
        "last": str(source),
        "reviews": {
            str(source): {
                "destination": str(tmp_path / "elsewhere"),
                "decisions": [{"name": "a.png", "verdict": "keep"}],
            }
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    store = Store.load(path)

    assert store.last is None
    # The stored review is dropped as well, not only the pointer to it.
    assert store.open(source).decisions == []


def test_load_of_a_missing_key_starts_empty(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"version": SCHEMA_VERSION}), encoding="utf-8")

    store = Store.load(path)

    assert store.last is None


def test_open_a_new_source_uses_the_default_destination(tmp_path: Path, source: Path) -> None:
    store = Store(tmp_path / "state.json")

    review = store.open(source)

    assert review.destination == default_destination(source)
    assert review.destination == tmp_path / "source_keep"


def test_open_keeps_the_custom_destination_of_an_existing_review(
    tmp_path: Path, source: Path
) -> None:
    store = Store(tmp_path / "state.json")
    store.open(source, tmp_path / "elsewhere")

    resumed = store.open(source)

    assert resumed.destination == tmp_path / "elsewhere"


def test_open_replaces_the_destination_when_a_new_one_is_given(
    tmp_path: Path, source: Path
) -> None:
    store = Store(tmp_path / "state.json")
    store.open(source, tmp_path / "first")

    resumed = store.open(source, tmp_path / "second")

    assert resumed.destination == tmp_path / "second"


def test_open_keeps_one_review_per_source(tmp_path: Path, source: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    store = Store(tmp_path / "state.json")
    store.open(source).decide("a.png", Verdict.KEEP)

    store.open(other)

    assert store.last == other
    assert list(store.open(source).verdicts) == ["a.png"]


def test_save_replaces_the_previous_file_instead_of_appending(tmp_path: Path, source: Path) -> None:
    path = tmp_path / "state.json"
    store = Store(path)
    review = store.open(source)
    review.decide("a.png", Verdict.KEEP)
    store.save()
    review.undo()
    store.save()

    assert Store.load(path).open(source).decisions == []


def test_load_survives_reviews_of_the_wrong_shape(tmp_path: Path) -> None:
    """A hand-edited file must not stop the app from starting."""
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"version": SCHEMA_VERSION, "last": None, "reviews": []}))

    assert Store.load(path).last is None


def test_pair_raws_is_on_by_default_and_survives_a_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store = Store(path)
    assert store.pair_raws is True

    store.pair_raws = False
    store.save()

    assert Store.load(path).pair_raws is False


def test_pair_raws_defaults_to_on_when_the_file_predates_it(tmp_path: Path) -> None:
    """An older file has no such key, and the previous behaviour was to pair."""
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"version": SCHEMA_VERSION, "last": None, "reviews": {}}))

    assert Store.load(path).pair_raws is True
