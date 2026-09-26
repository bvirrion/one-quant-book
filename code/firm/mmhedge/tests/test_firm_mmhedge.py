import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_mmhedge as h  # noqa: E402


def test_exposure_variance_and_choice():
    q, p, b, se = np.array([100.0, -50.0]), np.array([50.0, 100.0]), np.array([1.2, 0.8]), np.array([0.02, 0.01])
    assert h.delta_equivalent(q, p, b) == 100 * 50 * 1.2 - 50 * 100 * 0.8
    d = 2000.0
    assert math.isclose(h.book_var(q, p, b, 0.01, se), d * d * 1e-4 + (5000 * 0.02) ** 2 + (5000 * 0.01) ** 2)
    assert math.isclose(h.book_var(q, p, b, 0.01, se, hedge=d), (5000 * 0.02) ** 2 + (5000 * 0.01) ** 2)
    # a concentrated factor exposure: the future wins; a tiny book: keep it; a huge risk aversion: the stocks
    big = np.full(40, 1000.0)
    pp, bb, ss = np.full(40, 50.0), np.ones(40), np.full(40, 0.01)
    assert h.choose(big, pp, bb, 0.01, ss, 5e-5, 2e-4, lam=1e-5)["best"] == "future"
    assert h.choose(big / 1000, pp, bb, 0.01, ss, 5e-5, 2e-4, lam=1e-6)["best"] == "none"
    assert h.choose(big, pp, bb, 0.01, ss, 5e-5, 2e-4, lam=1.0)["best"] == "stocks"


def test_partial_hedge_is_the_argmin():
    for D in (-3e5, -1e4, 0.0, 2e4, 5e5):
        grid = np.linspace(-6e5, 6e5, 240001)
        f = 5e-5 * np.abs(grid) + 1e-5 * 1e-4 * (D - grid) ** 2
        assert abs(h.partial_hedge(D, 5e-5, 1e-5, 1e-4) - grid[np.argmin(f)]) < 10.0
    assert h.partial_hedge(1e4, 5e-5, 1e-5, 1e-4) == 0.0          # inside the dead zone of half-width 25,000


def test_future_rules():
    rng = np.random.default_rng(3)
    D = np.cumsum(rng.normal(0, 30000, 5000))
    H0, c0, n0 = h.hedge_future(D, "zero")
    Hb, cb, nb = h.hedge_future(D, "band", band=200000)
    assert np.all(np.abs(D - H0) <= 25000 + 1e-6) and np.all(np.abs(D - Hb) <= 225000 + 1e-6)
    assert nb < n0 / 5 and math.isclose(c0, 5e-5 * 50000 * n0)
    Hn, cn, nn = h.hedge_future(D, "none")
    assert cn == 0 and nn == 0 and not Hn.any()


def test_flow_day():
    d = h.FlowDay(seed=2)
    Q, nfill, _ = d.inventory()
    x = Q * d.p
    corr = np.corrcoef(x.T)
    assert corr[np.triu_indices(d.n, 1)].mean() > 0.2                    # the tilt makes the names move together
    assert abs(np.mean(Q)) < 200 and np.abs(Q).max() < 5000              # the skew pulls each name back
    Qs, _, cost = d.inventory(stock_band=20000.0, c_stk=1.7e-4)
    assert np.all(np.abs(Qs * d.p) <= 20000.0 + 1e-6) and cost > 0
    r = h.day_pnl(d, "none")
    assert math.isclose(r["spread"], float(nfill.sum()) * 100 * 0.01)
    assert h.day_pnl(d, "future zero")["risk_min"] < 0.6 * r["risk_min"]


def test_overnight_and_flatten():
    q, p, b, se = np.full(10, 1000.0), np.full(10, 50.0), np.ones(10), np.full(10, 0.01)
    loss = h.overnight(q, p, b, 0.008, se, n=200000, seed=1)
    assert abs(loss.std() / math.sqrt(h.book_var(q, p, b, 0.008, se)) - 1) < 0.02
    lh = h.overnight(q, p, b, 0.008, se, hedge=500000.0, n=200000, seed=1)
    assert lh.std() < 0.4 * loss.std()
    c = h.flatten_cost([1000.0], [50.0], half_spread=0.01, eta=0.1, adv=[390000.0], sigma=0.02, minutes=10.0)
    assert math.isclose(c, 10.0 + 50000.0 * 0.1 * 0.02 * math.sqrt(1000.0 / 10000.0))


def test_optimal_band():
    b = h.optimal_band(1e6, 1e-5, 0.01, 5e-5)
    assert math.isclose(b, (3 * 5e-5 * 1e12 / (4 * 1e-5 * 1e-4)) ** (1 / 3))


def test_flattening_through_the_quotes():
    d = h.FlowDay(seed=5)
    q0 = d.inventory()[0][-1]
    q1 = d.inventory(eod_from=21600.0, eod_skew=4.0)[0][-1]
    assert np.abs(q1).sum() < 0.6 * np.abs(q0).sum()
