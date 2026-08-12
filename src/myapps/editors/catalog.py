"""Curated catalog of known code editors: CLI shim names, macOS app bundle
names, and launch argv templates.

Each entry is OS-agnostic metadata; detectors decide which ones are actually
present on the current machine.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    display_name: str
    cli_names: tuple[str, ...]  # names to look for on PATH, in priority order
    mac_app_names: tuple[str, ...]  # /Applications/<name>.app candidates
    windows_exe_names: tuple[str, ...]  # exe filenames to search common install dirs for
    windows_dir_hints: tuple[str, ...]  # subpaths under Program Files / LocalAppData to check
    linux_desktop_ids: tuple[str, ...]  # flatpak/snap application ids
    cli_open_args: tuple[str, ...]  # args appended after the executable to open a folder
    download_url: str
    open_source: bool


# `cli_open_args` uses "{path}" as a placeholder for the project path.
CATALOG: list[CatalogEntry] = [
    CatalogEntry(
        id="vscode",
        display_name="Visual Studio Code",
        cli_names=("code",),
        mac_app_names=("Visual Studio Code",),
        windows_exe_names=("Code.exe",),
        windows_dir_hints=(r"Microsoft VS Code",),
        linux_desktop_ids=("com.visualstudio.code",),
        cli_open_args=("-n", "{path}"),
        download_url="https://code.visualstudio.com/download",
        # MS's distributed build is proprietary-licensed, even though core VS Code is OSS.
        open_source=False,
    ),
    CatalogEntry(
        id="vscode-insiders",
        display_name="Visual Studio Code - Insiders",
        cli_names=("code-insiders",),
        mac_app_names=("Visual Studio Code - Insiders",),
        windows_exe_names=("Code - Insiders.exe",),
        windows_dir_hints=(r"Microsoft VS Code Insiders",),
        linux_desktop_ids=("com.visualstudio.code.insiders",),
        cli_open_args=("-n", "{path}"),
        download_url="https://code.visualstudio.com/insiders/",
        open_source=False,
    ),
    CatalogEntry(
        id="cursor",
        display_name="Cursor",
        cli_names=("cursor",),
        mac_app_names=("Cursor",),
        windows_exe_names=("Cursor.exe",),
        windows_dir_hints=(r"cursor",),
        linux_desktop_ids=("com.cursor.Cursor",),
        cli_open_args=("{path}",),
        download_url="https://cursor.com/download",
        open_source=False,
    ),
    CatalogEntry(
        id="vscodium",
        display_name="VSCodium",
        cli_names=("codium",),
        mac_app_names=("VSCodium",),
        windows_exe_names=("VSCodium.exe",),
        windows_dir_hints=(r"VSCodium",),
        linux_desktop_ids=("com.vscodium.codium",),
        cli_open_args=("-n", "{path}"),
        download_url="https://vscodium.com/",
        open_source=True,
    ),
    CatalogEntry(
        id="sublime_text",
        display_name="Sublime Text",
        cli_names=("subl",),
        mac_app_names=("Sublime Text",),
        windows_exe_names=("subl.exe",),
        windows_dir_hints=(r"Sublime Text",),
        linux_desktop_ids=("com.sublimetext.three", "com.sublimetext.four"),
        cli_open_args=("-n", "{path}"),
        download_url="https://www.sublimetext.com/download",
        open_source=False,
    ),
    CatalogEntry(
        id="zed",
        display_name="Zed",
        cli_names=("zed",),
        mac_app_names=("Zed",),
        windows_exe_names=("Zed.exe",),
        windows_dir_hints=(r"Zed",),
        linux_desktop_ids=("dev.zed.Zed",),
        cli_open_args=("{path}",),
        download_url="https://zed.dev/download",
        open_source=True,
    ),
    CatalogEntry(
        id="pycharm",
        display_name="PyCharm",
        cli_names=("pycharm",),
        mac_app_names=("PyCharm.app",),
        windows_exe_names=("pycharm.cmd", "pycharm64.exe"),
        windows_dir_hints=(r"JetBrains\Toolbox\scripts",),
        linux_desktop_ids=("com.jetbrains.PyCharm-Community", "com.jetbrains.PyCharm"),
        cli_open_args=("{path}",),
        download_url="https://www.jetbrains.com/pycharm/download/",
        open_source=False,
    ),
    CatalogEntry(
        id="idea",
        display_name="IntelliJ IDEA",
        cli_names=("idea",),
        mac_app_names=("IntelliJ IDEA.app", "IntelliJ IDEA CE.app"),
        windows_exe_names=("idea.cmd",),
        windows_dir_hints=(r"JetBrains\Toolbox\scripts",),
        linux_desktop_ids=("com.jetbrains.IntelliJ-IDEA-Community",),
        cli_open_args=("{path}",),
        download_url="https://www.jetbrains.com/idea/download/",
        open_source=False,
    ),
    CatalogEntry(
        id="webstorm",
        display_name="WebStorm",
        cli_names=("webstorm",),
        mac_app_names=("WebStorm.app",),
        windows_exe_names=("webstorm.cmd",),
        windows_dir_hints=(r"JetBrains\Toolbox\scripts",),
        linux_desktop_ids=("com.jetbrains.WebStorm",),
        cli_open_args=("{path}",),
        download_url="https://www.jetbrains.com/webstorm/download/",
        open_source=False,
    ),
    CatalogEntry(
        id="goland",
        display_name="GoLand",
        cli_names=("goland",),
        mac_app_names=("GoLand.app",),
        windows_exe_names=("goland.cmd",),
        windows_dir_hints=(r"JetBrains\Toolbox\scripts",),
        linux_desktop_ids=("com.jetbrains.GoLand",),
        cli_open_args=("{path}",),
        download_url="https://www.jetbrains.com/go/download/",
        open_source=False,
    ),
    CatalogEntry(
        id="clion",
        display_name="CLion",
        cli_names=("clion",),
        mac_app_names=("CLion.app",),
        windows_exe_names=("clion.cmd",),
        windows_dir_hints=(r"JetBrains\Toolbox\scripts",),
        linux_desktop_ids=("com.jetbrains.CLion",),
        cli_open_args=("{path}",),
        download_url="https://www.jetbrains.com/clion/download/",
        open_source=False,
    ),
    CatalogEntry(
        id="rubymine",
        display_name="RubyMine",
        cli_names=("rubymine",),
        mac_app_names=("RubyMine.app",),
        windows_exe_names=("rubymine.cmd",),
        windows_dir_hints=(r"JetBrains\Toolbox\scripts",),
        linux_desktop_ids=("com.jetbrains.RubyMine",),
        cli_open_args=("{path}",),
        download_url="https://www.jetbrains.com/ruby/download/",
        open_source=False,
    ),
    CatalogEntry(
        id="neovide",
        display_name="Neovide (Neovim)",
        cli_names=("neovide",),
        mac_app_names=("Neovide",),
        windows_exe_names=("neovide.exe",),
        windows_dir_hints=(r"Neovide",),
        linux_desktop_ids=(),
        cli_open_args=("{path}",),
        download_url="https://neovide.dev/",
        open_source=True,
    ),
]

CATALOG_BY_ID: dict[str, CatalogEntry] = {entry.id: entry for entry in CATALOG}

# Editors suggested in the "install missing editor" flow, prioritized because
# they're genuinely open source (MVP scope = link to the download page only).
SUGGESTED_OPEN_SOURCE_IDS = ["vscodium", "zed", "neovide"]
