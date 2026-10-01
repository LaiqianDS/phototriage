# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Two groups, with equal weight.

- The working photographer.
  They come back from a shoot with hundreds of frames, JPG plus RAW.
  They sit at a desktop and want to cull fast, with the keyboard.
- The hobbyist.
  They clear a camera or phone dump now and then.
  They need to be sure that nothing is deleted before they start.

Speed for the first group and safety for the second group get the same weight in each decision.

## Product Purpose

PhotoTriage shows one image at a time and takes one decision for each image: keep or discard.
It then copies or moves the kept images into a folder of their own.
It exists because a file manager makes the user open, compare and drag, and the folder stays unsorted for weeks.
Success is a full folder reviewed in one sitting, with the kept images collected and all other files unchanged.

## Positioning

The program has no delete action, and it runs on the user's machine only.
The server listens on `127.0.0.1` and no option changes that.
A discarded image is not moved, not marked and not renamed.

## Operating Context

- The user starts the program from a terminal: `uv run phototriage <folder>`, then opens `http://127.0.0.1:8000`.
- The review is one screen that does not scroll.
  The photo takes the middle and the controls take the four edges.
- Right arrow keeps, left arrow discards, `U` undoes, `F` enters focused mode, `Space` zooms to one image pixel per screen pixel, `Escape` leaves focused mode.
- The user judges sharpness and colour, so the interface must not change how the photo reads.
- Each decision goes to disk at once, and a review can stop and continue later.
- The public page in `site/` describes the program.
  It is not the program.

## Capabilities and Constraints

- Reviewable images: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp`, `.tiff`.
- RAW files travel with the kept image of the same name.
  This is on by default.
- Videos are never reviewed.
  A video can travel with a kept image of the same name.
  This is off by default.
- Subfolders are not searched by default.
  A switch turns the search on.
- Copy mode leaves the source folder complete.
  Move mode leaves only the discarded files in the source folder.
- A name that is already taken in the destination becomes `name_1`, then `name_2`.
  Nothing is overwritten.
- Undo removes the most recent decision only.
- The program has no ratings, no edits and no thumbnails.
- The interface in `src/phototriage/web/` is static HTML, CSS and JavaScript with no build step.
- The page in `site/` is static HTML, CSS and one script.
  It must be complete with the script blocked and with the font request blocked.
- The app has a light theme and a dark theme.
  It follows the system until the user presses the theme button.

## Brand Commitments

- The name is PhotoTriage.
- The app interface, the public page and the documentation are in English.
- The public page tells its limits plainly ("the parts we would rather not mention").
- No visual identity is binding.
  The maintainer asked for a replacement of the look on 2026-10-01.

## Evidence on Hand

- The program itself, the README and `docs/architecture.md`.
- The figures 480 and 31 on the public page are an illustration of one review.
  They are not measured data and must not be shown as a benchmark.
- There are no screenshots of the app in the repository.
- There are no testimonials, no user counts and no press.
  Future work must not invent them.

## Product Principles

1. The photo is the subject, and the interface gives way to it.
2. One image, one question, one key.
3. Nothing happens to a file until the user runs the transfer, and nothing is deleted.
4. Say what the program does not do as plainly as what it does.
5. Nothing leaves the machine.

## Accessibility & Inclusion

- The existing code holds WCAG AA contrast for text on the bars, with 3:1 for large text and graphical marks.
- Each control is reachable by keyboard and has a visible focus ring.
- Reduced motion is respected: the bars do not fade and the page animations stop.
