"""The color tokens a theme (built-in or plugin-contributed) must supply,
one full set per mode (light/dark) — see plugins/api.py's `ThemePalette`.
Both `ui/theme/palettes.py` (QPalette, native widgets) and the `.qss`
stylesheets (templated with `string.Template`, `$token` placeholders) are
driven from the same token dict, so a palette only has to be defined once.

Not every literal color in the `.qss` files is tokenized — hover/pressed
micro-shades that aren't part of the brand identity stay hardcoded per mode
(see the comment atop each `.qss` file). Only the tokens below are ever
overridable by a plugin.
"""

from __future__ import annotations

from myapps.ui.theme import brand

TOKEN_KEYS = (
    "bg",
    "surface",
    "surface_alt",
    "border",
    "text",
    "subtext",
    "accent_blue",
    "accent_purple",
    "accent_blend",
    "accent_blend_hover",
    "pin_color",
)


def default_light_tokens() -> dict[str, str]:
    return {
        "bg": brand.LIGHT_BG,
        "surface": brand.LIGHT_SURFACE,
        "surface_alt": brand.LIGHT_SURFACE_ALT,
        "border": brand.LIGHT_BORDER,
        "text": brand.LIGHT_TEXT,
        "subtext": brand.LIGHT_SUBTEXT,
        "accent_blue": brand.ACCENT_BLUE,
        "accent_purple": brand.ACCENT_PURPLE,
        "accent_blend": brand.ACCENT_BLEND,
        "accent_blend_hover": brand.ACCENT_BLEND_HOVER,
        "pin_color": brand.PIN_COLOR,
    }


def default_dark_tokens() -> dict[str, str]:
    return {
        "bg": brand.DARK_BG,
        "surface": brand.DARK_SURFACE,
        "surface_alt": brand.DARK_SURFACE_ALT,
        "border": brand.DARK_BORDER,
        "text": brand.DARK_TEXT,
        "subtext": brand.DARK_SUBTEXT,
        "accent_blue": brand.ACCENT_BLUE,
        "accent_purple": brand.ACCENT_PURPLE,
        "accent_blend": brand.ACCENT_BLEND,
        "accent_blend_hover": brand.ACCENT_BLEND_HOVER,
        "pin_color": brand.PIN_COLOR,
    }


def validate_tokens(tokens: dict[str, str]) -> list[str]:
    """Returns the list of missing/invalid token keys, empty if `tokens` is
    a complete, well-formed set. Used to reject a malformed plugin-
    contributed palette (falls back to default) without ever crashing the
    host on a bad `contribute_theme_palettes()` return value."""
    problems = []
    for key in TOKEN_KEYS:
        value = tokens.get(key)
        if not isinstance(value, str) or not value.startswith("#"):
            problems.append(key)
    return problems
