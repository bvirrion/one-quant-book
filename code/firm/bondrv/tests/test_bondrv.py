import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_bondrv import BondConfig, book, fit_residuals, loadings, neutralise, simulate_market  # noqa: E402


def test_loadings_limits():
    L = loadings(np.array([1e-9, 1.5, 300.0]), 1.5)
    assert np.allclose(L[:, 0], 1) and abs(L[0, 1] - 1) < 1e-6 and abs(L[0, 2]) < 1e-6 and L[2, 1] < 0.01


def test_a_pure_curve_leaves_no_residual():
    cfg = BondConfig(days=30, err_sd=0.0, slow_sd=0.0, noise=0.0)
    sim = simulate_market(cfg)
    assert np.abs(fit_residuals(sim["seen"], sim["tau"], cfg.decay)).max() < 1e-12


def test_neutralised_weights_have_no_factor_exposure():
    X = loadings(np.linspace(1, 30, 40), 1.5)
    w = neutralise(np.random.default_rng(0).standard_normal(40), X)
    assert np.abs(X.T @ w).max() < 1e-12


def test_factor_hedge_removes_curve_moves_but_not_costs():
    cfg = BondConfig(days=120, err_sd=0.0, slow_sd=0.0, noise=0.0)
    sim = simulate_market(cfg)
    b, d = book(sim, cfg, "factors"), book(sim, cfg, "dv01")
    assert np.abs(b["pnl"]).max() < 0.01 < np.abs(d["pnl"]).max()     # only a day's roll-down is left
    assert b["cost"].sum() > 0
