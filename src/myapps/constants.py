"""App-wide constants."""

import os

APP_NAME = "MyAppsLibrary"
APP_ID = "myapps"
ORG_NAME = "MyAppsLibrary"
VERSION = "0.9.0"

# Bumped whenever the on-disk JSON schema changes in a way that requires migration.
SCHEMA_VERSION = 1

DEFAULT_VIEW_MODE = "list"
UNCATEGORIZED_ID = "__uncategorized__"

# The marketplace is now live at marketplace.rodolphe-augusto.fr. Still read
# from MYAPPS_MARKETPLACE_URL rather than hardcoding that domain - keeps
# local dev pointed at `npm run dev`'s localhost:5173 by default, and
# packaging/CI free to override without a code change either way.
MARKETPLACE_URL = os.environ.get("MYAPPS_MARKETPLACE_URL", "https://marketplace.rodolphe-augusto.fr")
# The marketplace's API, not the website - used to check an installed
# plugin for updates and to download one (core/plugin_marketplace_client.py).
# Same public, no-auth endpoints the CLI (MAL_PLUGIN_API_BASE_URL) and web
# app already talk to.
MARKETPLACE_API_URL = os.environ.get(
    "MYAPPS_MARKETPLACE_API_URL", "https://api.marketplace.rodolphe-augusto.fr"
)
