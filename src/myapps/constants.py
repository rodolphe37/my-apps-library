"""App-wide constants."""

import os

APP_NAME = "MyAppsLibrary"
APP_ID = "myapps"
ORG_NAME = "MyAppsLibrary"
VERSION = "0.5.1"

# Bumped whenever the on-disk JSON schema changes in a way that requires migration.
SCHEMA_VERSION = 1

DEFAULT_VIEW_MODE = "list"
UNCATEGORIZED_ID = "__uncategorized__"

# The marketplace web app isn't deployed anywhere public yet (it currently
# only runs locally via `npm run dev`, see the marketplace repo's own
# README) and its final production domain isn't decided. Rather than bake
# in a guessed domain, this reads MYAPPS_MARKETPLACE_URL from the
# environment — packaging/CI can set it to the real URL once one exists —
# and falls back to the local dev server address, matching how the
# marketplace's own frontend points at its backend via VITE_API_BASE_URL.
MARKETPLACE_URL = os.environ.get("MYAPPS_MARKETPLACE_URL", "http://localhost:5173")
