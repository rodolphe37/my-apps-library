# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> This file was reconstructed from the git history when the project moved to
> semantic-versioned releases; entries before that point are grouped by their
> nearest release commit.

## [Unreleased]

## [0.9.0] - 2026-08-16

### Added

- **One-click plugin updates** - the Plugin Manager dialog now checks each
  installed plugin against the marketplace on open, and shows an "Update
  available" badge with an "Update" button right on its card when a newer
  version is published. Clicking it downloads and installs the update in
  place - no more "Plugin is already installed" dead end from trying to
  reinstall over an existing one. A currently-enabled plugin is reloaded
  immediately with the new code, no app restart needed; a disabled one
  just gets its files updated for next time it's enabled.

## [0.8.0] - 2026-08-16

### Added

- **Plugin logos** - `plugin.toml` gains an optional `icon` field (a PNG/SVG/etc.
  path relative to the plugin's own folder). Shown in the Plugin Manager
  dialog and its Details view; a plugin with none gets a generated
  fallback badge in the app's own brand gradient.

### Changed

- **Plugin Manager dialog redesigned** - each installed plugin is now a
  card (logo, name, version, status, description, an animated toggle
  switch instead of a checkbox), with an accent-colored border marking
  the selected plugin. The Details dialog got the same treatment.
- **Folder icon** (list/grid view) - replaced the plain rounded-square
  gradient with an actual folder silhouette (tab + body), same
  blue-to-purple brand gradient.
- Every dialog's OK/Cancel/Close/Yes/No button now shows the app's own
  translation instead of Qt's built-in (always-English) label.
- Consistent margin/spacing polish across several dialogs (Plugin
  Manager, Category Manager, Add Project, Editor Picker, Icon Picker,
  Update Available, Settings).

## [0.7.1] - 2026-08-15

### Fixed

- **Homebrew cask release automation** - the "Update Homebrew cask" release
  job pushed straight to `main` with the default `GITHUB_TOKEN`, which
  branch protection always rejected (`GH013`), even after adding a
  ruleset bypass entry (turned out "GitHub Actions" isn't an available
  bypass actor on a personal, non-organization repo). The job now opens
  a small PR with the version/checksum bump instead, same as every other
  change on this repo - no more manual cask resyncs after each release.

## [0.7.0] - 2026-08-15

### Added

- **Update check** - on startup, MyAppsLibrary now checks GitHub's latest
  release against the running version and, if a newer one exists, shows a
  dialog with the exact upgrade command for the current OS (`brew upgrade`
  or the curl install script on macOS, the curl install script on Linux;
  Windows gets a link to the releases page instead, since winget isn't
  published yet). Fully async and silent on any failure (offline, GitHub
  down) - never blocks startup or shows an error for this. "Skip this
  version" remembers the choice so it won't nag again until an even newer
  release comes out.

## [0.6.1] - 2026-08-15

### Fixed

- **Project menu actions did nothing when clicked with no project
  selected** - Open, Open With..., Reveal, Edit Categories..., and Remove
  now stay disabled until a project is actually selected, instead of
  silently no-oping with zero feedback.

## [0.6.0] - 2026-08-15

### Added

- **Icon picker for categories and folders (projects)** - `Category`/`Project`
  now carry an optional `icon` glyph, chosen from a built-in emoji pack or
  any pack contributed by a plugin (see below). Wired into the category
  manager, each project's right-click menu, and rendered in the sidebar,
  category chips, and the list/grid delegate.
- **Plugin API: `contribute_icon_packs()` and `contribute_theme_palettes()`**
  - a plugin can now offer additional icon packs (`plugins/api.py`'s
  `IconPack`/`IconDef`) and named color palettes (`ThemePalette`, light +
  dark token dicts - see `ui/theme/tokens.py`) selectable from
  Preferences → Theme, alongside the built-in default. A palette with
  incomplete or malformed tokens is rejected at collection time rather
  than reaching the stylesheet engine.
- `ui/theme/palettes.py` and the `.qss` stylesheets are now driven by the
  same token dict (built-in brand colors by default, a plugin palette's
  when one is selected) via `string.Template` substitution - a handful of
  neutral hover/pressed micro-shades stay hardcoded per mode (not brand
  identity, see the comment atop each `.qss` file).

### Fixed

- **A plugin's theme palette never showed up in Preferences until a full
  app restart.** `theme_manager.set_available_palettes()` was only ever
  called once at startup, never refreshed when a plugin got enabled at
  runtime via Plugin Manager. Now refreshed on every plugin
  enable/disable, alongside the other plugin-derived UI.
- **A project's picked icon replaced its folder shape entirely** instead
  of being overlaid on it. `_paint_folder_icon()` now always draws the
  folder gradient first, with the glyph centered on top (smaller than
  before, so it stays within the folder's outline).

## [0.5.2] - 2026-08-13

### Fixed

- The **List/Grid view choice wasn't actually persisted** - it silently
  reset to List on every single app launch, regardless of what was saved.
  `MainWindow` wired each view's signals before the full set of views was
  known, which made a bogus "unknown view mode" fallback fire and
  immediately re-save "list" over a legitimately-saved "grid", before the
  window's own (correct) startup-restore logic even ran. The same flawed
  check existed in the plugin-view-reload path too.

## [0.5.1] - 2026-08-13

### Fixed

- Packaged builds (PyInstaller) were missing `i18n/locales/` from the
  bundle entirely, so every translated string fell back to its raw key
  (e.g. the UI showed literal `search.placeholder` instead of the
  actual translated text). Only affected frozen builds - `python -m
  myapps` from source was never affected. First shipped, broken this
  way, in the `v0.5.0` release; fixed here.
- CI packaging builds now also target Intel Macs (`macos-15-intel`)
  alongside Apple Silicon (`macos-latest`) - a build made only on
  `macos-latest` can't run at all on an Intel Mac ("isn't supported by
  this Mac"), since neither PyInstaller nor PySide6 produce universal2
  binaries.
- The macOS build is now zipped with `ditto` instead of `zip`, which was
  stripping the extended attributes the app's ad-hoc code signature
  relies on (showed up as a barred icon / "app is damaged" in Finder).

### Added

- New `Release` GitHub Actions workflow: builds macOS (Apple Silicon +
  Intel), Windows, and Linux bundles and publishes them as assets on a
  GitHub Release, triggered by pushing a version tag or manually.

### Changed

- Enabled a branch protection ruleset on `main` (`main-protection`): all
  changes now require a pull request, 3 required status checks must pass,
  and force pushes / branch deletion are blocked - for everyone, including
  the repo owner.

## [0.5.0] - 2026-08-13

### Added

- Marketplace link - `Plugins → Browse Marketplace…` opens the companion
  plugins marketplace web app, configurable via `MYAPPS_MARKETPLACE_URL`.

### Changed

- Selected projects are now indicated with a border-only accent outline
  instead of a filled background, keeping each project's own icon/chip
  colors readable.

## [0.4.0] - 2026-08-13

### Added

- **Sort By** menu (**View → Sort By**) - sort projects by name, date added,
  date modified, or size, ascending or descending. Pinned projects always
  stay on top regardless of sort order.

### Fixed

- Drag-and-drop of folders now works identically in both list and grid
  views (previously grid-view-only).

## [0.3.0] - 2026-08-12 / 2026-08-13

### Added

- Multi-select (`Ctrl`/`Cmd`-click, `Shift`-click range-select) with bulk
  actions: edit categories, pin/unpin, and remove for the whole selection
  at once.
- Category drag-and-drop - drag a project onto a category in the sidebar to
  move it there directly.
- Full visual rebrand around the app's blue-to-purple logo gradient
  (see `src/myapps/ui/theme/brand.py`).
- Internationalization (i18n): built-in English and French locales, live
  language switching with no restart, and third-party translation plugins.

### Fixed

- VS Code launch bug.

## [0.2.0] - 2026-08-12

Initial public snapshot. Core feature set:

- Add/remove projects by folder reference, including drag-and-drop import.
- Fully custom categories, assignable per project.
- Search and filter by category.
- List and grid/thumbnail views.
- Auto-detection of installed code editors, with "Open With…" for others.
- "Show in Finder/Explorer" from the right-click menu.
- Light/dark theme with OS auto-detection.
- Native menu bar.
- Initial plugin system (install from local `.zip`/folder, manage, enable/
  disable; contribute context-menu actions, menu actions, and view modes).

<!--
No git tags exist yet (see the Roadmap in README.md - signed releases are
planned). Once tags are cut, replace the plain version headers above with
links, e.g. [0.5.0]: https://github.com/rodolphe37/my-apps-library/releases/tag/v0.5.0
-->

[Unreleased]: https://github.com/rodolphe37/my-apps-library/commits/main
