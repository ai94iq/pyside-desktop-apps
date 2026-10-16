# PyInstaller spec for the desktop bundles:
#     pyinstaller --noconfirm packaging/app.spec        (build_bundle.py runs it for you)
# Windows: one __App__.exe. Linux: a __App__ folder (tarred by build_bundle.py).
# macOS: __App__.app (put in a .dmg). Licenses of everything shipped go in licenses/.
import importlib.metadata
import os
import sys

ROOT = os.path.dirname(SPECPATH)
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import __app__  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from __app__.icons import app_icon  # noqa: E402

NAME = "__App__"
qt = QGuiApplication.instance() or QGuiApplication([])
ICON = os.path.join(workpath, "app.png")      # PyInstaller makes the .ico or .icns from it (needs Pillow)
os.makedirs(workpath, exist_ok=True)
app_icon().pixmap(256, 256).save(ICON)

# Every license of what ships: the packages' own files, plus Qt's LGPL (PySide6 wheels carry no text).
LICENSED = ("PySide6_Essentials", "shiboken6")
licenses = [(os.path.join(ROOT, "LICENSE"), "licenses/__app__"),
            (os.path.join(SPECPATH, "licenses", "LGPL-3.0.txt"), "licenses/Qt-PySide6"),
            (os.path.join(SPECPATH, "licenses", "GPL-3.0.txt"), "licenses/Qt-PySide6")]
for dist in LICENSED:
    for file in importlib.metadata.distribution(dist).files or []:
        if any(k in file.name.upper() for k in ("LICENSE", "COPYING")) and file.suffix not in (".py", ".pyc"):
            licenses.append((str(file.locate()), f"licenses/{dist}"))

# Qt modules the app never loads; each one left out saves megabytes. Remove a line when the app starts using it.
EXCLUDES = ["tkinter", "PIL", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
            "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.Qt3DCore", "PySide6.QtMultimedia",
            "PySide6.QtMultimediaWidgets", "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtCharts",
            "PySide6.QtDesigner"]

a = Analysis([os.path.join(SPECPATH, "entry.py")], pathex=[os.path.join(ROOT, "src")], datas=licenses,
             excludes=EXCLUDES)
pyz = PYZ(a.pure)
if sys.platform == "win32":
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, name=NAME, console=False, icon=ICON, upx=False)
else:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=NAME, console=False, icon=ICON, upx=False)
    coll = COLLECT(exe, a.binaries, a.datas, name=NAME, upx=False)
    if sys.platform == "darwin":
        app = BUNDLE(coll, name=f"{NAME}.app", icon=ICON, bundle_identifier="io.github." + "__app__".replace("_", "-"),   # no underscores allowed
                     version=__app__.__version__, info_plist={"NSHighResolutionCapable": True})
