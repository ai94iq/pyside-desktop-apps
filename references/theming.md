# Theming: tokens, stylesheet, light and dark

Code: `src/<package>/theme.py` in a scaffolded project (from `assets/template/src/__app__/theme.py`).

## Contents

- [Tokens](#tokens)
- [One stylesheet](#one-stylesheet)
- [Light and dark depth](#light-and-dark-depth)
- [Text hierarchy and contrast](#text-hierarchy-and-contrast)
- [The theme button](#the-theme-button)
- [Retheming live](#retheming-live)
- [Qt quirks met so far](#qt-quirks-met-so-far)

## Tokens

`THEMES` holds one dict per theme with the same keys. Every color in the app comes from a token: the
stylesheet, `QPalette`, custom `paintEvent` code and icon colors. A literal color anywhere else is a bug.

| Token | Use |
|---|---|
| `ground` | window background behind the cards |
| `panel` | cards, toolbar, menus |
| `raised` | inputs, pills, segmented switch track, tooltips |
| `hover`, `line` | hover fill; borders, dividers, scrollbar handle |
| `ink`, `ink2`, `ink3` | primary text; secondary text and hints; placeholders and empty-state icons |
| `accent`, `accent_soft`, `accent_text`, `accent_ink` | brand fill; selection and checked fill; text on `accent_soft`; text on `accent` |
| `ok`, `warn`, `bad` (+ `_soft`) | status text and its tinted background |
| `shadow_alpha`, `shadow_blur`, `shadow_y`, `edge`, `card_line` | card depth (see below) |

Adding a token: add it to both themes in the same commit; `test_both_themes_have_the_same_tokens` fails
otherwise. Changing a color: run the contrast test before looking at screenshots.

## One stylesheet

`QSS` is one template formatted with the tokens (`{ink}`, `{panel}`...; literal braces doubled). Widgets get an
`objectName` (`card`, `pill`, `seg`, `title`, `hint`, `chip`, `primary`) and the stylesheet styles names, not
classes, so one rule never leaks into a widget it was not written for. Fusion is the base style on every
platform: the app looks the same on Windows, Linux and macOS and the stylesheet behaves the same everywhere.
Native per-platform styles ignore parts of a stylesheet; do not mix them in.

Rules worth keeping when you edit it:

- One border radius per level: cards 14, bars 12, buttons and inputs 8, list items 6.
- Toolbar buttons: transparent until hover; checked = `accent_soft` fill with `accent` text; the segmented
  switch's checked button = solid `accent` with `accent_ink`.
- Scrollbars: 8 px, transparent track, rounded `line` handle that darkens on hover, no arrow buttons.
- Menus and tooltips: `panel` / `raised` surface, 1 px `line` border, rounded. They only look rounded with the
  see-through popup filter in [widgets-and-polish.md](widgets-and-polish.md#popups-menus-and-tooltips).

## Light and dark depth

Cards must read as separate surfaces in both themes. Low contrast between ground and panel and a faint shadow
were the first two review complaints.

- Light: `ground` clearly darker than `panel` (#e9ecf1 vs #ffffff) and a visible shadow (alpha 70, blur 28,
  6 px down).
- Dark: shadows do not show on a near-black ground, so `shadow_alpha` is 0 and the card gets a 1 px
  `card_line` border with a lighter `edge` on top. Never both a shadow and an edge in one theme.
- `shade()` applies the theme's shadow to a card; call it for every card on a theme change.

## Text hierarchy and contrast

Titles and hints must differ in more than color: titles 17 px bold `ink`, pane captions and hints 12 px
`ink2`, empty-state titles 14 px semibold. One title style for every pane (two panes with different title
styles was a review finding).

`theme.contrast(fg, bg)` returns the WCAG ratio. `test_text_has_enough_contrast_in_both_themes` pins:
`ink` on `panel` >= 7, `ink2` on `panel` and `ground` >= 4.5, chip text >= 4.5, `accent_ink` on `accent`
>= 4.5, status text on its soft background >= 4.5, `ink3` >= 3 (icons and placeholders only). Add a line there
for every new text-on-surface pair. Hint text must never be drawn semi-transparent: a translucent `ink2`
fails contrast, and in right-to-left layouts it was reported as "half transparent" text.

Disabled controls use `ink3`, never a darker fill: a disabled search box that turned near-black was reported
as broken, not disabled.

## The theme button

An icon-only toolbar button cycles System, Light, Dark (icons `monitor`, `sun`, `moon`) with the tooltip
"Theme: <mode> (click to change)". No "Theme" text and no dropdown: a labelled dropdown was reviewed as
clutter. The choice is saved in `QSettings` under `theme`; an unknown stored value falls back to System
(`test_invalid_stored_theme_falls_back_to_system`). `--theme dark` on the command line applies without saving.

System mode reads `app.styleHints().colorScheme()` (Qt 6.5+).

## Retheming live

`MainWindow.set_theme()` reapplies everything that baked a color in:

1. `apply_theme(app, mode)` - palette and stylesheet.
2. Every action icon registered through `_iconed()` (icons are drawn in a color, so they are rebuilt).
3. `shade()` on every card and floating bar.
4. Widgets with painted parts (`EmptyState.retheme`, the pill's dot and chevron).

A new widget that paints with a token needs a `retheme(theme)` method and a call in `set_theme()`.

## Qt quirks met so far

| Symptom | Cause | Fix in the template |
|---|---|---|
| Toolbar opens 49 px high, grows to 73 on the first theme switch | Qt applies the toolbar's QSS padding to a shown toolbar only on a later stylesheet change | `showEvent` sets a one-space stylesheet on the toolbar once (`test_toolbar_keeps_its_height_across_themes`) |
| Text clips when a button becomes checked | a font weight that changes with `:checked` is not in the size hint | keep one weight in every state of a widget |
| Tree arrows ignore the theme | QSS `image:` takes files, not icons | `icons.chevrons()` writes PNG + @2x per color to a temp folder |
