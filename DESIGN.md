# PhotoTriage

**For:** A working photographer who must trust the speed, and a hobbyist who must trust the safety.
**Stack:** Static HTML, CSS and JavaScript with no build step, in `site/` (the public page) and in `src/phototriage/web/` (the app).

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

The real content of the public page is the copy in `site/index.html` at commit `91e75ed`: the headline, the sections and their texts.
The real content of the app is the labels and messages in `src/phototriage/web/` at the same commit.
The redesign changes layout and look.
Small changes to the copy are allowed, and each one needs the maintainer's agreement.
The limits in `PRODUCT.md` hold: no invented testimonials, user counts or benchmarks, and the figures 480 and 31 stay an illustration.

## Decisions

Agreed with the maintainer on 2026-10-01.
Where a decision and the reference disagree, the decision wins.

**Keep from the reference**

- The warm surface ladder: eggshell `#fdfcfc`, taupe `#f5f3f1`, stone `#ebe8e4`.
- Light, tight display headlines over a calm body face.
- Pill buttons, filled ink and outline, as the only button hierarchy.
- Hairline dividers and almost no shadow.
- One major visual for each section, and generous space.

**Change**

- **Ink:** `#14191C`, the ink of the logo, in place of `#000000`.
- **Accent:** `#E4531F`, the orange of the kept slide in the logo, in place of the violet and ember sparks.
  It has one job: it marks what is kept.
  It is about 3.7 to 1 on eggshell, so it is for marks, fills and large type, and never for small text.
  Ink text on an orange fill is 4.7 to 1.
- **Discard in the app:** neutral, with no red, because a discard changes nothing on disk.
  Built this way, and the maintainer has not confirmed it yet.
  Red stays for error messages only.
- **Logo:** `site/logo.svg` and `favicon.svg` stay as they are.
  The design is built around them.
- **Display typeface:** Bricolage Grotesque at weight 300, in place of Waldenburg.
  Its licence is the SIL Open Font License 1.1.
- **Body typeface:** the system face on both surfaces, in place of Inter.
- **Direction:** the maintainer skipped the comparison of directions in Claude Design, so the build has one direction and no alternative was drawn.
- **Voice:** the PhotoTriage voice, which states its limits plainly.
- **Removed components:** trust logo grid, audio sphere, tab pill, log-in and sign-up buttons.
- **Text colours:** body text is Graphite `#44403b`.
  Smoke `#777169` is for text on eggshell only, and Ash `#a59f97` is not used for text.
- **Sizes:** the smallest text is 13px, and each button is at least 44px high.
- **Photo stage in the app:** the area around the photo is neutral with no warm tint, and the photo never gets a radius.
- **Themes:** the app has a light and a dark theme, and the dark palette is derived from the same ladder.
  The public page is light only.
- **Fonts:** the app stays on the system font and makes no font request.
  The public page requests the display face only, and it falls back to the system face at the same weight when that request is blocked.

## Reference

The starting point is the ElevenLabs style reference, brought by the maintainer on 2026-10-01.
The Tailwind block of the reference is left out, because this project has no Tailwind.
The sections below are the reference as it came, and they do not yet describe PhotoTriage.

> Warm cream editorial with whispered headlines.
> A Bauhaus studio notebook - eggshell paper, black ink, a single violet and orange spark for product moments.

**Theme:** light

Source measurements are normalized; roles and recommendations are interpreted.
Font summary lists are independent, not paired by position.
HTML examples are reconstructions, not source components.

ElevenLabs runs on a warm-white minimalism: an off-white eggshell canvas (#fdfcfc) holding black type and a single layer of warm taupe surfaces (#f5f3f1).
The brand voice is quiet and confident - whisper-weight Waldenburg at 300 carves display headlines with extreme tightness (-0.02em), while Inter at 400/500 carries everything else with calm neutrality.
Two accent sparks - vivid violet #0447ff and vivid orange #ff4704 - only ignite inside product visuals (audio spheres, product icons), never as UI chrome.
Components stay flat or barely elevated with hairline 1px borders, generous 20px radii on cards, and fully-pilled 9999px buttons.
The system feels like a Bauhaus studio on cream paper: restrained, editorial, and technically precise.

## Tokens - Colors

| Name | Value | Token | Role |
|------|-------|-------|------|
| Eggshell | `#fdfcfc` | `--color-eggshell` | Page canvas, button surfaces, card surfaces - warm off-white rather than clinical white avoids digital glare and gives the site a paper-like calm |
| Warm Taupe | `#f5f3f1` | `--color-warm-taupe` | Section bands, feature cards, and secondary surface level - one step deeper than eggshell, creates quiet separation without borders |
| Stone | `#ebe8e4` | `--color-stone` | Hairline borders, dividers, icon plate backgrounds - warm gray that sits between taupe and mid-gray without feeling cold |
| Ink | `#000000` | `--color-ink` | Primary text, filled buttons, nav, links - pure black anchors the otherwise warm palette and creates the system's only hard contrast |
| Graphite | `#44403b` | `--color-graphite` | Strong secondary text, section labels - barely-warm dark gray for text that needs weight without true-black harshness |
| Smoke | `#777169` | `--color-smoke` | Body text, muted descriptions, caption labels - mid warm-gray; the dominant readable-but-quiet voice across cards and feature copy |
| Ash | `#a59f97` | `--color-ash` | Faintest helper text, tertiary descriptions - the softest gray, used when text should feel like a footnote |
| Violet Spark | `#0447ff` | `--color-violet-spark` | Product visual accent - appears inside audio sphere illustrations and decorative product icons only; never used for UI chrome |
| Ember Orange | `#ff4704` | `--color-ember-orange` | Product visual accent - second sphere color and product icon highlight; paired with Violet Spark inside artwork, never in buttons or links |

## Tokens - Typography

### Waldenburg (`--font-waldenburg`)
- **Substitute:** Inter (300) or Söhne Light
- **Weights:** 300
- **Sizes:** 32px, 36px, 48px
- **Line height:** 1.08-1.17
- **Letter spacing:** -0.96px at 48px, -0.72px at 36px, -0.64px at 32px (-0.0200em throughout)
- **OpenType features:** `"ss01" on if available`
- **Role:** Display and heading type only.
  Used at 48/36/32px with weight 300 - the ultra-light weight is anti-convention; most sites use 600-700, this whisper-weight creates authority through restraint.
  Tight -0.02em tracking pulls letters closer at large sizes.
  Substitute: "Inter" weight 300, or "Söhne" light as a premium alternative.

### Inter (`--font-inter`)
- **Substitute:** Inter or system-ui
- **Weights:** 400, 500
- **Sizes:** 10px, 12px, 13px, 14px, 15px, 16px, 18px, 20px
- **Line height:** 1.20-2.06
- **Letter spacing:** 0.0100em at 14/15/16px sizes, normal elsewhere
- **Role:** Everything outside display: body, nav, buttons, links, captions, inputs, cards.
  Weight 400 is the default; weight 500 reserved for buttons and emphasized links.
  Sizes span 10-20px with relaxed line-heights (1.47-1.6) that give paragraphs breathing room.
  Slight +0.01em tracking (0.0100em) at 14-16px sizes adds legibility at small sizes.

### Geist Mono (`--font-geist-mono`)
- **Substitute:** JetBrains Mono or IBM Plex Mono
- **Weights:** 400
- **Sizes:** 13px
- **Line height:** 1.69
- **Role:** Code-adjacent or technical micro-copy at 13px - used sparingly (freq=28) for technical labels or metadata.
  Single weight, generous 1.69 line-height.

### Type Scale

| Role | Family | Weight | Size | Line Height | Letter Spacing | Token |
|------|--------|--------|------|-------------|----------------|-------|
| caption | - | - | 10px | 1.6 | - | `--text-caption` |
| body-sm | - | - | 14px | 1.5 | 0.14px | `--text-body-sm` |
| body | - | - | 16px | 1.5 | 0.16px | `--text-body` |
| subheading | - | - | 18px | 1.6 | - | `--text-subheading` |
| body-lg | - | - | 20px | 1.35 | - | `--text-body-lg` |
| heading-sm | - | - | 32px | 1.13 | -0.64px | `--text-heading-sm` |
| heading | - | - | 36px | 1.17 | -0.72px | `--text-heading` |
| display | - | - | 48px | 1.08 | -0.96px | `--text-display` |

## Tokens - Spacing & Shapes

**Base unit:** 4px

**Density:** comfortable

### Spacing Scale

| Name | Value | Token |
|------|-------|-------|
| 4 | 4px | `--spacing-4` |
| 8 | 8px | `--spacing-8` |
| 12 | 12px | `--spacing-12` |
| 16 | 16px | `--spacing-16` |
| 20 | 20px | `--spacing-20` |
| 24 | 24px | `--spacing-24` |
| 28 | 28px | `--spacing-28` |
| 32 | 32px | `--spacing-32` |
| 36 | 36px | `--spacing-36` |
| 40 | 40px | `--spacing-40` |
| 48 | 48px | `--spacing-48` |
| 56 | 56px | `--spacing-56` |
| 64 | 64px | `--spacing-64` |
| 72 | 72px | `--spacing-72` |
| 96 | 96px | `--spacing-96` |
| 160 | 160px | `--spacing-160` |

### Border Radius

| Element | Value |
|---------|-------|
| tags | 9999px |
| cards | 20px |
| inputs | 4px |
| buttons | 9999px |
| large-cards | 24px |
| small-elements | 4-10px |

### Shadows

| Name | Value | Token |
|------|-------|-------|
| subtle | `rgba(0, 0, 0, 0.4) 0px 0px 1px 0px, rgba(0, 0, 0, 0.04) 0px 1px 1px 0px, rgba(0, 0, 0, 0.04) 0px 2px 4px 0px` | `--shadow-subtle` |
| subtle-2 | `rgba(0, 0, 0, 0.075) 0px 0px 0px 0.5px inset` | `--shadow-subtle-2` |
| subtle-3 | `rgba(0, 0, 0, 0.1) 0px 0px 0px 0.5px inset` | `--shadow-subtle-3` |
| subtle-4 | `rgba(0, 0, 0, 0.1) 0px 0px 0px 1px inset` | `--shadow-subtle-4` |
| subtle-5 | `rgba(0, 0, 0, 0.4) 0px 0px 1px 0px, rgba(0, 0, 0, 0.04) 0px 2px 4px 0px` | `--shadow-subtle-5` |
| subtle-6 | `rgba(255, 255, 255, 0.6) 0px 0px 0px 1px inset` | `--shadow-subtle-6` |
| subtle-7 | `rgb(235, 232, 228) 0px 0px 0px 0.5px inset` | `--shadow-subtle-7` |

### Layout

- **Page max-width:** 1280px
- **Section gap:** 96-125px
- **Card padding:** 32px
- **Element gap:** 8-16px

## Components

### Filled Pill Button
**Role:** Primary action

Black (#000000) fill, white text, 9999px radius, 16px horizontal padding, Inter 14px/500.
1px solid #e5e5e5 border (legacy support).
Used for 'Sign up', 'Create an AI agent', 'Learn more'.
The pill shape is the system's most recognizable component.

### Outline Pill Button
**Role:** Secondary action

White (#fdfcfc) fill, black text, 9999px radius, 14px horizontal padding, Inter 14px/500.
1px solid #e5e5e5 border.
Used for 'Contact sales', 'Log in'.
Lower visual weight than the filled variant - pairs beside it without competing.

### Ghost Link Button
**Role:** Tertiary navigation or in-text action

Transparent fill, black text, 9999px radius, Inter 14px/500.
1px solid #e5e5e5 border.
Used for nav items and inline actions.
No visible fill until hover.

### Feature Card (Taupe)
**Role:** Feature showcase panel

#f5f3f1 warm taupe fill, 20px radius, 32px horizontal padding, no shadow, no border.
The dominant card pattern (22 occurrences).
Flat, quiet, sits on the canvas without elevation.

### White Card with Whisper Shadow
**Role:** Elevated content card

White (#fdfcfc) fill, 20px radius, 16px all-side padding, three-layer whisper shadow (1px hard edge + 1px blur + 4px blur at 4% opacity).
Used sparingly - only when a card needs to sit above other content with subtle separation.

### Large Feature Card
**Role:** Hero feature block

#f5f3f1 fill, 24px radius (slightly larger than standard 20px), generous internal padding.
Used for flagship feature showcases that need more visual breathing room.

### Tab Pill
**Role:** Product switcher in feature panels

White fill, black text, 9999px radius, 1px border.
Active state marked by a small colored dot (orange for ElevenCreative, teal for ElevenAgents, gray for ElevenAPI).
Tabs sit inline above the card content.

### Hairline Divider
**Role:** Section separation

1px solid #ebe8e4 stone-colored line.
Preferred over whitespace when sections need explicit separation.
Used 54 times across the page - the most common border pattern.

### Audio Sphere Visual
**Role:** Product showcase graphic

Large circular gradient sphere (roughly 200px diameter) with soft radial gradients blending violet #0447ff, orange #ff4704, pink, and warm tones.
Centered play-button overlay.
No hard edges - these are the system's signature visual and appear 3x in a carousel row.

### Logo Wordmark
**Role:** Brand identity

Black text reading 'ElevenLabs' in Inter bold/semibold.
Consistent across header and footer.
No icon mark - the wordmark alone carries the brand.

### Top Nav Bar
**Role:** Primary navigation

Transparent on eggshell canvas, 50px height.
Logo left, nav links center-left (Inter 14px), auth buttons right (outline 'Log in' + filled 'Sign up').
No background fill - the nav is invisible until scroll.

### Trust Logo Grid
**Role:** Social proof section

6-column grid of partner logos (Twilio, Disney, KPN, NVIDIA, Meta, etc.) rendered in grayscale at low contrast.
Logos sit on the eggshell canvas with generous padding - not boxed in cards.
'Read all stories' outline button top-right.

## Do's and Don'ts

### Do
- Use Waldenburg at weight 300 for all display headlines 32px+; never apply bold or semibold weights to it - the whisper-weight is the brand's signature restraint.
- Set all buttons, tags, and tab pills to 9999px radius; the pill shape is non-negotiable and defines the system's most recognizable component.
- Use #000000 filled buttons paired with #fdfcfc outline buttons as the only button hierarchy - do not introduce colored CTA fills.
- Reserve #0447ff violet and #ff4704 orange exclusively for product visuals (audio spheres, product icons, illustration accents); never apply them to UI text, borders, or interactive elements.
- Use 1px solid #ebe8e4 hairline borders for section separation; prefer borders over drop shadows for the flat editorial feel.
- Apply -0.02em letter-spacing on all Waldenburg headlines at 32px+ and +0.01em tracking on Inter body at 14-16px - the opposite tracking directions create a deliberate contrast between display and body.
- Stack surfaces as eggshell → taupe → stone; never use pure white or pure gray - warmth is the system's defining tonal quality.

### Don't
- Do not bold or semibold Waldenburg - the weight-300 whisper is the brand's most distinctive choice and bolding destroys it.
- Do not use violet #0447ff or orange #ff4704 for buttons, links, badges, or any interactive UI element; these colors are decoration-only.
- Do not add heavy drop shadows; the system uses near-invisible 1px shadows only - no blurred elevation effects.
- Do not introduce new accent colors beyond the two product-visual sparks; the palette is intentionally 97% achromatic.
- Do not use sharp corners (<8px) on cards or feature panels; the 20-24px radii are a signature.
- Do not use pure white #ffffff for backgrounds; always use #fdfcfc eggshell to maintain the warm paper-like canvas.
- Do not use display-weight fonts (anything heavier than Waldenburg 300) for body copy; Inter 400/500 owns everything below 24px.

## Surfaces

| Level | Name | Value | Purpose |
|-------|------|-------|---------|
| 1 | Eggshell Canvas | `#fdfcfc` | Base page background - warm off-white that reads as paper, not screen |
| 2 | Warm Taupe | `#f5f3f1` | Section bands and card surfaces that need to sit one step above the canvas without a border |
| 3 | Stone Plate | `#ebe8e4` | Icon plates, subtle elevated backgrounds - slightly deeper than taupe for small isolated elements |

## Elevation

- **Buttons and elevated cards:** `rgba(0, 0, 0, 0.4) 0px 0px 1px 0px, rgba(0, 0, 0, 0.04) 0px 1px 1px 0px, rgba(0, 0, 0, 0.04) 0px 2px 4px 0px`
- **Inset borders / focus halos:** `rgba(0, 0, 0, 0.075) 0px 0px 0px 0.5px inset`

## Imagery

Product visuals dominate the imagery language: large soft-edged audio sphere gradients (200px+ circles with radial violet-to-orange-to-pink blends) serve as the hero graphic.
Logos in the trust section appear in low-contrast grayscale against the eggshell canvas.
Photography is minimal - no lifestyle or product photography detected.
Iconography is sparse and monochrome (black outlined or filled icons, no chromatic icons).
The visual system feels more like a design publication than a product catalog - editorial restraint over marketing spectacle.

## Layout

Full-width sections flow vertically in a single max-width 1280px centered column with 64px outer gutters.
Hero is asymmetric: left-aligned headline at 48px Waldenburg, right-aligned body description, with two pill buttons stacked below the headline.
Below the hero, a large feature panel with tab navigation spans the full content width.
Sections alternate between eggshell canvas and taupe band backgrounds with 96-125px vertical gaps.
Footer is a compact single band.
Navigation is a minimal top bar - no sticky behavior, no mega-menu.
Content rhythm is editorial: generous whitespace, one major visual per section, no card grids below the trust section.

## Agent Prompt Guide

**Quick Color Reference**
- text: #000000 (primary), #777169 (body), #a59f97 (caption)
- background: #fdfcfc (canvas), #f5f3f1 (card surface)
- border: #ebe8e4 (hairline), #e5e5e5 (button border)
- accent: #0447ff (violet spark - product visuals only)
- accent: #ff4704 (ember orange - product visuals only)
- primary action: #000000 (filled action)

**3-5 Example Component Prompts**

1. Create a hero headline: 'Bringing technology to life' at 48px Waldenburg weight 300, color #000000, letter-spacing -0.96px, line-height 1.08.
   Left-aligned on #fdfcfc canvas.
2. Create a primary button: 'Sign up' - 9999px radius, #000000 fill, white text, Inter 14px/500, 16px horizontal padding, 1px solid #e5e5e5 border.
3. Create a secondary button: 'Contact sales' - 9999px radius, #fdfcfc fill, #000000 text, Inter 14px/500, 14px horizontal padding, 1px solid #e5e5e5 border.
4. Create a feature card: #f5f3f1 fill, 20px radius, 32px horizontal padding, no shadow.
   Title at 36px Waldenburg 300, description at 16px Inter 400 in #777169.
5. Create an audio sphere visual: 200px circle with radial-gradient blending #0447ff, #ff4704, and pink, no hard edge.
   Center play icon in white circle 48px diameter.

## Similar Brands

- **Linear** - Same whisper-weight display headlines paired with monochrome UI and pill-shaped buttons; both achieve authority through typographic restraint rather than color.
- **Vercel** - Same near-white warm canvas with stark black text and pill buttons; both use minimal color and let typography carry the brand.
- **Stripe** - Same editorial restraint with hairline borders, generous whitespace, and accent colors reserved for illustrations rather than UI chrome.
- **Notion** - Same warm off-white palette with taupe secondary surfaces and pill-shaped interactive elements; both feel like paper rather than glass.
- **Framer** - Same Bauhaus-influenced minimalism with whisper-weight headlines and a 97% achromatic palette that lets single accent colors feel significant.

## Quick Start

### CSS Custom Properties

```css
:root {
  /* Colors */
  --color-eggshell: #fdfcfc;
  --color-warm-taupe: #f5f3f1;
  --color-stone: #ebe8e4;
  --color-ink: #000000;
  --color-graphite: #44403b;
  --color-smoke: #777169;
  --color-ash: #a59f97;
  --color-violet-spark: #0447ff;
  --color-ember-orange: #ff4704;

  /* Typography - Font Families */
  --font-waldenburg: 'Waldenburg', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-inter: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-geist-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  /* Typography - Scale */
  --text-caption: 10px;
  --leading-caption: 1.6;
  --text-body-sm: 14px;
  --leading-body-sm: 1.5;
  --tracking-body-sm: 0.14px;
  --text-body: 16px;
  --leading-body: 1.5;
  --tracking-body: 0.16px;
  --text-subheading: 18px;
  --leading-subheading: 1.6;
  --text-body-lg: 20px;
  --leading-body-lg: 1.35;
  --text-heading-sm: 32px;
  --leading-heading-sm: 1.13;
  --tracking-heading-sm: -0.64px;
  --text-heading: 36px;
  --leading-heading: 1.17;
  --tracking-heading: -0.72px;
  --text-display: 48px;
  --leading-display: 1.08;
  --tracking-display: -0.96px;

  /* Typography - Weights */
  --font-weight-light: 300;
  --font-weight-regular: 400;
  --font-weight-medium: 500;

  /* Spacing */
  --spacing-unit: 4px;
  --spacing-4: 4px;
  --spacing-8: 8px;
  --spacing-12: 12px;
  --spacing-16: 16px;
  --spacing-20: 20px;
  --spacing-24: 24px;
  --spacing-28: 28px;
  --spacing-32: 32px;
  --spacing-36: 36px;
  --spacing-40: 40px;
  --spacing-48: 48px;
  --spacing-56: 56px;
  --spacing-64: 64px;
  --spacing-72: 72px;
  --spacing-96: 96px;
  --spacing-160: 160px;

  /* Layout */
  --page-max-width: 1280px;
  --section-gap: 96-125px;
  --card-padding: 32px;
  --element-gap: 8-16px;

  /* Border Radius */
  --radius-md: 4px;
  --radius-lg: 10px;
  --radius-2xl: 16px;
  --radius-2xl-2: 20px;
  --radius-3xl: 24px;
  --radius-3xl-2: 28px;
  --radius-full: 9999px;

  /* Named Radii */
  --radius-tags: 9999px;
  --radius-cards: 20px;
  --radius-inputs: 4px;
  --radius-buttons: 9999px;
  --radius-large-cards: 24px;
  --radius-small-elements: 4-10px;

  /* Shadows */
  --shadow-subtle: rgba(0, 0, 0, 0.4) 0px 0px 1px 0px, rgba(0, 0, 0, 0.04) 0px 1px 1px 0px, rgba(0, 0, 0, 0.04) 0px 2px 4px 0px;
  --shadow-subtle-2: rgba(0, 0, 0, 0.075) 0px 0px 0px 0.5px inset;
  --shadow-subtle-3: rgba(0, 0, 0, 0.1) 0px 0px 0px 0.5px inset;
  --shadow-subtle-4: rgba(0, 0, 0, 0.1) 0px 0px 0px 1px inset;
  --shadow-subtle-5: rgba(0, 0, 0, 0.4) 0px 0px 1px 0px, rgba(0, 0, 0, 0.04) 0px 2px 4px 0px;
  --shadow-subtle-6: rgba(255, 255, 255, 0.6) 0px 0px 0px 1px inset;
  --shadow-subtle-7: rgb(235, 232, 228) 0px 0px 0px 0.5px inset;

  /* Surfaces */
  --surface-eggshell-canvas: #fdfcfc;
  --surface-warm-taupe: #f5f3f1;
  --surface-stone-plate: #ebe8e4;
}
```
