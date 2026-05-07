import json
import re

import pytest


pytestmark = pytest.mark.integration


def _get_host_paths(run_govc):
    result = run_govc(["find", "-type", "h"])
    assert result.returncode == 0, result.stdout + result.stderr

    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert paths, "no host paths returned by govc find -type h"
    return paths


def _get_vm_paths(run_govc):
    result = run_govc(["find", "-type", "m"])
    assert result.returncode == 0, result.stdout + result.stderr

    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert paths, "no vm paths returned by govc find -type m"
    return paths


def _get_datastore_names(run_govc):
    result = run_govc(["find", "-type", "s"])
    assert result.returncode == 0, result.stdout + result.stderr

    names = [
        line.strip().rsplit("/", 1)[-1]
        for line in result.stdout.splitlines()
        if line.strip()
    ]
    assert names, "no datastore paths returned by govc find -type s"
    return names


def _get_vm_devices(run_govc, vm_path):
    result = run_govc(["device.ls", "-json", "-vm", vm_path])
    assert result.returncode == 0, result.stdout + result.stderr

    payload = json.loads(result.stdout)
    return payload.get("devices", [])


def _disconnect_removable_devices(run_govc, vm_path):
    devices = _get_vm_devices(run_govc, vm_path)

    for device in devices:
        if device.get("type") not in ("VirtualCdrom", "VirtualFloppy"):
            continue

        disconnect_result = run_govc(
            ["device.disconnect", "-vm", vm_path, device["name"]]
        )
        assert disconnect_result.returncode == 0, (
            disconnect_result.stdout + disconnect_result.stderr
        )


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


def test_datastores_warns_when_filter_matches_nothing(run_cli, cli_connection_args):
    result = run_cli([
        "datastores",
        "--allowed",
        "^definitely-not-a-datastore$",
    ] + cli_connection_args)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "WARNING:" in result.stdout
    assert "no datastores found" in result.stdout


def test_power_state_command_works_with_vcsim(run_cli, cli_connection_args):
    result = run_cli(["power-state"] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    assert "hosts" in result.stdout


def test_list_metrics_outputs_metric_identifiers(run_cli, cli_connection_args):
    result = run_cli(["list-metrics"] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert re.search(r"\b\d+\s+\w+:\w+:\w+", result.stdout)


def test_vm_tools_default_is_ok_on_vcsim(run_cli, cli_connection_args):
    result = run_cli(["vm-tools"] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    assert "VMs checked for VMware Tools state" in result.stdout


def test_vm_tools_not_installed_flag_can_escalate(run_cli, cli_connection_args):
    result = run_cli(["vm-tools", "--not-installed"] + cli_connection_args)

    assert result.returncode == 2, result.stdout + result.stderr
    assert "CRITICAL:" in result.stdout
    assert "tools not installed" in result.stdout


def test_vm_tools_vihost_filter_works_with_vcsim(
    run_cli, run_govc, cli_connection_args
):
    host_name = _get_host_paths(run_govc)[0].rsplit("/", 1)[-1]

    result = run_cli(["vm-tools", "--vihost", host_name] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    assert "VMs checked for VMware Tools state" in result.stdout


def test_vm_guestfs_unknown_vm_returns_unknown(run_cli, cli_connection_args):
    result = run_cli(
        ["vm-guestfs", "--vm-name", "definitely-missing-vm"] + cli_connection_args
    )

    assert result.returncode == 3, result.stdout + result.stderr
    assert "UNKNOWN:" in result.stdout
    assert "not found" in result.stdout


def test_vm_guestfs_existing_vm_returns_ok(run_cli, run_govc, cli_connection_args):
    vm_path = _get_vm_paths(run_govc)[0]
    vm_name = vm_path.rsplit("/", 1)[-1]
    result = run_cli(["vm-guestfs", "--vm-name", vm_name] + cli_connection_args)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout


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


def test_snapshots_age_threshold_with_created_snapshot(
    run_cli, run_govc, cli_connection_args
):
    vm_path = _get_vm_paths(run_govc)[0]
    vm_name = vm_path.rsplit("/", 1)[-1]
    snapshot_name = "pytest-snap-age"

    create_result = run_govc(["snapshot.create", "-vm", vm_path, snapshot_name])
    assert create_result.returncode == 0, create_result.stdout + create_result.stderr

    result = run_cli(
        [
            "snapshots",
            "--mode",
            "age",
            "--warning",
            "0",
            "--allowed",
            "^{};".format(re.escape(vm_name)),
        ]
        + cli_connection_args
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "WARNING:" in result.stdout
    assert "too old snapshots found" in result.stdout
    assert vm_name in result.stdout


def test_snapshots_vihost_filter_works_with_created_snapshot(
    run_cli, run_govc, cli_connection_args
):
    vm_path = _get_vm_paths(run_govc)[0]
    vm_name = vm_path.rsplit("/", 1)[-1]
    host_name = re.sub(r"_VM\d+$", "", vm_name)
    snapshot_name = "pytest-snap-host"

    create_result = run_govc(["snapshot.create", "-vm", vm_path, snapshot_name])
    assert create_result.returncode == 0, create_result.stdout + create_result.stderr

    result = run_cli(
        [
            "snapshots",
            "--mode",
            "count",
            "--warning",
            "0",
            "--vihost",
            host_name,
        ]
        + cli_connection_args
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "WARNING:" in result.stdout
    assert "snapshots" in result.stdout


def test_perf_host_maintenance_state_can_be_configured(
    run_cli, run_govc, cli_connection_args
):
    host_path = _get_host_paths(run_govc)[0]
    host_name = host_path.rsplit("/", 1)[-1]
    perf_args = [
        "perf",
        "--vimtype",
        "HostSystem",
        "--vimname",
        host_name,
        "--perfcounter",
        "cpu:usage:average",
        "--maintenance-state",
        "WARNING",
    ]

    baseline_result = run_cli(perf_args + cli_connection_args)
    assert baseline_result.returncode == 0, baseline_result.stdout + baseline_result.stderr
    assert "OK:" in baseline_result.stdout
    assert "Counter cpu:usage:average" in baseline_result.stdout

    maintenance_result = run_govc(["host.maintenance.enter", host_path])
    assert maintenance_result.returncode == 0, (
        maintenance_result.stdout + maintenance_result.stderr
    )

    degraded_result = run_cli(perf_args + cli_connection_args)
    assert degraded_result.returncode == 1, degraded_result.stdout + degraded_result.stderr
    assert "WARNING:" in degraded_result.stdout
    assert "is in maintenance" in degraded_result.stdout


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


def test_media_changes_state_with_cdrom_insert(
    run_cli, run_govc, cli_connection_args, tmp_path
):
    vm_path = _get_vm_paths(run_govc)[0]
    vm_name = vm_path.rsplit("/", 1)[-1]
    allowed_regex = "^{}$".format(re.escape(vm_name))

    _disconnect_removable_devices(run_govc, vm_path)

    baseline_result = run_cli(["media", "--allowed", allowed_regex] + cli_connection_args)
    assert baseline_result.returncode == 0, baseline_result.stdout + baseline_result.stderr
    assert "OK:" in baseline_result.stdout

    before_cdroms = {
        d["name"]
        for d in _get_vm_devices(run_govc, vm_path)
        if d.get("type") == "VirtualCdrom"
    }

    add_result = run_govc(["device.cdrom.add", "-vm", vm_path])
    assert add_result.returncode == 0, add_result.stdout + add_result.stderr

    after_cdroms = {
        d["name"]
        for d in _get_vm_devices(run_govc, vm_path)
        if d.get("type") == "VirtualCdrom"
    }

    new_cdroms = sorted(after_cdroms - before_cdroms)
    cdrom_name = new_cdroms[0] if new_cdroms else add_result.stdout.strip()
    assert cdrom_name, "unable to determine added cdrom device"

    eject_result = run_govc(["device.cdrom.eject", "-vm", vm_path, "-device", cdrom_name])
    assert eject_result.returncode == 0, eject_result.stdout + eject_result.stderr

    datastore_name = _get_datastore_names(run_govc)[0]
    iso_path = tmp_path / "pytest-media.iso"
    iso_path.write_bytes(b"pytest-media")

    upload_result = run_govc(
        [
            "datastore.upload",
            "-ds",
            datastore_name,
            str(iso_path),
            "pytest-media.iso",
        ]
    )
    assert upload_result.returncode == 0, upload_result.stdout + upload_result.stderr

    insert_result = run_govc(
        [
            "device.cdrom.insert",
            "-vm",
            vm_path,
            "-device",
            cdrom_name,
            "-ds",
            datastore_name,
            "pytest-media.iso",
        ]
    )
    assert insert_result.returncode == 0, insert_result.stdout + insert_result.stderr

    faulty_result = run_cli(["media", "--allowed", allowed_regex] + cli_connection_args)
    assert faulty_result.returncode == 2, faulty_result.stdout + faulty_result.stderr
    assert "CRITICAL:" in faulty_result.stdout
    assert vm_name in faulty_result.stdout

    cleanup_eject = run_govc(["device.cdrom.eject", "-vm", vm_path, "-device", cdrom_name])
    assert cleanup_eject.returncode == 0, cleanup_eject.stdout + cleanup_eject.stderr

    cleanup_disconnect = run_govc(
        ["device.disconnect", "-vm", vm_path, cdrom_name]
    )
    assert cleanup_disconnect.returncode == 0, (
        cleanup_disconnect.stdout + cleanup_disconnect.stderr
    )

    restored_result = run_cli(["media", "--allowed", allowed_regex] + cli_connection_args)
    assert restored_result.returncode == 0, restored_result.stdout + restored_result.stderr
    assert "OK:" in restored_result.stdout


def test_media_vihost_filter_works_with_vcsim(run_cli, run_govc, cli_connection_args):
    vm_path = _get_vm_paths(run_govc)[0]
    vm_name = vm_path.rsplit("/", 1)[-1]
    host_name = re.sub(r"_VM\d+$", "", vm_name)
    allowed_regex = "^{}$".format(re.escape(vm_name))

    _disconnect_removable_devices(run_govc, vm_path)

    result = run_cli(
        ["media", "--vihost", host_name, "--allowed", allowed_regex]
        + cli_connection_args
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
