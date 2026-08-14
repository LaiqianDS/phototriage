# Changelog

All notable changes to this project are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/LaiqianDS/phototriage/releases/tag/v0.1.0
