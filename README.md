# pyside-desktop-apps

An agent skill (`building-pyside-desktop-apps`) for cross-platform desktop tools in Python and PySide6: a
working app template, the rules behind its look, and scripts that scaffold a tested project and ship it as
Windows, Linux and macOS downloads on every tagged release.

## What it gives you

- **A template app** that already passes review: design tokens for light and dark, one stylesheet, sharp
  Lucide icons at any display scale, cards with depth in both themes, 50 ms see-through tooltips and menus, a
  target picker, a segmented mode switch, and jobs off the UI thread with instant pending rows.
- **UI tests that pin past defects** (contrast, blurry icons, toolbar jumps, focus rings, double
  backgrounds), running offscreen on every system.
- **Review tooling**: `--screenshots` writes light and dark shots side by side; `--self-check` proves a
  bundle starts without a display.
- **Releases**: a PyInstaller spec and build script, CI that builds and self-checks four bundles on every push
  and attaches them with `SHA256SUMS` to the GitHub release of a `vX.Y.Z` tag.

## Requirements

- Python 3.12 or newer, Git
- PySide6 (installed into each new project; `pip install PySide6-Essentials` to run the template's tests)
- Linux: Qt's system libraries (Debian and Ubuntu: `libxcb-cursor0`)

## Install

Link (or clone) the repository into your agent's skills folder:

```powershell
git clone git@github.com:ai94iq/pyside-desktop-apps $HOME\pyside-desktop-apps
New-Item -ItemType Junction -Path $HOME\.claude\skills\building-pyside-desktop-apps -Target $HOME\pyside-desktop-apps
```

```bash
git clone git@github.com:ai94iq/pyside-desktop-apps ~/pyside-desktop-apps
ln -s ~/pyside-desktop-apps ~/.claude/skills/building-pyside-desktop-apps
```

## Use

Ask your agent for a desktop tool, or scaffold directly:

```bash
python scripts/new_project.py "My Tool" ../my-tool
cd ../my-tool
python -m pip install -e .[dev]
python -m my_tool
python ../pyside-desktop-apps/scripts/add_icons.py folder-open list    # more Lucide icons by name
```

## Layout

| Path | Contents |
|---|---|
| `SKILL.md` | Agent rules, locked stack, new-project steps, review checklist, reference map |
| `references/` | Theming, icons, widgets and polish, responsiveness, testing, packaging and releases |
| `assets/template/` | The app template with `__app__`, `__App__` and `__App Name__` placeholders |
| `scripts/` | `new_project.py`, `add_icons.py`, `check_skill.py` (standard library only) |

## Evaluations

Three scenarios to try on the models that will run the skill:

1. "Make me a desktop tool that lists the files in a folder and lets me rename them in bulk." Expect: the
   scaffold script, a `window.py` rewritten around the task, work on the worker with pending rows, tests
   passing, screenshots in both themes.
2. On an existing PySide6 app: "the icons look blurry and dark mode looks flat." Expect: `SvgIconEngine` and
   the `edge` / shadow tokens brought in, the matching tests added, screenshots checked at 125% scaling.
3. "Ship this as an exe, a dmg and a tarball whenever I tag." Expect: `packaging/` and the CI workflow from
   the template, `--self-check` wired in, the tag-equals-version check, no secrets needed.

## Checks

`python scripts/check_skill.py` checks the skill's own files (size, links, contents lists, plain ASCII, no
leaked names). CI runs it, then scaffolds a project on Linux, Windows and macOS, runs its tests and builds and
self-checks its bundle.
