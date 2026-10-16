# Testing a Qt app

Code: `tests/test_ui.py` in a scaffolded project.

## Contents

- [Offscreen tests](#offscreen-tests)
- [Invariants worth a test](#invariants-worth-a-test)
- [Fakes, not threads](#fakes-not-threads)
- [Launch checks](#launch-checks)
- [Visual review](#visual-review)

## Offscreen tests

`QT_QPA_PLATFORM=offscreen` (set at the top of the test module and in CI) runs Qt with no display on every
system. One `QApplication` per process (`QApplication.instance() or QApplication([])` in `setUpClass`).
`QSettings` points at a temp `.ini` per test, so tests never read or write the user's settings. Tests are
`unittest` classes, so `python -m unittest` and `pytest` both run them.

Offscreen Qt has no fonts: text renders as boxes. Assert on widget state, not on pixels of text; take
screenshots on the real platform (below).

macOS temp paths: `tempfile` gives `/var/...` while some tools answer `/private/var/...`; compare with
`os.path.realpath` on both sides.

## Invariants worth a test

Each test in the template pins a defect that was reported once. Keep them and add one per new finding:

| Test | Guards against |
|---|---|
| `test_checked_icon_is_drawn_in_its_own_color` | checked toolbar icons invisible on the accent |
| `test_stroke_lands_on_whole_device_pixels` | blurry icons at 125% and 150% |
| `test_text_has_enough_contrast_in_both_themes` | hints unreadable in dark mode |
| `test_dark_cards_use_an_edge_not_a_shadow` | flat cards in dark mode |
| `test_toolbar_keeps_its_height_across_themes` | toolbar jumping on the first theme switch |
| `test_menus_and_tooltips_are_see_through_and_quick` | double backgrounds, tooltip lag |
| `test_buttons_take_focus_by_keyboard_only` | focus ring on mouse clicks |
| `test_labels_never_render_rich_text` | outside text rendered as HTML |
| `test_a_job_shows_at_once_as_pending_then_fills_in` | delay before an action shows |
| `test_a_job_that_ends_at_once_still_fills_its_row` | results lost when a job is instant |
| `test_theme_button_cycles_and_persists`, `test_invalid_stored_theme_falls_back_to_system` | theme lost or crashing on a bad setting |

## Fakes, not threads

`FakeWorker` has the real worker's signals and `submit` / `reserve` but runs nothing, so a test decides when a
job finishes or fails. Use the real `Worker` on a real thread in only the tests about threading, and wait with
`QTest.qWait` in a bounded loop (100 x 20 ms), never a bare sleep.

Inject everything slow or external through the window's constructor (`worker=`, `settings=`, `targets=`,
`task=`) so tests build the window without a network, device or file.

## Launch checks

"Tests pass but the app does not open" happened twice: once from code no test imported, once from a bundle
that failed only on Linux. Two guards:

- `python -m <package> --self-check REPORT` builds the window offscreen in both themes and exits non-zero with
  the error in the report. `SelfCheckTest` runs it; `packaging/build_bundle.py` runs it against the built
  bundle on every CI system.
- Before telling the user a build works, start it for real once on each system you can reach and look at it.

## Visual review

`python -m <package> --screenshots DIR` shows the window, grabs it in light and dark and writes `review.html`
with both side by side. Use it:

1. After a batch of UI changes, not after each one; one review per batch, in both themes.
2. With the `impeccable` skill or the user, reading the page against [widgets-and-polish.md](widgets-and-polish.md).
3. Before saying a visual fix is done: open the PNG and look at the exact spot that was reported.

Screenshots of a real app can contain real data; check them before sharing and stop taking them if they do.
