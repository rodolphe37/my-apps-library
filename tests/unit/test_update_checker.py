"""Only the pure response-parsing half (parse_latest_version) is unit
tested - UpdateChecker.check() itself issues a real QNetworkAccessManager
request, which these tests deliberately never do (no real network calls in
the test suite, matching the rest of this project's offline-first tests).
"""

from myapps.core.update_checker import parse_latest_version


def test_returns_new_version_when_release_is_newer():
    raw = b'{"tag_name": "v0.7.0"}'
    assert parse_latest_version(raw, "0.6.1") == "0.7.0"


def test_returns_none_when_release_is_the_current_version():
    raw = b'{"tag_name": "v0.6.1"}'
    assert parse_latest_version(raw, "0.6.1") is None


def test_returns_none_when_release_is_older():
    raw = b'{"tag_name": "v0.5.0"}'
    assert parse_latest_version(raw, "0.6.1") is None


def test_returns_none_on_malformed_json():
    assert parse_latest_version(b"not json at all", "0.6.1") is None


def test_returns_none_when_tag_name_is_missing():
    assert parse_latest_version(b"{}", "0.6.1") is None


def test_returns_none_on_invalid_utf8():
    assert parse_latest_version(b"\xff\xfe not utf-8", "0.6.1") is None


def test_strips_leading_v_from_tag_name():
    raw = b'{"tag_name": "v1.0.0"}'
    assert parse_latest_version(raw, "0.9.0") == "1.0.0"
