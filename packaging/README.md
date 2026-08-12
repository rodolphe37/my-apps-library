# Packaging

Native builds only — PyInstaller does not cross-compile, so each OS's build must run on that OS (a GitHub Actions matrix with `macos-latest` / `windows-latest` / `ubuntu-latest` is the recommended way to produce all three from one push).

Common first step on every OS:

```bash
source .venv/bin/activate   # or the venv used for development
pip install -e ".[dev]"
pyinstaller packaging/pyinstaller/myapps.spec --noconfirm
```

This produces `dist/MyAppsLibrary/` (onedir build), and on macOS also `dist/MyAppsLibrary.app`.

## macOS → `.dmg`

```bash
pip install dmgbuild
dmgbuild -s packaging/macos/dmg_settings.py "MyAppsLibrary" dist/MyAppsLibrary.dmg
```

(`dmg_settings.py` is not yet checked in — add one when preparing a real release; until then, distribute `dist/MyAppsLibrary.app` directly.)

Unsigned MVP builds trigger Gatekeeper's "unidentified developer" warning; the workaround is right-click → Open on first launch. Proper Developer ID signing + `notarytool` submission is a Phase 3 item.

## Windows → installer

Wrap `dist/MyAppsLibrary/` with [Inno Setup](https://jrsoftware.org/isinfo.php) (a `.iss` script is not yet checked in — add one alongside a real release, pointing `Source:` at `dist\MyAppsLibrary\*`).

## Linux → AppImage

```bash
# using linuxdeploy + the Qt plugin, downloaded from https://github.com/linuxdeploy
./linuxdeploy-x86_64.AppImage --appdir AppDir \
  --executable dist/MyAppsLibrary/MyAppsLibrary \
  --desktop-file packaging/linux/myapps.desktop \
  --icon-file packaging/icons/app.png \
  --plugin qt \
  --output appimage
```

A `.desktop` file (`packaging/linux/myapps.desktop`) is also suitable for manual/distro-native installs without an AppImage.

See [`packaging/icons/README.md`](icons/README.md) — real icon artwork needs to be added before any of the above produces a properly-branded build.
