import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "invmm"))
import firm_invmm as inv  # noqa: E402
import firm_multimm as mm  # noqa: E402


def test_stationary_is_the_long_horizon_limit():
    b, a = mm.stationary(140, 1.5, 0.5, 20)
    sol = inv.CJSolution(140, 1.5, 0.5, 0.0, 20, 20.0, 400)
    assert np.allclose(b[:-1], sol.bid[0, :-1], atol=1e-8) and np.allclose(a[1:], sol.ask[0, 1:], atol=1e-8)


def test_closed_form_close_when_penalty_small():
    qs = np.arange(-20, 21)
    b, _ = mm.stationary(140, 1.5, 0.5, 20)
    cb, _ = mm.asymptotic(140, 1.5, 0.5, qs)
    sel = np.abs(qs) <= 10
    assert np.max(np.abs(cb[sel] - b[sel])) < 0.05
    c = math.sqrt(0.5 * math.e / (140 * 1.5))
    assert math.isclose(cb[21] - cb[20], c)                     # the skew per unit is c


def test_drift_targets_a_position():
    b0, a0 = mm.stationary(140, 1.5, 0.5, 20)
    b1, a1 = mm.stationary(140, 1.5, 0.5, 20, mu=2.0)           # q0 = mu / (2 phi) = 2
    assert np.allclose(b1[20 + 2], b0[20], atol=1e-3) and np.allclose(a1[20 + 2], a0[20], atol=1e-3)


def test_eps_shifts_both_depths_by_eps_in_the_closed_form():
    qs = np.arange(-3, 4)
    b0, a0 = mm.asymptotic(140, 1.5, 0.5, qs)
    b1, a1 = mm.asymptotic(140, 1.5, 0.5, qs, eps=0.3)
    assert np.allclose(b1 - b0, 0.3) and np.allclose(a1 - a0, 0.3)


def test_two_uncorrelated_assets_quote_like_one():
    ms = mm.MultiStationary(140, 1.5, 0.5, np.eye(2), 8)
    b1, a1 = mm.stationary(140, 1.5, 0.5, 8)
    b, a = ms.depths(np.array([[3, -2], [0, 5]]))
    assert np.allclose(b[:, 0], [b1[8 + 3], b1[8]], atol=1e-9) and np.allclose(a[:, 1], [a1[8 - 2], a1[8 + 5]], atol=1e-9)


def test_correlation_makes_a_short_hedge_attractive():
    cov = np.array([[4.0, 3.2], [3.2, 4.0]])
    ms = mm.MultiStationary(140, 1.5, 0.1, cov, 8)
    b, _ = ms.depths(np.array([[0, -4], [0, 0], [0, 4]]))
    assert b[0, 0] < b[1, 0] < b[2, 0]                         # short asset 2: keener to buy asset 1


def test_simulate_multi_deterministic():
    ms = mm.MultiStationary(140, 1.5, 0.5, np.eye(2), 5)
    kw = dict(T=0.5, dt=0.005, cov=np.eye(2), A=140, k=1.5, paths=50, seed=3, qmax=5)
    r1, r2 = mm.simulate_multi(ms.depths, **kw), mm.simulate_multi(ms.depths, **kw)
    assert np.array_equal(r1["pnl"], r2["pnl"]) and (np.abs(r1["q_T"]) <= 5).all()
