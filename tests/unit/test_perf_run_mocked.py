import types

import pytest
from monplugin import Status

from checkvsphere.vcmd import perf


class DummyParser:
    def __init__(self, args):
        self._args = args

    def get_args(self):
        return self._args


def make_args(**overrides):
    defaults = {
        "warning": "10",
        "critical": None,
        "vimtype": "HostSystem",
        "vimname": "DC0_C0_H0",
        "perfcounter": "cpu:usage:average",
        "perfinstance": "",
        "interval": 20,
        "maintenance_state": "UNKNOWN",
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def setup_common_mocks(monkeypatch, args):
    monkeypatch.setattr(perf, "get_argparser", lambda: DummyParser(args))

    fake_si = types.SimpleNamespace(
        content=types.SimpleNamespace(perfManager=object(), rootFolder=object())
    )
    monkeypatch.setattr(perf.service_instance, "connect", lambda _args: fake_si)

    fake_obj = object()
    monkeypatch.setattr(
        perf,
        "find_entity_views",
        lambda *a, **k: [
            {"obj": types.SimpleNamespace(obj=fake_obj), "props": {"name": "host-1"}}
        ],
    )


def test_perf_run_can_be_tested_with_mocked_perf_data(monkeypatch, capsys):
    args = make_args(warning="10")
    setup_common_mocks(monkeypatch, args)

    counter = types.SimpleNamespace(
        unitInfo=types.SimpleNamespace(summary="percent", key="percent")
    )
    monkeypatch.setattr(perf, "get_metric", lambda *a, **k: (counter, object()))

    sample = types.SimpleNamespace(
        id=types.SimpleNamespace(instance=""),
        value=[2500],
    )
    monkeypatch.setattr(
        perf,
        "get_perf_values",
        lambda *a, **k: [types.SimpleNamespace(value=[sample])],
    )

    with pytest.raises(SystemExit) as exc:
        perf.run()

    assert exc.value.code == Status.WARNING.value
    output = capsys.readouterr().out
    assert "WARNING:" in output
    assert "cpu:usage:average" in output


def test_perf_run_raises_useful_error_when_metric_is_missing(monkeypatch):
    args = make_args()
    setup_common_mocks(monkeypatch, args)
    monkeypatch.setattr(perf, "get_metric", lambda *a, **k: (None, None))

    with pytest.raises(Exception) as exc:
        perf.run()

    assert "metric not found" in str(exc.value)


def test_get_counter_info_percent_conversion():
    counter = types.SimpleNamespace(
        unitInfo=types.SimpleNamespace(summary="percent", key="percent")
    )
    info = perf.get_counter_info(counter)

    assert info["factor"] == 0.01
    assert info["unit"] == "%"
    assert info["perfUnit"] == "%"
