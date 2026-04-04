import pytest


pytestmark = pytest.mark.integration


def _get_host_paths(run_govc):
    result = run_govc(["find", "-type", "h"])
    assert result.returncode == 0, result.stdout + result.stderr

    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert paths, "no host paths returned by govc find -type h"
    return paths


def test_about_command_works_with_vcsim(run_cli, cli_connection_args):
    result = run_cli(["about"] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    assert "govmomi simulator" in result.stdout


def test_datastores_command_works_with_vcsim(run_cli, cli_connection_args):
    result = run_cli(["datastores"] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    assert "everything ok" in result.stdout
    assert "|" in result.stdout


def test_power_state_command_works_with_vcsim(run_cli, cli_connection_args):
    result = run_cli(["power-state"] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    assert "hosts" in result.stdout


def test_snapshots_threshold_with_created_snapshot(
    run_cli, run_govc, cli_connection_args
):
    snapshot_name = "pytest-snap"
    create_result = run_govc(["snapshot.create", "-vm", "DC0_H0_VM0", snapshot_name])
    assert create_result.returncode == 0, create_result.stdout + create_result.stderr

    result = run_cli(
        [
            "snapshots",
            "--mode",
            "count",
            "--warning",
            "0",
        ]
        + cli_connection_args
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "WARNING:" in result.stdout
    assert "snapshots" in result.stdout


def test_host_runtime_maintenance_changes_state(run_cli, run_govc, cli_connection_args):
    host_paths = _get_host_paths(run_govc)
    host_path = host_paths[0]
    host_name = host_path.rsplit("/", 1)[-1]

    initial_result = run_cli(
        [
            "host-runtime",
            "--mode",
            "maintenance",
            "--vihost",
            host_name,
        ]
        + cli_connection_args
    )
    assert initial_result.returncode == 0, initial_result.stdout + initial_result.stderr
    assert "OK:" in initial_result.stdout
    assert "Host is not in maintenance" in initial_result.stdout

    enter_maintenance_result = run_govc(["host.maintenance.enter", host_path])
    assert (
        enter_maintenance_result.returncode == 0
    ), enter_maintenance_result.stdout + enter_maintenance_result.stderr

    result = run_cli(
        [
            "host-runtime",
            "--mode",
            "maintenance",
            "--vihost",
            host_name,
        ]
        + cli_connection_args
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert "CRITICAL:" in result.stdout
    assert "is in maintenance" in result.stdout


def test_host_runtime_con_changes_state_when_disconnected(
    run_cli, run_govc, cli_connection_args
):
    host_paths = _get_host_paths(run_govc)
    if len(host_paths) < 2:
        pytest.skip("need at least two hosts to test disconnect separately")

    host_path = host_paths[1]
    host_name = host_path.rsplit("/", 1)[-1]

    initial_result = run_cli(
        [
            "host-runtime",
            "--mode",
            "con",
            "--vihost",
            host_name,
        ]
        + cli_connection_args
    )
    assert initial_result.returncode == 0, initial_result.stdout + initial_result.stderr
    assert "OK:" in initial_result.stdout
    assert "connection state is 'connected'" in initial_result.stdout

    disconnect_result = run_govc(["host.disconnect", host_path])
    assert disconnect_result.returncode == 0, disconnect_result.stdout + disconnect_result.stderr

    result = run_cli(
        [
            "host-runtime",
            "--mode",
            "con",
            "--vihost",
            host_name,
        ]
        + cli_connection_args
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "WARNING:" in result.stdout
    assert "connection state is 'disconnected'" in result.stdout
