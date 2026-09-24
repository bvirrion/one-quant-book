"""Tests of the Chapter 15 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_cex as m


def test_inclusion_proofs_verify_and_detect_tampering():
    leaves = [m.leaf(f"a{i}", f"n{i}", b) for i, b in enumerate([30, 5, 40, 15])]
    levels = m.build(leaves)
    root = levels[-1][0]
    assert root[1] == 90
    for i in range(4):
        assert m.verify(leaves[i], m.proof(levels, i), root)
    assert not m.verify(m.leaf("a3", "n3", 16), m.proof(levels, 3), root)


def test_odd_number_of_leaves():
    leaves = [m.leaf(f"a{i}", f"n{i}", i + 1) for i in range(5)]
    levels = m.build(leaves)
    assert levels[-1][0][1] == 15
    assert all(m.verify(leaves[i], m.proof(levels, i), levels[-1][0]) for i in range(5))


def test_negative_leaf_counterexample():
    b = m.customers()
    total, published, hash_only, with_sums = m.fake_negative(b, 0.6, 0)
    assert len(b) == 1023 and hash_only == 1023 and with_sums == 0
    assert published == total - int(0.6 * total)
    assert m.fake_negative(b, 0.02, 0)[3] == 1008


def test_ftx_and_fees():
    c = m.ftx_coverage()
    assert round(100 * c["located_A"], 1) == 6.6 and round(100 * c["with_receivables_A"], 1) == 10.2
    assert round(100 * c["all_assets"], 1) == 22.6
    assert m.round_trip_bp(40, 80, 0) == 160 and m.round_trip_bp(1.1, 2.3, 2) == 2.2


def test_burst():
    r = m.burst()
    assert max(x[2] for x in r) == 900 and max(x[3] for x in r) == 89
    assert max(x[2] for x in m.burst(coalesce=True)) == 0
