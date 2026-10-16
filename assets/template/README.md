# __App Name__

A desktop app in Python and PySide6 (Qt) for Windows, Linux and macOS.

## Run

Needs Python 3.12 or newer.

```
python -m pip install -e .[dev]
python -m __app__                      # open the window
python -m __app__ --theme dark         # start in a theme without saving it
```

Or download the Windows `.exe`, Linux `.tar.gz` or macOS `.dmg` from the GitHub release.

## Develop

| Task | Command |
|---|---|
| Tests (no window opens) | `QT_QPA_PLATFORM=offscreen python -m pytest -q` |
| Light and dark screenshots for a review | `python -m __app__ --screenshots tmp/screens` (opens `review.html`) |
| Bundle for this system | `python packaging/build_bundle.py bundles` |
| Release | set `__version__` in `src/__app__/__init__.py`, commit, tag `vX.Y.Z`, push the tag |

Shortcuts: `Ctrl+1` Edit, `Ctrl+2` Inspect, `Ctrl+R` Run. The theme button cycles System, Light and Dark and
is remembered between runs. On Linux, Qt needs `libxcb-cursor0` (Debian and Ubuntu).

## Layout

| Path | Contents |
|---|---|
| `src/__app__/theme.py` | Design tokens for light and dark, the stylesheet, `apply_theme` |
| `src/__app__/icons.py`, `lucide.py` | Sharp SVG icons at any scale; the vendored Lucide set |
| `src/__app__/widgets.py` | Cards, pill, segmented switch, empty states, plain labels |
| `src/__app__/worker.py` | Jobs off the UI thread, coalesced refresh, newest-value handoff |
| `src/__app__/window.py` | The main window |
| `packaging/` | PyInstaller spec, bundle build and self-check, release notes, license texts |
