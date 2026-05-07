import types

from monplugin import Status

from checkvsphere.vcmd import vsan


class ExplodingClusterMoref:
    @property
    def name(self):
        raise AssertionError("unexpected remote name fetch")


class FakeCheck:
    def __init__(self):
        self.messages = []

    def add_message(self, status, message):
        self.messages.append((status, message))

    def check_messages(self, separator='\n', separator_all='\n', **opts):
        return (Status.OK, separator.join(message for _, message in self.messages))

    def exit(self, status, message):
        raise SystemExit((status, message))


def test_check_healthtest_uses_prefetched_cluster_name(monkeypatch):
    monkeypatch.setattr(vsan, "args", types.SimpleNamespace(
        banned=[],
        allowed=[],
        exclude_group=[],
        include_group=[],
        exclude_test=[],
        include_test=[],
        match_method="search",
        verbose=0,
    ))

    check = FakeCheck()
    clusters = [{
        "name": "cluster-a",
        "moref": ExplodingClusterMoref(),
        "healthSummary": types.SimpleNamespace(
            vsanConfig=types.SimpleNamespace(vsanEnabled=True),
            groups=[
                types.SimpleNamespace(
                    groupName="group-a",
                    groupTests=[
                        types.SimpleNamespace(
                            testHealth="green",
                            testName="test-a",
                        )
                    ],
                )
            ],
        ),
    }]

    try:
        vsan.check_healthtest(check, clusters)
    except SystemExit as exc:
        status, message = exc.code
    else:
        raise AssertionError("expected check_healthtest to exit")

    assert status == Status.OK
    assert "Cluster: cluster-a" in message
