import types

import pytest
from monplugin import Check, Status, Threshold

from checkvsphere.vcmd import vmguestfs


def _set_args(metric="usage", warning=None, critical=None, allowed=None, banned=None):
    vmguestfs.args = types.SimpleNamespace(
        metric=metric,
        warning=warning,
        critical=critical,
        allowed=allowed or [],
        banned=banned or [],
        match_method="search",
    )


def _disk(path, capacity, free):
    return types.SimpleNamespace(diskPath=path, capacity=capacity, freeSpace=free)


def test_fs_info_critical_on_usage_threshold(capsys):
    _set_args(metric="usage", warning="10", critical="20")
    check = Check(threshold=Threshold("10", "20"))

    with pytest.raises(SystemExit) as exc:
        vmguestfs.fs_info(check, [_disk("/", 100, 70)])

    assert exc.value.code == Status.CRITICAL.value
    out = capsys.readouterr().out
    assert "CRITICAL:" in out
    assert "usage on / is in state CRITICAL" in out


def test_fs_info_warning_on_free_gb_threshold_with_converted_ranges(capsys):
    gib = 2 ** 30
    _set_args(metric="free_GB", warning="5:", critical="2:")
    check = Check(threshold=Threshold("5:", "2:"))

    with pytest.raises(SystemExit) as exc:
        vmguestfs.fs_info(check, [_disk("/", 20 * gib, 3 * gib)])

    assert exc.value.code == Status.WARNING.value
    out = capsys.readouterr().out
    assert "free_GB on / is in state WARNING" in out
    assert "5368709120.0:" in out
    assert "2147483648.0:" in out


def test_fs_info_warns_when_all_filesystems_are_filtered(capsys):
    _set_args(metric="usage", allowed=["^/var$"])
    check = Check(threshold=Threshold(None, None))

    with pytest.raises(SystemExit) as exc:
        vmguestfs.fs_info(check, [_disk("/", 100, 80)])

    assert exc.value.code == Status.WARNING.value
    assert "WARNING: no filesystems found" in capsys.readouterr().out


def test_fs_info_critical_when_capacity_is_zero(capsys):
    _set_args(metric="usage")
    check = Check(threshold=Threshold(None, None))

    with pytest.raises(SystemExit) as exc:
        vmguestfs.fs_info(check, [_disk("/zero", 0, 0)])

    assert exc.value.code == Status.CRITICAL.value
    assert "/zero has a capacity of zero" in capsys.readouterr().out


class DummyParser:
    def __init__(self, args):
        self._args = args

    def add_required_arguments(self, *args):
        return None

    def add_optional_arguments(self, *args):
        return None

    def get_args(self):
        return self._args


def test_run_unknown_vm_exits_unknown(monkeypatch, capsys):
    args = types.SimpleNamespace(
        vm_name="missing-vm",
        warning=None,
        critical=None,
        metric="usage",
        allowed=[],
        banned=[],
        match_method="search",
    )
    fake_si = types.SimpleNamespace(content=types.SimpleNamespace(rootFolder=object()))

    monkeypatch.setattr(vmguestfs.cli, "Parser", lambda: DummyParser(args))
    monkeypatch.setattr(vmguestfs.service_instance, "connect", lambda _args: fake_si)
    monkeypatch.setattr(vmguestfs, "find_entity_views", lambda *a, **k: [])

    with pytest.raises(SystemExit) as exc:
        vmguestfs.run()

    assert exc.value.code == Status.UNKNOWN.value
    assert "vm missing-vm not found" in capsys.readouterr().out


def test_run_unknown_when_guest_filesystem_data_missing(monkeypatch, capsys):
    args = types.SimpleNamespace(
        vm_name="vm-a",
        warning=None,
        critical=None,
        metric="usage",
        allowed=[],
        banned=[],
        match_method="search",
    )
    fake_si = types.SimpleNamespace(content=types.SimpleNamespace(rootFolder=object()))
    vm_data = [{"props": {"name": "vm-a", "guest": None}}]

    monkeypatch.setattr(vmguestfs.cli, "Parser", lambda: DummyParser(args))
    monkeypatch.setattr(vmguestfs.service_instance, "connect", lambda _args: fake_si)
    monkeypatch.setattr(vmguestfs, "find_entity_views", lambda *a, **k: vm_data)

    with pytest.raises(SystemExit) as exc:
        vmguestfs.run()

    assert exc.value.code == Status.UNKNOWN.value
    assert "guest filesystem data for vm-a is unavailable" in capsys.readouterr().out
