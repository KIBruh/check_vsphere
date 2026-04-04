import types

import pytest

from checkvsphere import VsphereConnectException
from checkvsphere.tools import service_instance


def _args(sessionfile=None):
    return types.SimpleNamespace(
        host="127.0.0.1",
        port=443,
        password="pass",
        user="user",
        disable_ssl_verification=True,
        sessionfile=sessionfile,
    )


def test_connect_retries_without_session_id(monkeypatch):
    calls = []
    fake_service_instance = object()

    def fake_smart_connect(**kwargs):
        calls.append(dict(kwargs))
        if "sessionId" in kwargs:
            raise RuntimeError("session expired")
        return fake_service_instance

    written = []

    monkeypatch.setattr(service_instance, "SmartConnect", fake_smart_connect)
    monkeypatch.setattr(service_instance, "read_session_id", lambda _path: "stale")
    monkeypatch.setattr(
        service_instance,
        "write_session_id",
        lambda si, path: written.append((si, path)),
    )

    args = _args(sessionfile="/tmp/session.txt")
    result = service_instance.connect(args)

    assert result is fake_service_instance
    assert len(calls) == 2
    assert "sessionId" in calls[0]
    assert "sessionId" not in calls[1]
    assert written == [(fake_service_instance, "/tmp/session.txt")]


def test_connect_raises_wrapped_exception_when_connect_nofail_is_set(monkeypatch):
    def always_fail(**_kwargs):
        raise RuntimeError("connect failed")

    monkeypatch.setenv("CONNECT_NOFAIL", "1")
    monkeypatch.setattr(service_instance, "SmartConnect", always_fail)

    with pytest.raises(VsphereConnectException) as exc:
        service_instance.connect(_args())

    assert "cannot connect" in str(exc.value)
    assert isinstance(exc.value.__cause__, RuntimeError)
