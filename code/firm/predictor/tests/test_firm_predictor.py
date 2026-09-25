"""Acceptance tests of firm.predictor."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_predictor import (
    PredictorCard,
    forward_return,
    ic_series,
    ic_summary,
    quantile_spread,
    rank_transform,
    residualise,
    zscore,
)


def test_forward_return_compounds_and_respects_gaps():
    r = np.array([[0.1], [0.1], [np.nan], [0.1]])
    f = forward_return(r, 1)
    assert np.isclose(f[0, 0], 0.1) and np.isnan(f[1, 0]) and np.isnan(f[3, 0])
    assert np.isclose(forward_return(np.array([[0.1], [0.1], [0.1]]), 2)[0, 0], 0.21)


def test_normalisers():
    x = np.array([[1.0, 2.0, 3.0, 100.0, np.nan]])
    z = zscore(x, clip=1.0)
    assert np.nanmax(np.abs(z)) <= 1.0 and np.isnan(z[0, 4])
    r = rank_transform(x)
    assert np.allclose(r[0, :4], [-0.375, -0.125, 0.125, 0.375]) and np.isnan(r[0, 4])


def test_residualise_removes_a_factor():
    rng = np.random.default_rng(0)
    f = rng.normal(size=(50, 1))
    X = rng.normal(size=(200, 1))
    y = f @ X.T + rng.normal(0, 0.1, (50, 200))
    res = residualise(y, X)
    assert abs(np.corrcoef(res[7], X[:, 0])[0, 1]) < 1e-8


def test_ic_and_its_errors():
    rng = np.random.default_rng(1)
    T, N = 400, 300
    s = rng.normal(size=(T, N))
    y = 0.05 * s + rng.normal(size=(T, N))
    ic = ic_series(s, y, "pearson")
    st = ic_summary(ic)
    assert abs(st["mean"] - 0.05) < 0.01 and abs(st["sd"] - 1 / np.sqrt(N)) < 0.01 and st["t_hac"] == st["t_naive"]
    p = np.empty((T, N))                                                # a persistent signal
    p[0] = rng.normal(size=N)
    for t in range(1, T):
        p[t] = 0.95 * p[t - 1] + np.sqrt(1 - 0.95**2) * rng.normal(size=N)
    yp = 0.02 * p + rng.normal(size=(T, N))
    y20 = sum(np.roll(yp, -k, axis=0) for k in range(1, 21))[:-20]     # overlapping 20-day targets
    ic20 = ic_series(p[:-20], y20, "pearson")
    st20 = ic_summary(ic20, h=20)
    assert st20["t_naive"] > 2.5 * st20["t_hac"]
    qs = quantile_spread(s, y)
    assert np.nanmean(qs) > 0


def test_card_fields():
    c = PredictorCard("reversal", "minus the 5-day return", "closes to t", "liquidity provision", 5, "rank",
                      "news", "Jegadeesh (1990)")
    assert [k for k, _ in c.fields()][0] == "Definition" and "not yet measured" in dict(c.fields())["Horizon and half-life"]
