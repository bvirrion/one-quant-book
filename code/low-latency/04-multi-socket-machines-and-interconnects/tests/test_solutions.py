"""Numbers gate, Book 13 chapter 4."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_topo as t  # noqa: E402

cp = t.cp
FIX = t.ROOT / "code/firm/coreplan/data/two_socket"


def test_arithmetic():
    assert round(t.pcie_gbytes(32, 16)) == 63 and 100 / 8 == 12.5          # dated box
    assert round(t.pcie_gbytes(16, 8), 2) == 15.75 and 2 * 25 / 8 == 6.25  # exercise 1
    assert -(-300 // 64) == 5                                              # exercise 2
    assert t.remote_penalty(3, 1) == 316 and t.remote_penalty() == 316     # exercise 3, proposition
    assert round(100 * 316 / 2500, 1) == 12.6                              # problem 6
    assert (2 * 59, 2 * 138) == (118, 276)                                 # problem 9


def test_fixture_plan():
    topo = cp.read_topology(FIX)
    assert topo.nodes[1] == tuple(range(16, 32)) and topo.cpus[17].siblings == (17, 25)
    p = cp.plan(topo, "ens1f0")
    assert (p.roles["feed"], p.roles["strategy"], p.roles["gateway"]) == (21, 22, 23) and p.idle == (29, 30, 31)
    assert cp.check(p, topo) == []


def test_measured_matrix():
    fast, fmed, smed = t.classes()
    neighbours = {(i, i + 1) for i in range(21)}
    assert neighbours <= set(fast)                                         # every neighbouring pair is fast
    assert round(fmed, -1) == 40 and 170 <= smed <= 200 and round(smed, -1) == 190  # about 40, 170-200, 190
    assert 4.0 <= smed / fmed <= 5.0                                       # four to five times slower
    assert round(t.c2c()[(0, 1)], -1) == 40
