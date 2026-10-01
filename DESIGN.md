# PhotoTriage

**For:** A working photographer who must trust the speed, and a hobbyist who must trust the safety.
**Stack:** Static HTML, CSS and JavaScript with no build step, in `site/` (the public page) and in `src/phototriage/web/` (the app).

This file describes the design as it shipped.
Each value below was read from `site/style.css`, `site/demo.js` and `src/phototriage/web/style.css`.
When the code and this file disagree, correct this file.

## Brief

One design system for two surfaces.

- **The public page, `site/`.**
  A one-page site for PhotoTriage, a local photo culling tool: one photo, one key, nothing deleted, nothing uploaded.
  It must make a working photographer trust the speed and a hobbyist trust the safety, then send both to GitHub to install it.
  It must be complete with the script blocked and with the font request blocked.
- **The app, `src/phototriage/web/`.**
  One review screen that does not scroll: the photo takes the middle and the controls take the four edges.
  The user judges sharpness and colour, so the interface must not change how the photo reads.
  It has a light theme and a dark theme.

## Content

The copy of the public page is in `site/index.html`, and the labels of the app are in `src/phototriage/web/index.html`.
A change to the copy needs the maintainer's agreement.
The limits in `PRODUCT.md` hold: no invented testimonials, user counts or benchmarks, and the figures 480 and 31 stay an illustration.

## Overview

Warm paper, one dark ink, light headlines and pill buttons: a quiet page that reads like a studio notebook.
The system started from the ElevenLabs style reference.
The difference is the colour rule: the only accent is the orange of the kept slide in the logo, and it marks what is kept and nothing else.
All other colour comes from the photos.

## Tokens - Colors

| Name | Value | Token on the page | Token in the app | Role |
|------|-------|-------------------|------------------|------|
| Eggshell | `#fdfcfc` | `--color-eggshell` | `--surface`, `--bar` | Page canvas, bars, sheets, buttons, slide mounts |
| Taupe | `#f5f3f1` | `--color-taupe` | `--surface-hover` | Section bands, the demo panel, hover of an outline control |
| Stone | `#ebe8e4` | `--color-stone` | `--track`, `--border`, `--bar-line` | Hairlines, tracks, the background of `code` on taupe |
| Ink | `#14191c` | `--color-ink` | `--text`, `--fill`, `--focus` | Headings, filled buttons, focus ring. It is the ink of the logo. |
| Graphite | `#44403b` | `--color-graphite` | `--text-muted`, `--discard` | Body text on the page, muted text and Discard in the app |
| Warm grey | `#8a847c` | not used | `--border-strong` | Border of inputs and outline buttons, the Discard icon in focused mode |
| Kept orange | `#e4531f` | `--color-kept` | `--keep` | The Keep control, the kept dots, the line under "31 photos" |
| Kept orange, hover | `#ee6a3a` | `--color-kept-hover` | `--keep-hover` | Hover of the Keep control |
| Stage grey | `oklch(94% 0 0)` | not used | `--bg` | The area around the photo. It has no hue, so it cannot tint the photo. |
| Error red | `oklch(52% 0.19 28)` | not used | `--error` | Error messages only |

**Dark theme, app only.**
The public page is light only.

| Role | Value | Token |
|------|-------|-------|
| Stage | `oklch(17% 0 0)` | `--bg` |
| Bars and sheets | `#1f1d1b` | `--surface`, `--bar` |
| Hover | `#2a2725` | `--surface-hover` |
| Track | `#33302d` | `--track` |
| Hairline | `#36322f` and `#3d3936` | `--border`, `--bar-line` |
| Text | `#f5f3f1` | `--text`, `--fill`, `--focus` |
| Muted text and Discard | `#b8b2aa` | `--text-muted`, `--bar-muted`, `--discard` |
| Error | `oklch(70% 0.19 27)` | `--error` |

The orange, its hover and the ink on it (`--on-keep: #14191c`) are the same in both themes.

**The sample photos on the public page** carry their own colour, and the colour rule does not apply to them.

## Tokens - Typography

### Bricolage Grotesque (`--font-display`)
- **Use:** `h1`, `h2` and the result statement on the public page only.
- **Weight:** 300. Never bold.
- **Letter spacing:** -0.02em.
- **Line height:** 1.1 for `h1`, 1.15 for `h2`.
- **Fallback:** `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` at the same weight.
- **Request:** one request to Google Fonts, `Bricolage+Grotesque:opsz,wght@12..96,300`.

### System face (`--font-body` on the page, `--font` in the app)
- **Stack:** `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`.
- **Use:** everything else on the page, and everything in the app.
- **Weights:** 400 for text, 500 for buttons, `h3`, terms and counts.
  No 600 and no 700.

### System monospace (`--font-mono`)
- **Stack:** `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`.
- **Use:** file names, paths, commands, keys and the table of files, at 13px.

### Type Scale

| Role | Size | Weight | Line height | Token |
|------|------|--------|-------------|-------|
| display (`h1`) | `clamp(2.25rem, 3vw + 1.25rem, 3.5rem)` | 300 | 1.1 | `--text-display` |
| heading (`h2`) | `clamp(1.75rem, 1.5vw + 1.25rem, 2.25rem)` | 300 | 1.15 | `--text-xl` |
| subheading (`h3`), hero text | 18px | 500 for `h3`, 400 for text | 1.3 for `h3`, 1.5 for text | `--text-md` |
| body on the page | 16px | 400 | 1.5 | `--text-base` |
| body in the app | 15px | 400 | 1.5 | none |
| button | 14px on the page, 15px in the app | 500 | 1 | none |
| note, mono, table | 13px | 400 | 1.5 | `--text-sm` |
| Keep and Discard cards in the app | 20px | 500 | 1.5 | none |
| sheet title in the app | 20px | 400 | 1.5 | none |

The smallest text is 13px.

## Tokens - Spacing & Shapes

**Base unit:** 4px

### Spacing Scale

| Page token | App token | Value |
|------------|-----------|-------|
| `--space-2xs` | `--space-1` | 4px |
| `--space-xs` | `--space-2` | 8px |
| `--space-sm` | `--space-3` | 12px |
| `--space-md` | `--space-4` | 16px |
| `--space-lg` | `--space-5` | 24px |
| `--space-xl` | none | 40px |
| `--space-2xl` | none | 64px |
| `--space-section` | none | `clamp(4rem, 8vw, 6rem)` |
| `--gutter` | none | `clamp(1rem, 4vw, 4rem)` |

### Border Radius

| Element | Value |
|---------|-------|
| Buttons, keys, chips, the segmented control, switches | pill (`9999px` on the page, `999px` in the app) |
| The demo panel on the page | 24px |
| Keep and Discard cards, sheets and notices in the app | 20px |
| Slide mounts, `pre`, the folder list | 10px |
| Inputs, `code`, `kbd`, folder rows | 4px |
| A photo, in the app and in a slide mount | 0 |

### Shadows

One shadow, `--shadow-whisper`, on the public page only:
`0 0 1px rgb(0 0 0 / 0.4), 0 1px 1px rgb(0 0 0 / 0.04), 0 2px 4px rgb(0 0 0 / 0.04)`.
It is on outline buttons, slide mounts and `pre`.
The app has no shadow.

## Layout

**Public page**

- One centred column, 80rem wide at most, with the gutter on each side.
- Sections are `--space-section` apart.
- The top bar is plain and not sticky: the logo with the name on the left, an outline GitHub button on the right.
- The hero puts the headline on the left and the text, the button and the run command on the right.
- Below it, the demo is one taupe panel as wide as the column.
- The order of the grounds is: hero on eggshell, problem on eggshell, the idea on a taupe band, the three steps on eggshell, the table of files on eggshell under a hairline, the result on taupe, the guarantee on eggshell, the fine print under a hairline, the close on taupe.
- The taupe band of the idea section reaches both window edges with a `box-shadow` of `100vmax` cut by a `clip-path`.
- The three steps are rows with a hairline above each one, not a grid of cards.

**Breakpoints of the public page**

- Below 40rem everything is one column, and the demo puts the large slide above the two trays.
- From 40rem the demo is three columns (tray, slide of 34rem at most, tray), and each step puts its path beside its text.
- From 60rem the hero and each split section are two columns, and the idea section is three.

**App**

- The stage is fixed to the window, less the bars and the two cards, with an inset of 8px.
- The top bar holds the counts, the source field, Browse, the theme button and the settings button.
- The bottom bar holds Undo, Focused mode, Zoom, Copy or Move, Run, and one line for the file name and the status.
- Discard is a card on the left edge and Keep is a card on the right edge, each 7.5rem wide.
- Below 44rem the cards are 4.5rem wide and the top bar wraps.

## Components

### Filled pill button
Ink fill, eggshell text, 44px high, 500 weight.
Hover is graphite on the page and `--fill-hover` in the app.
It is the main action: "Get it on GitHub", "Run", "Use this folder", "Done".

### Outline pill button
Eggshell fill and ink text, 44px high.
On the page it has a stone border and the whisper shadow.
In the app it has a `--border-strong` border and no shadow.
Hover is taupe.
A toggle that is on (`aria-pressed="true"`) takes the track colour.
Disabled is 40% opacity.

### Keep
The one control that carries the orange: orange fill, ink text.
On the page it is the Keep key of the demo.
In the app it is the card on the right edge, 20px radius, with the icon, the label and the key.
Hover is `--keep-hover`.

### Discard
Neutral, because a discard changes nothing on disk.
In the app it is the card on the left edge: bar fill, `--border-strong` border, ink text.
On the page it is the outline key "Leave".

### Chip
A pill with a dot and a count, in the top bar of the app.
The kept chip has an orange dot on a tint of the orange (`rgb(228 83 31 / 0.12)`, or `0.2` in the dark theme).
The discarded chip has a graphite dot on the track colour.

### Segmented control
A pill track with two pill labels, Copy and Move.
The chosen label takes the surface colour.

### Switch
A pill track of 2.75rem by 1.5rem.
On is the ink (`--fill`), not the orange.

### Sheet
A `dialog` with a 20px radius, a hairline border and a scrim of `rgb(20 25 28 / 0.45)`.
It holds the folder explorer and the settings.

### Notice
A card in the middle of the stage, 20px radius, for the states with no photo.

### Slide mount
On the page only: an eggshell card with a 10px radius and the whisper shadow, with a sample photo inside and the file name below.
A kept mount has an orange dot on its corner.

### Demo panel
On the page only: a taupe panel with a 24px radius.
It holds the title and the count, the "left alone" tray, the slide with the next one under it, the "kept" tray, and three keys.

### Rows
A term and its meaning with a stone hairline above each pair.

### Table of files
Monospace at 13px with stone hairlines.
A kept row has ink text and an orange dot before the file name.

### Focused mode in the app
The bars are hidden and the cards lose their fill.
The Keep icon is orange and the Discard icon is `--border-strong`, at 62% opacity.
A pill at the bottom holds the file name and the counts, and a pill at the top right leaves the mode.

## States

- **Empty, app:** "Choose a source folder to start." before a folder is chosen, and "That folder has no images." for a folder with none.
- **Finished, app:** "Review finished."
- **Loading, app:** the stage goes to 55% opacity, but only after 250ms, so a fast answer never flickers.
- **Error, app:** the status line, or the count line of the explorer, shows the message in `--error`.
- **Disabled:** 40% opacity for buttons, 35% for the two cards.
- **Finished, demo on the page:** the label says "Review finished" and Leave and Keep are disabled.
- **No script, page:** the keys and the hint "Press the arrow keys." stay hidden, and the panel shows the roll as it stands.
- **No font, page:** the headlines use the system face at weight 300.

## Motion

- **Hover and press:** 120ms for colour, 90ms to 120ms for the press, with `cubic-bezier(0.16, 1, 0.3, 1)`.
  A press moves a page button down 1px and scales an app button to 0.98.
- **Verdict in the demo:** a copy of the slide travels to its tray and shrinks to the size of the tray in 320ms with `cubic-bezier(0.5, 0, 0.2, 1)`.
  It shows where the photo went.
  At the same time the next slide comes up straight in 220ms, so a new verdict never waits for the trip.
- **Count in the demo:** when the slide lands, the count of that tray comes up from below in 200ms.
- **Undo in the demo:** the slide comes back from the tray it went to, in 280ms.
- **Result section:** the three kept frames fade in and grow from 80% in 500ms, 150ms apart, the first time the section is 30% on screen.
  Without the script they are there from the start.
- **Bars in the app:** fade and move 0.75rem in 240ms when the pointer rests, and return when it moves.
- **Sheet:** rises 0.5rem and fades in, in 180ms.
- **Progress line:** its width follows the count in 260ms.
- **Switch and segmented control:** 140ms to 160ms.
- **Reduced motion:** each transition and animation is cut to 0.01ms, the demo and the result section skip their animations, and the bars do not fade.
  The 250ms delay of the loading state stays.

## Accessibility

Contrast was measured with a script on 2026-10-01.

- Graphite text: 10.0 to 1 on eggshell, 9.3 on taupe, 8.4 on stone.
- Eggshell on ink: 17.3 to 1.
- Ink on the orange: 4.7 to 1, and 5.7 on the hover orange.
- The orange as a mark: 3.7 to 1 on eggshell, 3.4 on taupe, 4.5 on the dark bar.
  It is never the colour of small text.
- `--border-strong`: 3.6 to 1 on eggshell and 4.5 on the dark surface.
- Dark theme: text 15.2 to 1, muted text 8.0 to 1.
- **Focus:** a 2px ring in the ink (in `--focus` in the dark theme), offset 2px to 3px, on each control.
- **Keyboard:** each control is a native button, link, input or `dialog`.
  In the app the right arrow keeps, the left arrow discards, `U` undoes, `F` enters focused mode, `Space` zooms and `Escape` leaves.
  The demo answers the same three keys only while it is on screen.
- **Targets:** buttons, keys, folder rows, footer links and the segmented control are 44px high.
- **Not by colour alone:** kept has a label or a dot beside the colour in each place.
- **Selection:** ink ground with light text on both surfaces.

## Do's and Don'ts

### Do
- Use the orange only for what is kept.
- Keep headlines at weight 300 in the display face.
- Use pill buttons with two levels: filled ink and outline.
- Separate with a stone hairline or with space before a shadow.
- Keep the area around a photo free of hue, and keep the corners of a photo square.
- State a limit of the program as plainly as a feature.

### Don't
- Do not use the orange for a link, an emphasis, a switch or a progress line.
- Do not give Discard a colour, and do not use red outside an error message.
- Do not use a weight above 500.
- Do not use text below 13px.
- Do not add a second accent colour.
- Do not load a font in the app.
- Do not add testimonials, customer logos or counts that are not real.

## Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 1 | Eggshell | `#fdfcfc` | The page, the bars and the sheets |
| 2 | Taupe | `#f5f3f1` | Bands and the demo panel, one step above the canvas with no border |
| 3 | Stone | `#ebe8e4` | Hairlines, tracks and small plates |
| App only | Stage | `oklch(94% 0 0)` light, `oklch(17% 0 0)` dark | Under the photo |

## Elevation

The design is flat.
The whisper shadow on the public page is an edge more than a lift.
The app separates with hairlines only.

## Imagery

- **Logo:** `site/logo.svg`, two ink bars for the pile and one orange slide for the keeper.
  The tab icon is `favicon.svg`, a simpler cut on a dark tile.
- **Sample roll:** eleven photographs from one trip to the Gobi desert, in `site/photos/`, each 960 by 640 pixels and 1.2 MB in total.
  Nine are the roll, with near-identical frames as in a real shoot, and two fill the trays at the start.
  Each one is an SVG `symbol`, `#p1` to `#p11` in `site/index.html`, so the demo and the sheet of mounts use the same file.
  The page credits the photographer under the demo.
- **The sheet of mounts:** an SVG pattern of forty blank mounts, shown once undecided and once with three kept.
- **Icons in the app:** inline SVG with a stroke in `currentColor`, drawn for this project.
  There is no icon font and no icon library.
- There are no screenshots of the app in the repository.

## Agent Prompt Guide

**Quick Color Reference**
- text: `#14191c` (headings), `#44403b` (body)
- background: `#fdfcfc` (canvas), `#f5f3f1` (band and panel)
- border: `#ebe8e4` (hairline), `#8a847c` (control border in the app)
- accent: `#e4531f` (kept only), with `#14191c` text on it
- primary action: `#14191c` fill with `#fdfcfc` text

**Example Component Prompts**

1. Create a headline: Bricolage Grotesque weight 300, `clamp(2.25rem, 3vw + 1.25rem, 3.5rem)`, colour `#14191c`, letter spacing -0.02em, line height 1.1, left aligned on `#fdfcfc`.
2. Create a primary button: pill, `#14191c` fill, `#fdfcfc` text, system face 14px at weight 500, 44px high, 24px horizontal padding.
3. Create a Keep control: pill or 20px card, `#e4531f` fill, `#14191c` text, hover `#ee6a3a`.
4. Create a section band: `#f5f3f1` ground, a weight 300 heading, then three columns of an 18px weight 500 title with 16px `#44403b` text, with no cards.
5. Create a slide mount: `#fdfcfc` card, 10px radius, the whisper shadow, a square frame inside with 7% padding, and a 13px monospace file name below.

## Quick Start

```css
:root {
  --color-eggshell: #fdfcfc;
  --color-taupe: #f5f3f1;
  --color-stone: #ebe8e4;
  --color-ink: #14191c;
  --color-graphite: #44403b;
  --color-kept: #e4531f;
  --color-kept-hover: #ee6a3a;

  --font-display: "Bricolage Grotesque", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  --text-sm: 0.8125rem;
  --text-base: 1rem;
  --text-md: 1.125rem;
  --text-xl: clamp(1.75rem, 1.5vw + 1.25rem, 2.25rem);
  --text-display: clamp(2.25rem, 3vw + 1.25rem, 3.5rem);

  --space-2xs: 0.25rem;
  --space-xs: 0.5rem;
  --space-sm: 0.75rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2.5rem;
  --space-2xl: 4rem;
  --space-section: clamp(4rem, 8vw, 6rem);
  --gutter: clamp(1rem, 4vw, 4rem);

  --radius-sm: 4px;
  --radius-md: 10px;
  --radius-lg: 24px;
  --radius-full: 9999px;
  --shadow-whisper: 0 0 1px rgb(0 0 0 / 0.4), 0 1px 1px rgb(0 0 0 / 0.04), 0 2px 4px rgb(0 0 0 / 0.04);

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-micro: 120ms;
}
```

## Sources

- **Reference:** the ElevenLabs style reference, brought by the maintainer on 2026-10-01 from one of the two galleries, [Refero Styles](https://styles.refero.design/) or [getdesign.md](https://getdesign.md/).
  The full text of the reference is in the git history of this file, at commit `92bed3f`.
- **Display typeface:** Bricolage Grotesque, SIL Open Font License 1.1, read in `OFL.txt` of <https://github.com/ateliertriay/bricolage>.
  The page links to the font at Google Fonts and does not ship the font file.
  If the file is added to the repository, read the licence again for what a copy must carry.
- **Photographs:** by Bernard Gagnon, from Wikimedia Commons.
  The Commons API reported the licence of each file as CC0 on 2026-10-01, so no attribution is due, and the page gives one all the same.
  The files, in the order `01.jpg` to `11.jpg`: Khongoryn Els 03, Khongoryn Els 04, Khongoryn Els 05, Camels at Khongoryn Els 01, Camel in Gobi Desert 01, Camels in Gobi Desert 02, Khongoryn Els 14, Khongoryn Els 15, Yurt in Gobi Desert, Yak at Yolyn Am 03, Khongoryn Els 12.
  Each one is at `https://commons.wikimedia.org/wiki/File:<name with underscores>.jpg`.
  Each was cut to 3 by 2 and reduced, with no other change.
- **Icons:** drawn for this project as inline SVG.
  No licence applies and no attribution is due.
- **Logo:** the concepts were made with the logo-design skill of kaankiziltug, as recorded in commit `8d7a049`.
- **Changed from the reference:**
  - Ink is `#14191c`, the ink of the logo, in place of `#000000`.
  - One accent, the logo orange `#e4531f` for what is kept, in place of the violet and ember sparks.
  - Bricolage Grotesque 300 in place of Waldenburg, and the system face in place of Inter.
  - Body text is Graphite, because Smoke and Ash did not reach 4.5 to 1 on each ground.
  - The smallest text is 13px in place of 10px, and each button is 44px high.
  - The trust logo grid, the audio sphere, the tab pill and the account buttons are not used.
  - The area around a photo is a grey with no hue, and a photo has no radius.
  - A dark theme for the app, which the reference does not have.
- **Process:** the comparison of directions in Claude Design was skipped, so one direction was built.
  The review was an audit with the `impeccable` skill on 2026-10-01.
