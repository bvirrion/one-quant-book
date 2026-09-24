"""Numbers gate: every numerical answer printed in Book 4, Chapter 9 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_merton import (
    ce_rate,
    discrete_merton,
    dp_merton,
    merton_fraction,
    problem,
    simulate_strategies,
    viscosity_profile,
)

P = problem()


def test_text():
    assert round(100 * P["pi_star"], 1) == 51.4 and round(100 * P["ce_star"], 2) == 3.29 and round(P["loss_60_bp"], 1) == 3.6
    assert round(100 * P["kelly"]) == 154 and round(0.18 / math.sqrt(10), 3) == 0.057
    assert round(0.01 / (3 * 0.0324), 2) == 0.10                      # ten points of fraction per point of mu
    assert abs(viscosity_profile(1e-3, 0.3) - 0.7) < 1e-6


def test_exercises():
    assert round(merton_fraction(mu=0.06, r=0.02, sigma=0.2, gamma=4), 2) == 0.25
    assert round(100 * ce_rate(1.0), 2) == 2.14
    assert round(1e4 * 0.5 * 3 * 0.0324 * (0.60 - P["pi_star"]) ** 2, 1) == 3.6
    d5 = dp_merton(gamma=5.0)
    assert d5["pi_dp_spread"] == 0 and round(d5["pi_dp"], 3) == 0.315
    assert round(discrete_merton(gamma=5.0), 3) == 0.309 and round(merton_fraction(gamma=5.0), 3) == 0.309
    assert round(100 * 0.057 / (3 * 0.0324)) == 59


def test_problem():
    assert round(P["loss_52_bp"], 2) == 0.02 and round(100 * (0.52 - P["pi_star"]), 1) == 0.6
    assert (round(100 * P["pi_gamma2"]), round(100 * P["pi_gamma5"])) == (77, 31)
    assert (round(100 * P["pi_mu6"]), round(100 * P["pi_mu8"])) == (41, 62)
    assert P["pi_dp"] == 0.52 and P["pi_dp_spread"] == 0 and round(P["pi_discrete"], 3) == 0.517
    assert (round(100 * P["ce_const60_sim"], 2), round(100 * P["ce_merton_sim"], 2), round(100 * P["ce_buyhold_sim"], 2)) == (3.28, 3.31, 3.24)
    assert (round(100 * P["w_bh_p10"]), round(100 * P["w_bh_p90"])) == (51, 81)
    assert round(P["bh_cost_bp"], 1) == 3.3
    assert (round(100 * merton_fraction(mu=0.127)), round(100 * merton_fraction(mu=0.013))) == (110, -7)


def test_time_step_and_ablation():
    """WRITING section 9. The simulated certainty equivalents lean on daily rebalancing: with steps four
    times finer the constant-60% result must not move beyond noise; and the mechanism credited for the
    buy-and-hold cost (the drift of the weight) is ablated by rebalancing: then the cost vanishes."""
    fine = simulate_strategies(steps_per_year=1008, n=5000, seed=3)
    coarse = simulate_strategies(steps_per_year=252, n=5000, seed=3)
    assert abs(fine["const60"] - coarse["const60"]) < 5e-4
    assert abs(coarse["const60"] - ce_rate(0.60)) < 5e-4
