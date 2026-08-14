# PhotoTriage

Review a folder of photos one at a time, and collect the ones you keep.

A shoot leaves you with hundreds of files and no quick way to separate the good ones.
A file manager makes you open, compare and drag.
This app shows one image at a time, takes one decision per image, and then puts the kept images into a folder of their own.
A RAW original travels with the image it belongs to, unless you turn that off.

Everything runs on your machine.
The server listens on `127.0.0.1` only, so no image and no folder name leaves the computer.

The interface is in Spanish.
This documentation is in English.

## What the app never does

- It never deletes a file.
- It never touches a discarded image.
  A discarded image stays in the source folder.
- In copy mode it leaves the source folder complete, so you can check the result before you change anything.
- It never overwrites a file in the destination.
  A name that is already taken becomes `name_1`, then `name_2`, and so on.
- It never serves an image from outside the source folder, not even through a symbolic link.
- It never listens on a public address.
  The host is fixed to `127.0.0.1` and no option changes it.

## Install

You need Python 3.12 or later.
[uv](https://docs.astral.sh/uv/) installs Python, the app and its two dependencies, FastAPI and uvicorn:

```sh
git clone https://github.com/LaiqianDS/phototriage.git
cd phototriage
uv sync
```

## Quickstart

```sh
uv run phototriage ~/Pictures/2024
```

Open <http://127.0.0.1:8000>.

Press the right arrow to keep the image on screen, the left arrow to discard it.
When the queue is empty, choose copy or move and press the run button.
The kept images are then in `~/Pictures/2024_keep`.

Stop the server with `Ctrl-C`.
Your decisions are already on disk.

## The interface

The window is one screen that does not scroll.
The photo takes the middle of it, and the controls take the four edges.

**The photo.**
It is shown as large as the room the controls leave, and centred in it.
That room is measured rather than guessed, so no part of an image is ever hidden behind the interface.
A photo smaller than the space is shown at its own size instead of being enlarged, and a rotated photo is shown the right way up.

**The two bars.**
A top bar runs along the top of the window and a bottom bar along the bottom.
They fade out after about two and a half seconds without input, and come back as soon as you move the mouse, press a key or move the focus.
They are held open while a dialog is open, while the cursor is in a field, and while a message is on the status line.
A bar you reached with the keyboard stays up as long as it holds the focus ring.
When your system asks for reduced motion, the bars do not fade at all.
The photo does not grow when they fade, because their room stays reserved.

**The edges.**
Discard and keep are two large buttons on the left and right edges of the window, on the sides the arrow keys point to.
They never fade.

**The dialogs.**
The browse button and the settings button each open a dialog over the whole window.
`Escape` closes either one, as does its own close button.

**The theme.**
The theme button in the top bar switches between light and dark, and the icon on it shows the theme in use.
Until you press it, the interface follows the system appearance and keeps following it when the system changes.
From the first press your choice wins, and the browser remembers it.
The theme is a browser preference and is not part of the state file, so another browser starts from the system appearance again.

The controls are:

| Control | Where | What it does |
| --- | --- | --- |
| Counters | Top bar | Images reviewed out of the total (`revisadas`), kept (`mantenidas`) and discarded (`desechadas`), with a progress bar along the edge of the bar. |
| Source field (`Origen`) | Top bar | Opens the folder you type, when you press Enter or leave the field. |
| Browse button (`Explorar`) | Top bar | Opens the folder browser. |
| Theme button | Top bar | Switches between light and dark. It carries no text, and it is named after the theme it switches to: `Cambiar a tema oscuro` or `Cambiar a tema claro`. |
| Settings button (`Ajustes`) | Top bar | Opens the settings dialog. |
| Discard button (`Desechar`) | Left edge | Marks the current image as discarded and moves on. |
| Keep button (`Mantener`) | Right edge | Marks the current image as kept and moves on. |
| Undo button (`Deshacer`) | Bottom bar | Cancels the most recent decision. |
| Mode control (`Al ejecutar`) | Bottom bar | Copy the kept images (`Copiar`), or move them (`Mover`). |
| Run button (`Ejecutar`) | Bottom bar | Asks you to confirm, then transfers the kept images to the destination. |
| File name | Bottom bar | The name of the image on screen. |
| Status line | Bottom bar | The result of the last action, or the error it ran into. |
| RAW switch (`Mover los RAW junto a la imagen`) | Settings dialog | Whether a RAW original travels with the image that shares its name. On by default. |
| Destination field (`Carpeta destino`) | Settings dialog | Sets where the kept images will go. |

A control that has nothing to act on is disabled.
Keep and discard are disabled when there is no image to review, undo when no decision has been taken, the run button when nothing is kept, and the destination field until a source folder is open.

## The review workflow

1. Choose the source folder.
   Type its path in the source field (`Origen`), or press the browse button (`Explorar`) and walk the disk.
   The browser starts at the folder in the source field, or at your home folder when that field is empty.
   `Subir un nivel` takes you up, and a folder name takes you into it.
   It reports how many images are in the folder you are looking at, which tells you that you are in the right place before you open it.
   `Usar esta carpeta` opens the folder you are looking at, and `Cancelar` leaves the review as it was.
2. Check the destination.
   It lives in the settings dialog, behind the settings button (`Ajustes`) in the top bar, because it is configuration rather than review.
   It is filled in for you and you can edit it.
   The same dialog holds the RAW switch.
   See [Where the kept images go](#where-the-kept-images-go) and [RAW pairing](#raw-pairing).
3. Review the images.
   One image is on screen at a time, as large as the window allows, and its file name is in the bottom bar.
   The counters in the top bar show how many images you have reviewed out of the total, how many you kept, and how many you discarded.
   The next image is loaded in the background while you look at the current one.
4. Run the transfer.
   When every image has a decision, the app says `Revisión terminada.` in place of the photo.
   Choose `Copiar` or `Mover`, press the run button (`Ejecutar`), and confirm.
   The app reports on the status line how many files it transferred and where they went.
   You do not have to reach the end of the queue first: the run button transfers whatever is kept so far.

Nothing is transferred until you press the run button.
Until then, a decision is only a line in a file.

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| Left arrow | Discard the current image |
| Right arrow | Keep the current image |
| `U` | Undo the most recent decision |

`U` works in either case.

Shortcuts are ignored while the folder browser or the settings dialog is open, and while the focus is in a text field or on the copy and move control.
There the arrow keys move between `Copiar` and `Mover` instead.
There are no other shortcuts.

One action runs at a time.
A key pressed while the previous decision is still in flight is dropped rather than queued, so a burst of keystrokes cannot decide the same image twice.

## Which files are reviewed

Files directly inside the source folder are reviewed.
Subfolders are not searched, and their images are not part of the queue.

These extensions count as reviewable images: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp` and `.tiff`.
Case does not matter, so `IMG_1.JPG` is reviewed like `img_1.jpg`.

Nothing else is part of the queue.
A video file is neither reviewed nor paired with an image, so a clip that sits next to the photos is left where it is, whatever you decide about the images around it.

The queue is sorted by file name, ignoring case, so a camera that numbers its files gives you the images in the order you took them.
The folder is read again on every action, so an image you add or remove while the app runs is picked up without a restart.

## Copy or move

The kept images are transferred when you press the run button.
The mode control decides what happens to the source folder.

**Copy** (`Copiar`) leaves the source folder complete.
Use it when you want to check the result before you change anything.

**Move** (`Mover`) takes the kept images out of the source folder.
What stays behind is exactly what you discarded.
The counters are read from the source folder, so after a move they count only the files that are still there.
Seeing the total drop and the kept count fall to zero means the move worked.

You review `Pictures/2024`:

```
Pictures/
└── 2024/
    ├── IMG_01.jpg    you discard this one
    ├── IMG_02.jpg    you keep this one
    └── IMG_02.CR2    the RAW original of IMG_02
```

After a run in **copy** mode:

```
Pictures/
├── 2024/             unchanged
│   ├── IMG_01.jpg
│   ├── IMG_02.jpg
│   └── IMG_02.CR2
└── 2024_keep/        created for you
    ├── IMG_02.jpg
    └── IMG_02.CR2
```

After a run in **move** mode:

```
Pictures/
├── 2024/             only the discarded images are left
│   └── IMG_01.jpg
└── 2024_keep/        created for you
    ├── IMG_02.jpg
    └── IMG_02.CR2
```

`IMG_01.jpg` is never copied, moved or deleted in either mode.
It is discarded, which here means "left alone".

You can run the transfer more than once.
A second run transfers the kept images again, and because no name is ever overwritten, the destination gets `IMG_02_1.jpg` next to `IMG_02.jpg`.
In copy mode nothing stops you: the kept count does not change, so the run button stays enabled after a successful run.
In move mode there is nothing left to transfer the second time, and the run button is disabled once the kept count reaches zero.

## RAW pairing

By default a kept image takes its RAW originals with it.
A RAW file is paired with an image when both have the same stem, so `IMG_0042.CR2` follows `IMG_0042.JPG`.
Case is ignored in the extension, and one stem can have several RAW files.

These extensions count as RAW: `.cr2`, `.cr3`, `.nef`, `.arw`, `.raf`, `.dng`, `.rw2`, `.orf`, `.srw`, `.pef` and `.raw`.

Two points follow from pairing by stem:

- A RAW file with no kept image of the same stem is never transferred.
  It stays in the source folder, like a discarded image.
  A folder of RAW files alone has nothing to review, because a RAW file is not shown in the viewer.
- If you keep both `IMG_1.jpg` and `IMG_1.png`, the shared `IMG_1.CR2` is transferred once, not twice.

**Turning it off.**
Open the settings dialog with the settings button (`Ajustes`) and turn off the switch `Mover los RAW junto a la imagen`.
The next run then transfers the kept images alone, and every RAW file stays in the source folder.
The switch is on when you first start the app.

The choice is global, not a property of one folder.
It applies to every review, and switching source folders does not change it.
It is saved with your decisions in the state file, so it survives a restart.
A state file written before this option existed reads as "on".

Turning the switch off changes nothing that has already been transferred.
It changes what the next run does.

## Where the kept images go

The destination is a sibling of the source folder with a `_keep` suffix.
Reviewing `~/Pictures/2024` collects into `~/Pictures/2024_keep`.
A sibling gives every source folder its own destination, so reviewing several folders never mixes the results.

Type another path in the destination field (`Carpeta destino`), in the settings dialog, to change it.
The path must be absolute.
A relative path is refused, because resolving it against the folder the server was started from would scatter your images somewhere you never named.
`~` is expanded, so `~/Selection` is accepted.

Clear the field to go back to the default.

Unlike the RAW switch, the destination belongs to one source folder.
Each folder you review keeps the destination you last gave it.

The destination folder does not have to exist.
It is created when you press the run button, together with any parent folder it needs.

## Decisions are saved as you go

Every decision is written to disk as soon as you take it.
There is nothing to save by hand, and closing the browser or stopping the server loses nothing.

Decisions live in one JSON file, by default `~/.phototriage/state.json`.
The file holds one review per source folder, the folder you opened last, and the RAW switch.
So you can review several folders, switch between them, close the app, and resume each one where you left it.
Starting the app without a folder argument reopens the last folder you reviewed.

Inside a review, a decision is stored under the file name of the image, not under its position in the queue.
Adding or removing images between runs therefore does not shift the queue.
An image you already decided about stays decided.
A decision about an image that is no longer in the folder is kept in the file, and is skipped when the transfer runs.

Nothing is written inside your photo folders, except the transferred files themselves.

The file carries a schema version.
When the app finds a version it does not know, it starts with an empty store, and the next decision you take overwrites the file.
An upgrade that changes the format therefore costs you the decisions you had not run yet.
Run your pending transfers before you upgrade.

## Command line

```
phototriage [source] [--state-file PATH] [--port N]
```

| Argument | Default | What it does |
| --- | --- | --- |
| `source` | the last folder reviewed | Folder of images to open at startup. `~` is expanded and a relative path is resolved against the current folder. If the path is not a folder, the app starts with nothing open and waits for you to choose. |
| `--state-file PATH` | `~/.phototriage/state.json` | Where the decisions are saved. The folder is created if it does not exist. |
| `--port N` | `8000` | Port to listen on. |
| `-h`, `--help` | | Print this list and exit. |

The host is always `127.0.0.1`.
There is no option to change it.

## Known limits

These are real.
They are written down so that you do not meet them by surprise.

- **A second run in copy mode copies everything again.**
  The decisions are not cleared by a transfer, and the run button stays enabled after a successful copy.
  The second run finds every name taken, so the destination ends with `IMG_02.jpg` and `IMG_02_1.jpg` side by side.
- **A transfer that fails part way leaves what it already transferred.**
  The files sent before the failure stay in the destination, and the message says only that the transfer was interrupted, not how far it got.
  Running again is safe, because no name is ever overwritten, but the destination may then hold numbered duplicates.
- **A decision can be undone, not changed.**
  There is no way to rewrite the verdict of a named image.
  Undo removes the most recent decision, so correcting an older one means undoing everything taken after it.
- **Only the top level of the source folder is reviewed.**
  Images one level down are not in the queue and are never transferred.
- **Video files are ignored.**
  They are not reviewed, and they are not paired with an image the way a RAW file is.
- **Two browser windows share one review.**
  The server holds a single active review, so choosing a folder in one window changes what the other one shows.
- **Two servers sharing one state file overwrite each other.**
  Each save writes the whole file, so the last one wins.
  Give a second instance its own `--state-file`.

## Troubleshooting

**The app says `Esa carpeta no tiene imágenes.`**
Only files directly inside the folder are reviewed, so check that the images are not one level down in a subfolder.
Check the extension as well: a file type outside the list in [Which files are reviewed](#which-files-are-reviewed) is not part of the queue.
A folder that holds only RAW files looks empty, because a RAW file is transferred with an image and is never reviewed on its own.

**Permission denied on a folder.**
The folder browser reports `Sin acceso a ...` for a folder your user account cannot read, and lets you go back up.
Choosing such a folder as the source is refused with the same message.
The folder is not recorded, so the review you had open stays open and a restart is unaffected.

**Port already in use.**
The server prints `[Errno 48] error while attempting to bind on address ('127.0.0.1', 8000): [errno 48] address already in use` and exits with status 3.
Another program holds the port, or an earlier run of this app is still open in a terminal.
Use another port with `--port 8123`, and open `http://127.0.0.1:8123`.

**I want to keep my decisions somewhere else.**
Pass `--state-file`:

```sh
uv run phototriage --state-file ~/Documents/culling.json
```

Every run that should see those decisions needs the same option, because the app never merges two state files.
A second state file is also the way to start from a clean slate without losing the decisions you already have.

**My decisions are gone.**
The app starts with an empty store when the state file is missing, unreadable, or written by a version of the app with a different schema.
It never stops on a damaged file, because that would leave you unable to review anything.
Check that you are not passing a different `--state-file` than usual, and see the note about upgrades in [Decisions are saved as you go](#decisions-are-saved-as-you-go).

**The destination field refuses my path.**
It answers `Usa una ruta absoluta` when the path does not start at the root.
Type the full path, or use `~`.

**The RAW files did not travel with the images.**
Check the switch `Mover los RAW junto a la imagen` in the settings dialog.
Check the names as well: a RAW file is paired by stem, so `IMG_0042.CR2` follows `IMG_0042.JPG` but `IMG_42.CR2` does not.

**The bars disappeared.**
They fade after about two and a half seconds without input.
Move the mouse or press a key and they come back.

## Documentation

- [docs/architecture.md](docs/architecture.md): the modules, the flow of a request, and why the design is what it is.
- [docs/api.md](docs/api.md): the complete HTTP reference.
- [CONTRIBUTING.md](CONTRIBUTING.md): how to set up, test and lint the project.

## License

MIT.
See [LICENSE](LICENSE).
