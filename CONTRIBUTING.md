# Contributing to MyAppsLibrary

*[Français ci-dessous ⬇️](#contribuer-à-myapplibrary)*

Thanks for considering a contribution — MyAppsLibrary started as a personal
tool and is now open for anyone to help shape. This guide covers everything
you need to get productive.

## Table of contents

- [Code of Conduct](#code-of-conduct)
- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Project structure](#project-structure)
- [Coding style](#coding-style)
- [Testing](#testing)
- [Commit messages](#commit-messages)
- [Pull request process](#pull-request-process)
- [Writing a plugin or translation](#writing-a-plugin-or-translation)
- [Reporting bugs](#reporting-bugs)
- [Suggesting features](#suggesting-features)
- [License of contributions](#license-of-contributions)

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you're expected to uphold it.

## Ways to contribute

You don't need to write Python to help:

- 🐛 **Report bugs** — see [Reporting bugs](#reporting-bugs)
- ✨ **Suggest features** — see [Suggesting features](#suggesting-features)
- 🌍 **Add or improve a translation** — see [Writing a plugin or translation](#writing-a-plugin-or-translation)
- 🧩 **Write a plugin** — either a real one to share, or an example that helps document the API
- 🖥️ **Add editor support** — extend [`src/myapps/editors/catalog.py`](src/myapps/editors/catalog.py)
- 📖 **Improve the docs** — README typos, unclear setup steps, missing examples all count
- 🧪 **Improve test coverage**, especially around platform-specific code (`editors/detectors/`)

## Development setup

Requirements: **Python 3.11+**, Git, and a desktop environment able to run Qt apps.

```bash
git clone https://github.com/rodolphe37/my-apps-library.git
cd my-apps-library

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
python -m myapps
```

This installs the app in editable mode plus the dev toolchain: `pytest`, `pytest-qt`, `ruff`, `pyinstaller`, and `Pillow`.

## Project structure

```
src/myapps/
├── core/       # Data layer — models, ProjectManager, SettingsManager, JSON store
├── editors/     # Editor detection (macOS/Windows/Linux) & launch
├── plugins/      # Plugin system — manifest, loader, manager, public API
├── i18n/         # Translation catalog, tr(), built-in en/fr locales
├── ui/           # PySide6 widgets, dialogs, views, theming
└── utils/        # Filesystem & process helpers, logging

packaging/     # PyInstaller spec, OS-specific metadata, icons
examples/plugins/  # Working example plugins
tests/unit/         # Fast, no-GUI unit tests
tests/integration/  # pytest-qt integration tests
```

See the [Architecture diagram in the README](README.md#architecture) for how these pieces fit together.

## Coding style

- Linted with [`ruff`](https://github.com/astral-sh/ruff) (`E`, `F`, `I`, `UP`, `B` rule sets), 100-character lines, target `py311`.
- Run `ruff check src tests examples` before opening a PR (and `ruff check --fix` for auto-fixable issues).
- Prefer explicit, readable code over clever one-liners; match the naming and structure already used in the module you're editing.
- Type hints are expected on new code; the codebase uses `from __future__ import annotations` throughout.
- UI code should go through the existing theming (`ui/theme/brand.py`, `palettes.py`) rather than hardcoding colors.
- Core logic changes (models, store schema) should stay backward-compatible with existing on-disk data, or include a `SCHEMA_VERSION` bump and migration — see [`src/myapps/constants.py`](src/myapps/constants.py).

## Testing

```bash
pytest
```

- `tests/unit/` — fast, no GUI required.
- `tests/integration/` — uses `pytest-qt`; runs headless via the Qt `offscreen` platform plugin in CI.
- New features should come with tests. Bug fixes should ideally include a regression test.
- GUI tests run headless locally too — set `QT_QPA_PLATFORM=offscreen` if you don't want windows popping up while testing.

## Commit messages

Write clear, imperative-mood commit messages (`Fix drag-and-drop in grid view`, not `Fixed` or `Fixing`). A short body explaining *why*, not just *what*, is appreciated for anything non-trivial. This project doesn't enforce a strict conventional-commits format, but grouping related changes into focused commits makes review much easier.

## Pull request process

1. **Fork** the repo and create a branch from `main` (`git checkout -b feature/my-change`).
2. Make your changes, following the [coding style](#coding-style) above.
3. Add or update tests as needed, and make sure `pytest` and `ruff check src tests examples` both pass locally.
4. Update relevant docs (`README.md` **and** `README.fr.md` if user-facing behavior changed, `CHANGELOG.md` under `[Unreleased]`).
5. Open a PR against `main` with a clear description of the change and, for UI changes, a screenshot or short clip if possible.
6. A maintainer will review; expect feedback and please be responsive to review comments. CI must be green before merge.

Small, focused PRs are much easier to review than large ones — if you're planning something big, consider opening an issue first to discuss the approach.

## Writing a plugin or translation

- **Plugin API**: the full contract lives in [`src/myapps/plugins/api.py`](src/myapps/plugins/api.py) (`PluginBase`, `PluginContext`). Start from [`examples/plugins/`](examples/plugins/) for working templates.
- **New translation**: add `src/myapps/i18n/locales/<code>.json` mirroring `en.json`'s keys (including `meta.language_name`), or ship it as a plugin via `contribute_translations()` — see [`examples/plugins/german_translation`](examples/plugins/german_translation).
- Full details in the [README's Plugin system](README.md#the-plugin-system) and [Internationalization](README.md#internationalization) sections.

## Reporting bugs

Please use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include your OS, Python version, MyAppsLibrary version, and steps to reproduce. For security vulnerabilities, **do not** open a public issue — see [`SECURITY.md`](SECURITY.md).

## Suggesting features

Please use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md). Check the [Roadmap](README.md#roadmap) first — your idea might already be planned, in which case a 👍 on the related issue is still very useful signal.

## License of contributions

MyAppsLibrary is distributed under the [PolyForm Noncommercial License 1.0.0](LICENSE) — noncommercial use only, see [`README.md#license`](README.md#license). By submitting a pull request, you agree that your contribution is licensed to the project under those same terms, and that you have the right to make that grant.

---

# Contribuer à MyAppsLibrary

*[English above ⬆️](#contributing-to-myapplibrary)*

Merci d'envisager de contribuer — MyAppsLibrary a démarré comme un outil personnel et est maintenant ouvert à toute personne qui souhaite aider à le façonner. Ce guide couvre tout ce dont vous avez besoin pour être productif rapidement.

## Sommaire

- [Code de conduite](#code-de-conduite)
- [Façons de contribuer](#façons-de-contribuer)
- [Mise en place de l'environnement](#mise-en-place-de-lenvironnement)
- [Structure du projet](#structure-du-projet)
- [Style de code](#style-de-code)
- [Tests](#tests)
- [Messages de commit](#messages-de-commit)
- [Processus de pull request](#processus-de-pull-request)
- [Écrire un plugin ou une traduction](#écrire-un-plugin-ou-une-traduction)
- [Signaler un bug](#signaler-un-bug)
- [Suggérer une fonctionnalité](#suggérer-une-fonctionnalité)
- [Licence des contributions](#licence-des-contributions)

## Code de conduite

Ce projet suit un [Code de conduite](CODE_OF_CONDUCT.md). En participant, vous vous engagez à le respecter.

## Façons de contribuer

Pas besoin d'écrire du Python pour aider :

- 🐛 **Signaler des bugs** — voir [Signaler un bug](#signaler-un-bug)
- ✨ **Suggérer des fonctionnalités** — voir [Suggérer une fonctionnalité](#suggérer-une-fonctionnalité)
- 🌍 **Ajouter ou améliorer une traduction** — voir [Écrire un plugin ou une traduction](#écrire-un-plugin-ou-une-traduction)
- 🧩 **Écrire un plugin** — un vrai à partager, ou un exemple qui aide à documenter l'API
- 🖥️ **Ajouter le support d'un éditeur** — étendre [`src/myapps/editors/catalog.py`](src/myapps/editors/catalog.py)
- 📖 **Améliorer la documentation** — coquilles dans le README, étapes de mise en place peu claires, exemples manquants : tout compte
- 🧪 **Améliorer la couverture de tests**, en particulier sur le code spécifique à chaque plateforme (`editors/detectors/`)

## Mise en place de l'environnement

Prérequis : **Python 3.11+**, Git, et un environnement de bureau capable de faire tourner des applications Qt.

```bash
git clone https://github.com/rodolphe37/my-apps-library.git
cd my-apps-library

python3 -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate

pip install -e ".[dev]"
python -m myapps
```

Cela installe l'application en mode éditable ainsi que les outils de développement : `pytest`, `pytest-qt`, `ruff`, `pyinstaller` et `Pillow`.

## Structure du projet

```
src/myapps/
├── core/       # Couche de données — modèles, ProjectManager, SettingsManager, stockage JSON
├── editors/     # Détection des éditeurs (macOS/Windows/Linux) & lancement
├── plugins/      # Système de plugins — manifest, loader, manager, API publique
├── i18n/         # Catalogue de traduction, tr(), langues en/fr intégrées
├── ui/           # Widgets PySide6, dialogues, vues, thème
└── utils/        # Utilitaires fichiers & process, logging

packaging/     # Spec PyInstaller, métadonnées par OS, icônes
examples/plugins/  # Exemples de plugins fonctionnels
tests/unit/         # Tests unitaires rapides, sans interface graphique
tests/integration/  # Tests d'intégration pytest-qt
```

Voir le [diagramme d'architecture du README](README.fr.md#architecture) pour comprendre comment ces éléments s'articulent.

## Style de code

- Linté avec [`ruff`](https://github.com/astral-sh/ruff) (jeux de règles `E`, `F`, `I`, `UP`, `B`), lignes de 100 caractères, cible `py311`.
- Lancez `ruff check src tests examples` avant d'ouvrir une PR (et `ruff check --fix` pour les corrections automatiques).
- Préférez un code explicite et lisible plutôt que des raccourcis trop malins ; respectez le nommage et la structure déjà utilisés dans le module que vous modifiez.
- Le typage (type hints) est attendu sur le nouveau code ; la base de code utilise `from __future__ import annotations` partout.
- Le code d'interface doit passer par le système de thème existant (`ui/theme/brand.py`, `palettes.py`) plutôt que de coder des couleurs en dur.
- Les changements de logique cœur (modèles, schéma de stockage) doivent rester rétrocompatibles avec les données existantes sur disque, ou inclure une incrémentation de `SCHEMA_VERSION` et une migration — voir [`src/myapps/constants.py`](src/myapps/constants.py).

## Tests

```bash
pytest
```

- `tests/unit/` — rapides, sans interface graphique requise.
- `tests/integration/` — utilise `pytest-qt` ; s'exécute en mode headless via le plugin de plateforme Qt `offscreen` en CI.
- Les nouvelles fonctionnalités doivent être accompagnées de tests. Les corrections de bugs devraient idéalement inclure un test de non-régression.
- Les tests graphiques peuvent aussi tourner en headless en local — utilisez `QT_QPA_PLATFORM=offscreen` si vous ne voulez pas voir de fenêtres s'ouvrir pendant les tests.

## Messages de commit

Écrivez des messages de commit clairs, à l'impératif (`Fix drag-and-drop in grid view`, pas `Fixed` ni `Fixing`). Un court corps expliquant *pourquoi*, pas seulement *quoi*, est apprécié pour tout changement non trivial. Ce projet n'impose pas de format « conventional commits » strict, mais regrouper les changements liés dans des commits ciblés facilite grandement la revue.

## Processus de pull request

1. **Forkez** le dépôt et créez une branche depuis `main` (`git checkout -b feature/ma-fonctionnalite`).
2. Faites vos changements en suivant le [style de code](#style-de-code) ci-dessus.
3. Ajoutez ou mettez à jour les tests si nécessaire, et assurez-vous que `pytest` et `ruff check src tests examples` passent tous les deux en local.
4. Mettez à jour la documentation concernée (`README.md` **et** `README.fr.md` si le comportement visible a changé, `CHANGELOG.md` sous `[Unreleased]`).
5. Ouvrez une PR sur `main` avec une description claire du changement et, pour les changements d'interface, une capture d'écran ou un court clip si possible.
6. Un mainteneur relira la PR ; attendez-vous à des retours et merci d'y répondre. La CI doit être verte avant la fusion.

Des PR petites et ciblées sont bien plus faciles à relire que de grosses PR — si vous prévoyez quelque chose d'important, envisagez d'ouvrir d'abord une issue pour discuter de l'approche.

## Écrire un plugin ou une traduction

- **API de plugin** : le contrat complet vit dans [`src/myapps/plugins/api.py`](src/myapps/plugins/api.py) (`PluginBase`, `PluginContext`). Partez des [`examples/plugins/`](examples/plugins/) pour des modèles fonctionnels.
- **Nouvelle traduction** : ajoutez `src/myapps/i18n/locales/<code>.json` en reprenant les clés de `en.json` (y compris `meta.language_name`), ou distribuez-la comme un plugin via `contribute_translations()` — voir [`examples/plugins/german_translation`](examples/plugins/german_translation).
- Détails complets dans les sections [Système de plugins](README.fr.md#le-système-de-plugins) et [Internationalisation](README.fr.md#internationalisation) du README.

## Signaler un bug

Merci d'utiliser le [modèle de rapport de bug](.github/ISSUE_TEMPLATE/bug_report.md) et d'inclure votre OS, votre version de Python, la version de MyAppsLibrary, et les étapes pour reproduire. Pour une vulnérabilité de sécurité, **n'ouvrez pas** d'issue publique — voir [`SECURITY.md`](SECURITY.md).

## Suggérer une fonctionnalité

Merci d'utiliser le [modèle de suggestion de fonctionnalité](.github/ISSUE_TEMPLATE/feature_request.md). Vérifiez d'abord la [feuille de route](README.fr.md#feuille-de-route) — votre idée y est peut-être déjà prévue, auquel cas un 👍 sur l'issue correspondante reste un signal très utile.

## Licence des contributions

MyAppsLibrary est distribuée sous la [licence PolyForm Noncommercial 1.0.0](LICENSE) — usage non commercial uniquement, voir [`README.fr.md#licence`](README.fr.md#licence). En soumettant une pull request, vous acceptez que votre contribution soit distribuée au projet sous ces mêmes conditions, et vous garantissez disposer des droits nécessaires pour le faire.
