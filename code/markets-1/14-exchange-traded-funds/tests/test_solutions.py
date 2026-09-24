"""Numbers gate: every numerical answer printed in the Chapter 14 text and solutions."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from etf_demo import ArbCosts, decay_factor, leveraged_path, premium_bp, rebalance_trade, simulate_premium, stale_nav


def test_text():
    assert ArbCosts(4.0, 1.5, 1.0, 0.5).band_bp == 7.0 and round(50 * 7e-4, 3) == 0.035
    assert [rebalance_trade(b, 1.0, 1.0) for b in (3, -1, -3)] == [6.0, 2.0, 12.0]
    assert rebalance_trade(3, 10.0, 0.05) == pytest.approx(3.0)
    assert round(decay_factor(3, 0.3, 1), 2) == 0.76 and round(decay_factor(-1, 0.3, 1), 2) == 0.91
    rng = np.random.default_rng(142)
    r = rng.normal(0.0, 0.02, 252)
    r -= r.mean()
    idx, l3 = np.cumprod(1 + r)[-1], leveraged_path(r, 3.0)[-1]
    assert round((idx - 1) * 100, 1) == -5.8 and round(3 * (idx - 1) * 100, 1) == -17.4
    assert round((l3 - 1) * 100, 1) == -41.8


def test_exercises():
    assert round(premium_bp(82.31, 82.40), 1) == -10.9
    assert 500 / (50_000 * 40) * 1e4 == pytest.approx(2.5)
    assert rebalance_trade(-2, 800, -0.04) == pytest.approx(-192.0) and 800 * 1.08 == pytest.approx(864.0)
    two = [round(((1 + b * 0.10) * (1 - b * 0.0909) - 1) * 100, 2) for b in (2, 3, -1)]
    assert two == [-1.82, -5.45, -1.82]
    assert [round(decay_factor(b, 0.4, 1), 3) for b in (2, 3, -2)] == [0.852, 0.619, 0.619]
    assert round(-math.log(0.9) / (0.5 * 6 * 0.16) * 252) == 55
    true = np.array([100.0] + [94.0] * 14)
    nav = stale_nav(true, 0.8)
    disc = (true / nav - 1) * 100
    assert [round(x, 2) for x in nav[1:5]] == [98.8, 97.84, 97.07, 96.46]
    assert [round(x, 2) for x in disc[1:5]] == [-4.86, -3.92, -3.16, -2.55]
    assert disc[11] < -0.5 < disc[12]                      # eleven days after the day of the fall
    out = []
    for cb in (4.0, 2.0):
        c = ArbCosts(cb, 1.5, 1.0, 0.5)
        p, _ = simulate_premium(c, 5000, 1)
        out.append((int(np.isclose(np.abs(p), c.band_bp / 2).sum()), round(float(np.abs(p).mean()), 2)))
    assert out == [(1638, 3.28), (2219, 2.42)]


def test_problem():
    vol10 = 30.0
    for r, sig, navs, trades, frac, imp_bp in (
        (0.01, 0.01, (8.24, 2.91), (0.48, 0.36), 0.028, 1.9),
        (-0.05, 0.03, (6.8, 3.45), (-2.4, -1.8), 0.14, 12.6),
    ):
        assert (8 * (1 + 3 * r), 3 * (1 - 3 * r)) == pytest.approx(navs)
        t = (rebalance_trade(3, 8, r), rebalance_trade(-3, 3, r))
        assert t == pytest.approx(trades)
        assert abs(sum(t)) / vol10 == pytest.approx(frac)
        impact = 0.7 * sig * math.sqrt(10 / 390) * math.sqrt(abs(sum(t)) / vol10)
        assert round(impact * 1e4, 1) == imp_bp
    x = 0.7 * 0.03 * math.sqrt(10 / 390) * math.sqrt(0.14)
    assert round((6 * 8 + 12 * 3) * x, 2) == 0.11 and round((6 * 8 + 12 * 3) * x / 4.2 * 100, 1) == 2.5
    rs = [-0.05, 0.04, -0.06, 0.05, 0.025]
    i = math.prod(1 + v for v in rs) - 1
    up = math.prod(1 + 3 * v for v in rs) - 1
    dn = math.prod(1 - 3 * v for v in rs) - 1
    assert [round(v * 100, 2) for v in (i, up, 3 * i, dn, -3 * i, (up + dn) / 2)] == [-0.05, -3.49, -0.14, -6.11, 0.14, -4.80]
    assert round(1 / 3 * 100, 1) == 33.3
    assert round(1.21 * decay_factor(2, 0.2, 1), 3) == 1.163      # interview question 2
