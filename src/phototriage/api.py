"""HTTP layer: a thin shell over library, store and transfer."""

from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import library, transfer
from .config import companion_exts, default_destination
from .review import Review, Verdict
from .store import Store

WEB_DIR = Path(__file__).parent / "web"


@dataclass
class Active:
    """The folder being reviewed right now, empty until one is chosen."""

    source: Path | None = None
    review: Review | None = None
    #: How far the run in flight has gone, or None when no run is in flight.
    progress: Progress | None = None


class State(BaseModel):
    """Everything the interface needs to draw itself."""

    source: str | None = None
    destination: str | None = None
    total: int = 0
    reviewed: int = 0
    kept: int = 0
    discarded: int = 0
    current: str | None = None
    upcoming: str | None = None
    pair_raws: bool
    search_subfolders: bool
    pair_videos: bool


class Listing(BaseModel):
    """One folder as shown by the browser."""

    path: str
    parent: str | None
    folders: list[str]
    images: int


class FolderRequest(BaseModel):
    path: str


class SettingsRequest(BaseModel):
    """A change to the preferences, naming only the ones that change."""

    pair_raws: bool | None = None
    search_subfolders: bool | None = None
    pair_videos: bool | None = None


class DecideRequest(BaseModel):
    verdict: Verdict
    #: The image the verdict was taken on, which has to still be the current one.
    name: str


class ApplyRequest(BaseModel):
    mode: transfer.Mode


class Plan(BaseModel):
    """What a run would transfer, for the confirmation before it."""

    files: int
    bytes: int
    destination: str


class Progress(BaseModel):
    """A run in flight: the file being handled now, and the bytes of those before it."""

    mode: transfer.Mode
    files: int
    total_files: int
    bytes: int
    total_bytes: int


class ApplyResponse(BaseModel):
    transferred: int
    already_present: int
    failed: dict[str, str]
    destination: str


def as_folder(raw: str) -> Path:
    """Read a user-typed path, accepting `~` and relative forms."""
    path = Path(raw).expanduser()
    try:
        resolved = path.resolve()
    except OSError as error:
        raise HTTPException(status_code=400, detail=f"Invalid path: {raw}") from error
    if not resolved.is_dir():
        raise HTTPException(status_code=404, detail=f"Not a folder: {resolved}")
    return resolved


def as_destination(raw: str, source: Path) -> Path:
    """Read a user-typed destination, which need not exist yet."""
    text = raw.strip()
    if not text:
        return default_destination(source)
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise HTTPException(status_code=400, detail=f"Use an absolute path: {text}")
    return path


def left_out(folder: Path, destination: Path) -> Path | None:
    """The destination, when it is a subfolder of the source that the walk would reach."""
    inner = destination.resolve()
    return inner if inner != folder and inner.is_relative_to(folder) else None


def create_app(store: Store, source: Path | None = None) -> FastAPI:
    """Build the application, resuming `source` or the last folder reviewed."""
    app = FastAPI(title="PhotoTriage")
    active = Active()
    # One run at a time.
    transferring = threading.Lock()

    def open_source(folder: Path, destination: Path | None = None) -> None:
        active.source = folder
        active.review = store.open(folder, destination)
        store.save()

    resumed = source or store.last
    if resumed is not None and resumed.is_dir():
        open_source(resumed)

    def snapshot() -> State:
        """Read the source folder and the active review, and combine them."""
        folder, review = active.source, active.review
        switches = {
            "pair_raws": store.pair_raws,
            "search_subfolders": store.search_subfolders,
            "pair_videos": store.pair_videos,
        }
        if folder is None or review is None:
            return State(**switches)
        skip = left_out(folder, review.destination)
        images = library.list_images(folder, store.search_subfolders, skip)
        verdicts = review.verdicts
        pending = [name for name in images if name not in verdicts]
        reviewed = [verdicts[name] for name in images if name in verdicts]
        return State(
            source=str(folder),
            destination=str(review.destination),
            total=len(images),
            reviewed=len(reviewed),
            kept=sum(verdict is Verdict.KEEP for verdict in reviewed),
            discarded=sum(verdict is Verdict.DISCARD for verdict in reviewed),
            current=pending[0] if pending else None,
            upcoming=pending[1] if len(pending) > 1 else None,
            **switches,
        )

    def require_review() -> tuple[Path, Review]:
        folder, review = active.source, active.review
        if folder is None or review is None:
            raise HTTPException(status_code=409, detail="Choose a source folder.")
        return folder, review

    @app.get("/api/state")
    def read_state() -> State:
        return snapshot()

    @app.get("/api/browse")
    def browse(path: str = "~") -> Listing:
        """List the subfolders of `path` so the interface can walk the disk."""
        folder = as_folder(path)
        try:
            folders = library.list_folders(folder)
        except OSError as error:
            raise HTTPException(status_code=403, detail=f"No access to {folder}") from error
        return Listing(
            path=str(folder),
            parent=str(folder.parent) if folder.parent != folder else None,
            folders=folders,
            images=len(library.list_images(folder)),
        )

    @app.post("/api/source")
    def set_source(request: FolderRequest) -> State:
        folder = as_folder(request.path)
        if not library.is_readable(folder):
            raise HTTPException(status_code=403, detail=f"No access to {folder}")
        open_source(folder)
        return snapshot()

    @app.post("/api/destination")
    def set_destination(request: FolderRequest) -> State:
        folder, _ = require_review()
        open_source(folder, as_destination(request.path, folder))
        return snapshot()

    @app.post("/api/settings")
    def set_settings(request: SettingsRequest) -> State:
        if request.pair_raws is not None:
            store.pair_raws = request.pair_raws
        if request.search_subfolders is not None:
            store.search_subfolders = request.search_subfolders
        if request.pair_videos is not None:
            store.pair_videos = request.pair_videos
        store.save()
        return snapshot()

    @app.post("/api/decide")
    def decide(request: DecideRequest) -> State:
        _, review = require_review()
        current = snapshot().current
        if current is None:
            raise HTTPException(status_code=409, detail="Nothing to review.")
        # The queue is read from the folder on every request, so it can move between the photo a
        # page shows and the verdict taken on it: another window decides that photo, or a new file
        # sorts in front of it.
        if request.name != current:
            raise HTTPException(
                status_code=409, detail="The queue has changed. Decide on the photo you see now."
            )
        review.decide(current, request.verdict)
        store.save()
        return snapshot()

    @app.post("/api/undo")
    def undo() -> State:
        _, review = require_review()
        review.undo()
        store.save()
        return snapshot()

    def plan_for(folder: Path, review: Review) -> list[Path]:
        """The files a run would transfer, from the switches as they stand."""
        return transfer.build_plan(
            folder,
            review.verdicts,
            companion_exts(store.pair_raws, store.pair_videos),
            store.search_subfolders,
            left_out(folder, review.destination),
        )

    @app.get("/api/plan")
    def read_plan() -> Plan:
        """Count and weigh the plan without touching the destination."""
        folder, review = require_review()
        plan = plan_for(folder, review)
        return Plan(
            files=len(plan),
            bytes=sum(path.stat().st_size for path in plan),
            destination=str(review.destination),
        )

    @app.get("/api/progress")
    def read_progress() -> Progress | None:
        """How far the run in flight has gone, asked while `POST /api/apply` waits."""
        return active.progress

    @app.post("/api/apply")
    def apply(request: ApplyRequest) -> ApplyResponse:
        folder, review = require_review()
        if not transferring.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="A transfer is already running.")
        try:
            plan = plan_for(folder, review)
            # The bytes sent before each file, and after the last one.
            before = [0, *itertools.accumulate(path.stat().st_size for path in plan)]

            def on_file(index: int) -> None:
                active.progress = Progress(
                    mode=request.mode,
                    files=index + 1,
                    total_files=len(plan),
                    bytes=before[index],
                    total_bytes=before[-1],
                )

            try:
                outcome = transfer.execute(
                    plan, folder, review.destination, request.mode, on_file=on_file
                )
            except OSError as error:
                # A file that fails is reported in the answer, so only a destination that cannot be
                # created reaches here.
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not create the destination: {error}",
                ) from error
        finally:
            # Whatever happened, the next run must not be refused and the interface must not keep
            # reading a run that has ended.
            active.progress = None
            transferring.release()
        return ApplyResponse(
            transferred=outcome.transferred,
            already_present=outcome.already_present,
            failed=outcome.failed,
            destination=str(review.destination),
        )

    # `:path` because a name reaching into a subfolder carries a separator, and the default
    # converter stops at one.
    @app.get("/api/image/{name:path}")
    def read_image(name: str) -> FileResponse:
        folder, review = require_review()
        skip = left_out(folder, review.destination)
        path = library.resolve_image(folder, name, store.search_subfolders, skip)
        if path is None:
            raise HTTPException(status_code=404, detail=f"There is no image {name}.")
        return FileResponse(path)

    # Mounted last so that the /api routes above take precedence.
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
