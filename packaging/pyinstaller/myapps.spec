# PyInstaller spec for MyAppsLibrary.
#
# Build (run from the repo root, with the dev venv active):
#   pyinstaller packaging/pyinstaller/myapps.spec --noconfirm
#
# Produces a native bundle for whichever OS you run it on — PyInstaller does
# not cross-compile, so macOS/Windows/Linux builds must each run on that OS
# (e.g. via a CI matrix).

import sys
from pathlib import Path

block_cipher = None

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
ICONS = REPO_ROOT / "packaging" / "icons"

# QSS stylesheets aren't Python source, so they need an explicit --add-data
# entry to end up inside the frozen bundle at src/myapps/ui/theme/styles/.
datas = [
    (str(SRC / "myapps" / "ui" / "theme" / "styles"), "myapps/ui/theme/styles"),
    (str(SRC / "myapps" / "ui" / "resources"), "myapps/ui/resources"),
]

if sys.platform == "darwin":
    icon_file = str(ICONS / "app.icns")
elif sys.platform == "win32":
    icon_file = str(ICONS / "app.ico")
else:
    icon_file = None  # Linux: icon is supplied via the .desktop file instead

a = Analysis(
    [str(SRC / "myapps" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[str(Path(__file__).parent / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MyAppsLibrary",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="MyAppsLibrary",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="MyAppsLibrary.app",
        icon=icon_file,
        bundle_identifier="com.myappslibrary.app",
        info_plist={
            "CFBundleShortVersionString": "0.5.0",
            "NSHighResolutionCapable": True,
        },
    )
