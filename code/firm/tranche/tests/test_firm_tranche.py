"""Acceptance tests of the Book 2, Chapter 24 build (index intrinsic value and tranche losses)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tranche import (
    annuity_weighted_spread,
    base_correlation,
    expected_tranche_loss,
    intrinsic_upfront,
    simulate_pool,
    skew_pnl,
    tranche_loss,
)

P, R = 0.05, 0.40                       # five-year default probability, recovery


def test_intrinsic_and_weighting():
    assert intrinsic_upfront([0.01, 0.03]) == 0.02
    assert annuity_weighted_spread([0.01, 0.03], [4.4, 4.0]) < 0.02
    assert skew_pnl(1e9, -0.01, 0.0) == 1e7


def test_tranche_loss_bounds():
    assert tranche_loss(0.02, 0.03, 0.07) == 0.0
    assert tranche_loss(0.05, 0.03, 0.07) == 0.5
    assert tranche_loss(0.30, 0.03, 0.07) == 1.0


def test_tranches_add_up_to_the_pool():
    cuts = [0.0, 0.03, 0.07, 0.15, 1.0]
    total = sum((d - a) * expected_tranche_loss(a, d, P, 0.3, R) for a, d in zip(cuts, cuts[1:], strict=False))
    assert abs(total - P * (1 - R)) < 1e-6


def test_correlation_moves_risk_from_equity_to_senior():
    assert expected_tranche_loss(0, 0.03, P, 0.1, R) > expected_tranche_loss(0, 0.03, P, 0.5, R)
    assert expected_tranche_loss(0.15, 1.0, P, 0.1, R) < expected_tranche_loss(0.15, 1.0, P, 0.5, R)


def test_base_correlation_round_trip():
    el = expected_tranche_loss(0.0, 0.03, P, 0.25, R)
    assert abs(base_correlation(0.03, el, P, R) - 0.25) < 1e-6


def test_finite_pool_matches_the_large_pool():
    sims = simulate_pool(125, P, 0.3, R, trials=4000, seed=7)
    mc = sum(tranche_loss(x, 0.0, 0.03) for x in sims) / len(sims)
    assert abs(mc - expected_tranche_loss(0.0, 0.03, P, 0.3, R)) < 0.02
