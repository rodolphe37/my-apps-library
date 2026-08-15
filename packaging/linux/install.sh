#!/usr/bin/env bash
# Installs MyAppsLibrary on Linux: downloads the latest release zip
# (release.yml's onedir PyInstaller build - plain curl + unzip, both of
# which are quarantine-unaware, so nothing here needs macOS's Gatekeeper-
# style workaround), and - the part a bare curl+unzip alone wouldn't give
# you - registers a .desktop entry so the app actually shows up in your
# application menu/launcher (GNOME Activities, KDE menu, etc.). Linux
# discovers apps that way, not by scanning a folder the way macOS's
# /Applications or Windows' Start Menu do; without this step you'd have a
# working binary with no icon anywhere.
set -euo pipefail

REPO="rodolphe37/my-apps-library"
APP_DIR_NAME="MyAppsLibrary"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_DIR="${HOME}/.local/bin"
INSTALL_DIR="${DATA_HOME}/my-apps-library"
DESKTOP_DIR="${DATA_HOME}/applications"
ICON_DIR="${DATA_HOME}/icons/hicolor/256x256/apps"
ICON_URL="https://raw.githubusercontent.com/${REPO}/main/packaging/icons/app.png"

command -v curl >/dev/null 2>&1 || { echo "curl is required." >&2; exit 1; }
command -v unzip >/dev/null 2>&1 || { echo "unzip is required." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required (used to parse the GitHub API response)." >&2; exit 1; }

cleanup_files=()
cleanup() {
  rm -f "${cleanup_files[@]}"
}
trap cleanup EXIT

echo "Fetching latest release info..."
release_json_file=$(mktemp)
cleanup_files+=("$release_json_file")
curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" -o "$release_json_file"
# Read the response from a file, not interpolated into a Python string
# literal - a release body/notes containing a quote or control character
# would otherwise break (found via real testing) the naive
# json.loads('''$release_json''') approach.
download_url=$(python3 -c "
import json
with open('$release_json_file') as f:
    data = json.load(f)
asset = next(a for a in data['assets'] if a['name'] == 'MyAppsLibrary-Linux.zip')
print(asset['browser_download_url'])
")
version=$(python3 -c "
import json
with open('$release_json_file') as f:
    print(json.load(f)['tag_name'])
")

echo "Downloading MyAppsLibrary ${version} for Linux..."
tmp_zip=$(mktemp)
cleanup_files+=("$tmp_zip")
curl -fsSL -o "$tmp_zip" "$download_url"

echo "Installing to ${INSTALL_DIR}..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
unzip -q "$tmp_zip" -d "$INSTALL_DIR"
chmod +x "${INSTALL_DIR}/${APP_DIR_NAME}/${APP_DIR_NAME}"

mkdir -p "$BIN_DIR"
ln -sf "${INSTALL_DIR}/${APP_DIR_NAME}/${APP_DIR_NAME}" "${BIN_DIR}/my-apps-library"

mkdir -p "$ICON_DIR"
curl -fsSL -o "${ICON_DIR}/my-apps-library.png" "$ICON_URL" || echo "Warning: couldn't fetch the app icon - the .desktop entry will use a generic one." >&2

mkdir -p "$DESKTOP_DIR"
cat > "${DESKTOP_DIR}/my-apps-library.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=MyAppsLibrary
Comment=A personal launcher/library for your developer projects
Exec=${INSTALL_DIR}/${APP_DIR_NAME}/${APP_DIR_NAME}
Icon=my-apps-library
Categories=Development;Utility;
Terminal=false
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f "${DATA_HOME}/icons/hicolor" >/dev/null 2>&1 || true
fi

echo ""
echo "Installed MyAppsLibrary ${version}."
echo "Launch it from your application menu, or run: my-apps-library"
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  echo "(Note: ${BIN_DIR} isn't on your PATH - add it to your shell profile to use the 'my-apps-library' command directly.)"
fi
