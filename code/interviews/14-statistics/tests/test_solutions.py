"""Numbers gate: every numerical answer printed in Book 18, chapter 14 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_stats import (
    ar1_variance_inflation,
    expected_max_normal,
    omitted_variable_slope,
    outlier_r2,
    sharpe_se_annual,
    simulate_ar1_mean_se,
    stopping_rule_p_values,
    years_for_power,
)


def test_hook_and_q5_sharpe():
    se = sharpe_se_annual(2, 189)
    assert round(se, 2) == 1.16 and round(2 / se, 2) == 1.73
    assert 9 * 21 == 189


def test_table_best_of_k():
    vals = {k: round(expected_max_normal(k) / math.sqrt(5), 2) for k in (10, 100, 1000)}
    assert vals == {10: 0.69, 100: 1.12, 1000: 1.45}


def test_q2_mean_se():
    se_daily = 0.01 / math.sqrt(250)
    assert round(100 * se_daily, 4) == 0.0632
    assert round(se_daily * 250, 3) == 0.158 and round(0.01 * math.sqrt(250), 3) == 0.158


def test_q4_two_regressions():
    assert round(math.sqrt(0.8 * 0.45), 2) == 0.6
    rng = np.random.default_rng(0)
    x = rng.standard_normal(200_000)
    y = 0.6 * x + 0.8 * rng.standard_normal(200_000)
    b_yx = np.polyfit(x, y, 1)[0]
    b_xy = np.polyfit(y, x, 1)[0]
    assert abs(b_yx * b_xy - np.corrcoef(x, y)[0, 1] ** 2) < 1e-9


def test_q6_omitted_variable():
    assert round(omitted_variable_slope(1, 2, -0.8, 1), 6) == -0.6
    rng = np.random.default_rng(1)
    z = rng.standard_normal((200_000, 2))
    x1 = z[:, 0]
    x2 = -0.8 * x1 + 0.6 * z[:, 1]
    y = x1 + 2 * x2 + rng.standard_normal(200_000)
    assert abs(np.polyfit(x1, y, 1)[0] + 0.6) < 0.01


def test_q7_attenuation():
    rng = np.random.default_rng(2)
    s = rng.standard_normal(200_000)
    y = 0.4 * s + rng.standard_normal(200_000)
    x = s + rng.standard_normal(200_000)
    assert abs(np.polyfit(x, y, 1)[0] - 0.2) < 0.01


def test_q8_power():
    assert round(years_for_power(0.5), 1) == 24.7
    assert round(years_for_power(1.0), 1) == 6.2


def test_q9_multiple():
    assert round(1 - 0.95**100, 3) == 0.994
    assert 0.05 / 100 == 0.0005
    assert 100 * 0.05 == 5


def test_q10_best_of_200():
    best = expected_max_normal(200) / math.sqrt(5)
    assert round(best, 2) == 1.23
    assert round((1.9 - best) / (1 / math.sqrt(5)), 1) == 1.5


def test_q11_ar1():
    assert ar1_variance_inflation(0.5) == 3.0 and round(math.sqrt(3), 2) == 1.73
    assert abs(simulate_ar1_mean_se(0.5, 500, 2000, 1) - math.sqrt(3)) < 0.08


def test_q12_stopping_rule():
    p_bin, p_nb = stopping_rule_p_values(3, 12)
    assert round(p_bin, 3) == 0.073 and round(p_nb, 3) == 0.033


def test_q13_outlier():
    with_, without = outlier_r2()
    assert round(with_, 2) == 0.21 and round(without, 2) == 0.01


def test_worked_answers():
    from statistics import NormalDist

    nd = NormalDist()
    se = 1.5 * math.sqrt(1 / 52 + 1 / 208)
    t = 0.6 / se
    p = 2 * (1 - nd.cdf(t))
    assert round(se, 2) == 0.23 and round(t, 1) == 2.6 and round(p, 4) == 0.0099 and round(5 * p, 2) == 0.05
    s = math.sqrt(0.54 * 0.46 / 1000)
    assert round(100 * s, 2) == 1.58 and round(196 * s, 1) == 3.1
    deff = 1 + (10 - 1) * 0.1
    assert round(deff, 1) == 1.9 and round(math.sqrt(deff), 2) == 1.38 and round(196 * s * math.sqrt(deff), 1) == 4.3
    z = nd.inv_cdf(0.9)
    top = nd.pdf(z) / 0.1
    assert round(z, 4) == 1.2816 and round(top, 2) == 1.75 and round(0.3 * top, 2) == 0.53
    rng = np.random.default_rng(14)
    a = rng.standard_normal((4000, 100))
    b = 0.3 * a + math.sqrt(1 - 0.09) * rng.standard_normal((4000, 100))
    idx = np.argsort(a, axis=1)[:, -10:]
    assert abs(np.take_along_axis(b, idx, axis=1).mean() - 0.3 * np.take_along_axis(a, idx, axis=1).mean()) < 0.02


def test_figure_power():
    import csv

    import fig_iv_power

    fig_iv_power.main()
    rows = {r["sr"]: r for r in csv.DictReader(open(fig_iv_power.OUT / "power.csv"))}
    assert round(float(rows["1.00"]["p80"])) == 6 and round(float(rows["0.50"]["p80"])) == 25
