"""Time the requests a review makes, against a real folder of photos."""

from __future__ import annotations

import argparse
import statistics
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient

from phototriage import library
from phototriage.api import create_app
from phototriage.store import Store


def timed(request: Callable[[], object], runs: int) -> list[float]:
    """Milliseconds taken by each of `runs` calls to `request`."""
    spent = []
    for _ in range(runs):
        start = time.perf_counter()
        request()
        spent.append((time.perf_counter() - start) * 1000)
    return spent


def measure(folder: Path, deep: bool, runs: int, decisions: int) -> None:
    """Print the time of a state read and of a decision, with the switch set to `deep`."""
    with tempfile.TemporaryDirectory() as scratch:
        store = Store(Path(scratch) / "state.json", search_subfolders=deep)
        with TestClient(create_app(store, folder)) as client:
            total = client.get("/api/state").json()["total"]
            state = timed(lambda: client.get("/api/state").raise_for_status(), runs)
            # A verdict names its photo, and the queue goes in listing order.
            queue = iter(library.list_images(folder, deep))
            decide = timed(
                lambda: client.post(
                    "/api/decide", json={"verdict": "discard", "name": next(queue)}
                ).raise_for_status(),
                min(decisions, total),
            )

    label = "on " if deep else "off"
    print(f"subfolders {label}  {total:>6} images", end="  ")
    print(f"state {summary(state)}  decide {summary(decide)}")


def summary(spent: list[float]) -> str:
    """The median and the worst of `spent`, on one line so the two switches line up."""
    if not spent:
        return "      nothing to time"
    return f"median {statistics.median(spent):7.1f} ms, worst {max(spent):7.1f} ms"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", type=Path, help="source folder to time, read only")
    parser.add_argument("--runs", type=int, default=20, help="state reads to time (default: 20)")
    parser.add_argument("--decisions", type=int, default=50, help="decisions to time (default: 50)")
    args = parser.parse_args()

    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        parser.error(f"not a folder: {folder}")
    for deep in (False, True):
        measure(folder, deep, args.runs, args.decisions)


if __name__ == "__main__":
    main()
