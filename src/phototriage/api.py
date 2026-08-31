"""HTTP layer: a thin shell over library, store and transfer.

The API is the transaction boundary: a route mutates the active review and then
asks the store to persist it, so no lower layer needs to know about the disk.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import library, transfer
from .config import default_destination
from .review import Review, Verdict
from .store import Store

WEB_DIR = Path(__file__).parent / "web"


@dataclass
class Active:
    """The folder being reviewed right now, empty until one is chosen."""

    source: Path | None = None
    review: Review | None = None


class State(BaseModel):
    """Everything the interface needs to draw itself."""

    source: str | None
    destination: str | None
    total: int
    reviewed: int
    kept: int
    discarded: int
    current: str | None
    upcoming: str | None
    pair_raws: bool
    search_subfolders: bool


class Listing(BaseModel):
    """One folder as shown by the browser."""

    path: str
    parent: str | None
    folders: list[str]
    images: int


class FolderRequest(BaseModel):
    path: str


class SettingsRequest(BaseModel):
    """A change to the preferences, naming only the ones that change.

    An omitted field is left as it is, so a window with a stale view of one
    switch cannot move it by touching the other.
    """

    pair_raws: bool | None = None
    search_subfolders: bool | None = None


class DecideRequest(BaseModel):
    verdict: Verdict


class ApplyRequest(BaseModel):
    mode: transfer.Mode


class ApplyResponse(BaseModel):
    transferred: int
    destination: str


def as_folder(raw: str) -> Path:
    """Read a user-typed path, accepting `~` and relative forms."""
    path = Path(raw).expanduser()
    try:
        resolved = path.resolve()
    except OSError as error:
        raise HTTPException(status_code=400, detail=f"Ruta inválida: {raw}") from error
    if not resolved.is_dir():
        raise HTTPException(status_code=404, detail=f"No es una carpeta: {resolved}")
    return resolved


def as_destination(raw: str, source: Path) -> Path:
    """Read a user-typed destination, which need not exist yet.

    An empty field means "back to the default". A relative path is refused
    rather than resolved against the folder the server was started from, which
    would scatter the images somewhere the user never named.
    """
    text = raw.strip()
    if not text:
        return default_destination(source)
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise HTTPException(status_code=400, detail=f"Usa una ruta absoluta: {text}")
    return path


def create_app(store: Store, source: Path | None = None) -> FastAPI:
    """Build the application, resuming `source` or the last folder reviewed."""
    app = FastAPI(title="PhotoTriage")
    active = Active()

    def open_source(folder: Path, destination: Path | None = None) -> None:
        active.source = folder
        active.review = store.open(folder, destination)
        store.save()

    resumed = source or store.last
    if resumed is not None and resumed.is_dir():
        open_source(resumed)

    def snapshot() -> State:
        """Read the source folder and the active review, and combine them.

        The folder is read on every request, so images added or deleted while
        the server runs are picked up without a restart.
        """
        folder, review = active.source, active.review
        if folder is None or review is None:
            return State(
                source=None,
                destination=None,
                total=0,
                reviewed=0,
                kept=0,
                discarded=0,
                current=None,
                upcoming=None,
                pair_raws=store.pair_raws,
                search_subfolders=store.search_subfolders,
            )
        images = library.list_images(folder, store.search_subfolders)
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
            pair_raws=store.pair_raws,
            search_subfolders=store.search_subfolders,
        )

    def require_review() -> tuple[Path, Review]:
        folder, review = active.source, active.review
        if folder is None or review is None:
            raise HTTPException(status_code=409, detail="Elige una carpeta origen.")
        return folder, review

    @app.get("/api/state")
    def read_state() -> State:
        return snapshot()

    @app.get("/api/browse")
    def browse(path: str = "~") -> Listing:
        """List the subfolders of `path` so the interface can walk the disk.

        The server is bound to the loopback address, so this stays as reachable
        as the files it lists.
        """
        folder = as_folder(path)
        try:
            folders = library.list_folders(folder)
        except OSError as error:
            raise HTTPException(status_code=403, detail=f"Sin acceso a {folder}") from error
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
            raise HTTPException(status_code=403, detail=f"Sin acceso a {folder}")
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
        store.save()
        return snapshot()

    @app.post("/api/decide")
    def decide(request: DecideRequest) -> State:
        _, review = require_review()
        current = snapshot().current
        if current is None:
            raise HTTPException(status_code=409, detail="No hay nada que revisar.")
        review.decide(current, request.verdict)
        store.save()
        return snapshot()

    @app.post("/api/undo")
    def undo() -> State:
        _, review = require_review()
        review.undo()
        store.save()
        return snapshot()

    @app.post("/api/apply")
    def apply(request: ApplyRequest) -> ApplyResponse:
        folder, review = require_review()
        plan = transfer.build_plan(
            folder, review.verdicts, store.pair_raws, store.search_subfolders
        )
        try:
            transferred = transfer.execute(plan, folder, review.destination, request.mode)
        except OSError as error:
            # An unwritable destination or a full disk stops the run partway.
            # Without this, the failure leaves FastAPI to answer in plain text
            # and the interface reports a parser error instead of the cause.
            raise HTTPException(
                status_code=500,
                detail=f"La transferencia se interrumpió: {error}. Revisa el destino.",
            ) from error
        return ApplyResponse(transferred=transferred, destination=str(review.destination))

    # `:path` because a name reaching into a subfolder carries a separator, and
    # the default converter stops at one. What may be read is decided by
    # `resolve_image`, not by the shape of the route.
    @app.get("/api/image/{name:path}")
    def read_image(name: str) -> FileResponse:
        folder, _ = require_review()
        path = library.resolve_image(folder, name, store.search_subfolders)
        if path is None:
            raise HTTPException(status_code=404, detail=f"No existe la imagen {name}.")
        return FileResponse(path)

    # Mounted last so that the /api routes above take precedence.
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app
