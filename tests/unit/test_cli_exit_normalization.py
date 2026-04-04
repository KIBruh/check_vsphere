import pytest

from checkvsphere import cli


def test_main_normalizes_invalid_system_exit_code(monkeypatch):
    def fake_run():
        raise SystemExit(9)

    monkeypatch.setattr(cli, "run", fake_run)

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 3
