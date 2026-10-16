---
name: building-pyside-desktop-apps
description: Builds and polishes cross-platform desktop apps in Python with PySide6 (Qt) from a tested template - design tokens for light and dark, one stylesheet, Fusion everywhere, sharp Lucide outline icons at any display scale, cards with real depth, quick see-through tooltips and menus, a target picker pill, jobs off the UI thread with instant pending rows, offscreen UI tests, light and dark screenshots for review, and PyInstaller bundles (Windows .exe, Linux .tar.gz, macOS .dmg) attached to GitHub releases on tags. Use when creating, scaffolding, styling, reviewing, testing, packaging or releasing a PySide6 or PyQt desktop tool or GUI, or when the user mentions Qt, QSS, stylesheet, dark mode, theme, icons blurry or pixelated, shadows, tooltips lag, dropdown with two backgrounds, focus outline, PyInstaller, exe, dmg, tarball or a GitHub release of a desktop app.
---

# PySide6 desktop apps

A recipe for desktop tools that look modern and the same on Windows, Linux and macOS, start from a working
template, and ship as downloads on every tagged release. Every rule here answers a defect that a reviewer
reported on a real app; the references say which.

## Agent rules

1. **Start from the template, never from memory.** New project: run `scripts/new_project.py`. Existing
   project: copy the matching file or function from `assets/template/` and adapt it.
2. **Measure, never assume.** Latency, sizes, contrast and "is it faster" come from a timestamp, a test or a
   screenshot taken now. When app behavior or the user's intent is unclear, ask with what was measured.
3. **Batch UI fixes, then one visual review.** Fix a batch of findings, run the tests, then
   `--screenshots` and look at both themes at the exact spots reported. Do not claim a visual fix from code.
4. **Every reported defect gets a test** in `tests/test_ui.py` when it can be stated as widget state
   (a color pair, a height, a flag, an order).
5. **Tokens only.** No literal colors outside `THEMES`; no new icon set; no per-platform native style.
6. **Ask before installing** anything (pip packages, PyInstaller, system libraries).

## Locked stack

| Concern | Use | Not allowed |
|---|---|---|
| Language | Python 3.12+ | - |
| UI | PySide6 (`PySide6-Essentials`, latest), widgets | PyQt (license), QML for tool UIs, Tkinter |
| Style | Fusion + one QSS from design tokens (`theme.py`) | qt-material, qdarkstyle, native styles per OS |
| Icons | Lucide outline SVG, vendored, drawn by `SvgIconEngine` | icon fonts, PNG icons, mixed icon sets |
| Settings | `QSettings` | hand-written config files for UI state |
| Background work | `Worker` on a `QThread` (`worker.py`) | blocking calls in slots, `QApplication.processEvents` loops |
| Tests | `unittest` classes run by pytest, `QT_QPA_PLATFORM=offscreen` | pixel tests on text, UI automation tools |
| Bundles | PyInstaller (pinned in `build_bundle.py`) | cx_Freeze, Nuitka, briefcase |
| CI and releases | GitHub Actions, release on `vX.Y.Z` tags | manual uploads |

## New project

1. `python <skill>/scripts/new_project.py "App Name" DEST` (run exactly; `--package` to override the Python
   name). It copies the template, fills placeholders, runs `git init -b main` and the tests.
2. `python -m pip install -e .[dev]` in DEST (ask first), then `python -m <package>` to see it.
3. Replace the sample: keep `theme.py`, `icons.py`, `widgets.py`, `worker.py` as they are; rewrite
   `window.py` panes and `sample_task` for the real work; rename `ICON_NAMES` entries.
4. Add icons: `python <skill>/scripts/add_icons.py NAME...` from DEST (names from lucide.dev).
5. After each batch of UI work: tests, then `python -m <package> --screenshots tmp/screens`, then review.
6. First release: push, let CI go green, set `__version__`, tag `vX.Y.Z`
   ([packaging-and-release.md](references/packaging-and-release.md#cutting-a-release)).

## Bringing an existing app up to the bar

Work through the review checklist below; for each failing line copy the template piece named in the
reference, add its test, then review screenshots in both themes.

## Review checklist

Each line is a defect reported on a real app. Check all of them before calling UI work done.

1. Cards flat or blending into the ground; shadow faint in light, missing depth in dark (edge instead).
2. Shadows clipped at card edges; card rounded at the top but square at the bottom.
3. Blurry or pixelated icons at 125% or 150% scaling; icons misaligned with their text.
4. Controls touching: buttons, pill and switch, scrollbar and row icons, icon and text.
5. Menus, dropdowns or tooltips with a square background behind the rounded one.
6. Tooltips slower than 50 ms, or missing on a control whose effect is not obvious.
7. Focus ring after a mouse click.
8. Titles and hints too alike; hints unreadable in dark mode; any text under 4.5:1.
9. Disabled controls drawn darker instead of dimmed; translucent hint text.
10. Text clipping when a state changes its weight; labels repeating the obvious.
11. A second background behind combo boxes or chips; two different title styles for panes.
12. Pending work invisible: no row shown until the slow call ends.
13. Switching a target rebuilds the window or loses data.
14. Toolbar height jumping on the first theme change.
15. Outside text rendered as rich text.
16. macOS: icon or app name in the title bar instead of the menu bar.
17. Success and failure messages with no color.
18. A build that passes tests but does not start: `--self-check` and one real launch per system.

## References

| When | Read |
|---|---|
| Colors, stylesheet, light and dark, contrast, theme button | [references/theming.md](references/theming.md) |
| Icons blurry, adding icons, app icon, status dots | [references/icons.md](references/icons.md) |
| Layout, cards, toolbar, pill, popups, focus, lists, labels, empty states, platform chrome | [references/widgets-and-polish.md](references/widgets-and-polish.md) |
| Slow actions, pending rows, refresh, streams, timing, calling programs | [references/responsiveness.md](references/responsiveness.md) |
| Tests, fakes, self-check, screenshots for review | [references/testing.md](references/testing.md) |
| PyInstaller, CI, tag releases, licenses, signing, installers | [references/packaging-and-release.md](references/packaging-and-release.md) |

## Scripts

| Script | Run or read |
|---|---|
| `scripts/new_project.py "App Name" DEST [--package name] [--no-test]` | run exactly |
| `scripts/add_icons.py NAME... [--file path/to/lucide.py]` | run exactly, from the project root |
| `scripts/check_skill.py` | run exactly, after editing this skill |
