"""QMainWindow: menu bar, splitter (category sidebar + search + project list),
status bar. Wires the UI widgets to core managers and the theme system."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QByteArray, QItemSelectionModel, QSize, Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QDesktopServices,
    QDragEnterEvent,
    QDropEvent,
    QIcon,
    QKeySequence,
    QPalette,
    QPixmap,
)
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from myapps.constants import APP_NAME, DEFAULT_VIEW_MODE, MARKETPLACE_URL, UNCATEGORIZED_ID, VERSION
from myapps.core.events import event_bus
from myapps.core.project_manager import ProjectManager
from myapps.core.settings_manager import SettingsManager
from myapps.editors.registry import EditorRegistry
from myapps.i18n import LanguageManager, tr
from myapps.plugins.manager import PluginManager
from myapps.ui.dialogs.add_project_dialog import AddProjectDialog
from myapps.ui.dialogs.category_manager_dialog import (
    BulkCategoryPickerDialog,
    CategoryManagerDialog,
    ProjectCategoryPickerDialog,
)
from myapps.ui.dialogs.editor_picker_dialog import EditorPickerDialog
from myapps.ui.dialogs.icon_picker_dialog import IconPickerDialog
from myapps.ui.dialogs.plugin_manager_dialog import PluginManagerDialog
from myapps.ui.dialogs.settings_dialog import SettingsDialog
from myapps.ui.models.project_list_model import ProjectIdRole, ProjectListModel
from myapps.ui.resources import app_icon_path
from myapps.ui.theme import toolbar_icons
from myapps.ui.theme.shapes import apply_elevation
from myapps.ui.theme.theme_manager import ThemeManager
from myapps.ui.views.builtin import register_builtin_views
from myapps.ui.views.registry import view_registry
from myapps.ui.widgets.category_sidebar import ALL_ITEM_ID, CategorySidebar
from myapps.ui.widgets.context_menu import (
    build_bulk_project_context_menu,
    build_project_context_menu,
)
from myapps.ui.widgets.dialog_buttons import ask_yes_no
from myapps.ui.widgets.search_bar import SearchBar
from myapps.utils.fs_utils import reveal_in_file_manager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        project_manager: ProjectManager,
        settings_manager: SettingsManager,
        editor_registry: EditorRegistry,
        theme_manager: ThemeManager,
        plugin_manager: PluginManager | None = None,
        language_manager: LanguageManager | None = None,
    ) -> None:
        super().__init__()
        self._pm = project_manager
        self._settings = settings_manager
        self._editors = editor_registry
        self._theme = theme_manager
        self._plugins = plugin_manager
        self._language = language_manager

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(app_icon_path())))
        self.resize(1000, 640)
        self.setAcceptDrops(True)

        self._model = ProjectListModel(self._pm)
        self._model.set_sort(
            self._settings.settings.sort_key, self._settings.settings.sort_direction
        )
        self._selection_model = QItemSelectionModel(self._model, self)
        register_builtin_views(view_registry, self._pm)
        self._plugin_view_mode_ids: set[str] = set()
        self._register_plugin_views()
        self._views: dict[str, QWidget] = {}

        self._build_ui()
        self._build_menu_bar()
        self._restore_geometry()
        # Connected once here (not in _build_menu_bar, which can re-run on
        # language change) - _selection_model itself outlives every menu
        # rebuild, and the slot always reads self._project_menu_actions
        # fresh, so a single long-lived connection is enough.
        self._selection_model.selectionChanged.connect(self._update_project_menu_enabled_state)
        # Toolbar icons are baked pixmaps (see ui/theme/toolbar_icons.py's
        # docstring for why), so - unlike QSS-driven colors - they need an
        # explicit refresh whenever the resolved theme or active palette
        # changes, including a plugin-contributed one. self._theme is only
        # ever None in tests isolating other behavior (see __init__'s own
        # parameter), never in the real app.
        if self._theme is not None:
            self._theme.theme_changed.connect(self._refresh_toolbar_icons)

        if self._plugins is not None:
            event_bus.plugins_changed.connect(self._on_plugins_changed)
        if self._language is not None:
            self._language.language_changed.connect(self._on_language_changed)

    def _register_plugin_views(self) -> None:
        if self._plugins is None:
            return
        for info in self._plugins.collect_views():
            view_registry.register(info.mode_id, info.label, info.factory)
            self._plugin_view_mode_ids.add(info.mode_id)

    # -- UI construction -------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        self._left_panel = QWidget()
        self._left_panel.setObjectName("SidebarPanel")
        left_layout = QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self._build_brand_header())
        left_layout.addWidget(self._build_sidebar_section_label(tr("sidebar.library_header")))

        self._sidebar = CategorySidebar(self._pm)
        self._sidebar.filter_changed.connect(self._on_filter_changed)
        self._sidebar.project_recategorized.connect(self._on_project_recategorized)
        left_layout.addWidget(self._sidebar, stretch=1)
        left_layout.addWidget(self._build_sidebar_footer())

        splitter.addWidget(self._left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        right_layout.addWidget(self._build_toolbar())

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 10, 12, 12)
        content_layout.setSpacing(6)
        right_layout.addWidget(content, stretch=1)

        self._view_stack = QStackedWidget()
        for info in view_registry.list_modes():
            widget = info.factory(self._model, self._selection_model)
            self._views[info.mode_id] = widget
            self._wire_view_signals(widget)
            self._view_stack.addWidget(widget)
        content_layout.addWidget(self._view_stack)
        # The one and only place the persisted view_mode is validated
        # against the now-fully-populated self._views and restored (or
        # falls back to DEFAULT_VIEW_MODE). _wire_view_signals() must NOT
        # also do this per-widget mid-loop - self._views is necessarily
        # incomplete for all but the last widget processed, so it used to
        # treat a legitimately-saved "grid" as unknown and silently reset +
        # persist it back to "list" on every single startup.
        self._populate_view_toggle()
        self._set_active_view_mode(
            self._settings.settings.view_mode
            if self._settings.settings.view_mode in self._views
            else DEFAULT_VIEW_MODE
        )

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([180, 800])
        self._left_panel.setVisible(self._settings.settings.sidebar_visible)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._update_status_bar()
        event_bus.project_added.connect(self._update_status_bar)
        event_bus.project_removed.connect(self._update_status_bar)

    def _build_brand_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("BrandHeader")
        header.setFixedHeight(52)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        logo_label = QLabel()
        logo_pixmap = QPixmap(str(app_icon_path()))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    QSize(28, 28),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(logo_label)

        title_label = QLabel(APP_NAME)
        title_label.setObjectName("BrandTitle")
        layout.addWidget(title_label)
        layout.addStretch()
        return header

    def _build_sidebar_section_label(self, text: str) -> QLabel:
        """A static "Library" group label above the sidebar's "All" row -
        unlike the "Categories" header (see category_sidebar.py's
        _make_section_header), this one never appears/disappears with data,
        so it's a plain QLabel outside CategorySidebar rather than a list
        row inside it. Stored on self so _on_language_changed() can
        retranslate it - it's the one piece of always-visible chrome this
        method builds that isn't rebuilt wholesale on language change."""
        self._sidebar_library_label = QLabel(text)
        self._sidebar_library_label.setObjectName("SidebarSectionLabel")
        return self._sidebar_library_label

    def _build_sidebar_footer(self) -> QWidget:
        """Pinned to the bottom of the sidebar - "Add category", not "Add
        project" (that's already the toolbar's primary button; a second
        add-project entry point here would just duplicate it). A quiet
        ghost/dashed button, matching the sidebar's own content rather than
        competing with the toolbar's filled gradient one."""
        footer = QWidget()
        footer.setObjectName("SidebarFooter")
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(10, 8, 10, 10)

        button = QPushButton(f"+ {tr('sidebar.add_category')}")
        button.setObjectName("SidebarAddProjectButton")
        button.clicked.connect(self._quick_add_category)
        layout.addWidget(button)
        return footer

    def _build_toolbar(self) -> QWidget:
        """The one place search, the view-mode switch, sort and "Add
        project" all live as direct, always-visible actions - previously
        view mode/sort/add were menu-bar-only, undiscoverable unless you
        already knew View > Mode / View > Sort / File > Add Project
        existed. The menu bar keeps its own copies (shortcuts, full command
        discoverability), this is just a second, faster way to reach the
        same actions - see _set_active_view_mode()/_set_sort_key() etc.,
        the single source of truth both paths call into."""
        bar = QWidget()
        bar.setObjectName("Toolbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self._search_bar = SearchBar()
        self._search_bar.search_changed.connect(self._model.set_search_text)
        layout.addWidget(self._search_bar, stretch=1)

        self._view_toggle_frame = QFrame()
        self._view_toggle_frame.setObjectName("ViewToggle")
        toggle_layout = QHBoxLayout(self._view_toggle_frame)
        toggle_layout.setContentsMargins(3, 3, 3, 3)
        toggle_layout.setSpacing(2)
        self._view_toggle_group = QButtonGroup(self)
        self._view_toggle_group.setExclusive(True)
        self._view_toggle_buttons: dict[str, QToolButton] = {}
        layout.addWidget(self._view_toggle_frame)

        self._sort_button = QToolButton()
        self._sort_button.setObjectName("SortButton")
        self._sort_button.setToolTip(tr("menu.view.sort"))
        self._sort_button.setIconSize(toolbar_icons.TOOLBAR_ICON_SIZE)
        self._sort_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        sort_menu = QMenu(self._sort_button)
        self._populate_sort_menu(sort_menu)
        self._sort_button.setMenu(sort_menu)
        layout.addWidget(self._sort_button)

        add_button = QPushButton(tr("menu.file.add_project"))
        add_button.setObjectName("PrimaryButton")
        add_button.clicked.connect(self._add_project)
        apply_elevation(add_button, blur=18, y_offset=4, alpha=70)
        layout.addWidget(add_button)

        # _populate_view_toggle() (always called right after this method
        # returns - see _build_ui()) does the first _refresh_toolbar_icons()
        # once the view-toggle buttons actually exist; nothing to icon here
        # yet besides the sort button, which that same call covers too.
        return bar

    def _toolbar_icon_colors(self) -> tuple[QColor, QColor]:
        """(off, on) colors for hand-painted toolbar icons (see
        ui/theme/toolbar_icons.py) - read from this window's own QPalette,
        which ThemeManager keeps in sync with the active theme *and* any
        plugin-contributed ThemePalette (see palettes.py), so these icons
        never hardcode a color a custom palette can't override."""
        palette = self.palette()
        return (
            palette.color(QPalette.ColorRole.PlaceholderText),
            palette.color(QPalette.ColorRole.Highlight),
        )

    def _refresh_toolbar_icons(self) -> None:
        """Rebuilds every toolbar icon's pixmaps from the current palette -
        called on initial build, and on a theme change (colors baked into a
        pixmap can't just follow a QSS token the way text/background colors
        do, so this is the explicit refresh QSS gets for free elsewhere)."""
        off_color, on_color = self._toolbar_icon_colors()
        self._sort_button.setIcon(
            toolbar_icons.toolbar_icon("sort", toolbar_icons.TOOLBAR_ICON_SIZE.width(), off_color)
        )
        for mode_id, button in self._view_toggle_buttons.items():
            kind = toolbar_icons.icon_kind_for_mode(mode_id)
            button.setIcon(
                toolbar_icons.toolbar_icon(
                    kind, toolbar_icons.TOOLBAR_ICON_SIZE.width(), off_color, on_color
                )
            )

    def _populate_view_toggle(self) -> None:
        """(Re)builds the toolbar's segmented list/grid (+ any
        plugin-contributed mode) switch from the live view registry -
        mirrors _populate_view_mode_menu()'s job for the View menu, and is
        called from the same three places: initial build, a plugins_changed
        view-registry change, and a language change (mode labels are
        re-translated text, e.g. "List"/"Grid")."""
        for button in list(self._view_toggle_buttons.values()):
            self._view_toggle_group.removeButton(button)
            button.deleteLater()
        self._view_toggle_buttons.clear()

        current_mode = (
            self._settings.settings.view_mode
            if self._settings.settings.view_mode in self._views
            else DEFAULT_VIEW_MODE
        )
        layout = self._view_toggle_frame.layout()
        for info in view_registry.list_modes():
            button = QToolButton(self._view_toggle_frame)
            button.setToolTip(info.label)  # icon-only button - label lives in the tooltip
            button.setIconSize(toolbar_icons.TOOLBAR_ICON_SIZE)
            button.setCheckable(True)
            button.setChecked(info.mode_id == current_mode)
            button.clicked.connect(lambda _, mid=info.mode_id: self._set_active_view_mode(mid))
            self._view_toggle_group.addButton(button)
            layout.addWidget(button)
            self._view_toggle_buttons[info.mode_id] = button
        self._refresh_toolbar_icons()

    def _populate_sort_menu(self, menu: QMenu) -> None:
        """Fills `menu` with the sort-key + direction actions - shared by
        the View > Sort submenu and the toolbar's sort button so the two
        never drift apart. Builds fresh QActions each call (menus are cheap
        to rebuild and this keeps it consistent with how the rest of the
        menu bar re-reads current settings on every open)."""
        sort_group = QActionGroup(menu)
        sort_group.setExclusive(True)
        sort_options = (
            (tr("menu.view.sort.name"), "name"),
            (tr("menu.view.sort.created"), "created_at"),
            (tr("menu.view.sort.modified"), "modified_at"),
            (tr("menu.view.sort.size"), "size"),
        )
        for label, key in sort_options:
            action = QAction(label, menu, checkable=True)
            action.setChecked(self._settings.settings.sort_key == key)
            action.triggered.connect(lambda _, k=key: self._set_sort_key(k))
            sort_group.addAction(action)
            menu.addAction(action)
        menu.addSeparator()
        descending_action = QAction(tr("menu.view.sort.descending"), menu, checkable=True)
        descending_action.setChecked(self._settings.settings.sort_direction == "desc")
        descending_action.toggled.connect(self._set_sort_descending)
        menu.addAction(descending_action)

    def _build_menu_bar(self) -> None:
        """Builds the whole menu bar from scratch. Safe to call again - the
        leading `clear()` makes this idempotent, which is what lets
        `_on_language_changed()` just re-run this method wholesale instead
        of maintaining a second, parallel retranslation code path."""
        menu_bar = self.menuBar()
        menu_bar.clear()
        menu_bar.setNativeMenuBar(True)

        # File
        file_menu = menu_bar.addMenu(tr("menu.file"))
        add_action = QAction(tr("menu.file.add_project"), self)
        add_action.setShortcut(QKeySequence.StandardKey.New)
        add_action.triggered.connect(self._add_project)
        file_menu.addAction(add_action)
        file_menu.addSeparator()
        prefs_action = QAction(tr("menu.file.preferences"), self)
        prefs_action.setShortcut(QKeySequence.StandardKey.Preferences)
        prefs_action.triggered.connect(self._open_preferences)
        file_menu.addAction(prefs_action)
        file_menu.addSeparator()
        quit_action = QAction(tr("menu.file.quit"), self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Project
        project_menu = menu_bar.addMenu(tr("menu.project"))
        open_action = QAction(tr("menu.project.open"), self)
        open_action.triggered.connect(lambda: self._open_project(self._current_project_id()))
        project_menu.addAction(open_action)
        open_with_action = QAction(tr("menu.project.open_with"), self)
        open_with_action.triggered.connect(lambda: self._open_with(self._current_project_id()))
        project_menu.addAction(open_with_action)
        reveal_action = QAction(tr("menu.project.reveal"), self)
        reveal_action.triggered.connect(lambda: self._reveal(self._current_project_id()))
        project_menu.addAction(reveal_action)
        project_menu.addSeparator()
        categories_action = QAction(tr("menu.project.edit_categories"), self)
        categories_action.triggered.connect(self._edit_categories_for_selection)
        project_menu.addAction(categories_action)
        project_menu.addSeparator()
        manage_categories_action = QAction(tr("menu.project.manage_categories"), self)
        manage_categories_action.triggered.connect(self._manage_categories)
        project_menu.addAction(manage_categories_action)
        project_menu.addSeparator()
        remove_action = QAction(tr("menu.project.remove"), self)
        remove_action.triggered.connect(self._remove_for_selection)
        project_menu.addAction(remove_action)

        # These five all operate on whatever's currently selected in the
        # project list/grid and used to silently do nothing when clicked
        # with nothing selected - now kept disabled instead, via
        # _update_project_menu_enabled_state() (wired to the shared
        # selection model once in __init__, and re-applied after every
        # rebuild of this menu, e.g. on language change).
        self._project_menu_actions = [
            open_action,
            open_with_action,
            reveal_action,
            categories_action,
            remove_action,
        ]
        self._update_project_menu_enabled_state()

        # View
        view_menu = menu_bar.addMenu(tr("menu.view"))
        sidebar_action = QAction(tr("menu.view.show_sidebar"), self, checkable=True)
        sidebar_action.setChecked(self._settings.settings.sidebar_visible)
        sidebar_action.toggled.connect(self._toggle_sidebar)
        view_menu.addAction(sidebar_action)
        view_menu.addSeparator()

        self._view_mode_menu = view_menu.addMenu(tr("menu.view.mode"))
        self._populate_view_mode_menu()
        view_menu.addSeparator()

        theme_menu = view_menu.addMenu(tr("menu.view.theme"))
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        theme_options = (
            (tr("menu.view.theme.system"), "system"),
            (tr("menu.view.theme.light"), "light"),
            (tr("menu.view.theme.dark"), "dark"),
        )
        for label, mode in theme_options:
            action = QAction(label, self, checkable=True)
            action.setChecked(self._settings.settings.theme_mode == mode)
            action.triggered.connect(lambda _, m=mode: self._set_theme_mode(m))
            theme_group.addAction(action)
            theme_menu.addAction(action)
        view_menu.addSeparator()

        sort_menu = view_menu.addMenu(tr("menu.view.sort"))
        self._populate_sort_menu(sort_menu)

        # Plugins - always present, even with zero plugins installed, so
        # "Manage Plugins…" is discoverable regardless.
        self._plugins_menu = menu_bar.addMenu(tr("menu.plugins"))
        self._populate_plugins_menu()

        # Help
        help_menu = menu_bar.addMenu(tr("menu.help"))
        about_action = QAction(tr("menu.help.about", app_name=APP_NAME), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _populate_view_mode_menu(self) -> None:
        self._view_mode_menu.clear()
        current_mode = (
            self._settings.settings.view_mode
            if self._settings.settings.view_mode in self._views
            else DEFAULT_VIEW_MODE
        )
        view_mode_group = QActionGroup(self._view_mode_menu)
        view_mode_group.setExclusive(True)
        for info in view_registry.list_modes():
            action = QAction(info.label, self._view_mode_menu, checkable=True)
            action.setChecked(info.mode_id == current_mode)
            action.triggered.connect(lambda _, mid=info.mode_id: self._set_active_view_mode(mid))
            view_mode_group.addAction(action)
            self._view_mode_menu.addAction(action)

    def _populate_plugins_menu(self) -> None:
        self._plugins_menu.clear()
        manage_action = QAction(tr("menu.plugins.manage"), self._plugins_menu)
        manage_action.triggered.connect(self._open_plugin_manager)
        self._plugins_menu.addAction(manage_action)

        browse_action = QAction(tr("menu.plugins.browseMarketplace"), self._plugins_menu)
        browse_action.triggered.connect(self._open_marketplace)
        self._plugins_menu.addAction(browse_action)

        if self._plugins is None:
            return
        contributed = self._plugins.collect_menu_actions()
        if contributed:
            self._plugins_menu.addSeparator()
            for plugin_action in contributed:
                action = QAction(plugin_action.label, self._plugins_menu)
                action.setEnabled(plugin_action.enabled)
                action.triggered.connect(plugin_action.callback)
                self._plugins_menu.addAction(action)

    # -- state helpers -----------------------------------------------------

    def _current_project_id(self) -> str | None:
        # The selection model is shared across every registered view (see
        # ui/views/registry.py's contract), so this is mode-agnostic.
        index = self._selection_model.currentIndex()
        if not index.isValid():
            return None
        return index.data(ProjectIdRole)

    def _selected_project_ids(self) -> list[str]:
        """Every currently selected project, mode-agnostic (shared
        selection model) and de-duplicated (QListView reports one index per
        selected row, but this stays defensive if a future view emits more
        than one column of indexes per row)."""
        ids: list[str] = []
        seen: set[str] = set()
        for index in self._selection_model.selectedIndexes():
            pid = index.data(ProjectIdRole)
            if pid and pid not in seen:
                seen.add(pid)
                ids.append(pid)
        return ids

    def _update_project_menu_enabled_state(self, *_args) -> None:
        """Keeps the Project menu's selection-dependent actions (Open, Open
        With…, Reveal, Edit Categories…, Remove) disabled while nothing is
        selected, instead of them silently doing nothing when clicked - the
        context menu equivalent simply doesn't appear in that case, but a
        top menu-bar item can't do that, so it needs to look inert instead.
        *_args swallows QItemSelectionModel.selectionChanged's (selected,
        deselected) arguments - this only ever needs to know whether
        anything is selected now."""
        has_selection = bool(self._selected_project_ids())
        for action in self._project_menu_actions:
            action.setEnabled(has_selection)

    def _update_status_bar(self, *_args) -> None:
        count = len(self._pm.list_projects())
        key = "status.project_count.one" if count == 1 else "status.project_count.other"
        self._status_bar.showMessage(tr(key, n=count))

    # -- actions -------------------------------------------------------

    def _add_project(self) -> None:
        dialog = AddProjectDialog(self._pm, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            data = dialog.result_data()
            if data:
                path, name, categories = data
                self._pm.add_project(path, name=name, categories=categories)

    def _open_project(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if not project:
            return
        editor_id = project.preferred_editor_id or self._settings.settings.global_default_editor_id
        if not editor_id:
            self._open_with(project_id)
            return
        if self._editors.launch(editor_id, project.path):
            self._pm.mark_opened(project_id, editor_id)
        else:
            QMessageBox.warning(
                self,
                tr("msg.couldnt_open_editor.title"),
                tr("msg.couldnt_open_editor.retry_body"),
            )

    def _open_with(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if not project:
            return
        dialog = EditorPickerDialog(self._editors, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            editor_id = dialog.selected_editor_id()
            if not editor_id:
                return
            if dialog.should_set_as_default():
                self._pm.update_project(project_id, preferred_editor_id=editor_id)
            if self._editors.launch(editor_id, project.path):
                self._pm.mark_opened(project_id, editor_id)
            else:
                QMessageBox.warning(
                    self, tr("msg.couldnt_open_editor.title"), tr("msg.couldnt_open_editor.body")
                )

    def _reveal(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if project and not reveal_in_file_manager(project.path):
            QMessageBox.warning(self, tr("msg.couldnt_reveal.title"), tr("msg.couldnt_reveal.body"))

    def _toggle_pin(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if project:
            self._pm.update_project(project_id, pinned=not project.pinned)

    def _edit_categories(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if not project:
            return
        dialog = ProjectCategoryPickerDialog(project, self._pm, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._pm.set_categories(project_id, dialog.selected_category_ids())

    def _edit_categories_for_selection(self) -> None:
        """Wired to the Project menu's "Edit Categories…" action: bulk when
        more than one project is selected, single-project otherwise -
        mirrors the context menu's own selection-aware branching."""
        selected_ids = self._selected_project_ids()
        if len(selected_ids) > 1:
            self._edit_categories_bulk(selected_ids)
        else:
            self._edit_categories(self._current_project_id())

    def _edit_categories_bulk(self, project_ids: list[str]) -> None:
        projects = [p for pid in project_ids if (p := self._pm.get_project(pid))]
        if not projects:
            return
        dialog = BulkCategoryPickerDialog(projects, self._pm, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            dialog.apply()

    def _toggle_pin_bulk(self, project_ids: list[str], *, pin: bool) -> None:
        for project_id in project_ids:
            self._pm.update_project(project_id, pinned=pin)

    def _rename(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if not project:
            return
        new_name, ok = QInputDialog.getText(
            self,
            tr("dialog.rename_project.title"),
            tr("dialog.rename_project.label"),
            text=project.name,
        )
        if ok and new_name.strip():
            self._pm.update_project(project_id, name=new_name.strip())

    def _remove(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if not project:
            return
        confirmed = ask_yes_no(
            self,
            tr("dialog.remove_project.title"),
            tr("dialog.remove_project.body", name=project.name),
        )
        if confirmed:
            self._pm.remove_project(project_id)

    def _remove_for_selection(self) -> None:
        selected_ids = self._selected_project_ids()
        if len(selected_ids) > 1:
            self._remove_bulk(selected_ids)
        else:
            self._remove(self._current_project_id())

    def _remove_bulk(self, project_ids: list[str]) -> None:
        projects = [p for pid in project_ids if (p := self._pm.get_project(pid))]
        if not projects:
            return
        n = len(projects)
        body_key = (
            "dialog.remove_projects.body.one" if n == 1 else "dialog.remove_projects.body.other"
        )
        confirmed = ask_yes_no(self, tr("dialog.remove_project.title"), tr(body_key, n=n))
        if confirmed:
            for project in projects:
                self._pm.remove_project(project.id)

    def _manage_categories(self) -> None:
        CategoryManagerDialog(self._pm, self, plugin_manager=self._plugins).exec()

    def _quick_add_category(self) -> None:
        """Wired to the sidebar footer's "Add category" button - a fast,
        single-field prompt (mirrors _rename()'s own QInputDialog pattern),
        not the full CategoryManagerDialog (Project > Manage Categories…
        stays the place for renaming/deleting/re-icon-ing)."""
        name, ok = QInputDialog.getText(
            self,
            tr("dialog.manage_categories.title"),
            tr("sidebar.add_category"),
        )
        if ok and name.strip():
            self._pm.add_category(name.strip())

    def _choose_icon(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = self._pm.get_project(project_id)
        if not project:
            return
        plugin_packs = self._plugins.collect_icon_packs() if self._plugins else []
        dialog = IconPickerDialog(plugin_packs, project.icon, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._pm.update_project(project_id, icon=dialog.selected_icon())

    def _open_plugin_manager(self) -> None:
        if self._plugins is None:
            QMessageBox.information(
                self, tr("msg.plugins_unavailable.title"), tr("msg.plugins_unavailable.body")
            )
            return
        PluginManagerDialog(self._plugins, self).exec()

    def _open_marketplace(self) -> None:
        """Opens the plugin marketplace in the system browser. The app
        itself stays network-free (installs are still local zip/folder
        only, per PLAN.md's Phase 3 boundary) - this is just a discovery
        shortcut, same role as the "install missing editor" download-page
        links in editor_picker_dialog.py."""
        QDesktopServices.openUrl(QUrl(MARKETPLACE_URL))

    def _show_context_menu(self, project_id: str, global_pos) -> None:
        # Right-clicking a project that's part of the current multi-selection
        # shows the bulk menu for the whole selection; right-clicking any
        # other project (including one outside an existing selection) always
        # shows the single-project menu for just that one - the standard
        # Finder/Explorer convention.
        selected_ids = self._selected_project_ids()
        if project_id in selected_ids and len(selected_ids) > 1:
            self._show_bulk_context_menu(selected_ids, global_pos)
            return

        project = self._pm.get_project(project_id)
        if not project:
            return
        menu = build_project_context_menu(
            project,
            self,
            on_open=lambda: self._open_project(project_id),
            on_open_with=lambda: self._open_with(project_id),
            on_reveal=lambda: self._reveal(project_id),
            on_toggle_pin=lambda: self._toggle_pin(project_id),
            on_edit_categories=lambda: self._edit_categories(project_id),
            on_choose_icon=lambda: self._choose_icon(project_id),
            on_rename=lambda: self._rename(project_id),
            on_remove=lambda: self._remove(project_id),
        )
        if self._plugins is not None:
            plugin_actions = self._plugins.collect_project_context_actions(project)
            if plugin_actions:
                menu.addSeparator()
                for plugin_action in plugin_actions:
                    action = menu.addAction(plugin_action.label, plugin_action.callback)
                    action.setEnabled(plugin_action.enabled)
        menu.exec(global_pos)

    def _show_bulk_context_menu(self, project_ids: list[str], global_pos) -> None:
        projects = [p for pid in project_ids if (p := self._pm.get_project(pid))]
        if not projects:
            return
        all_pinned = all(p.pinned for p in projects)
        menu = build_bulk_project_context_menu(
            len(projects),
            self,
            all_pinned=all_pinned,
            on_toggle_pin=lambda: self._toggle_pin_bulk(project_ids, pin=not all_pinned),
            on_edit_categories=lambda: self._edit_categories_bulk(project_ids),
            on_remove=lambda: self._remove_bulk(project_ids),
        )
        menu.exec(global_pos)

    def _on_filter_changed(self, filter_id: str) -> None:
        if filter_id == ALL_ITEM_ID:
            self._model.clear_filter()
            self._settings.set(last_selected_category=None)
        elif filter_id == UNCATEGORIZED_ID:
            self._model.set_category_filter(None)
            self._settings.set(last_selected_category=UNCATEGORIZED_ID)
        else:
            self._model.set_category_filter(filter_id)
            self._settings.set(last_selected_category=filter_id)

    def _on_project_recategorized(self, project_name: str, category_label: str) -> None:
        self._status_bar.showMessage(
            tr("status.moved_to", name=project_name, category=category_label), 3000
        )

    def _toggle_sidebar(self, visible: bool) -> None:
        self._left_panel.setVisible(visible)
        self._settings.set(sidebar_visible=visible)

    def _set_active_view_mode(self, mode_id: str) -> None:
        widget = self._views.get(mode_id)
        if widget is None:
            logger.warning("Unknown view mode %r, falling back to %r", mode_id, DEFAULT_VIEW_MODE)
            widget = self._views.get(DEFAULT_VIEW_MODE)
            mode_id = DEFAULT_VIEW_MODE
        if widget is not None:
            self._view_stack.setCurrentWidget(widget)
        self._settings.set(view_mode=mode_id)
        toggle_button = self._view_toggle_buttons.get(mode_id)
        if toggle_button is not None and not toggle_button.isChecked():
            toggle_button.setChecked(True)

    def _on_language_changed(self, _locale: str) -> None:
        """Rebuilds every piece of persistent, always-visible UI that carries
        translated text. Dialogs need no entry here - they're all freshly
        instantiated on each open, so a `tr()` call at construction time is
        always current (see i18n design notes)."""
        register_builtin_views(view_registry, self._pm)  # retranslate "List"/"Grid" labels
        self._build_menu_bar()  # idempotent full rebuild, see its own docstring
        self._populate_view_toggle()  # re-translate the toolbar's List/Grid labels too
        self._sidebar._refresh()  # "All"/"Uncategorized" labels; category names are user data
        self._sidebar_library_label.setText(tr("sidebar.library_header"))
        self._search_bar.retranslate()
        self._update_status_bar()

    def _on_plugins_changed(self) -> None:
        """Rebuilds plugin-derived UI after install/uninstall/enable/disable.
        Full rebuild rather than diffing - view-mode churn only happens via
        the Plugin Manager dialog (rare), so correctness-over-cleverness is
        the right tradeoff here."""
        for mode_id in self._plugin_view_mode_ids:
            view_registry.unregister(mode_id)
        self._plugin_view_mode_ids.clear()
        self._register_plugin_views()
        self._sync_view_stack()
        self._populate_view_mode_menu()
        self._populate_plugins_menu()
        if self._language is not None and self._plugins is not None:
            # A plugin enable/disable can add or remove a translation-plugin
            # contributed locale, or patch keys in an existing one.
            self._language.set_plugin_translations(self._plugins.collect_translations())
        if self._plugins is not None and self._theme is not None:
            # A plugin enable/disable can add or remove a theme palette (the
            # Preferences dialog's combo is only rebuilt on next open, but it
            # reads theme_manager.available_palette_choices() fresh each
            # time, so refreshing the source list here is enough - see
            # ThemeManager.set_available_palettes()'s docstring). theme_manager
            # is Optional here only in tests that construct MainWindow with
            # theme_manager=None to isolate other behavior (e.g.
            # test_language_switch.py) - never in the real app.
            self._theme.set_available_palettes(self._plugins.collect_theme_palettes())
            self._theme.set_palette(self._theme.palette_id)  # re-validate current choice

    def _sync_view_stack(self) -> None:
        active_mode_ids = {info.mode_id for info in view_registry.list_modes()}

        for mode_id in list(self._views):
            if mode_id not in active_mode_ids:
                widget = self._views.pop(mode_id)
                self._view_stack.removeWidget(widget)
                widget.deleteLater()

        for info in view_registry.list_modes():
            if info.mode_id in self._views:
                continue
            widget = info.factory(self._model, self._selection_model)
            self._views[info.mode_id] = widget
            self._wire_view_signals(widget)
            self._view_stack.addWidget(widget)

        self._populate_view_toggle()  # a plugin can add/remove a contributed view mode
        # Same validate-once-after-the-full-set-is-known pattern as the end
        # of _build_ui(), for the same reason: covers a plugin being
        # disabled while its contributed view was the active one.
        current_mode = self._settings.settings.view_mode
        if current_mode not in self._views:
            self._set_active_view_mode(DEFAULT_VIEW_MODE)

    def _wire_view_signals(self, widget: QWidget) -> None:
        """Connects the signals every registered view is contractually
        required to emit (see ui/views/registry.py), plus
        external_folders_dropped if this particular widget happens to
        provide it - built-in views do (see ProjectListView), a
        plugin-contributed view isn't required to."""
        widget.open_requested.connect(self._open_project)
        widget.context_menu_requested.connect(self._show_context_menu)
        if hasattr(widget, "external_folders_dropped"):
            widget.external_folders_dropped.connect(self._add_projects_from_paths)

    def _set_theme_mode(self, mode: str) -> None:
        self._settings.set(theme_mode=mode)
        self._theme.set_mode(mode)

    def _set_sort_key(self, key: str) -> None:
        self._settings.set(sort_key=key)
        self._model.set_sort(key, self._settings.settings.sort_direction)

    def _set_sort_descending(self, checked: bool) -> None:
        direction = "desc" if checked else "asc"
        self._settings.set(sort_direction=direction)
        self._model.set_sort(self._settings.settings.sort_key, direction)

    def _open_preferences(self) -> None:
        SettingsDialog(
            self._settings,
            self._editors,
            self,
            language_manager=self._language,
            theme_manager=self._theme,
        ).exec()

    def _show_about(self) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(tr("about.title", app_name=APP_NAME))
        box.setText(tr("about.body", app_name=APP_NAME, version=VERSION))
        pixmap = QPixmap(str(app_icon_path()))
        if not pixmap.isNull():
            box.setIconPixmap(
                pixmap.scaled(
                    QSize(72, 72),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        box.addButton(tr("action.ok"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    # -- drag & drop ---------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        folders = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile() and Path(url.toLocalFile()).is_dir()
        ]
        if not folders:
            return
        event.acceptProposedAction()
        self._add_projects_from_paths(folders)

    def _add_projects_from_paths(self, paths: list[str]) -> None:
        added = 0
        skipped = 0
        for path in paths:
            if self._pm.find_by_path(path):
                skipped += 1
            else:
                self._pm.add_project(path)
                added += 1
        key = "status.added_projects.one" if added == 1 else "status.added_projects.other"
        message = tr(key, n=added)
        if skipped:
            message += tr("status.already_in_library", n=skipped)
        self._status_bar.showMessage(message, 4000)

    # -- window state ------------------------------------------------------

    def _restore_geometry(self) -> None:
        geometry_b64 = self._settings.settings.window_geometry
        if geometry_b64:
            self.restoreGeometry(QByteArray.fromBase64(geometry_b64.encode("ascii")))

    def closeEvent(self, event) -> None:  # noqa: N802
        geometry_b64 = bytes(self.saveGeometry().toBase64()).decode("ascii")
        self._settings.set(window_geometry=geometry_b64)
        super().closeEvent(event)
