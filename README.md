# MyAppsLibrary

A personal desktop launcher/library for your developer projects — add them once, organize by category, and open any of them in your preferred code editor with one click, no matter where they live on disk.

## Features

- Add/remove projects (folder references only — your files are never touched), including drag-and-drop of one or more folders
- Fully custom categories — no built-in/generic ones. Create as many as you want (**Project → Manage Categories…**), assign a project to several at once via right-click → **Edit Categories…**, or drag a project onto a category in the sidebar to move it there directly
- Search and filter by category
- List and grid/thumbnail views, toggled from the View menu, with selection preserved across the switch
- Auto-detects installed code editors (VS Code, Cursor, Sublime Text, JetBrains IDEs, Zed, VSCodium, and more) and opens a project directly in one
- "Open With…" to pick a different editor, or add a custom one
- Right-click → "Show in Finder/Explorer" to reveal a project's folder
- Light/dark theme with automatic OS detection, plus a manual switch — the whole UI (selection highlights, sidebar, buttons) is themed around the app's blue-to-purple logo gradient (see `src/myapps/ui/theme/brand.py`)
- Native menu bar with all major actions
- A VS Code-style **plugin system**: install from a local `.zip` or folder, enable/disable from **Plugins → Manage Plugins…**, with plugins able to contribute context-menu actions, menu actions, and even new view modes. See [`examples/plugins/`](examples/plugins/) for working examples and [`src/myapps/plugins/api.py`](src/myapps/plugins/api.py) for the API surface.
- **Multi-language** (English/French built in), switchable live from **Preferences → Language** with no restart — and extensible by third-party **translation plugins** that add a whole new language (see [`examples/plugins/german_translation/`](examples/plugins/german_translation/)) or patch/override individual strings in an existing one.

Planned next: a plugin marketplace client (browse/install remotely, once the marketplace service exists), code signing/notarization, auto-update.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m myapps
```

Run tests:

```bash
pytest
```

Lint:

```bash
ruff check src tests examples
```

## Project layout

See `src/myapps/` — `core/` (data layer), `editors/` (detection & launch), `plugins/` (plugin system: manifest, loader, manager, API), `i18n/` (translation catalog, `tr()`, built-in `en`/`fr` locales), `ui/` (PySide6 widgets, theming, views), `utils/`. Packaging configs live in `packaging/`. Example plugins live in `examples/plugins/`.

## License

MIT
