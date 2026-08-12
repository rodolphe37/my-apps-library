from myapps.i18n.translator import Translator


def test_tr_returns_translated_string():
    t = Translator()
    t.set_locale("en")
    assert t.tr("menu.file.add_project") == "Add Project…"


def test_tr_switches_locale():
    t = Translator()
    t.set_locale("fr")
    assert t.tr("menu.file.add_project") == "Ajouter un projet…"


def test_tr_missing_key_returns_key_itself():
    t = Translator()
    t.set_locale("en")
    assert t.tr("does.not.exist") == "does.not.exist"


def test_tr_interpolates_placeholders():
    t = Translator()
    t.set_locale("en")
    assert t.tr("status.moved_to", name="X", category="Y") == "Moved 'X' to Y"


def test_tr_tolerates_missing_placeholder_kwarg():
    t = Translator()
    t.set_locale("en")
    # "status.moved_to" needs {name} and {category}; only giving one should
    # not raise, and should fall back to the raw template.
    result = t.tr("status.moved_to", name="X")
    assert result == "Moved '{name}' to {category}" or "X" in result


def test_display_name_reads_without_mutating_active_locale():
    t = Translator()
    t.set_locale("en")
    assert t.display_name("fr") == "Français"
    assert t.locale == "en"  # unaffected


def test_set_plugin_translations_registers_new_locale():
    t = Translator()
    t.set_plugin_translations(
        {"de": {"meta.language_name": "Deutsch", "menu.file.quit": "Beenden"}}
    )
    assert "de" in t.available_locales()
    t.set_locale("de")
    assert t.tr("menu.file.quit") == "Beenden"
    # Falls back to English for keys the plugin didn't provide.
    assert t.tr("menu.file.add_project") == "Add Project…"


def test_plugin_translation_overrides_builtin_key():
    t = Translator()
    t.set_plugin_translations({"en": {"menu.file.quit": "Exit App"}})
    t.set_locale("en")
    assert t.tr("menu.file.quit") == "Exit App"


def test_available_locales_includes_builtins():
    t = Translator()
    locales = t.available_locales()
    assert "en" in locales
    assert "fr" in locales
