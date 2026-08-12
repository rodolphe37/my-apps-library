# Icons

Place the app icon here in each OS's required format before packaging:

- `app.icns` — macOS (use `iconutil` or `png2icns` to generate from a 1024×1024 PNG)
- `app.ico` — Windows (multi-resolution .ico, e.g. via ImageMagick or Pillow)
- `app.png` — Linux (512×512 or 256×256 PNG, referenced by `packaging/linux/myapps.desktop`)

These are referenced by `packaging/pyinstaller/myapps.spec` and the Linux `.desktop` file. No icon is checked in yet — the MVP build currently falls back to PyInstaller's default icon until real artwork is added.
