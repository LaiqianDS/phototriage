"""Command line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from .api import create_app
from .config import DEFAULT_STATE_FILE
from .store import Store

LOOPBACK = "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="phototriage",
        description="Review a folder of images and collect the kept ones.",
    )
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        help="folder of images to review (default: the last one reviewed)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_FILE,
        help=f"where the decisions are saved (default: {DEFAULT_STATE_FILE})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port to listen on (default: 8000)",
    )
    args = parser.parse_args()

    store = Store.load(args.state_file)
    source = args.source.expanduser().resolve() if args.source else None
    # Fixed to the loopback address, with no option to change it: the interface
    # browses and copies local folders, so anyone who can reach it can read them.
    print(f"Open http://{LOOPBACK}:{args.port}")
    uvicorn.run(create_app(store, source), host=LOOPBACK, port=args.port)


if __name__ == "__main__":
    main()
