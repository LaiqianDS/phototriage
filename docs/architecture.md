# Architecture

This page describes how the app is put together and why.
For what it does from the outside, read the [README](../README.md).
For the HTTP contract, read [api.md](api.md).

## Shape of the app

The app is a local HTTP server with a browser interface.
The server is a Python package, `phototriage`.
The interface is one HTML file, one CSS file and one JavaScript module, served as static files by the same server.
There is no build step and no frontend framework.

The server owns the disk.
The browser holds no copy of the review: every action sends a request and redraws the interface from the response.
This is why a reload never loses anything, and why two windows on the same server see the same review.

The page is one screen with no scrolling.
The photo takes the middle, and the chrome takes the edges: a top bar, a bottom bar, one verdict button on each side, and two dialogs.
The chrome is positioned against the window rather than laid out in flow, so the script measures the bars and one verdict button and hands their sizes to the stylesheet as custom properties.
That is what keeps the photo clear of them at any window size, without a fixed number in the stylesheet that a wrapped label would break.
Only the bars fade when the mouse and the keyboard go quiet.
The verdict buttons never fade, and the room held for the chrome does not change when a bar does.

Resting and the choice of light or dark are matters for the browser alone.
Neither one makes a request, the server knows about neither, and the theme is remembered in `localStorage` rather than in the state file.

## Module map

```
src/phototriage/
├── config.py     file types and the destination naming rule
├── library.py    read-only view of the files on disk
├── review.py     the decisions about one folder
├── store.py      every review, saved to one JSON file
├── transfer.py   copy or move the kept files
├── api.py        HTTP routes
├── __main__.py   command line
└── web/          the interface
```

| Module | Responsibility | Depends on |
| --- | --- | --- |
| `config.py` | The image and RAW extension sets, the default state file path, and `default_destination`, the rule that names the destination folder. | nothing |
| `library.py` | Reading the filesystem. Lists images and subfolders in a stable order, resolves an image name to a safe path, and indexes RAW files by stem. It never writes. | `config` |
| `review.py` | The decisions taken about one source folder, and the destination those decisions lead to. Pure data and three operations: `decide`, `undo`, `verdicts`. It knows nothing about files or HTTP. | nothing |
| `store.py` | Every review, keyed by source folder, the folder opened last, and the RAW pairing preference. Loads and saves the JSON state file. | `config`, `review` |
| `transfer.py` | Turning kept decisions into file copies or moves. Builds a plan of paths, then executes it. | `library`, `review` |
| `api.py` | The HTTP layer. Validates input, mutates the active review or a stored preference, asks the store to persist, and returns a snapshot of the state. | all of the above |
| `__main__.py` | Argument parsing, loading the store, and starting uvicorn on the loopback address. | `api`, `config`, `store` |
| `web/` | The interface. Calls the API, renders the state it gets back, binds the keyboard. | the API |

Dependencies point one way, from `__main__` down to `config`.
No lower module imports a higher one, and no module below `api` knows that an HTTP server exists.

## The flow of one request

A keypress on the right arrow keeps the current image.
This is what happens.

1. `web/app.js` catches the key and calls `POST /api/decide` with `{"verdict": "keep"}`.
   One request is in flight at a time.
   A burst of keystrokes would otherwise send several decisions against the same image before the first response came back.
2. FastAPI validates the body against `DecideRequest`.
   An unknown verdict never reaches the route: it is answered with 422.
3. The route asks for the active review.
   Without one it answers 409, so no route below has to handle a missing source folder.
4. The route takes a snapshot to learn which image is current.
   The snapshot lists the source folder again and takes the first name that has no decision yet.
   The current image is therefore always a file that exists right now, not a remembered index.
5. `Review.decide` appends a `Decision(name, verdict)` to the list.
6. `Store.save` writes the whole store to a temporary file and replaces the state file with it.
7. The route takes a second snapshot and returns it.
   The response carries the new counters, the next image and the one after that.
8. `web/app.js` renders the response, points the viewer at the new current image, and preloads the upcoming one.

Every route that changes something follows the same three steps: mutate, save the store, return a fresh snapshot.
`POST /api/settings` is the same shape one level up: it changes a field on the store rather than the active review, and then saves and answers with a snapshot like the rest.
`POST /api/apply` is the one route outside that pattern.
It changes files rather than decisions, so it writes no state file and answers with a count instead of a snapshot.

Startup follows the same path from the other end.
`main` parses the arguments, loads the store, and hands it to `create_app` together with the folder from the command line, if there is one.
`create_app` opens that folder, or the last folder the store remembers, and only if the path is still a folder.
The application object holds one `Active` record: the source folder and the review being worked on.

## Design decisions

### The decision list is the only state

A `Review` holds a destination and a list of decisions.
The cursor position, the keep count and the discard count are not stored.
They are computed from the decision list every time the interface asks for them.

The reason is undo.
A stored cursor and a stored list can disagree, and every operation then has to keep them in step.
Undo is the operation that gets this wrong: it has to remove a decision, move the cursor back, and lower one of two counters.
With one source of truth, undo is `decisions.pop()` and nothing can drift.

The cost is that the source folder is listed on every request.
That is a directory read, and it buys a second property: images added or deleted while the server runs are picked up without a restart.

### Decisions are keyed by file name

A decision records the name of the image, not its position in the queue.

Positions are not stable.
Between two runs you might delete a few files, or the camera might add some.
With an index, deleting one early file shifts every later decision by one, and the review silently applies your verdicts to the wrong images.
With a name, a file that disappears takes its decision out of use, and a new file arrives undecided.

This is also what makes the queue resumable in the first place.
The pending list is "every image in the folder without a decision", which is a set difference, not a saved position.

### One state file for every review

All reviews live in one JSON file, keyed by the absolute path of the source folder, with the folder opened last recorded next to them.

The alternative is one file per source folder, or a file inside each source folder.
A file inside the source folder would write into the very folder the app promises not to disturb.
One file per folder somewhere else means several files that have to agree with each other, and a rule for what happens when one of them is missing.

One file makes every save a single atomic operation: write a temporary file next to the target, then replace the target with it.
`state.json` is written by way of `state.tmp` in the same folder.
An interrupted save therefore leaves the previous state intact, never a truncated file.
The price is that the whole file is rewritten on every decision, which is acceptable at the size a photo review reaches.

Loading is forgiving on purpose.
A missing file, unreadable JSON, a payload of the wrong shape, or a schema version the code does not know all produce an empty store instead of an error.
The app has to start, because refusing to start would leave you unable to review anything at all.

### The RAW preference is global, not per source folder

`pair_raws` is a field on `Store`, next to the reviews rather than inside one.
`transfer.build_plan` takes it as an argument, so nothing below the API decides it.

The reason is what the flag describes.
It is a working habit, not a property of a folder.
Whether you archive your RAW files with the selection is a decision about how you work, and it does not change because you moved from one shoot to the next.
Stored per review, it would have to be set again for every folder, and a folder opened for the first time would need a default that the previous folder had just contradicted.

The cost is that there is no way to pair RAW files in one folder and not in another without touching the switch between them.
That is the trade the flag is worth: one control that means the same thing everywhere.

`Review` therefore keeps only what belongs to one folder, which is the destination and the decisions.

### The API layer is the transaction boundary

Routes are the only place where a change and its persistence meet.
A route mutates the review, then calls `store.save()`.

`Review` never saves itself, and `Store` never decides anything.
So `review.py` can be tested with no filesystem, and `transfer.py` can be tested with no HTTP.
It also means there is exactly one list of places where the disk is written, and it is the list of routes in `api.py`.

### The server sends original image bytes

`GET /api/image/{name}` returns the file from disk with no processing.
There is no resizing, no thumbnail and no re-encoding.

Browsers already apply EXIF orientation to an image they display, so a rotated photo shows the right way up without the server touching it.
Doing the rotation on the server would mean decoding and re-encoding every image, which is slower than sending the bytes and would show you a picture that is not exactly the file you are judging.

This is why the project has no Pillow dependency.
The whole runtime is FastAPI and uvicorn.

### `resolve_image` refuses anything outside the source folder

The image route takes a name from the URL.
`library.resolve_image` joins it to the source folder, resolves the result, and returns `None` unless the resolved parent is the source folder itself and the extension is a known image type.

Resolving first is what makes the check hold.
`../../etc/passwd` fails it, and so does a symbolic link inside the source folder that points somewhere else, which a string comparison on the name would miss.
The extension check stops the route from serving a text file that happens to sit next to the photos.

The route answers 404 for all of these, and the tests cover the escaped separator, the escaped dots, two levels up, the symlink and the non-image file.

### `free_name` is evaluated immediately before each transfer

`transfer.execute` asks for a free name in the destination just before it copies or moves each file, not once when the plan is built.

Names are decided one at a time because the destination changes as the run proceeds.
If two files in the same plan are called `photo.png`, and free names were chosen up front, both would be offered the same free name and the second would overwrite the first.
Checking immediately before each transfer means the first file has already taken `photo.png` when the second one asks, so the second becomes `photo_1.png`.

The same check covers a destination that already holds files from an earlier run.
No file in the destination is ever overwritten.

### The folder browser lives on the server

`GET /api/browse` lists the subfolders of a path, and the interface uses it to walk the disk.

A browser cannot give a web page an absolute filesystem path.
A file input hands over file contents and a bare name, never the folder they came from.
The app needs the folder, because it works on a folder and copies files next to it.
So the walking has to happen on the server, and the browser only draws the result.

That endpoint can list any folder the user account running the server can read.
This is the reason the server binds to `127.0.0.1` only.
See the security note in [api.md](api.md#why-loopback-and-json-are-the-boundary).

## The state file

```json
{
  "version": 1,
  "last": "/home/you/Pictures/2024",
  "pair_raws": true,
  "reviews": {
    "/home/you/Pictures/2024": {
      "destination": "/home/you/Pictures/2024_keep",
      "decisions": [
        { "name": "IMG_01.jpg", "verdict": "keep" },
        { "name": "IMG_02.jpg", "verdict": "discard" }
      ]
    }
  }
}
```

- `version` is `SCHEMA_VERSION` in `store.py`, which is `1`.
  Any other value makes the app start with an empty store.
  Raise it whenever the shape of `reviews` changes.
- `last` is the source folder to reopen at startup, or `null`.
- `pair_raws` is the RAW pairing preference, and it applies to every review in the file.
  A file without the key reads as `true`, which was the behaviour before the key existed.
  A value that is present is read through `bool()`, so a hand-edited `null` or `0` reads as off.
  Only `POST /api/settings` writes it, and it always writes a boolean.
- Keys of `reviews` are absolute source folder paths.
- `decisions` is in the order the decisions were taken, which is the order undo walks back through.
  It is not the order of the queue.

The file is written with `ensure_ascii=False`, so accented file names stay readable.

## Known limits

These follow from the design above.
They are recorded here so that a reader does not have to find them by surprise.

- **One active review per running server.**
  The `Active` record holds a single source folder.
  Two browser windows on the same server share it, so choosing a folder in one changes what the other shows.
- **Two servers sharing one state file overwrite each other.**
  Each save writes the whole file.
  The last save wins, and the reviews the other process held in memory are written back over it.
  Give a second instance its own `--state-file`.
- **A transfer is not a transaction.**
  `execute` walks the plan file by file.
  If the filesystem refuses part way through, the files already transferred stay in the destination and the route reports a server error instead of a count.
  The error says the transfer was interrupted, but not how far it got.
  Running again is safe, because no name is overwritten.
- **A decision cannot be changed, only undone.**
  There is no route that rewrites a verdict for a named image.
  Undo removes the most recent decision, so correcting an older one means undoing everything after it.
- **A second run in copy mode transfers everything again.**
  `POST /api/apply` changes no decision, so the kept images are still kept when it returns.
  The interface only disables the run button when the kept count is zero, which a copy never causes, so a second press is one click away and lands the whole selection in the destination again under `name_1` names.
- **Only the top level of the source folder is reviewed.**
  `library.list_images` lists the folder itself and does not walk into subfolders.
  A video file is not a reviewable image and not a RAW file, so it is neither reviewed nor paired.
