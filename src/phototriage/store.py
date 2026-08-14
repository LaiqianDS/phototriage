"""Everything the app remembers between runs, in a single JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from .config import default_destination
from .review import Decision, Review, Verdict

SCHEMA_VERSION = 1


class Store:
    """The reviews started so far, keyed by source folder.

    Every review is kept, so switching folders and coming back does not lose
    the decisions. One file means one atomic write per change, instead of a
    scheme that has to keep several files in step.
    """

    def __init__(
        self,
        path: Path,
        reviews: dict[Path, Review] | None = None,
        last: Path | None = None,
        pair_raws: bool = True,
    ) -> None:
        self._path = path
        self._reviews = reviews if reviews is not None else {}
        self._last = last
        #: Whether a RAW original travels with the image that shares its name.
        #: A working habit rather than a property of one folder, so it is stored
        #: once instead of per review.
        self.pair_raws = pair_raws

    @classmethod
    def load(cls, path: Path) -> Store:
        """Read the store from disk, or start an empty one if it is unusable."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload["version"] != SCHEMA_VERSION:
                return cls(path)
            reviews = {
                Path(source): Review(
                    destination=Path(review["destination"]),
                    decisions=[
                        Decision(item["name"], Verdict(item["verdict"]))
                        for item in review["decisions"]
                    ],
                )
                for source, review in payload["reviews"].items()
            }
            last = Path(payload["last"]) if payload["last"] is not None else None
            pair_raws = bool(payload.get("pair_raws", True))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return cls(path)
        return cls(path, reviews, last, pair_raws)

    def save(self) -> None:
        """Write the store to disk in one step.

        The write goes to a temporary file that then replaces the target, so an
        interrupted run leaves the previous state intact instead of a truncated
        file.
        """
        payload = {
            "version": SCHEMA_VERSION,
            "last": str(self._last) if self._last is not None else None,
            "pair_raws": self.pair_raws,
            "reviews": {
                str(source): {
                    "destination": str(review.destination),
                    "decisions": [
                        {"name": decision.name, "verdict": decision.verdict.value}
                        for decision in review.decisions
                    ],
                }
                for source, review in self._reviews.items()
            },
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    @property
    def last(self) -> Path | None:
        """The source folder reviewed most recently, if any."""
        return self._last

    def open(self, source: Path, destination: Path | None = None) -> Review:
        """Make `source` the active review, resuming it if it already exists.

        `destination` defaults to the one already stored for this source, or to
        a fresh sibling folder the first time the source is opened.
        """
        review = self._reviews.get(source)
        if review is None:
            review = Review(destination or default_destination(source))
            self._reviews[source] = review
        elif destination is not None:
            review.destination = destination
        self._last = source
        return review
