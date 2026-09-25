"""Numbers gate: every numerical answer printed in Book 7, chapter 1 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_process import (
    deflated_annual,
    expected_best,
    friday,
    kill_pvalue,
    p_best,
    p_single,
    ppv,
    search,
    years_to_detect,
)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "multitest"))
from firm_multitest import norm_cdf, norm_ppf


def r(x, d=3):
    return round(float(x), d)


def test_ppv_section():
    assert (r(ppv(0.05, 0.5, 0.05)), r(ppv(0.05, 0.5, 0.05, 2)), r(ppv(0.05, 0.5, 0.05, 3))) == (0.345, 0.840, 0.981)
    assert r(ppv(0.1, 0.8, 0.05), 2) == 0.64


def test_best_section():
    assert r(100 * p_single(2, 2), 2) == 0.23 and r(100 * p_best(2, 20, 2), 1) == 4.6
    assert r(100 * p_best(2, 1000, 2)) == 90.383 and r(expected_best(1000, 2), 2) == 2.30
    assert p_best(2, 1000, 1) > 0.999 and r(100 * p_best(2, 1000, 5), 2) == 0.39
    assert r(100 * p_best(2, 20, 2, 0.6), 1) == 2.6
    assert 20 + math.comb(20, 2) == 210


def test_evidence_and_kill():
    a2 = 1 - 0.95**5
    assert r(100 * a2, 1) == 22.6
    assert r(0.05 * 0.25 / (0.05 * 0.25 + 0.95 * 0.05 * a2), 2) == 0.54
    assert r(kill_pvalue(1.5, 0.2, 1), 3) == 0.097 and r(years_to_detect(1.5), 1) == 2.7


def test_portfolio_of_bets():
    real, false = 200 * 0.05, 200 * 0.95
    assert (real * 0.5, false * 0.05) == (5.0, 9.5)
    assert (real * 0.25, round(false * 0.0025, 3)) == (2.5, 0.475)


def test_tutorial():
    s = search()
    assert s["best_lookback"] == 2 and r(s["best_sr"], 2) == 2.14
    assert int((s["srs"] > 1).sum()) == 5 and r(s["srs"].mean(), 2) == 0.07
    assert s["log"].trial_count("reversal") == 50 and s["log"].verify() == -1 and not s["log"].post_hoc("reversal")
    assert r(deflated_annual(s["best_sr"], 2, 1)) == 0.999 and r(deflated_annual(s["best_sr"], 2, 50), 2) == 0.77


def test_exercises():
    assert r(ppv(0.1, 0.8, 0.05), 2) == 0.64 and r(ppv(0.02, 0.8, 0.05)) == 0.246
    assert r(1 - norm_cdf(2) ** 20) == 0.369 and r(20 * (1 - norm_cdf(2))) == 0.455
    assert r(kill_pvalue(1.2, -0.5, 0.5)) == 0.115
    assert r(years_to_detect(0.8, 0.05, 0.9), 1) == 13.4
    assert 30 + math.comb(30, 2) == 465 and r(norm_ppf(1 - 0.05 / 465), 2) == 3.70
    real, false = 150 * 0.04, 150 * 0.96
    assert (r(real * 0.6, 2), r(false * 0.05, 2), r(ppv(0.04, 0.6, 0.05))) == (3.6, 7.2, 0.333)
    assert (r(ppv(0.04, 0.6, 0.05, 2)), r(ppv(0.04, 0.6, 0.05, 3))) == (0.857, 0.986)
    assert (r(real * 0.6**3, 2), r(false * 0.05**3, 3)) == (1.3, 0.018)
    assert [r(p_best(2, 1000, 2, rho)) for rho in (0.3, 0.6, 0.9)] == [0.420, 0.167, 0.030]
    target = p_best(2, 20, 2)
    assert abs(p_best(2, 1000, 2, 0.85) - target) < 0.002 and r(p_best(2, 13, 2), 2) == r(p_best(2, 1000, 2, 0.9), 2)


def test_problem():
    f = friday()
    assert r(f["p_single"], 5) == 0.00234 and r(1000 * f["p_single"], 2) == 2.34
    assert r(f["p_week_indep"], 4) == 0.0458 and r(f["p_week_corr"], 4) == 0.0262
    assert r(f["p_year_corr"]) == 0.735 and r(f["p_year_indep"]) == 0.904 and r(f["expected_best_indep"], 2) == 2.30
    assert (r(f["dsr_1"]), r(f["dsr_20"]), r(f["dsr_1000"])) == (0.998, 0.822, 0.336)
    assert r((norm_ppf(1 - 1e-5) / 2) ** 2, 2) == 4.55
    alpha, power = 1 - norm_cdf(1), norm_cdf(0.5)
    assert (r(alpha), r(power), r(ppv(0.05, power, alpha))) == (0.159, 0.691, 0.187)
    assert r(1 - (1 - alpha) ** 4) == 0.499


def test_interviews():
    assert r(norm_cdf(-1.5)) == 0.067
