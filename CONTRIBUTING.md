# Contributing

Thank you for looking at this project.
Bug reports, questions and pull requests are all welcome.

Before you change code, read [docs/architecture.md](docs/architecture.md).
It explains what each module is responsible for and why the design is what it is.
A change that fits that shape is much easier to review.

## Set up

You need Python 3.12 or later.
[uv](https://docs.astral.sh/uv/) installs Python, the app and the development tools in one step:

```sh
uv sync
```

## Run the app

```sh
uv run phototriage
```

Point it at a folder of throwaway copies while you work, not at your only copy of a shoot:

```sh
uv run phototriage /tmp/photos --state-file /tmp/phototriage.json --port 8123
```

A separate `--state-file` keeps your experiments out of `~/.phototriage/state.json`.

The interface under `src/phototriage/web/` is served as static files and has no build step.
Editing it needs nothing more than a reload in the browser.
Editing Python needs a restart of the server.

## Run the tests

```sh
uv run pytest
```

One test file per module, plus shared fixtures in `tests/conftest.py`:

| File | Covers |
| --- | --- |
| `tests/test_library.py` | Listing, ordering, path resolution and RAW indexing. |
| `tests/test_review.py` | Decisions and undo. |
| `tests/test_store.py` | Saving, loading and recovering from a damaged state file. |
| `tests/test_transfer.py` | Plans, copy and move, and free names. |
| `tests/test_api.py` | The routes, driven through a real ASGI client. |
| `tests/test_web.py` | The interface read as text: every id the script asks for, and every `for` and `aria-*` reference, points at an element the page defines. |

Every fixture builds inside `tmp_path`, so a run never reads or writes a real photo folder and two tests never see each other's files.
Keep it that way.
A test that needs an image should use the `write_image` fixture, which writes a real PNG, because the API serves bytes straight from disk.

To run one file, or one test:

```sh
uv run pytest tests/test_api.py
uv run pytest -k undo
```

## Run the linter

```sh
uv run ruff check .
uv run ruff format .
```

Continuous integration runs the same three commands, with `ruff format --check` instead of `ruff format`.
Run them before you merge.

The workflow also runs `uv sync --locked`, which fails when `pyproject.toml` and `uv.lock` disagree.
If you change a dependency, commit the updated `uv.lock` with it.

## Style

- Type hints on every signature, and `from __future__ import annotations` at the top of each module.
- A docstring on every module and on every public function.
  Say why the code does what it does, not only what it does.
- Comment the reasoning that the code cannot show by itself.
  Do not comment the obvious.
- Line length is 100, set in `pyproject.toml`.
  `ruff format` handles it.
- Code, comments, docstrings and documentation are in English.
  Strings shown in the interface are in Spanish.
  Keep that split.

## Documentation

- `README.md` is the entry point and should stay readable in one sitting.
  Deep detail belongs in `docs/`.
- `docs/architecture.md` explains the modules and the decisions behind them.
  A design decision that a future reader would question belongs there, with its reason.
- `docs/api.md` is the HTTP reference.
  A new route, a new field or a new status code is only finished when it appears there.
- A control added to, moved in or removed from the interface changes the control
  table in `README.md`.
  Quote its Spanish label there exactly as `index.html` spells it.
- Write one sentence per line.
  It keeps diffs readable.

## Things worth knowing before you change them

- **Dependencies are two: FastAPI and uvicorn.**
  Adding a third is a real decision, not a detail.
  Say in the merge commit why the standard library cannot do it.
  In particular, the server sends image bytes untouched so that no image library is needed at all.
- **The state file has a schema version.**
  Changing the shape of what `Store` writes means raising `SCHEMA_VERSION` in `store.py`.
  A version the app does not know makes it start with an empty store, which silently drops the reader's decisions, so do not raise it without cause.
- **The decision list is the only state.**
  Counters and the current image are derived from it.
  Do not add a stored cursor or a stored count.
- **A preference that describes how the user works belongs on `Store`.**
  `pair_raws` sits next to the reviews, not inside one, so it means the same
  thing in every folder.
  Something that belongs to one source folder, such as the destination, belongs
  on `Review` instead.
  The reason is in [docs/architecture.md](docs/architecture.md#the-preferences-are-global-not-per-source-folder).
- **Nothing is ever deleted.**
  No route, and no function under `transfer.py`, may remove a file from the source folder except by moving it to the destination the user chose.
- **The server binds `127.0.0.1`.**
  Do not make the host configurable, and do not add a CORS middleware.
  The reason is in [docs/api.md](docs/api.md#why-loopback-and-json-are-the-boundary).

## Branches

`main` holds released versions, and every release is tagged there.
`dev` is where work is collected between releases.
Nothing is committed straight to either.

Start a branch off `dev`, named after what it does:

```sh
git switch dev
git pull
git switch -c feat/zoom-to-100
```

Prefixes in use: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`.

Merge it back into `dev` yourself when it is finished, and keep the merge
commit:

```sh
git switch dev
git merge --no-ff feat/zoom-to-100
git branch -d feat/zoom-to-100
```

`--no-ff` is the whole point of the command.
A fast-forward would spread the branch out as loose commits and lose the fact
that they were one piece of work, which is exactly what you want back when you
are reading the history to find out why something was done.

When `dev` is ready to release, it is merged into `main`, the version is raised
in `pyproject.toml` and `__init__.py`, `CHANGELOG.md` gets its entry, and the
commit on `main` is tagged.
Pushing `main` is also what publishes the site, because the Pages workflow
watches that branch and no other.

## Finishing a change

Work by the maintainers goes straight into `dev`.
There is no pull request step and no review queue: the review is the one you
carry out on yourself before you merge, and the merge commit message is where
it is written down.

A patch from outside still arrives as a pull request, because that is the only
way to offer one.
The four parts below are what its description should carry, all the same.

- One change per branch.
- Add a test that fails without your change.
- Update the documentation the change touches, in the same branch.
- Continuous integration runs on every push.
  Do not merge a branch whose last run is red.

Write the merge commit in four parts.
The last one is the one that earns its place:

1. **What this changes.**
   One or two sentences, for a reader of the log.
2. **Why.**
   The problem, not the solution.
   Name the roadmap entry or the issue if there is one.
3. **How it was verified.**
   Not "tests pass".
   What you actually ran and what you saw.
   For a change to the interface, name the browser and the window size.
4. **The weakest part.**
   What you did not verify, and the conditions under which this breaks.
   Leave nothing out because it is inconvenient.
   Everything above it can be reconstructed from the diff by whoever comes
   next. This cannot.
