import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_futmm as ff  # noqa: E402

fm = ff.fm


def test_continuous_fills_match_firm_match_up_to_rounding():
    sizes = [100, 400, 300, 200]
    book = [fm.Resting(str(i), q) for i, q in enumerate(sizes)]
    for x in (7, 250, 999, 1500):
        exact = fm.pro_rata(book, x)
        approx = ff.fills(sizes, [x])[0]
        got = np.array([exact.get(str(i), 0) for i in range(4)])
        assert np.all(np.abs(got - approx) <= len(sizes)) and got.sum() == min(x, 1000)


def test_best_response_and_fifo():
    X = ff.aggressors(5000, 1)
    grid = np.arange(10, 2001, 10.0)
    q = ff.fifo_size(X, 1.0, 0.01, grid)
    assert 50 <= q <= 150
    # alone at the level a maker's pro-rata problem is the time-priority problem
    assert ff.best_response(0.0, X, 1.0, 0.01, grid) == q
    # against a large crowd the best response is larger than against a small one
    assert ff.best_response(5000.0, X, 1.0, 0.01, grid) > ff.best_response(200.0, X, 1.0, 0.01, grid)


def test_equilibrium_grows_with_makers_and_hurts_them():
    X = ff.aggressors(5000, 2)
    grid = np.unique(np.round(np.geomspace(10, 3000, 80)))
    q = ff.fifo_size(X, 1.0, 0.01, grid)
    s5, s10 = ff.equilibrium(5, X, 1.0, 0.01, grid), ff.equilibrium(10, X, 1.0, 0.01, grid)
    assert q < s5 < s10
    assert ff.utility(s10, 9 * s10, X, 1.0, 0.01) < ff.utility(q, 9 * q, X, 1.0, 0.01)


def test_implied_scan():
    assert ff.scan(ff.Strip(lag=0, steps=2000))["count"] == 0
    a, b = ff.scan(ff.Strip(lag=5, steps=2000)), ff.scan(ff.Strip(lag=30, steps=2000))
    assert b["count"] > a["count"] and b["mean_edge"] >= 1.0
    st = ff.Strip(lag=0, steps=10)
    imp = fm.implied_in(st.outright(3, 0), st.outright(3, 1))
    assert imp.ask - imp.bid == 2 and st.spread(3, 0).ask - st.spread(3, 0).bid == 1
