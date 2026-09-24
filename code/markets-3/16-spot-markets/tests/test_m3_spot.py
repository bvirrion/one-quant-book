"""Tests of the Chapter 16 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_spot as m


def test_counts_fall_with_fees():
    assert m.count_opportunities(0.0) == (1254, 2953)
    assert m.count_opportunities(0.001) == (26, 120)


def test_p_loss():
    assert round(100 * m.p_loss(100, 20, 30, 0.6), 1) == 3.9
    assert round(100 * m.p_loss(50, 20, 60, 0.6)) == 32


def test_wash_tests():
    g, x = m.genuine_tape(20_000), m.mixed_tape(20_000, 0.7)
    assert m.benford_chi2(g) < 15.5 < m.benford_chi2(x)
    assert m.clustering_ratio(g) > 40 > 5 > m.clustering_ratio(m.wash_tape(20_000))
    bench = m.genuine_tape(20_000, seed=99)
    assert abs(m.wash_share_estimate(x, bench) - 0.7) < 0.03


def test_kimchi():
    assert round(100 * m.kimchi_breakeven(), 2) == 4.03
    assert round(100 * m.kimchi_breakeven(repatriation=0), 2) == 1.95
