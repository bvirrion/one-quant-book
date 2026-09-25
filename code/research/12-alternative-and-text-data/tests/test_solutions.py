"""Numbers gate: every numerical answer printed in Book 7, chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_altdata import CAPITAL, COST, HALF_LIFE, YEARS, breakeven_curve, ic_break, text_scores, trial_report, value


def r(x, d=2):
    return round(float(x), d)


def test_trial():
    t = trial_report()
    assert t["rows"] == 5_980 and (round(t["coverage_backfill"]), round(t["coverage_live"])) == (338, 273)
    assert r(100 * t["backfill_share"], 1) == 39.6
    fit = t["fit"]
    assert [r(fit[y][0]) for y in range(1, 6)] == [0.92, 0.87, 0.37, 0.39, 0.35]
    assert [r(fit[y][2]) for y in range(1, 6)] == [0.85, 0.84, 0.35, 0.35, 0.32]
    assert [r(fit[y][1]) for y in range(1, 6)] == [0.02, 0.02, 0.12, 0.17, 0.12]
    assert (t["break_quarter_year"], r(t["break_stat"])) == (3.0, 3.05)
    assert [r(t["ic_year"][y]) for y in range(1, 6)] == [0.38, 0.37, 0.12, 0.14, 0.15]
    assert (r(t["ic_live"]), r(t["ic_old_live"])) == (0.13, 0.20)
    inc, tstat, k = t["inc"]
    assert (r(inc), r(tstat, 1), k) == (0.10, 4.0, 12)
    assert (r(100 * t["ls_back"], 1), r(100 * t["ls_new"], 1), r(100 * t["ls_inc"], 1)) == (10.4, 3.4, 2.9)
    assert round(t["ls_back"] / t["ls_new"]) == 3


def test_value():
    t = trial_report()
    assert (CAPITAL, COST, HALF_LIFE, YEARS) == (20e6, 0.004, 2.0, 3)
    assert (r(value(t["ls_back"]) / 1e6), r(value(t["ls_new"]) / 1e6), r(value(t["ls_inc"]) / 1e6)) == (5.06, 1.59, 1.35)
    c = breakeven_curve()
    assert (r(c[0.5]["ls_inc"] / 1e6), r(c[1.0]["ls_inc"] / 1e6), r(c[5.0]["ls_inc"] / 1e6)) == (0.43, 0.87, 1.81)
    assert round(100 * (1 - value(t["ls_inc"]) / value(t["ls_new"]))) == 15
    assert round(value(t["ls_inc"]) / c[0.5]["ls_inc"]) == 3
    assert round(value(t["ls_back"]) / value(t["ls_inc"])) == 4


def test_break_by_ic_and_text():
    x, k, year, stat = ic_break()
    assert (len(x), k, year, r(stat)) == (20, 8, 3.0, 1.85)
    assert (r(x[:8].min()), r(x[:8].max()), r(x[8:].min()), r(x[8:].max())) == (0.32, 0.45, -0.03, 0.27)
    s = text_scores()
    assert (r(s["general"]), r(s["finance"]), r(s["net"]), round(100 * s["fin_share"])) == (0.74, 0.87, 0.95, 77)


def test_exercises():
    assert r(1200 / 3000) == 0.40
    assert (r(100 * 12 / 400), r(100 * 3 / 400), r(100 * (3 - 5) / 400)) == (3.0, 0.75, -0.5)
    assert r(4 * 0.029 * 20 - 0.004 * 20) == 2.24
    assert r(2.3 / 3 * sum(2 ** (-(k + 0.5) / 2) for k in range(3))) == 1.42
    assert [r(2 ** (-(k + 0.5) / 2), 3) for k in range(3)] == [0.841, 0.595, 0.420]


def test_cusum_break_critical_value():
    """The text's 5% critical value of the CUSUM break statistic (sup of a Brownian bridge): the Kolmogorov
    distribution's 95% quantile, 1 - 2 sum (-1)^(k-1) exp(-2 k^2 x^2) = 0.95."""
    import math

    cdf = lambda x: 1 - 2 * sum((-1) ** (k - 1) * math.exp(-2 * k * k * x * x) for k in range(1, 100))  # noqa: E731
    x = next(i / 1000 for i in range(1000, 2000) if cdf(i / 1000) >= 0.95)
    assert r(x) == 1.36
