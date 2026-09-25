import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "tcost"))
from firm_reversal import book, forecast, industry_adjusted, intraday, overnight, raw, residual  # noqa: E402


def test_signals_by_hand():
    r = np.array([0.02, -0.01, 0.03, 0.00])
    assert raw(r).tolist() == [-0.02, 0.01, -0.03, -0.0]
    ia = industry_adjusted(r, np.array([0, 0, 1, 1]), np.array([True, True, True, False]))
    assert np.allclose(ia[:3], [-0.015, 0.015, 0.0]) and np.isnan(ia[3])
    assert np.allclose(overnight([101.0], [100.0]), [-0.01]) and np.allclose(intraday([99.0], [100.0]), [0.01])
    assert np.allclose(forecast([1.0, -2.0], 0.05, [0.02, 0.01]), [0.001, -0.001])


def test_residual_removes_factors():
    rng = np.random.default_rng(0)
    X = np.column_stack([np.ones(200), rng.standard_normal(200)])
    e = rng.standard_normal(200) * 0.01
    r = X @ np.array([0.01, 0.02]) + e
    s = residual(r, X)
    assert abs(s @ X[:, 0]) < 1e-12 and abs(s @ X[:, 1]) < 1e-12
    assert np.corrcoef(s, -e)[0, 1] > 0.99


def test_book_without_costs_is_mean_variance_and_neutral():
    rng = np.random.default_rng(1)
    a, v = rng.standard_normal(50) * 1e-3, rng.uniform(1e-4, 4e-4, 50)
    w = book(a, v, np.zeros(50), 10.0, 1e9, np.full(50, 0.02), np.full(50, 1e7), np.full(50, 2e-4), 0.7, costs=False)
    mu = np.sum(a / v) / np.sum(1 / v)                         # the closed form with sum w = 0
    assert abs(w.sum()) < 1e-12 and np.allclose(w, (a - mu) / (10.0 * v), atol=1e-12)


def test_costs_shrink_trades():
    rng = np.random.default_rng(2)
    a, v = rng.standard_normal(50) * 1e-3, rng.uniform(1e-4, 4e-4, 50)
    w0 = rng.standard_normal(50) * 0.01
    w0 -= w0.mean()
    args = (a, v, w0, 10.0, 1e9, np.full(50, 0.02), np.full(50, 1e7), np.full(50, 2e-4), 0.7)
    free, costly = book(*args, costs=False), book(*args)
    assert np.abs(costly - w0).sum() < 0.5 * np.abs(free - w0).sum()
    assert abs(costly.sum()) < 1e-10


def test_factor_neutral_with_costs():
    rng = np.random.default_rng(3)
    n = 200
    X = np.column_stack([np.ones(n), rng.standard_normal((n, 3))])
    a, v = rng.standard_normal(n) * 1e-3, rng.uniform(1e-4, 4e-4, n)
    w0 = rng.standard_normal(n) * 0.005
    w = book(a, v, w0, 10.0, 1e9, np.full(n, 0.02), np.full(n, 1e7), np.full(n, 2e-4), 0.7, X=X)
    assert np.abs(X.T @ w).max() < 1e-10
