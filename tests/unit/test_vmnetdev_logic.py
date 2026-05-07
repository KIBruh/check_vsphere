import types

from monplugin import Status

from checkvsphere.vcmd import vmnetdev


class VirtualEthernetCardBackingInfo:
    pass


class VirtualDiskBackingInfo:
    pass


class FakeCheck:
    def __init__(self):
        self.messages = []

    def add_message(self, status, message):
        self.messages.append((status, message))


def _vm_with_devices(name, devices):
    return {
        "props": {
            "name": name,
            "config.hardware": types.SimpleNamespace(device=devices),
        }
    }


def _eth_device(label, connected, start_connected):
    return types.SimpleNamespace(
        backing=VirtualEthernetCardBackingInfo(),
        deviceInfo=types.SimpleNamespace(label=label),
        connectable=types.SimpleNamespace(
            connected=connected,
            startConnected=start_connected,
        ),
    )


def _disk_device(label):
    return types.SimpleNamespace(
        backing=VirtualDiskBackingInfo(),
        deviceInfo=types.SimpleNamespace(label=label),
        connectable=types.SimpleNamespace(
            connected=True,
            startConnected=True,
        ),
    )


def test_check_start_not_connected_reports_critical(monkeypatch):
    fake_check = FakeCheck()
    monkeypatch.setattr(vmnetdev, "check", fake_check)
    monkeypatch.setattr(
        vmnetdev,
        "args",
        types.SimpleNamespace(allowed=[], banned=[], match_method="search"),
    )

    vm = _vm_with_devices(
        "vm-a",
        [
            _eth_device("Network adapter 1", connected=True, start_connected=False),
            _disk_device("Hard disk 1"),
        ],
    )

    vmnetdev.check_start_not_connected(vm)

    assert len(fake_check.messages) == 1
    assert fake_check.messages[0][0] == Status.CRITICAL
    assert "Connect At Power On is off" in fake_check.messages[0][1]


def test_check_start_not_connected_ignores_disconnected_nics(monkeypatch):
    fake_check = FakeCheck()
    monkeypatch.setattr(vmnetdev, "check", fake_check)
    monkeypatch.setattr(
        vmnetdev,
        "args",
        types.SimpleNamespace(allowed=[], banned=[], match_method="search"),
    )

    vm = _vm_with_devices(
        "vm-a",
        [
            _eth_device("Network adapter 1", connected=False, start_connected=False),
        ],
    )

    vmnetdev.check_start_not_connected(vm)

    assert fake_check.messages == []
