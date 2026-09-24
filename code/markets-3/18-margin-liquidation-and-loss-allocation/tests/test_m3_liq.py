"""Tests of the Chapter 18 teaching module (Book 3), including the cascade's stability under a finer
time step and the ablation of each mechanism."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_liq as m

POP = m.population()


def test_population():
    assert len(POP) == 4_000 and all(p.liq < m.P0 for p in POP)
    assert round(sum(p.units * p.entry for p in POP) / 1e6, 1) == 166.6


def test_stable_under_finer_time_step():
    s = m.critical_shock(POP) + 1e-4
    coarse = m.cascade(POP, s)
    for batch in (100, 10, 1):
        fine = m.cascade(POP, s, batch=batch)
        assert abs(fine.price - coarse.price) < 1e-9 and fine.liquidated == coarse.liquidated
        assert abs(fine.fund_change - coarse.fund_change) < 1e-6 * max(1.0, abs(coarse.fund_change))


def test_threshold_and_ablations():
    s = m.critical_shock(POP)
    assert round(100 * s, 2) == 1.11
    assert 1 - m.cascade(POP, s - 1e-4).price / m.P0 < 0.10 <= 1 - m.cascade(POP, s + 1e-4).price / m.P0
    assert m.cascade(POP, 0.05, forced_selling=False).price == 95.0           # no forced selling: no cascade
    assert round(100 * m.critical_shock(m.population(max_leverage=10)), 2) == 5.37
    assert round(100 * m.critical_shock(POP, impact=0.6e-5), 2) == 5.55


def test_gap_loss():
    r = m.cascade(POP, 0.05)
    assert round(r.deficit / 1e6, 2) == 3.21 and round(r.price, 2) == 83.83
