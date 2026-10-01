"""Everything the app remembers between runs, in a single JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from .config import default_destination
from .review import Decision, Review, Verdict

SCHEMA_VERSION = 1


class Store:
    """The reviews started so far, keyed by source folder."""

    def __init__(
        self,
        path: Path,
        reviews: dict[Path, Review] | None = None,
        last: Path | None = None,
        pair_raws: bool = True,
        search_subfolders: bool = False,
        pair_videos: bool = False,
    ) -> None:
        self._path = path
        self._reviews = reviews if reviews is not None else {}
        self.last = last
        #: Whether a RAW original travels with the image that shares its name.
        self.pair_raws = pair_raws
        #: Whether the review reaches into the subfolders of the source.
        self.search_subfolders = search_subfolders
        #: Whether a video travels with the image that shares its name, the way a phone writes one
        #: beside a still.
        self.pair_videos = pair_videos

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
            # Read with a default rather than a key, so a file written before the option existed
            # loads instead of being thrown away whole.
            pair_raws = bool(payload.get("pair_raws", True))
            search_subfolders = bool(payload.get("search_subfolders", False))
            pair_videos = bool(payload.get("pair_videos", False))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return cls(path)
        return cls(path, reviews, last, pair_raws, search_subfolders, pair_videos)

    def save(self) -> None:
        """Write the store to disk in one step."""
        payload = {
            "version": SCHEMA_VERSION,
            "last": str(self.last) if self.last is not None else None,
            "pair_raws": self.pair_raws,
            "search_subfolders": self.search_subfolders,
            "pair_videos": self.pair_videos,
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

    def open(self, source: Path, destination: Path | None = None) -> Review:
        """Make `source` the active review, resuming it if it already exists."""
        review = self._reviews.get(source)
        if review is None:
            review = Review(destination or default_destination(source))
            self._reviews[source] = review
        elif destination is not None:
            review.destination = destination
        self.last = source
        return review
