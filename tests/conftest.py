"""Global test fixtures.

Autouse, session-wide: no test should ever make a real network call
through PluginMarketplaceClient - constructing a PluginManagerDialog
triggers one automatically (its own marketplace update check), so without
this every test that builds one would fire a real HTTP request. Matches
this project's existing "tests never touch the real network" rule (see
core/update_checker.py / test_update_checker.py's own docstring, which
only unit-tests the pure response-parsing half for the same reason).

A test that wants to exercise the update-available/download flow does so
by calling the dialog's own signal handlers directly (_on_update_available,
_on_download_finished, ...), simulating what PluginMarketplaceClient would
have emitted, rather than needing a real HTTP round trip.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _no_real_plugin_marketplace_requests(monkeypatch):
    from myapps.core.plugin_marketplace_client import PluginMarketplaceClient

    monkeypatch.setattr(PluginMarketplaceClient, "check_for_update", lambda self, *a, **kw: None)
    monkeypatch.setattr(PluginMarketplaceClient, "download_update", lambda self, *a, **kw: None)
