import types

from checkvsphere.tools import helper


def test_isallowed_uses_search_by_default():
    args = types.SimpleNamespace(allowed=["vm"], banned=[])

    assert helper.isallowed(args, "prefix-vm-suffix")


def test_isallowed_respects_match_method_match():
    args = types.SimpleNamespace(allowed=["vm"], banned=[], match_method="match")

    assert helper.isallowed(args, "vm-01")
    assert not helper.isallowed(args, "prefix-vm")


def test_isallowed_respects_match_method_fullmatch():
    args = types.SimpleNamespace(allowed=["vm"], banned=[], match_method="fullmatch")

    assert helper.isallowed(args, "vm")
    assert not helper.isallowed(args, "vm-01")


def test_isbanned_respects_match_methods():
    args = types.SimpleNamespace(allowed=[], banned=["vm"], match_method="fullmatch")

    assert helper.isbanned(args, "vm")
    assert not helper.isbanned(args, "prod-vm")


def test_isallowed_without_patterns_returns_true():
    args = types.SimpleNamespace(banned=[], match_method="search")

    assert helper.isallowed(args, "anything")
