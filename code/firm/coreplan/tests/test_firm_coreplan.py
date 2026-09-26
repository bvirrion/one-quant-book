import dataclasses
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_coreplan as cp

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


def test_cpulist():
    assert cp.parse_cpulist("0-3,8,10-11\n") == [0, 1, 2, 3, 8, 10, 11]


def test_two_socket_topology_and_plan():
    t = cp.read_topology(DATA / "two_socket")
    assert len(t.cpus) == 32 and sorted(t.nodes) == [0, 1] and len(t.nodes[1]) == 16
    assert t.cpus[17].siblings == (17, 25) and t.cpus[17].node == 1
    card = t.card_for("ens1f0")
    assert card.node == 1 and card.local_cpus == tuple(range(16, 32))
    p = cp.plan(t, "ens1f0")
    assert p.node == 1 and all(t.cpus[p.roles[r]].node == 1 for r in ("feed", "strategy", "gateway"))
    assert cp.check(p, t) == []
    assert set(p.idle) == {t.cpus[p.roles[r]].siblings[1] for r in ("feed", "strategy", "gateway")}
    assert 0 in p.housekeeping and p.roles["logger"] in p.housekeeping


def test_check_catches_bad_plans():
    t = cp.read_topology(DATA / "two_socket")
    p = cp.plan(t, "ens1f0")
    wrong_socket = dataclasses.replace(p, roles={**p.roles, "strategy": 5})
    assert any("node 0" in e for e in cp.check(wrong_socket, t))
    shared = dataclasses.replace(p, roles={**p.roles, "gateway": t.cpus[p.roles["feed"]].siblings[1]})
    assert any("shares a physical core" in e for e in cp.check(shared, t))


def test_unknown_node_and_penalty():
    t = cp.read_topology(DATA / "one_node")
    p = cp.plan(t, "eth0")
    assert p.node == 0 and cp.check(p, t) == []
    assert cp.remote_penalty_ns(2, 2, 59, 138) == 316
    t2 = cp.read_topology(DATA / "two_socket")
    assert t2.card_for("nosuch").node == -1 and cp.plan(t2, "nosuch").node == 0


def test_plan_file_round_trip(tmp_path):
    t = cp.read_topology(DATA / "two_socket")
    p = cp.plan(t, "ens1f0")
    cp.write_plan(p, tmp_path / "plan.txt")
    assert cp.read_plan(tmp_path / "plan.txt") == p.roles
