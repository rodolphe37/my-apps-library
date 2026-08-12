from myapps.i18n.catalog import TranslationCatalog, discover_builtin_locales, load_builtin_locale


def test_discover_builtin_locales_finds_en_and_fr():
    locales = discover_builtin_locales()
    assert "en" in locales
    assert "fr" in locales


def test_load_builtin_locale_missing_returns_empty_dict():
    assert load_builtin_locale("xx") == {}


def test_load_builtin_locale_en_has_expected_keys():
    en = load_builtin_locale("en")
    assert en["menu.file.add_project"] == "Add Project…"
    assert en["meta.language_name"] == "English"


def test_load_corrupt_locale_file_returns_empty_dict(tmp_path, monkeypatch):
    from myapps.i18n import catalog

    monkeypatch.setattr(catalog, "BUILTIN_LOCALES_DIR", tmp_path)
    (tmp_path / "xx.json").write_text("not valid [json", encoding="utf-8")
    assert catalog.load_builtin_locale("xx") == {}


def test_load_non_object_locale_file_returns_empty_dict(tmp_path, monkeypatch):
    from myapps.i18n import catalog

    monkeypatch.setattr(catalog, "BUILTIN_LOCALES_DIR", tmp_path)
    (tmp_path / "xx.json").write_text("[1, 2, 3]", encoding="utf-8")
    assert catalog.load_builtin_locale("xx") == {}


def test_catalog_build_falls_back_to_english_for_missing_key():
    catalog = TranslationCatalog.build("fr")
    # A key present only in English (simulated by asking for something that
    # exists in en.json's real content) should resolve via the fallback layer.
    assert catalog.get("menu.file.add_project") is not None


def test_catalog_get_missing_key_returns_none():
    catalog = TranslationCatalog.build("en")
    assert catalog.get("does.not.exist") is None


def test_catalog_build_with_plugin_overrides_patches_keys():
    catalog = TranslationCatalog.build("en", plugin_overrides={"menu.file.quit": "Exit App"})
    assert catalog.get("menu.file.quit") == "Exit App"
    # Unrelated keys still resolve from the built-in file.
    assert catalog.get("menu.file.add_project") == "Add Project…"


def test_catalog_build_for_new_locale_with_only_plugin_data():
    catalog = TranslationCatalog.build(
        "de", plugin_overrides={"meta.language_name": "Deutsch", "menu.file.quit": "Beenden"}
    )
    assert catalog.get("meta.language_name") == "Deutsch"
    assert catalog.get("menu.file.quit") == "Beenden"
    # Falls back to English for keys the plugin didn't provide.
    assert catalog.get("menu.file.add_project") == "Add Project…"
