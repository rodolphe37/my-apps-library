#!/usr/bin/env bash
# Advanced/secondary macOS install path — alongside the Homebrew Cask
# (Casks/my-apps-library.rb), not instead of it. Pick this one instead if
# you specifically want zero Gatekeeper warning on first launch; pick
# Homebrew instead if you'd rather have `brew upgrade`/`uninstall` and
# don't mind a one-time right-click -> Open.
#
# Why this one genuinely has no warning where Homebrew Cask still does
# (verified for real — see Casks/my-apps-library.rb's own comment): macOS
# only applies the com.apple.quarantine flag when a file is written by
# something that calls Apple's quarantine API — browsers, Mail, AirDrop,
# and (a deliberate choice on their part) Homebrew Cask. Plain `curl` and
# `unzip` run from a terminal have no such integration at all, so nothing
# here ever gets flagged in the first place. `xattr -cr` at the end is a
# safety net, not the mechanism doing the actual work.
set -euo pipefail

REPO="rodolphe37/my-apps-library"
APP_NAME="MyAppsLibrary.app"
INSTALL_DIR="/Applications"

command -v curl >/dev/null 2>&1 || { echo "curl is required." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required (used to parse the GitHub API response)." >&2; exit 1; }

case "$(uname -m)" in
  arm64)  asset_arch="ARM64" ;;
  x86_64) asset_arch="X64" ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

cleanup_files=()
cleanup() { rm -f "${cleanup_files[@]}"; }
trap cleanup EXIT

echo "Fetching latest release info..."
release_json_file=$(mktemp)
cleanup_files+=("$release_json_file")
curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" -o "$release_json_file"

# Reads from a file rather than interpolating the response into a Python
# string literal — a release body containing a quote/control character
# would otherwise break that naive approach (found via real testing of
# the Linux counterpart to this script).
download_url=$(python3 -c "
import json
with open('$release_json_file') as f:
    data = json.load(f)
asset = next(a for a in data['assets'] if a['name'] == 'MyAppsLibrary-macOS-${asset_arch}.zip')
print(asset['browser_download_url'])
")
version=$(python3 -c "
import json
with open('$release_json_file') as f:
    print(json.load(f)['tag_name'])
")

echo "Downloading MyAppsLibrary ${version} for macOS (${asset_arch})..."
tmp_zip=$(mktemp -t my-apps-library).zip
cleanup_files+=("$tmp_zip")
curl -fsSL -o "$tmp_zip" "$download_url"

if [ ! -w "$INSTALL_DIR" ]; then
  echo "Warning: ${INSTALL_DIR} isn't writable — installing to ~/Applications instead." >&2
  INSTALL_DIR="${HOME}/Applications"
  mkdir -p "$INSTALL_DIR"
fi

echo "Installing to ${INSTALL_DIR}/${APP_NAME}..."
rm -rf "${INSTALL_DIR:?}/${APP_NAME}"
# ditto, not unzip -d directly: unzip can mangle the .app bundle's
# resource fork / extended attributes on extraction; ditto is Apple's own
# tool for this and is what release.yml itself uses to build the zip.
ditto -x -k "$tmp_zip" "$INSTALL_DIR"

# Belt-and-suspenders — see header comment. Should already be a no-op
# given curl+ditto from a terminal never apply the flag in the first
# place, but costs nothing to guarantee.
xattr -cr "${INSTALL_DIR}/${APP_NAME}"

echo ""
echo "Installed MyAppsLibrary ${version} to ${INSTALL_DIR}/${APP_NAME}."
echo "No update mechanism here — re-run this script to update, or use the Homebrew Cask instead if you want 'brew upgrade' to handle that for you."
