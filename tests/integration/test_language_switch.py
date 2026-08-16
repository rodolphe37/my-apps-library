from pathlib import Path

from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.i18n import LanguageManager
from myapps.plugins.manager import PluginManager
from myapps.ui.dialogs.settings_dialog import SettingsDialog
from myapps.ui.main_window import MainWindow

REPO_ROOT = Path(__file__).resolve().parents[2]
GERMAN_PLUGIN_EXAMPLE = REPO_ROOT / "examples" / "plugins" / "german_translation"


def make_window(tmp_path, qtbot, qapp, with_plugins=False):
    pm = ProjectManager(path=tmp_path / "library.json")
    sm = SettingsManager(path=tmp_path / "settings.json")
    er = EditorRegistry(path=tmp_path / "editors.json")
    pgm = PluginManager(pm, plugins_dir=tmp_path / "plugins") if with_plugins else None
    lang = LanguageManager()
    if pgm is not None:
        lang.set_plugin_translations(pgm.collect_translations())
    lang.set_mode("en")  # force a non-"system" locale to avoid CI machine-locale flakiness

    window = MainWindow(pm, sm, er, None, pgm, lang)
    qtbot.addWidget(window)
    return window, pgm, lang


def test_menu_text_updates_live_on_language_switch(tmp_path, qtbot, qapp):
    window, _pgm, lang = make_window(tmp_path, qtbot, qapp)

    file_action = window.menuBar().actions()[0]
    assert file_action.menu().actions()[0].text() == "Add Project…"

    lang.set_mode("fr")

    file_action = window.menuBar().actions()[0]  # re-fetch: menu bar was rebuilt
    assert file_action.menu().actions()[0].text() == "Ajouter un projet…"


def test_search_placeholder_updates_live(tmp_path, qtbot, qapp):
    window, _pgm, lang = make_window(tmp_path, qtbot, qapp)
    assert window._search_bar.placeholderText() == "Search projects…"

    lang.set_mode("fr")
    assert window._search_bar.placeholderText() == "Rechercher des projets…"


def test_sidebar_all_item_updates_live(tmp_path, qtbot, qapp):
    window, _pgm, lang = make_window(tmp_path, qtbot, qapp)
    assert window._sidebar.item(0).text() == "All"
    assert window._sidebar_library_label.text() == "Library"

    lang.set_mode("fr")
    assert window._sidebar.item(0).text() == "Tous"
    assert window._sidebar_library_label.text() == "Bibliothèque"


def test_plugin_locale_appears_in_settings_dropdown_when_enabled(tmp_path, qtbot, qapp):
    _window, pgm, lang = make_window(tmp_path, qtbot, qapp, with_plugins=True)
    pgm.install_from_path(GERMAN_PLUGIN_EXAMPLE)
    pgm.enable("german-translation")
    lang.set_plugin_translations(pgm.collect_translations())

    dialog = SettingsDialog(
        SettingsManager(path=tmp_path / "settings.json"),
        EditorRegistry(path=tmp_path / "editors.json"),
        None,
        language_manager=lang,
    )
    qtbot.addWidget(dialog)
    labels = [dialog._language_combo.itemText(i) for i in range(dialog._language_combo.count())]
    assert "Deutsch" in labels


def test_plugin_locale_disappears_from_settings_dropdown_when_disabled(tmp_path, qtbot, qapp):
    _window, pgm, lang = make_window(tmp_path, qtbot, qapp, with_plugins=True)
    pgm.install_from_path(GERMAN_PLUGIN_EXAMPLE)
    pgm.enable("german-translation")
    lang.set_plugin_translations(pgm.collect_translations())

    pgm.disable("german-translation")
    lang.set_plugin_translations(pgm.collect_translations())

    dialog = SettingsDialog(
        SettingsManager(path=tmp_path / "settings.json"),
        EditorRegistry(path=tmp_path / "editors.json"),
        None,
        language_manager=lang,
    )
    qtbot.addWidget(dialog)
    labels = [dialog._language_combo.itemText(i) for i in range(dialog._language_combo.count())]
    assert "Deutsch" not in labels
