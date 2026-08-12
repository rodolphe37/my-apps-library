# Icons

The app icon, generated from the source artwork and checked in here:

- `app.icns` — macOS bundle icon (built via `iconutil` from a 1024×1024-based iconset)
- `app.ico` — Windows, multi-resolution (16–256px)
- `app.png` — master 1024×1024 PNG (source for everything else, and used by the Linux `.desktop` file)
- `app-32.png` … `app-256.png` — pre-resized PNGs for contexts that want a specific size without scaling a huge source image (e.g. Linux icon themes)

These are referenced by `packaging/pyinstaller/myapps.spec` (per-OS `icon_file`) and `packaging/linux/myapps.desktop` (`Icon=app`). A copy of `app.png` (plus 128/256px variants) also lives in `src/myapps/ui/resources/icons/` — that's the one the *running app* loads at startup for the window/taskbar icon and the About dialog; this folder is purely for OS-level packaging.

To regenerate from new source artwork (a single high-res PNG with transparency, any aspect ratio — it gets padded to a square canvas): see the image-processing snippet in the project's build notes, or re-run the same steps by hand with Pillow (`Image.open(...).convert("RGBA")`, pad to square, resize per target, `iconutil -c icns` for `.icns`, `Image.save(..., sizes=[...])` for `.ico`).
