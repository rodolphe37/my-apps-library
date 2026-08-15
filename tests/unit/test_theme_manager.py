"""Tests for ThemeManager's palette selection/fallback and the QSS
`string.Template` substitution - see plugins/api.py's ThemePalette and
ui/theme/tokens.py.
"""

from myapps.plugins.api import ThemePalette
from myapps.ui.theme.theme_manager import DEFAULT_PALETTE_ID, ThemeManager
from myapps.ui.theme.tokens import default_dark_tokens, default_light_tokens


def make_palette(palette_id: str, accent_blue: str = "#00ff00") -> ThemePalette:
    light = default_light_tokens()
    light["accent_blue"] = accent_blue
    return ThemePalette(id=palette_id, label=palette_id, light=light, dark=default_dark_tokens())


def test_default_palette_applies_without_error(qapp):
    tm = ThemeManager(qapp)
    tm.set_mode("light")
    assert tm.palette_id == DEFAULT_PALETTE_ID
    assert tm.resolved_theme == "light"
    assert len(qapp.styleSheet()) > 0


def test_dark_mode_applies_without_error(qapp):
    tm = ThemeManager(qapp)
    tm.set_mode("dark")
    assert tm.resolved_theme == "dark"
    assert len(qapp.styleSheet()) > 0


def test_plugin_palette_is_applied_to_stylesheet(qapp):
    tm = ThemeManager(qapp)
    tm.set_available_palettes([make_palette("ocean", accent_blue="#123456")])
    tm.set_palette("ocean")
    tm.set_mode("light")
    assert tm.palette_id == "ocean"
    assert "#123456" in qapp.styleSheet()


def test_unavailable_palette_falls_back_to_default(qapp):
    tm = ThemeManager(qapp)
    tm.set_palette("does-not-exist")
    assert tm.palette_id == DEFAULT_PALETTE_ID


def test_palette_becomes_unavailable_after_plugin_disabled(qapp):
    """Simulates a plugin being disabled/uninstalled after its palette was
    selected - set_available_palettes([]) then re-applying must not raise
    and must fall back cleanly."""
    tm = ThemeManager(qapp)
    tm.set_available_palettes([make_palette("ocean")])
    tm.set_palette("ocean")
    assert tm.palette_id == "ocean"

    tm.set_available_palettes([])
    tm.set_palette("ocean")  # re-select what the user had chosen
    assert tm.palette_id == DEFAULT_PALETTE_ID
    assert len(qapp.styleSheet()) > 0  # still renders something sane


def test_available_palette_choices_includes_default_first(qapp):
    tm = ThemeManager(qapp)
    tm.set_available_palettes([make_palette("ocean")])
    choices = tm.available_palette_choices()
    assert choices[0][0] == DEFAULT_PALETTE_ID
    assert ("ocean", "ocean") in choices


def test_stylesheet_has_no_leftover_unfilled_placeholders(qapp):
    """Regression test for a real bug hit during development: an explanatory
    comment inside light.qss/dark.qss itself containing the literal text
    "$token" collided with string.Template's substitution syntax."""
    tm = ThemeManager(qapp)
    for mode in ("light", "dark"):
        tm.set_mode(mode)
        assert "$" not in qapp.styleSheet(), f"unfilled template placeholder in {mode} stylesheet"
