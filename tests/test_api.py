"""Tests for the HTTP layer, driven through a real ASGI client."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from phototriage.api import create_app
from phototriage.review import Verdict
from phototriage.store import Store


@pytest.fixture
def client(store: Store) -> Iterator[TestClient]:
    """A client on an app that has no folder open yet."""
    with TestClient(create_app(store)) as test_client:
        yield test_client


def choose(client: TestClient, folder: Path) -> dict:
    response = client.post("/api/source", json={"path": str(folder)})
    assert response.status_code == 200
    return response.json()


def test_state_is_empty_before_a_folder_is_chosen(client: TestClient) -> None:
    state = client.get("/api/state").json()

    assert state == {
        "source": None,
        "destination": None,
        "total": 0,
        "reviewed": 0,
        "kept": 0,
        "discarded": 0,
        "current": None,
        "upcoming": None,
        "pair_raws": True,
        "search_subfolders": False,
    }


def test_decide_without_a_source_is_refused(client: TestClient) -> None:
    response = client.post("/api/decide", json={"verdict": "keep"})

    assert response.status_code == 409


def test_undo_without_a_source_is_refused(client: TestClient) -> None:
    assert client.post("/api/undo", json={}).status_code == 409


def test_setting_the_source_reports_the_queue(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "b.png")
    write_image(source / "a.png")

    state = choose(client, source)

    assert state["source"] == str(source)
    assert state["destination"] == str(tmp_path / "source_keep")
    assert state["total"] == 2
    assert state["current"] == "a.png"
    assert state["upcoming"] == "b.png"


def test_setting_a_missing_source_is_refused(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/api/source", json={"path": str(tmp_path / "absent")})

    assert response.status_code == 404


def test_a_restart_resumes_the_last_folder(
    store: Store, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    """The store is the only memory, so a fresh app must pick the folder back up."""
    write_image(source / "a.png")
    with TestClient(create_app(store)) as first:
        choose(first, source)
        first.post("/api/decide", json={"verdict": "keep"})

    with TestClient(create_app(Store.load(tmp_path / "state.json"))) as second:
        state = second.get("/api/state").json()

    assert state["source"] == str(source)
    assert state["kept"] == 1


def test_decide_undo_decide_walks_the_queue(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "a.png")
    write_image(source / "b.png")
    choose(client, source)

    kept = client.post("/api/decide", json={"verdict": "keep"}).json()
    assert kept["kept"] == 1
    assert kept["current"] == "b.png"

    undone = client.post("/api/undo", json={}).json()
    assert undone["kept"] == 0
    assert undone["reviewed"] == 0
    assert undone["current"] == "a.png"

    dropped = client.post("/api/decide", json={"verdict": "discard"}).json()
    assert dropped["discarded"] == 1
    assert dropped["current"] == "b.png"


def test_decide_past_the_end_is_refused(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "only.png")
    choose(client, source)
    client.post("/api/decide", json={"verdict": "keep"})

    response = client.post("/api/decide", json={"verdict": "keep"})

    assert response.status_code == 409


def test_an_unknown_verdict_is_rejected(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "a.png")
    choose(client, source)

    response = client.post("/api/decide", json={"verdict": "maybe"})

    assert response.status_code == 422


def test_setting_the_destination_keeps_the_source(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "a.png")
    choose(client, source)
    client.post("/api/decide", json={"verdict": "keep"})

    state = client.post("/api/destination", json={"path": str(tmp_path / "elsewhere")}).json()

    assert state["destination"] == str(tmp_path / "elsewhere")
    assert state["source"] == str(source)
    assert state["kept"] == 1


def test_browse_lists_the_subfolders_of_a_real_folder(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    (source / "Beta").mkdir()
    (source / "alpha").mkdir()
    (source / ".hidden").mkdir()
    write_image(source / "a.png")

    listing = client.get("/api/browse", params={"path": str(source)}).json()

    assert listing == {
        "path": str(source),
        "parent": str(tmp_path),
        "folders": ["alpha", "Beta"],
        "images": 1,
    }


def test_browse_of_a_missing_folder_is_refused(client: TestClient, tmp_path: Path) -> None:
    response = client.get("/api/browse", params={"path": str(tmp_path / "absent")})

    assert response.status_code == 404


def test_read_image_serves_a_real_image(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    image = write_image(source / "a.png")
    choose(client, source)

    response = client.get("/api/image/a.png")

    assert response.status_code == 200
    assert response.content == image.read_bytes()


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("..%2Fsecret.png", id="escaped-separator"),
        pytest.param("%2e%2e%2fsecret.png", id="escaped-dots"),
        pytest.param("..%2F..%2Fsecret.png", id="two-levels-up"),
    ],
)
def test_read_image_refuses_to_leave_the_source(
    client: TestClient, source: Path, name: str, write_image: Callable[[Path], Path]
) -> None:
    write_image(source.parent / "secret.png")
    choose(client, source)

    assert client.get(f"/api/image/{name}").status_code == 404


def test_read_image_refuses_a_symlink_out_of_the_source(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    """A single name can still point outside, so the folder check must resolve it."""
    write_image(source.parent / "secret.png")
    (source / "link.png").symlink_to(source.parent / "secret.png")
    choose(client, source)

    assert client.get("/api/image/link.png").status_code == 404


def test_read_image_refuses_a_file_that_is_not_an_image(client: TestClient, source: Path) -> None:
    (source / "notes.txt").write_text("private")
    choose(client, source)

    assert client.get("/api/image/notes.txt").status_code == 404


def test_read_image_without_a_source_is_refused(client: TestClient) -> None:
    assert client.get("/api/image/a.png").status_code == 409


def test_apply_copies_the_kept_images_and_their_raws(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "drop.png")
    write_image(source / "keep.png")
    (source / "keep.CR2").write_bytes(b"raw")
    choose(client, source)
    client.post("/api/decide", json={"verdict": "discard"})  # drop.png
    client.post("/api/decide", json={"verdict": "keep"})  # keep.png

    response = client.post("/api/apply", json={"mode": "copy"})

    destination = tmp_path / "source_keep"
    assert response.json() == {"transferred": 2, "destination": str(destination)}
    assert sorted(path.name for path in destination.iterdir()) == ["keep.CR2", "keep.png"]
    assert sorted(path.name for path in source.iterdir()) == [
        "drop.png",
        "keep.CR2",
        "keep.png",
    ]


def test_apply_in_move_mode_empties_the_source_of_the_kept(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "drop.png")
    write_image(source / "keep.png")
    choose(client, source)
    client.post("/api/decide", json={"verdict": "discard"})
    client.post("/api/decide", json={"verdict": "keep"})

    client.post("/api/apply", json={"mode": "move"})

    assert [path.name for path in source.iterdir()] == ["drop.png"]
    assert [path.name for path in (tmp_path / "source_keep").iterdir()] == ["keep.png"]


def test_apply_without_a_source_is_refused(client: TestClient) -> None:
    assert client.post("/api/apply", json={"mode": "copy"}).status_code == 409


def test_apply_rejects_an_unknown_mode(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "a.png")
    choose(client, source)

    assert client.post("/api/apply", json={"mode": "delete"}).status_code == 422


def test_the_decisions_reach_the_disk_after_every_keypress(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "a.png")
    choose(client, source)

    client.post("/api/decide", json={"verdict": "keep"})

    reloaded = Store.load(tmp_path / "state.json")
    assert reloaded.open(source).verdicts == {"a.png": Verdict.KEEP}


def test_an_empty_destination_returns_to_the_default(
    client: TestClient, source: Path, tmp_path: Path
) -> None:
    """Clearing the field must not silently target the folder the server runs in."""
    choose(client, source)
    client.post("/api/destination", json={"path": str(tmp_path / "elsewhere")})

    state = client.post("/api/destination", json={"path": "   "}).json()

    assert state["destination"] == str(tmp_path / "source_keep")


def test_a_relative_destination_is_refused(client: TestClient, source: Path) -> None:
    choose(client, source)

    response = client.post("/api/destination", json={"path": "seleccion"})

    assert response.status_code == 400


def test_apply_reports_an_unwritable_destination(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    """A failed transfer must answer with the error envelope, not plain text."""
    write_image(source / "a.png")
    choose(client, source)
    client.post("/api/decide", json={"verdict": "keep"})
    blocked = tmp_path / "blocked"
    blocked.write_text("this is a file, so it cannot become the destination folder")
    client.post("/api/destination", json={"path": str(blocked)})

    response = client.post("/api/apply", json={"mode": "copy"})

    assert response.status_code == 500
    assert "interrumpió" in response.json()["detail"]


def test_setting_an_unreadable_source_is_refused(client: TestClient, tmp_path: Path) -> None:
    """A folder stored as the source is reopened on every restart, so refuse it early."""
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    try:
        response = client.post("/api/source", json={"path": str(locked)})
    finally:
        locked.chmod(0o755)

    assert response.status_code == 403
    assert client.get("/api/state").json()["source"] is None


def test_settings_turn_raw_pairing_off_and_apply_obeys(
    client: TestClient, source: Path, tmp_path: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "IMG_1.png")
    (source / "IMG_1.CR2").write_bytes(b"raw")
    choose(client, source)
    client.post("/api/decide", json={"verdict": "keep"})

    state = client.post("/api/settings", json={"pair_raws": False}).json()
    assert state["pair_raws"] is False

    client.post("/api/apply", json={"mode": "copy"})
    destination = tmp_path / "source_keep"

    assert [path.name for path in destination.iterdir()] == ["IMG_1.png"]


def test_the_queue_reaches_into_subfolders_once_the_switch_is_on(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    """The folder per day case, which is how a camera imports.

    Before the switch this folder has nothing to review at all, which is the
    dead end the option exists to open.
    """
    write_image(source / "2024-08-30" / "IMG_1.png")
    write_image(source / "2024-08-31" / "IMG_2.png")

    assert choose(client, source)["total"] == 0

    state = client.post("/api/settings", json={"search_subfolders": True}).json()

    assert state["total"] == 2
    assert state["current"] == "2024-08-30/IMG_1.png"
    assert state["upcoming"] == "2024-08-31/IMG_2.png"


def test_read_image_serves_a_photo_from_a_subfolder(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    """The name carries a separator, which the default route converter stops at."""
    written = write_image(source / "2024-08-30" / "IMG_1.png")
    choose(client, source)
    client.post("/api/settings", json={"search_subfolders": True})

    response = client.get("/api/image/2024-08-30%2FIMG_1.png")

    assert response.status_code == 200
    assert response.content == written.read_bytes()


def test_read_image_refuses_a_subfolder_while_the_switch_is_off(
    client: TestClient, source: Path, write_image: Callable[[Path], Path]
) -> None:
    write_image(source / "2024-08-30" / "IMG_1.png")
    choose(client, source)

    assert client.get("/api/image/2024-08-30%2FIMG_1.png").status_code == 404


def test_settings_change_only_the_flag_they_name(client: TestClient) -> None:
    """A stale view of one switch must not drag the other back with it.

    Both preferences answer on the same route, so a request that always sent
    the pair it had on screen would undo a change taken in another window, or
    in this one before the dialog was opened.
    """
    client.post("/api/settings", json={"pair_raws": False})

    state = client.post("/api/settings", json={"search_subfolders": True}).json()

    assert state["pair_raws"] is False
    assert state["search_subfolders"] is True
