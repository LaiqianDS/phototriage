# Changelog

All notable changes to this project are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- A verdict now names the photo it was taken on, and the server refuses it when
  that photo is no longer the next one.
  Before, a second window showing a photo already decided, or a new file that
  sorted in front of the photo on screen, sent the verdict to a photo nobody
  saw.
  The page then shows the photo that is next, with `La cola ha cambiado`.

## [0.4.0] - 2026-09-17

### Added

- The confirmation before a run names how many files would go, their size and
  the destination: `¿Copiar 312 archivos (8,4 GB) a ...?`.
  A new route, `GET /api/plan`, counts the plan without touching the
  destination.
- Progress during a run on the status line: `Copiando 120 de 312 (3,2 GB de
  8,4 GB)`, from a new route, `GET /api/progress`.
  A page reloaded during a run picks the progress up again, and a second run
  is refused with 409 while one is in flight.

### Changed

- The workflows use the versions of their GitHub actions that run on Node.js
  24, ahead of the removal of Node.js 20 from the runners.

### Fixed

- Leaving focused mode no longer throws in Safari before 16.4, which has no
  unprefixed fullscreen API.

## [0.3.0] - 2026-09-17

### Added

- Zoom.
  `Space` shows the photo at one image pixel per screen pixel, so a soft photo
  no longer passes for a sharp one, and `Space` again fits it back in the
  window.
  Dragging pans the photo, and the next photo always arrives fitted.
- Search subfolders, a switch in the settings dialog, off by default.
  The queue then holds every image in the tree under the source folder, named
  by its path, and a kept image keeps its subfolder inside the destination.
- Carry videos, a switch in the settings dialog, off by default.
  A kept image then takes the video of the same name in the same folder with
  it, the other half of a live photo.
- Buttons for focused mode and the zoom in the bottom bar, each naming its key,
  and a button in focused mode that leaves it.
  Both used to be reachable from the keyboard only.
- `scripts/measure.py`, which times a state read and a decision against a
  folder with the subfolder switch off and on, and writes nothing to it.

### Changed

- The queue is listed about twenty times faster.
  On a folder of 4,500 images a decision took 171 ms and now takes 9 ms, and on
  a month of daily folders with subfolders searched, 260 ms and now 15 ms.
- A second copy run copies only what the destination does not already hold,
  byte for byte, instead of the whole selection again under `_1` names.
  `POST /api/apply` reports the files left alone in `already_present`.
- A file that cannot be transferred no longer ends the run.
  The others are still transferred, the failures are reported by name and
  reason in the new `failed` field and on the status line, and a copy cut short
  is removed from the destination.
  `POST /api/apply` now answers 500 only when the destination cannot be
  created.

### Fixed

- Focused mode no longer paints the verdict colours along the edges of the
  photo, where they changed the colours read in it.
- A destination inside the source folder no longer feeds the queue with its own
  copies when subfolders are searched.

## [0.2.0] - 2026-08-30

### Added

- Focused mode.
  `F` gives the photo the whole window: the bars go, along with the room held
  for them, and the browser goes fullscreen when it is allowed to.
  What is left is the progress line, moved to the top edge of the window, the
  two verdicts as colour washed off the left and right edges, and one pill
  carrying the file name, the counters and any message.
  `Escape` leaves.
  It is reached from the keyboard only, and nothing on screen announces it.
- A landing page under `site/`, published to GitHub Pages from `main` at
  <https://laiqiands.github.io/phototriage/>.

### Changed

- Branches merge straight into `dev` with `--no-ff` instead of going through a
  pull request.
  The pull request template is gone, and its four headings are now the shape
  asked of a merge commit message in `CONTRIBUTING.md`.

## [0.1.0] - 2026-08-14

First release.

### Added

- Review a folder of images one at a time and mark each one as keep or discard.
- Show one photo as large as the window allows, with the controls on the edges:
  a top bar and a bottom bar that fade after a few seconds without input and
  return on the next mouse move or keypress, and a discard button and a keep
  button on the left and right edges that never fade.
- Choose the source folder from the interface, by typing a path or by walking
  the disk in a folder browser.
- Collect the kept images into one destination folder, by copy or by move.
  The destination defaults to a sibling of the source with a `_keep` suffix,
  and can be changed.
- Transfer a RAW original together with the image that shares its name, for
  example `IMG_0042.CR2` with `IMG_0042.JPG`.
- Settings dialog behind a button in the top bar, holding the destination
  folder and a switch for RAW pairing.
- Turn RAW pairing off to transfer the kept images alone.
  The choice is global rather than per source folder, it is saved with the
  decisions, and it is on when the app first starts.
- Never overwrite a name already taken in the destination: the new file becomes
  `name_1`, `name_2`, and so on.
- Leave the discarded images untouched in the source folder.
  Nothing is deleted at any point.
- Keyboard review: left arrow discards, right arrow keeps, `U` undoes.
- Save decisions after every keypress, per source folder, so several folders can
  be reviewed in turn and each one resumes where it was left.
  Decisions are keyed by file name, so adding or removing images between runs
  does not shift the queue.
- Interface in light and dark, following the system appearance until the theme
  button in the top bar is used.
  The choice is then remembered by the browser.
- Serve on the loopback address only, so no folder is reachable from the
  network.
- Command line: `phototriage [source] [--state-file PATH] [--port N]`.

[Unreleased]: https://github.com/LaiqianDS/phototriage/compare/v0.4.0...dev
[0.4.0]: https://github.com/LaiqianDS/phototriage/releases/tag/v0.4.0
[0.3.0]: https://github.com/LaiqianDS/phototriage/releases/tag/v0.3.0
[0.2.0]: https://github.com/LaiqianDS/phototriage/releases/tag/v0.2.0
[0.1.0]: https://github.com/LaiqianDS/phototriage/releases/tag/v0.1.0
