# HTTP API

Every route the server answers, what it takes, what it returns, and every status code it can produce.
The routes are defined in `src/phototriage/api.py`.

The API exists for the interface bundled with the app.
It is not versioned, and it is reachable only from the machine it runs on.
Read [architecture.md](architecture.md) for why it is built this way.

## Conventions

The base URL is `http://127.0.0.1:8000`, or the port given by `--port`.
All routes below are under `/api`.
Everything else under `/` is the static interface.

A `POST` takes a JSON body and needs the `Content-Type: application/json` header.
A body in any other format is refused with 422 before the route runs.

Responses are JSON, except `GET /api/image/{name}`, which returns file bytes.

An error carries a single field:

```json
{ "detail": "Elige una carpeta origen." }
```

Messages in `detail` are in Spanish, because they are shown in the interface.

A 422 comes from the request validator rather than from the app, and there `detail` is a list of objects instead of a string:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "verdict"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

Every error uses this envelope, including a filesystem failure during a transfer.
The status codes each route can return are listed under it.

## Objects

### State

Everything the interface needs to draw itself.
Returned by `/api/state`, `/api/source`, `/api/destination`, `/api/settings`, `/api/decide` and `/api/undo`.

| Field | Type | Meaning |
| --- | --- | --- |
| `source` | string or null | Absolute path of the folder being reviewed. `null` when no folder is open. |
| `destination` | string or null | Absolute path where the kept images will go. `null` when no folder is open. The folder does not have to exist yet. |
| `total` | integer | Reviewable images currently in the source folder. |
| `reviewed` | integer | Images in the folder that have a decision. |
| `kept` | integer | Of those, how many were kept. |
| `discarded` | integer | Of those, how many were discarded. |
| `current` | string or null | File name of the image to review now, the first one without a decision. `null` when the queue is empty. |
| `upcoming` | string or null | File name of the next one after `current`, for preloading. `null` when there is no next one. |
| `pair_raws` | boolean | Whether a RAW original is transferred with the image that shares its name. `true` by default. |

The counters are read from the source folder on every request.
A file removed from the folder stops being counted, even though its decision is still recorded.
This is why `total` and `kept` fall after a run in move mode.

With no folder open, every field is `null` or `0`, except `pair_raws`.
That one is a global preference rather than a property of a review, so it is reported whether a folder is open or not.

### Listing

One folder as shown by the folder browser.
Returned by `/api/browse`.

| Field | Type | Meaning |
| --- | --- | --- |
| `path` | string | Absolute path of the folder that was listed. |
| `parent` | string or null | Absolute path of the parent folder, or `null` at the filesystem root. |
| `folders` | array of strings | Names of the visible subfolders, sorted ignoring case. Names starting with a dot are left out. |
| `images` | integer | Reviewable images directly inside this folder. Subfolders are not counted. |

## Routes

### `GET /api/state`

The current state.
Takes no parameters and changes nothing.

| Status | Cause |
| --- | --- |
| 200 | A [State](#state) object. |

This route has no failure of its own.
A source folder that has become unreadable since it was opened reads as empty, so the answer is a state with `total` at `0` rather than an error.

### `GET /api/browse`

List the subfolders of a path, so the interface can walk the disk.

| Parameter | In | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| `path` | query | string | `~` | `~` is expanded. A relative path is resolved against the folder the server was started from. |

| Status | Cause |
| --- | --- |
| 200 | A [Listing](#listing) object. |
| 400 | The path could not be resolved. `Ruta inválida: ...` |
| 403 | The folder exists but cannot be read by the user running the server. `Sin acceso a ...` |
| 404 | The path is not a folder, or does not exist. `No es una carpeta: ...` |

This route does not need an open source folder, and does not change one.

### `POST /api/source`

Open a folder for review, or resume it if it was reviewed before.

```json
{ "path": "~/Pictures/2024" }
```

| Field | Type | Notes |
| --- | --- | --- |
| `path` | string | Required. `~` is expanded, a relative path is resolved, and the result must be an existing folder. |

| Status | Cause |
| --- | --- |
| 200 | A [State](#state) object for the folder now open. |
| 400 | The path could not be resolved. `Ruta inválida: ...` |
| 404 | The path is not a folder, or does not exist. `No es una carpeta: ...` |
| 422 | `path` is missing, is not a string, or the body is not JSON. |
| 403 | The folder exists but cannot be listed. `Sin acceso a ...` It is not recorded, so a restart is unaffected. |

Side effects.
The folder becomes the active review.
Decisions taken about it in an earlier run come back, together with the destination stored for it.
The folder is recorded as the last one opened, and the state file is written.

### `POST /api/destination`

Set where the kept images will go.

```json
{ "path": "/home/you/Selection" }
```

| Field | Type | Notes |
| --- | --- | --- |
| `path` | string | Required. Must be absolute. `~` is expanded. Empty or blank means "back to the default", a sibling of the source folder with a `_keep` suffix. |

| Status | Cause |
| --- | --- |
| 200 | A [State](#state) object with the new `destination`. |
| 400 | The path is relative. `Usa una ruta absoluta: ...` |
| 409 | No source folder is open. `Elige una carpeta origen.` |
| 422 | `path` is missing, is not a string, or the body is not JSON. |

The path is not resolved and does not have to exist.
It is stored as typed, after `~` is expanded, and it is created when a transfer runs.
The decisions already taken are not affected.

### `POST /api/settings`

Set the RAW pairing preference.

```json
{ "pair_raws": false }
```

| Field | Type | Notes |
| --- | --- | --- |
| `pair_raws` | boolean | Required. `true` transfers a RAW original with the image that shares its name, `false` transfers the image alone. |

| Status | Cause |
| --- | --- |
| 200 | A [State](#state) object with the new `pair_raws`. |
| 422 | `pair_raws` is missing, cannot be read as a boolean, or the body is not JSON. |

The preference is global.
It is not tied to a source folder, so this route needs no open review and answers 200 with no folder open.
It is written to the state file straight away, under the key `pair_raws`, and it survives a restart.

It changes what the next `POST /api/apply` transfers.
Nothing already transferred is affected.

### `POST /api/decide`

Record a verdict for the current image and move to the next one.

```json
{ "verdict": "keep" }
```

| Field | Type | Notes |
| --- | --- | --- |
| `verdict` | string | Required. `keep` or `discard`. Any other value is refused. |

| Status | Cause |
| --- | --- |
| 200 | A [State](#state) object, with `current` already advanced. |
| 409 | No source folder is open. `Elige una carpeta origen.` |
| 409 | The queue is empty, so there is nothing to decide. `No hay nada que revisar.` |
| 422 | `verdict` is missing, is not one of the two values, or the body is not JSON. |

The route does not take an image name.
The verdict always applies to `current`, which the server works out from the folder at the moment of the request.
The state file is written before the response is sent.

### `POST /api/undo`

Cancel the most recent decision.

The route reads no body.
Sending `{}` and sending nothing both work.

| Status | Cause |
| --- | --- |
| 200 | A [State](#state) object. |
| 409 | No source folder is open. `Elige una carpeta origen.` |

Undo with no decisions left is not an error.
It returns the unchanged state.

Undo walks back through the order the decisions were taken, which is not always the order of the queue.
It cancels the decision, not the transfer: a file already copied or moved stays where it is.

### `POST /api/apply`

Transfer the kept images to the destination, with their RAW originals when `pair_raws` is on.

```json
{ "mode": "copy" }
```

| Field | Type | Notes |
| --- | --- | --- |
| `mode` | string | Required. `copy` or `move`. Any other value is refused. |

Response:

```json
{ "transferred": 2, "destination": "/home/you/Pictures/2024_keep" }
```

| Field | Type | Meaning |
| --- | --- | --- |
| `transferred` | integer | Files sent to the destination, images and RAW files together. |
| `destination` | string | The folder they went to. |

| Status | Cause |
| --- | --- |
| 200 | The transfer finished. |
| 409 | No source folder is open. `Elige una carpeta origen.` |
| 422 | `mode` is missing, is not one of the two values, or the body is not JSON. |
| 500 | The destination could not be created, or a file could not be copied or moved. `La transferencia se interrumpió: ...` Files transferred before the failure stay in the destination, and the count is not reported. |

Notes.
The plan is built from the verdicts and from `pair_raws` as it stands at the moment of the request.
With `pair_raws` off, no RAW file is in the plan.
A kept image whose file is no longer in the source folder is skipped, so the plan is always executable.
A RAW file shared by two kept images is transferred once.
No file in the destination is overwritten: a name already taken becomes `name_1`, `name_2`, and so on.
The destination folder is created even when nothing is transferred, so a call with no kept images answers `{"transferred": 0, ...}` and leaves an empty folder behind.
The decisions are not cleared, so calling twice in copy mode transfers everything twice under different names.
This route does not write the state file, because it changes no decision.

### `GET /api/image/{name}`

The bytes of one image from the source folder.

| Parameter | In | Type | Notes |
| --- | --- | --- | --- |
| `name` | path | string | File name inside the source folder, URL-encoded. Not a path: anything that resolves outside the folder is refused. |

| Status | Cause |
| --- | --- |
| 200 | The file. `Content-Type` is guessed from the extension, and range requests are supported. |
| 404 | The file does not exist, is not a reviewable image type, or resolves outside the source folder, including through a symbolic link. `No existe la imagen ...` |
| 409 | No source folder is open. `Elige una carpeta origen.` |

The file is sent exactly as it is on disk.
Nothing is resized or re-encoded, and browsers apply EXIF orientation themselves.

## Static routes

The interface is mounted at `/`, after the API routes, so `/api/...` always wins.

| Path | Result |
| --- | --- |
| `/` | `index.html` |
| `/style.css`, `/app.js` | The interface files. |
| `/docs`, `/redoc`, `/openapi.json` | The generated OpenAPI documentation, which FastAPI adds by default. |
| anything else | 404 with `{"detail": "Not Found"}` |

## Why loopback and JSON are the boundary

The API has no authentication, and it does not need one, as long as two properties hold together.

The API is powerful.
`GET /api/browse` lists any folder the user account running the server can read.
`POST /api/apply` in move mode moves files.
Anything that can send requests to the port can therefore read your folder names and rearrange your photos.

**The server binds `127.0.0.1`.**
The address is hard coded in `__main__.py` and no option changes it.
Only a process on the same machine can open a connection.
Binding `0.0.0.0` would hand a folder browser to the local network.

**Every route that changes something is a `POST` with a JSON body.**
This matters because the browser you review in also visits other pages.
A page from another site can make your browser send a form to `http://127.0.0.1:8000`, which is a local address the attacking page cannot read but can still reach.
Such a form can only be sent as `application/x-www-form-urlencoded`, `multipart/form-data` or `text/plain`, and all three fail validation with 422 before the route body runs.
Sending `application/json` from another origin is not a simple request, so the browser asks permission with a preflight first.
No CORS middleware is installed, the preflight is unanswered, and the browser drops the request.

The `GET` routes can be reached from another page, for example by pointing an `<img>` at `/api/image/...`.
That page cannot read the response, and no `GET` route changes anything, so what it learns is nothing.

Keep both properties.
Adding a CORS middleware, or serving on another host, removes the only thing standing between a web page and your photo folders.
