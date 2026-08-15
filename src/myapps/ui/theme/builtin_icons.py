"""The app's own built-in icon pack, offered in the icon picker alongside
any plugin-contributed ones (see plugins/api.py's IconPack/IconDef).
Emoji glyphs: render identically in light/dark, no image assets to ship.

Labels are plain English (used as hover tooltips only, not translated —
the glyph itself is the actual UI, a tooltip is a minor nicety, not worth
28 extra keys x N locales to localize).
"""

from __future__ import annotations

from myapps.plugins.api import IconDef, IconPack

BUILTIN_ICON_PACK = IconPack(
    id="builtin",
    label="Built-in",
    icons=[
        IconDef(id="folder", glyph="📁", label="Folder"),
        IconDef(id="code", glyph="💻", label="Code"),
        IconDef(id="design", glyph="🎨", label="Design"),
        IconDef(id="tools", glyph="🔧", label="Tools"),
        IconDef(id="rocket", glyph="🚀", label="Rocket"),
        IconDef(id="test", glyph="🧪", label="Test"),
        IconDef(id="package", glyph="📦", label="Package"),
        IconDef(id="game", glyph="🎮", label="Game"),
        IconDef(id="web", glyph="🌐", label="Web"),
        IconDef(id="mobile", glyph="📱", label="Mobile"),
        IconDef(id="settings", glyph="⚙️", label="Settings"),
        IconDef(id="lock", glyph="🔒", label="Lock"),
        IconDef(id="chart", glyph="📊", label="Chart"),
        IconDef(id="book", glyph="📚", label="Book"),
        IconDef(id="pencil", glyph="✏️", label="Pencil"),
        IconDef(id="music", glyph="🎵", label="Music"),
        IconDef(id="movie", glyph="🎬", label="Movie"),
        IconDef(id="camera", glyph="📷", label="Camera"),
        IconDef(id="star", glyph="⭐", label="Star"),
        IconDef(id="fire", glyph="🔥", label="Fire"),
        IconDef(id="bulb", glyph="💡", label="Idea"),
        IconDef(id="database", glyph="🗄️", label="Database"),
        IconDef(id="cloud", glyph="☁️", label="Cloud"),
        IconDef(id="bug", glyph="🐛", label="Bug"),
        IconDef(id="target", glyph="🎯", label="Target"),
        IconDef(id="puzzle", glyph="🧩", label="Puzzle"),
        IconDef(id="link", glyph="🔗", label="Link"),
        IconDef(id="flag", glyph="🚩", label="Flag"),
    ],
)
