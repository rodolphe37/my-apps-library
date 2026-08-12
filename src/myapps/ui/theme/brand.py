"""Brand color constants, sampled from the app logo (a blue-to-purple
gradient folder/puzzle-piece mark on a deep navy basket). Used by both
palettes.py (QPalette, Python-side) and the light/dark .qss files
(hand-kept in sync — QSS can't import Python constants, so if you change a
value here, mirror it in styles/light.qss and styles/dark.qss).
"""

from __future__ import annotations

# The logo's gradient endpoints.
ACCENT_BLUE = "#1AA3FD"
ACCENT_PURPLE = "#7D31FC"

# A single solid accent for QPalette.Highlight and other places that can't
# render a gradient (roughly the perceptual midpoint of the two colors above).
ACCENT_BLEND = "#4A6AFC"
ACCENT_BLEND_HOVER = "#5D7BFF"

# Dark theme surfaces — deep navy rather than neutral gray, echoing the
# logo's basket color.
DARK_BG = "#12182A"
DARK_SURFACE = "#1B2338"
DARK_SURFACE_ALT = "#232C46"
DARK_BORDER = "#2A3350"
DARK_TEXT = "#F2F4FA"
DARK_SUBTEXT = "#8891AD"

# Light theme surfaces — a faint blue tint instead of pure neutral gray.
LIGHT_BG = "#F4F6FB"
LIGHT_SURFACE = "#FFFFFF"
LIGHT_SURFACE_ALT = "#EBEFF9"
LIGHT_BORDER = "#DEE3F0"
LIGHT_TEXT = "#1B2338"
LIGHT_SUBTEXT = "#6B7390"

PIN_COLOR = "#F5A623"
