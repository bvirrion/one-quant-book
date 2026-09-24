"""Numbers gate: every numerical answer printed in Book 4, Chapter 4 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_sde import (
    bond_price_mc,
    bond_price_pde,
    feller_table,
    gamma_cdf,
    negative_fraction,
    problem,
    stationary_histograms,
)

P = problem()
FT = {round(r, 2): (d, f) for r, d, f in feller_table()}


def pct(x, k=1):
    return round(100 * x, k)


def test_text():
    assert round(P["feller"], 2) == 0.44 and round(P["stat_sd"], 2) == 0.06
    assert pct(gamma_cdf(0.004, 4 / 9, 0.09)) == 27.9
    assert pct(P["p_neg_step_from_0004"]) == 3.6
    assert pct(P["neg_daily"], 0) == 75 and pct(P["neg_4x"], 0) == 75 and pct(P["neg_16x"], 0) == 75
    assert pct(FT[1.0][0], 0) == 24                                  # "a quarter" at Feller ratio one
    assert round(bond_price_pde(), 4) == 0.8343
    mc, se = bond_price_mc()
    assert round(mc, 4) == 0.8341 and round(se, 4) == 0.0002
    h = stationary_histograms()
    assert abs(h["desk"][3] - h["desk"][4]) < 0.006                  # simulated vs Gamma mass below 0.004
    assert round(math.log(2) / 2, 2) == 0.35


def test_exercises():
    assert round(math.log(2) / 2 * 252) == 87
    assert pct(0.5 * math.erfc(0.15 / math.sqrt(2))) == 44.0
    assert round(0.04 + 0.05 * math.exp(-1), 4) == 0.0584
    B = (1 - math.exp(-2.5)) / 0.5
    A = (0.04 - 0.0002) * (B - 5) - 0.0001 * B**2 / 2
    assert (round(B, 4), round(A, 4), round(math.exp(A - 0.03 * B), 4)) == (1.8358, -0.1261, 0.8343)
    assert pct(FT[1.0][0]) == 24.5 and pct(FT[2.56][0], 2) == 0.08 and pct(FT[1.78][0]) == 1.6


def test_problem():
    assert round(P["eta_for_feller"], 2) == 0.4 and round(P["half_life"], 2) == 0.35
    assert (pct(P["neg_daily"]), pct(P["neg_4x"]), pct(P["neg_16x"]), pct(P["neg_weekly"])) == (75.2, 75.3, 74.6, 75.2)
    assert P["ex_min"] >= 0 and round(P["ex_mean"], 4) == 0.0394
    assert round(P["ft_mean"], 4) == 0.0393 and pct(P["ft_zero_share"]) == 5.2


def test_time_step_and_ablation():
    """WRITING section 9. The named result (75% of paths fail) must be stable when the step is divided
    by four, which the text states and the problem asserts; and the mechanism credited, a Feller ratio
    below one, must matter: at a Feller ratio of 4 no path fails, at any step."""
    assert abs(P["neg_4x"] - P["neg_daily"]) < 0.02
    assert negative_fraction(0.2, 252, 20_000, seed=7) == 0.0
    assert negative_fraction(0.2, 1008, 10_000, seed=8) == 0.0
