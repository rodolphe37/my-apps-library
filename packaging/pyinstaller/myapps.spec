# PyInstaller spec for MyAppsLibrary.
#
# Build (run from the repo root, with the dev venv active):
#   pyinstaller packaging/pyinstaller/myapps.spec --noconfirm
#
# Produces a native bundle for whichever OS you run it on - PyInstaller does
# not cross-compile, so macOS/Windows/Linux builds must each run on that OS
# (e.g. via a CI matrix).

import re
import sys
from pathlib import Path

block_cipher = None

# Spec files are exec'd by PyInstaller in a namespace that does NOT define
# `__file__` (this changed at some point - recent PyInstaller versions raise
# NameError if you rely on it). SPECPATH is the supported, documented way to
# get the spec file's own directory from inside a spec file.
SPEC_DIR = Path(SPECPATH).resolve()  # noqa: F821 -- SPECPATH is injected by PyInstaller
REPO_ROOT = SPEC_DIR.parents[1]  # SPEC_DIR is packaging/pyinstaller/, so up two levels
SRC = REPO_ROOT / "src"
ICONS = REPO_ROOT / "packaging" / "icons"

# The whole standard library, not just what MyAppsLibrary's own imports
# pull in - plugins are loaded at runtime from an external folder, so
# PyInstaller never sees what *they* import. See stdlib_modules.py (and
# check_stdlib_bundle.py, the CI check that it actually worked).
sys.path.insert(0, str(SPEC_DIR))
from stdlib_modules import stdlib_hiddenimports  # noqa: E402

# Single source of truth for the version shown in Finder's Get Info /
# About - read from the app's own constants.py instead of hardcoding it here.
APP_VERSION = re.search(
    r'^VERSION = "([^"]+)"', (SRC / "myapps" / "constants.py").read_text(encoding="utf-8"), re.M
).group(1)

# Non-Python files aren't picked up by PyInstaller's import analysis, so
# each needs an explicit --add-data entry to end up in the frozen bundle,
# at the same relative path core/catalog.py etc. look for it at (Path(
# __file__).parent / ...) - every such lookup in src/myapps must have a
# matching entry here, or it silently finds nothing at runtime (this is
# exactly what happened to i18n/locales/: missing here meant tr() always
# fell back to returning the raw key, e.g. "search.placeholder" showing
# up verbatim in the UI instead of actual translated text).
datas = [
    (str(SRC / "myapps" / "ui" / "theme" / "styles"), "myapps/ui/theme/styles"),
    (str(SRC / "myapps" / "ui" / "resources"), "myapps/ui/resources"),
    (str(SRC / "myapps" / "i18n" / "locales"), "myapps/i18n/locales"),
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
    hiddenimports=stdlib_hiddenimports(),
    hookspath=[str(SPEC_DIR / "hooks")],
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
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
            "NSHighResolutionCapable": True,
        },
    )
