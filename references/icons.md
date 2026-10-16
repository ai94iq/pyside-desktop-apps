# Icons: sharp outline icons at any scale

Code: `src/<package>/icons.py` and `lucide.py`. Add icons with `python <skill>/scripts/add_icons.py NAME...`.

## Contents

- [Source and license](#source-and-license)
- [Why an icon engine](#why-an-icon-engine)
- [Names and colors](#names-and-colors)
- [Placement](#placement)
- [Small painted marks](#small-painted-marks)
- [The app icon](#the-app-icon)

## Source and license

Lucide outline icons (ISC, part MIT from Feather), vendored as SVG bodies in `lucide.py` with the full license
header and `LUCIDE_VERSION`. Only the icons the app uses are vendored. `add_icons.py` fetches by name from the
newest `lucide-static` on jsDelivr and refetches the rest when the release moved, so one file never mixes
versions. Never hand-write SVG paths, never use an icon font (they render unevenly across platforms), never
PNG icons (blurry at 125% and 150% scaling), never mix icon sets.

## Why an icon engine

"Icons are pixelated" and "icons still blurry" came up in two review rounds. Causes and fixes:

- A pixmap made at 16 px and scaled to a 1.25 or 1.5 device pixel ratio is blurry. `SvgIconEngine.paint` reads
  the painter's real size and `devicePixelRatioF()` and renders the SVG at exactly that size.
- Lucide strokes are 2 units on a 24-unit grid: 1.67 physical px at 20 px, smeared over two pixels.
  `svg_bytes()` rounds the stroke to whole device pixels (`test_stroke_lands_on_whole_device_pixels`).
- Disabled state draws at 40% opacity; checked state draws in `on_color` (`test_checked_icon_is_drawn_in_its_own_color`).

## Names and colors

`ICON_NAMES` maps what the app calls an icon (`run`, `clear`, `target`) to the Lucide name. Call sites use the
app's names; swapping a glyph is one line.

`icon(name, color, on_color=None)` takes token values, never literals. Register action icons through
`MainWindow._iconed(action, name, key="ink", on="accent")` so a theme change redraws them. A checkable action
inside the segmented switch uses `on="accent_ink"` (white on the accent fill); elsewhere `on="accent"`.
Action icons in lists or rows can take `accent` so they read as actions, not decoration (a review asked
for this).

## Placement

- `ICON_SIZE` is 16 x 16, square. The gap between icon and text comes from the button's stylesheet padding,
  never from spaces in the text: icons and text looked misaligned until this was the only gap.
- Text beside icon for actions people learn (Run, Clear, Edit, Inspect); icon only for well-known toggles
  (theme) and dense rows. Every icon-only button has an accessible name and a tooltip
  (`test_icon_only_buttons_have_a_name_and_a_tip`).
- Leave room: a copy icon that clipped at a table edge and a pin icon too close to its text were both
  findings. Give icon buttons fixed square sizes with padding, and 6 px or more to neighbouring text.

## Small painted marks

`dot_pixmap(color, size, hollow, ratio)` draws status dots at the device pixel ratio with `DOT_MARGIN` of
clear space, because a dot drawn edge to edge had its antialiased rim cut off ("the green icon clips into
itself"). Use it for any small circle; do not draw circles with stylesheet `border-radius` on a label.

## The app icon

`app_icon(glyph)` draws a white glyph on a rounded `BRAND` square for 16 to 256 px, each size drawn, not
scaled. The window uses it and `packaging/app.spec` saves its 256 px pixmap for PyInstaller, which makes the
`.ico` and `.icns` (needs Pillow). Keep `BRAND` equal to the light `accent`.
