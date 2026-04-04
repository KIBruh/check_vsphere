from monplugin import Range

from checkvsphere.vcmd.datastores import Space, range_in_bytes


def test_space_calculates_usage_and_unit_conversion():
    gib = 2**30
    space = Space(capacity=10 * gib, free=5 * gib)

    assert space["usage"] == 50.0
    assert space["used_GB"] == 5.0
    assert space["free_GB"] == 5.0
    assert space["capacity_GB"] == 10.0


def test_range_in_bytes_converts_given_unit():
    converted = range_in_bytes(Range("1:2"), "GB")
    assert converted == "1073741824.0:2147483648.0"


def test_range_in_bytes_preserves_inclusive_prefix():
    converted = range_in_bytes(Range("@1:2"), "MB")
    assert converted.startswith("@")
