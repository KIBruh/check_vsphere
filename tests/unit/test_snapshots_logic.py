import types

from checkvsphere.vcmd import snapshots


class SnapshotNode:
    def __init__(self, name, children=None):
        self.name = name
        self.childSnapshotList = children or []


def test_count_snapshots_counts_recursive_tree(monkeypatch):
    monkeypatch.setattr(
        snapshots,
        "args",
        types.SimpleNamespace(banned=[], allowed=[], match_method="search"),
    )
    vm = {"props": {"name": "vm-a"}}

    tree = [
        SnapshotNode(
            "root",
            [
                SnapshotNode("child-1"),
                SnapshotNode("child-2", [SnapshotNode("leaf")]),
            ],
        )
    ]

    assert snapshots.count_snapshots(vm, tree) == 4


def test_count_snapshots_respects_banned_patterns(monkeypatch):
    monkeypatch.setattr(
        snapshots,
        "args",
        types.SimpleNamespace(
            banned=["child-2", "leaf"],
            allowed=[],
            match_method="search",
        ),
    )
    vm = {"props": {"name": "vm-a"}}

    tree = [
        SnapshotNode(
            "root",
            [
                SnapshotNode("child-1"),
                SnapshotNode("child-2", [SnapshotNode("leaf")]),
            ],
        )
    ]

    assert snapshots.count_snapshots(vm, tree) == 2


def test_count_snapshots_respects_allowed_patterns(monkeypatch):
    monkeypatch.setattr(
        snapshots,
        "args",
        types.SimpleNamespace(
            banned=[],
            allowed=["^vm-a;root$"],
            match_method="search",
        ),
    )
    vm = {"props": {"name": "vm-a"}}

    tree = [
        SnapshotNode(
            "root",
            [
                SnapshotNode("child-1"),
                SnapshotNode("child-2", [SnapshotNode("leaf")]),
            ],
        )
    ]

    assert snapshots.count_snapshots(vm, tree) == 1
