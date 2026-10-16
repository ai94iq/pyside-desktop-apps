# Widgets and polish

Code: `src/<package>/widgets.py` and `window.py`. Each rule here answers a defect a reviewer reported.

## Contents

- [Window layout](#window-layout)
- [Cards and floating bars](#cards-and-floating-bars)
- [Toolbar](#toolbar)
- [Target pill and switching in place](#target-pill-and-switching-in-place)
- [Popups: menus and tooltips](#popups-menus-and-tooltips)
- [Focus and keyboard](#focus-and-keyboard)
- [Lists, tables and selection](#lists-tables-and-selection)
- [Text and labels](#text-and-labels)
- [Empty, pending and status states](#empty-pending-and-status-states)
- [Platform conventions](#platform-conventions)

## Window layout

`QMainWindow` with a toolbar (`objectName` `shell`) and a central `ground` widget holding a `QSplitter` of
cards, then a floating action bar and one hint line. Splitter handles are 4 px because the cards' shadow room
already spaces them; `setChildrenCollapsible(False)` so a drag never hides a pane. A column that hugs its
content (a preview, a control bar) gets `setMinimumWidth` from that content's `sizeHint` and stretch 0.

Spacing is the most common finding ("buttons touching each other", "status box too close to the switch",
"scrollbar too close to the delete icon"): 8 px `gap()` between toolbar groups, 4 px between buttons in a
group, 6 px between an icon and its text, 16 px window margins.

## Cards and floating bars

`card(widget, theme)` wraps a pane in a `QFrame#card` with a `QGraphicsDropShadowEffect` and returns a holder
widget. Two defects it prevents:

- "Rounded at the top but not the bottom": square child widgets painted over the rounded corners. The card
  insets its content by 6 px.
- "Shadows clip at the end of each card": a shadow is drawn outside its frame and the parent clips it. The
  holder (`floating()`) has `SHADOW_ROOM` on every side and twice that at the bottom, sized for the deepest
  shadow in `THEMES`.

`floating(frame, theme)` does the same for any frame; the action bar under the cards uses it (`QFrame#bar`).
Keep `holder.frame` so `shade()` can reach the frame on a theme change.

## Toolbar

Left to right: product name (`product`), the target pill, the segmented mode switch, other toggles, an
expanding spacer, the icon-only theme button. `segmented(actions)` builds a pill track from an exclusive
`QActionGroup`; the checked segment is a solid accent fill. Widgets added to a toolbar stretch unless their
size policy is `Maximum`; the pill and the switch set it (a full-width pill was the first screenshot's defect).

Every action has a tooltip that says what it does and what it changes, on two lines: a short title, then one
sentence. Tooltips on controls were asked for after people guessed at them.

## Target pill and switching in place

`Pill` shows what the app works on (a server, a file, a device, an account): glyph, status dot, name, chevron.
With one target it is a plain label (no chevron, arrow cursor); with several it opens a `QMenu` of them, each
with an icon that tells kinds apart. A target that appears later turns it into a dropdown
(`set_targets`; tested). Switching keeps the same window, data and history: rebuilding or restarting on a
switch was reported as broken. If a switch fails, stay on the old target and say why in the hint line.

## Popups: menus and tooltips

"Dropdowns and tooltips have two backgrounds": a menu or tooltip is its own window with a square background,
and the stylesheet draws a rounded surface on top. `SurfaceFilter` (installed by `apply_theme`) makes every
`QMenu` and tooltip frameless and see-through at polish time. Never set a background on a `QComboBox` popup or
a menu by hand; style it in `QSS`.

"Tooltips lag": Qt waits 700 ms. `AppStyle` returns `TIP_DELAY` (50 ms) and `apply_theme` turns off the fade
and slide effects. Both are pinned by `test_menus_and_tooltips_are_see_through_and_quick`.

Prefer an icon-only toggle or a segmented switch to a combo box for two or three choices.

## Focus and keyboard

"Ugly blue outline when clicked": buttons get `Qt.FocusPolicy.TabFocus`, so a mouse click leaves no ring and
Tab still shows one (`border-color: {accent}` on `:focus`). The window sets it for every `QAbstractButton`
after building. Every main action has a shortcut (`Ctrl+1`/`Ctrl+2` modes, `Ctrl+R` run in the template);
list them in the README.

## Lists, tables and selection

- Lists and tables: transparent, no frame, no grid; items 4 px 8 px padding with a 6 px radius; hover `hover`;
  selected `accent_soft` with `ink` text. A selection colored with clipped corners came from padding on
  `::item` without a radius; keep both.
- A table that only displays values gets `NoSelection`.
- Header sections: transparent, `ink2`, 12 px semibold, one `line` underline.
- Tables in dark mode: outlines in `line`, never `ink3`; dark outlines were reported as too heavy.
- A long list shows its count in a `chip` next to the title, not in grey text that gets lost.

## Text and labels

- Text that comes from outside the app (files, servers, users, other programs) goes through
  `plain_label()` or `Qt.TextFormat.PlainText`; a `QLabel` otherwise guesses rich text and renders HTML.
- Labels say what is not obvious: a "Save .xyz" button that repeats a file type the user already knows was reviewed as noise.
- One font weight per widget in every state (see [theming.md](theming.md#qt-quirks-met-so-far)).
- Inputs centred in their row and aligned with their label baseline; a crooked search box was a finding.
- Error notes in the hint line are cut to 160 characters; the full text goes to the log.

## Empty, pending and status states

- `EmptyState(theme, icon, title, text)` for every pane that can be empty: a 32 px `ink3` icon, a title and
  one line on how to fill it.
- Work that takes time shows a pending row at once (dimmed `ink3`) and fills it in when the worker answers.
  "A big delay before a step shows up" was the cause; see [responsiveness.md](responsiveness.md).
- Results of an action get a color: success `ok` on `ok_soft`, failure `bad` on `bad_soft`. A plain grey
  "Exported" message was reported as unclear.

## Platform conventions

The theme is the same everywhere; the window chrome follows the platform:

- macOS: no app icon or app name inside the title bar, the app's name and menu in the system menu bar, and a
  menu bar extra (tray) icon if the app keeps running. A Windows-style icon in a mac title bar was a finding.
- Windows: the icon in the title bar and taskbar comes from `setWindowIcon(app_icon())`.
- Linux: test under both GNOME and KDE when the app uses a tray icon; tray support differs between them.
- Frame pacing: animations and live views run at the display's refresh rate, never a fixed 30 fps timer.
