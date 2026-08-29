# Roadmap

What is planned after 0.1.0, in the order it is worth doing.

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
If it is fine, zoom comes first.
If it stutters, thumbnails come first, and that reopens the question of adding an
image library.

## 0.1.1: what the first real use turns up

Fixes for whatever a session on real photos and a second browser reveal.

The interface uses `:has()`, `backdrop-filter` and the `translate` property.
They are supported in Safari 15.4 and later and in Firefox 121 and later, but
only Chromium has been exercised.
Safari matters most, because it is the default browser on the machine this was
built for.

## 0.2.0: make it a culling tool

**Zoom to 100 percent.**
This is the largest gap.
Fitted to the window every photo looks good, and the question a review actually
asks is whether the photo is sharp, which only a 1:1 view answers.
Space to toggle, drag to pan.
Without it the app sorts photos but does not let you judge them.

**Search subfolders.**
`library.list_images` reads one level with `iterdir()`.
A folder with one subfolder per day, which is how most cameras and phones
import, has to be reviewed one subfolder at a time.

**Carry video files.**
A `.MOV` or `.MP4` sharing its name with a kept image is not transferred and
nothing says so, because neither extension is in `IMAGE_EXTS` or `RAW_EXTS`.
A folder of holiday media is split in silence.
The settings dialog already exists, so the switch is cheap to add next to the
RAW one.

**Report a partial transfer.**
`transfer.execute` walks the plan file by file.
A failure part way through answers with the error envelope, but not with the
count of what was transferred before it stopped.
It should collect the failures, carry on with the rest, and report both.

## 0.3.0: confidence and comfort

**Preview before running.**
The confirmation says nothing about how many files, how many gigabytes, or
where they are going.
It should: `312 archivos, 8,4 GB` into `2024_keep`.
The same change removes the sharp edge where the run button stays enabled after
a successful copy, so a second click copies everything again under `_1` names.

**Progress during the transfer.**
The status line reads `Procesando...` and can sit there for minutes with no sign
of life.

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
