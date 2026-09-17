# Roadmap

What is planned after 0.3.0, in the order it is worth doing.

This file records intent, not promises.
The [Known limits](README.md#known-limits) section of the README describes what
the app does today, and every entry below that fixes one of them says so.

## Before anything else: measure with real photos

`GET /api/image/{name}` serves the original file with no re-encoding, because
browsers apply EXIF orientation themselves and that choice is what keeps Pillow
out of the dependency list.
The cost is not the transfer, which is local, but the decode: a 24 megapixel
JPEG is decoded in full to be painted at around 800 pixels wide.

A review session over a folder of camera files will show whether that is fine or
not, and the answer decides the order of everything below.
Zoom is in, so what is left to learn is whether the decode stutters.
If it does, thumbnails come next, and that reopens the question of adding an
image library.

Searching subfolders adds a second thing to time in the same session.
The queue is listed again on every request, by design, so with the switch on
that is a walk of the whole tree under the source, and a decision takes two.
`scripts/measure.py` times both requests against a folder, with the switch off
and on, and never writes to it:

```sh
uv run python scripts/measure.py ~/Pictures/2024
```

A synthetic tree has been timed, and it moved the question.
The tree was a month of imports, 30 folders of 150 JPEG and CR2 pairs, and a
flat folder of the same 4,500 JPEG files beside it, all empty files on the
internal SSD.

| Folder | Subfolders | State read | Decision |
| --- | --- | --- | --- |
| Flat, 4,500 images | off | 79 ms | 158 ms |
| Flat, 4,500 images | on | 88 ms | 174 ms |
| Month, 4,500 images in 30 folders | on | 117 ms | 233 ms |

These are medians.
The walk was not the cost, the listing was, and the flat folder paid it with the
switch off.
A profile put nearly all of it in building `Path` objects, above all in
`relative_to`, not in reading the disk.

The listing is now written with `os.scandir` and names kept as strings, with no
cache to keep in step with the disk.
On the same trees:

| Folder | Subfolders | State read | Decision |
| --- | --- | --- | --- |
| Flat, 4,500 images | off | 4 ms | 9 ms |
| Flat, 4,500 images | on | 4 ms | 9 ms |
| Month, 4,500 images in 30 folders | on | 7 ms | 15 ms |

`Store.save` rewrites the whole state file on every decision, so a long review
was timed as well: over 4,500 decisions in a row, the median decision went from
9 ms for the first hundred to 17 ms for the last hundred, with a state file of
365 KB at the end.
That grows, and it is still far below what a keypress can feel.

What is left to learn needs a real card and real photos.
A slow disk makes each directory read dearer, which the SSD above hides, and
the decode of a large JPEG in the browser is not timed by the script at all.

## 0.3.1: what the first real use turns up

Fixes for whatever a session on real photos and a second browser reveal.

The interface uses `:has()`, `backdrop-filter` and the `translate` property.
They are supported in Safari 15.4 and later and in Firefox 121 and later.
The maintainer tried the changes of 0.3.0 in Safari, the default browser on the
machine this was built for, and approved them, before the queue listing was
rewritten; the checks below were not reported one by one, and Firefox has not
been exercised at all.

Focused mode adds two more things to check there.
It asks for fullscreen through `requestFullscreen`, which Safari only spells
without a prefix from 16.4, so an older Safari gets focused mode in a window
instead; the code treats a refusal as normal and does not report it, and
leaving asks whether `document.fullscreenElement` is set rather than comparing
it with `null`, which that Safari leaves undefined.
It also turns the progress line back on with `visibility: visible` inside a bar
that is hidden and carries `backdrop-filter`, and whether a browser paints that
child without painting the parent's blur is the one thing that would show as a
smear across the top edge.

The landing page has been seen in Firefox alone, and never with the Google
Fonts request blocked.
Instrument Serif is much narrower than Georgia, its fallback, so the largest
headings are the place to look first.

## 0.4.0: confidence and comfort

**A grid of the decisions.**
Seeing what was kept and what was discarded, and changing one photo directly.
Today a wrong verdict on photo 40 costs forty undos, because a decision can only
be removed from the end.

**An EXIF strip.**
Date, camera, ISO, shutter and aperture while deciding.
This needs an image library, so it belongs with the thumbnail question rather
than on its own.

## Deliberately not planned

**A static web app on GitHub Pages.**
The File System Access API would let a page with no server read a folder and
write the destination, which fits this app well.
It also means rewriting every Python module in JavaScript, and it drops Safari
and Firefox, which do not support the API for user folders.
Not worth it while the local tool works.
The page published from `site/` is a description of the app, not the app.

**Adding Pillow for convenience.**
It was removed on purpose.
Thumbnails and the EXIF strip both bring it back, so decide it once for both
rather than letting it return through a side door.
