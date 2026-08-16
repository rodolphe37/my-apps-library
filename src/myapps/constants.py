"""App-wide constants."""

import os

APP_NAME = "MyAppsLibrary"
APP_ID = "myapps"
ORG_NAME = "MyAppsLibrary"
VERSION = "0.8.0"

# Bumped whenever the on-disk JSON schema changes in a way that requires migration.
SCHEMA_VERSION = 1

DEFAULT_VIEW_MODE = "list"
UNCATEGORIZED_ID = "__uncategorized__"

# The marketplace is now live at marketplace.rodolphe-augusto.fr. Still read
# from MYAPPS_MARKETPLACE_URL rather than hardcoding that domain - keeps
# local dev pointed at `npm run dev`'s localhost:5173 by default, and
# packaging/CI free to override without a code change either way.
MARKETPLACE_URL = os.environ.get("MYAPPS_MARKETPLACE_URL", "https://marketplace.rodolphe-augusto.fr")
