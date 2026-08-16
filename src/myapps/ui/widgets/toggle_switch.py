"""ToggleSwitch: a small iOS/macOS-style on/off switch, used wherever a
plain QCheckBox would otherwise stand for an enabled/disabled state (see
PluginManagerDialog). Custom-painted rather than styled via QSS
`::indicator` selectors - checkbox indicator theming is notoriously
inconsistent across platforms (macOS in particular tends to let the native
style win over QSS there) - so painting it directly guarantees the exact
same look everywhere, in both light and dark, with zero QSS involved.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPalette
from PySide6.QtWidgets import QAbstractButton, QSizePolicy, QWidget

from myapps.ui.theme import brand

_WIDTH = 40
_HEIGHT = 24
_OFF_COLOR_LIGHT = QColor("#c7cad9")
_OFF_COLOR_DARK = QColor("#454e6b")


class ToggleSwitch(QAbstractButton):
    """A checkable QAbstractButton - use exactly like a QCheckBox
    (`isChecked()`/`setChecked()`/`toggled` signal all work normally)."""

    toggledTo = Signal(bool)  # same payload as `toggled`, named for call-site clarity

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._thumb_position = 1.0 if self.isChecked() else 0.0
        self._anim = QPropertyAnimation(self, b"thumbPosition", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate_to)
        self.toggled.connect(self.toggledTo)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(_WIDTH, _HEIGHT)

    def set_checked_silently(self, checked: bool) -> None:
        """Sets the initial state (e.g. a freshly-built PluginManagerDialog
        card reflecting whether that plugin is already enabled) without
        emitting `toggled` or animating - the switch should just appear
        already resting in the right position, not visibly slide into it
        the instant the dialog opens. Use plain `setChecked()` for any
        state change that should animate (i.e. an actual user click)."""
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)
        self._anim.stop()
        self._thumb_position = 1.0 if checked else 0.0
        self.update()

    def _animate_to(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._thumb_position)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    # -- the animated Qt Property the QPropertyAnimation above drives -----

    def _get_thumb_position(self) -> float:
        return self._thumb_position

    def _set_thumb_position(self, value: float) -> None:
        self._thumb_position = value
        self.update()

    thumbPosition = Property(float, _get_thumb_position, _set_thumb_position)

    # -- painting ----------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        radius = rect.height() / 2

        off_color = self._off_color()
        on_color = QColor(brand.ACCENT_BLEND)
        track_color = _blend(off_color, on_color, self._thumb_position)
        if not self.isEnabled():
            track_color.setAlpha(110)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(rect, radius, radius)

        thumb_d = rect.height() - 4
        travel = rect.width() - thumb_d - 4
        thumb_x = rect.left() + 2 + travel * self._thumb_position
        thumb_rect = QRectF(thumb_x, rect.top() + 2, thumb_d, thumb_d)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(thumb_rect)

    def _off_color(self) -> QColor:
        # No direct "am I in dark mode" flag reaches this widget (plugins/
        # dialogs don't carry ThemeManager down to every child widget) -
        # the window's own palette background lightness is a reliable,
        # already-available proxy: the app's light/dark QSS always sets a
        # dark `$bg` in dark mode and a light one in light mode.
        bg = self.palette().color(QPalette.ColorRole.Window)
        return _OFF_COLOR_DARK if bg.lightness() < 128 else _OFF_COLOR_LIGHT


def _blend(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    )
