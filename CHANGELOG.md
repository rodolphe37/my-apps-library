# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> This file was reconstructed from the git history when the project moved to
> semantic-versioned releases; entries before that point are grouped by their
> nearest release commit.

## [Unreleased]

### Fixed

- The **List/Grid view choice wasn't actually persisted** — it silently
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
  actual translated text). Only affected frozen builds — `python -m
  myapps` from source was never affected. First shipped, broken this
  way, in the `v0.5.0` release; fixed here.
- CI packaging builds now also target Intel Macs (`macos-15-intel`)
  alongside Apple Silicon (`macos-latest`) — a build made only on
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
  and force pushes / branch deletion are blocked — for everyone, including
  the repo owner.

## [0.5.0] - 2026-08-13

### Added

- Marketplace link — `Plugins → Browse Marketplace…` opens the companion
  plugins marketplace web app, configurable via `MYAPPS_MARKETPLACE_URL`.

### Changed

- Selected projects are now indicated with a border-only accent outline
  instead of a filled background, keeping each project's own icon/chip
  colors readable.

## [0.4.0] - 2026-08-13

### Added

- **Sort By** menu (**View → Sort By**) — sort projects by name, date added,
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
- Category drag-and-drop — drag a project onto a category in the sidebar to
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
No git tags exist yet (see the Roadmap in README.md — signed releases are
planned). Once tags are cut, replace the plain version headers above with
links, e.g. [0.5.0]: https://github.com/rodolphe37/my-apps-library/releases/tag/v0.5.0
-->

[Unreleased]: https://github.com/rodolphe37/my-apps-library/commits/main
