# Packaging and releases

Code: `packaging/` and `.github/workflows/ci.yml` in a scaffolded project.

## Contents

- [What ships](#what-ships)
- [Building a bundle](#building-a-bundle)
- [CI and tag releases](#ci-and-tag-releases)
- [Cutting a release](#cutting-a-release)
- [Licenses](#licenses)
- [Native libraries built from source](#native-libraries-built-from-source)
- [Reproducing CI locally](#reproducing-ci-locally)
- [Signing and installers](#signing-and-installers)

## What ships

| System | File | Built on |
|---|---|---|
| Windows x64 | `<App>-<version>-windows-x64.exe` (one file) | `windows-latest` |
| Linux x64 | `<App>-<version>-linux-x64.tar.gz` (a folder) | `ubuntu-latest` |
| macOS Apple silicon | `<App>-<version>-macos-arm64.dmg` | `macos-latest` |
| macOS Intel | `<App>-<version>-macos-x64.dmg` | `macos-26-intel` |

Plus `SHA256SUMS`. Users still need any external programs the app calls; the release notes say which and
where the app looks for them (PATH, then the installers' usual folders).

## Building a bundle

Run exactly, from the project root: `python packaging/build_bundle.py bundles`. It installs the pinned build
tools (`TOOLS`) and the project, runs PyInstaller with `packaging/app.spec`, runs the built bundle's
`--self-check` headless (fails the build if it does not report both themes), then packs for this system.

`app.spec` notes:

- `console=False`; Windows gets one `.exe` (`EXE` with binaries), Linux and macOS a folder (`COLLECT`), macOS a
  `BUNDLE` with `NSHighResolutionCapable` (without it the app is blurry on Retina) and a bundle id with no
  underscores.
- The icon is drawn by `app_icon()` and saved as PNG; PyInstaller converts it (needs Pillow).
- `EXCLUDES` drops Qt modules the app does not import (WebEngine, QML, Multimedia, PDF, Charts...); remove a
  line when the app starts using one. Add `hiddenimports` for modules imported by name at runtime.
- `upx=False`: compressed executables trip antivirus scanners more often.
- Linux builds on a host without a desktop (CI, WSL) warn "Library not found: libxcb-..." for Qt's X11
  plugin, about 20 lines. Expected: those libraries come from the user's desktop (the release notes name
  `libxcb-cursor0`, the one many systems lack). Any other "Library not found" is a real gap.

Bump `TOOLS` to the latest PyInstaller and Pillow on purpose, in its own commit, with a CI run behind it.

## CI and tag releases

The template's workflow:

- `test`: offscreen tests on Linux, Windows and macOS on every push and pull request. All three, every time:
  a workflow that ran only the Windows and macOS jobs on push was a review finding.
- `bundles`: builds and self-checks all four bundles on every run, uploads them as artifacts. A bundle that
  breaks is found on the commit that broke it, not on release day.
- `release`: only on a `vX.Y.Z` tag; checks the tag equals `__version__`, downloads the artifacts, writes
  `SHA256SUMS`, attaches everything to the GitHub release with `packaging/release-notes.md` as its text.
- `concurrency` cancels superseded runs; `permissions: contents: read` everywhere except the release job.

Action versions are pinned to exact tags; update them to the latest releases (`gh api
repos/<owner>/<action>/releases/latest`) when touching the workflow.

## Cutting a release

1. Set `__version__` in `src/<package>/__init__.py`; update the CHANGELOG if the project keeps one.
2. Commit, push, wait for CI to pass on that commit.
3. `git tag -a vX.Y.Z -m "<App> X.Y.Z"` on that commit and `git push origin vX.Y.Z`.
4. Check the release page lists the four files and `SHA256SUMS`.

A tag that does not match `__version__` fails the release job; delete and re-create the tag on the right
commit rather than editing the version after tagging.

## Licenses

PySide6 is LGPL-3.0, so the bundle carries its license texts and the release notes name it. `app.spec` collects every
`LICENSE`/`COPYING` file of the packages listed in `LICENSED`, plus `packaging/licenses/` (LGPL-3.0 and the
GPL-3.0 it refers to), into the bundle's `licenses/` folder. Add each new runtime dependency to `LICENSED`.

## Native libraries built from source

Only when a dependency must be rebuilt (for example a media library limited to LGPL parts):

- Build it in CI with a cached prefix keyed on the build script's hash.
- On Windows, pass paths to setuptools build options with forward slashes (backslashes are dropped), build
  with the runner's Python (not MSYS2's), and repair wheels with `delvewheel` (macOS: `delocate`) so they carry
  the libraries.
- Make `--self-check` report what the bundle actually loaded (library license, decoded sample) and fail on
  anything unexpected.

## Reproducing CI locally

Do not iterate on CI by pushing. Linux: run the job's commands in WSL or a Docker container of the runner's
Ubuntu version. Windows: run the same commands in a clean virtual environment. Keep each workflow step a
single script call (`build_bundle.py`), so local and CI runs are the same command.

## Signing and installers

Bundles start unsigned; the release notes tell Windows users how to get past SmartScreen and macOS users how to
open an unidentified app. Signing (Authenticode, Apple notarization) and a per-user installer (Start menu and
desktop shortcuts, uninstall entry) are later steps; when the user asks for one, look up the current tools and
their requirements online before choosing, and add it as its own job after `bundles`.
