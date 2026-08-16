"""Only the pure response-parsing half (parse_latest_version) is unit
tested - PluginMarketplaceClient itself issues real QNetworkAccessManager
requests, which these tests deliberately never do (no real network calls
in the test suite, matching test_update_checker.py's own reasoning).
"""

from myapps.core.plugin_marketplace_client import parse_latest_version


def test_returns_new_version_when_marketplace_has_a_newer_one():
    raw = b'{"version": "0.2.0"}'
    assert parse_latest_version(raw, "0.1.2") == "0.2.0"


def test_returns_none_when_marketplace_version_is_the_current_one():
    raw = b'{"version": "0.1.2"}'
    assert parse_latest_version(raw, "0.1.2") is None


def test_returns_none_when_marketplace_version_is_older():
    raw = b'{"version": "0.1.0"}'
    assert parse_latest_version(raw, "0.1.2") is None


def test_returns_none_on_malformed_json():
    assert parse_latest_version(b"not json at all", "0.1.2") is None


def test_returns_none_when_version_field_is_missing():
    assert parse_latest_version(b"{}", "0.1.2") is None


def test_returns_none_when_version_field_is_not_a_string():
    assert parse_latest_version(b'{"version": 2}', "0.1.2") is None


def test_returns_none_when_version_field_is_empty():
    assert parse_latest_version(b'{"version": ""}', "0.1.2") is None


def test_returns_none_on_invalid_utf8():
    assert parse_latest_version(b"\xff\xfe not utf-8", "0.1.2") is None
