from myapps.utils.version_utils import is_newer, parse_version


def test_parse_version_basic():
    assert parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_non_numeric_segment_compares_as_zero():
    assert parse_version("1.2.rc1") == (1, 2, 0)


def test_parse_version_orders_correctly():
    assert parse_version("0.1.0") < parse_version("0.2.0")
    assert parse_version("1.0") < parse_version("1.0.1")


def test_is_newer_true_for_a_higher_version():
    assert is_newer("0.6.1", "0.6.0") is True


def test_is_newer_false_for_the_same_version():
    assert is_newer("0.6.0", "0.6.0") is False


def test_is_newer_false_for_an_older_version():
    assert is_newer("0.5.9", "0.6.0") is False


def test_is_newer_handles_different_segment_counts():
    assert is_newer("0.6.0.1", "0.6.0") is True
    assert is_newer("1.0", "1.0.1") is False
