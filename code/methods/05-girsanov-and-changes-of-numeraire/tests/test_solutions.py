"""Numbers gate: every numerical answer printed in Book 4, Chapter 5 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_numeraire import (
    SIGMA,
    B,
    Phi,
    caplet_closed_form,
    expected_short_rate,
    first_passage_with_drift,
    forward_rate,
    girsanov_histogram,
    mc_forward,
    mc_risk_neutral,
    problem,
    reweighting_check,
    zcb,
)

P = problem()
RW = reweighting_check()


def bp(x, k=2):
    return round(1e4 * x, k)


def test_text():
    assert round(bp(P["q_se"]), 2) == 0.05 and bp(P["closed"]) == 3.26 and P["normals_q"] == 260
    assert round(1e8 * P["closed"], -2) == 32_600
    assert (round(100 * P["m_Q"], 3), round(100 * P["f0T"], 3)) == (3.918, 3.901)
    assert round(bp(SIGMA**2 / (2 * 0.5**2)), 1) == 2.0 and round(bp(P["convexity_30y"]), 1) == 2.0
    sp = SIGMA * math.sqrt((1 - math.exp(-5)) / 1) * B(0.25)
    assert round(100 * sp, 3) == 0.234 and round(1 / (1 + 0.25 * 0.045), 5) == 0.98888
    assert abs(P["se_ratio"] - 1) < 0.005                                  # "within half a percent"
    assert (round(100 * RW["est"], 3), round(100 * RW["se"], 3)) == (3.906, 0.003) and round(RW["mean_w"], 3) == 1.000
    g = girsanov_histogram()
    assert abs(g["mean_q"] - 1) < 0.02 and abs(g["mean_z"] - 1) < 0.01


def test_exercises():
    assert round(0.8343 * 2.4, 3) == 2.002 and round(-(0.09 - 0.04) / 0.25, 2) == -0.2
    assert round(B(5.0), 4) == 1.8358 and round(bp(SIGMA**2 * B(5.0) ** 2 / 2), 1) == 1.7
    assert round(100 * (Phi(0.1) - Phi(-0.1)), 2) == 7.97
    assert round(100 * first_passage_with_drift(math.log(0.98), -0.045, 0.30, 21 / 252), 1) == 82.4
    # the drifted first passage against a fine simulation
    rng = np.random.default_rng(5)
    n, m, T, mu, s, b = 20_000, 2000, 0.25, 0.1, 0.3, -0.1
    x = np.cumsum(mu * T / m + s * math.sqrt(T / m) * rng.standard_normal((n, m)), axis=1)
    assert abs((x.min(axis=1) <= b).mean() - first_passage_with_drift(b, mu, s, T)) < 0.015


def test_problem():
    assert (round(P["p1"], 4), round(P["p2"], 4)) == (0.8343, 0.8262) and round(100 * P["fwd"], 2) == 3.92
    assert (bp(P["q_price"]), bp(P["q_se"])) == (3.34, 0.05) and (bp(P["f_price"]), bp(P["f_se"])) == (3.32, 0.05)
    assert round((P["q_price"] - P["closed"]) / P["q_se"], 1) == 1.6 and round((P["f_price"] - P["closed"]) / P["f_se"], 1) == 1.2
    assert round(P["se_ratio"], 3) == 0.996
    assert (bp(P["fine_price"]), bp(P["fine_se"])) == (3.32, 0.05)
    assert abs(expected_short_rate(5.0) - forward_rate(5.0) - SIGMA**2 * B(5.0) ** 2 / 2) < 1e-8


def test_interview():
    exact = 0.5 * math.erfc(5 / math.sqrt(2))
    assert round(exact * 1e7, 2) == 2.87 and round(1 / exact / 1e6, 1) == 3.5
    rng = np.random.default_rng(9)
    y = rng.standard_normal(10_000) + 5
    w = np.exp(-5 * y + 12.5) * (y > 5)
    assert (round(w.mean() * 1e7, 2), round(w.std() / 100 * 1e7, 2)) == (2.79, 0.07)


def test_time_step_and_ablation():
    """WRITING section 9. The named result compares two simulations with a closed form: the risk-
    neutral price must be stable when its step is divided by four, and the credited mechanism (the
    forward measure's drift correction) must matter: sampling r_T with the risk-neutral mean but
    discounting deterministically by P(0, T) misprices beyond the error."""
    assert abs(P["fine_price"] - P["q_price"]) < 3 * math.hypot(P["q_se"], P["fine_se"])
    rng = np.random.default_rng(13)
    m, v = expected_short_rate(5.0), SIGMA**2 * (1 - math.exp(-5.0)) / 1.0
    r = m + math.sqrt(v) * rng.standard_normal(400_000)
    x = 1 / (1 + 0.25 * 0.045)
    wrong = float(zcb(0.03, 5.0)) * np.mean((1 + 0.25 * 0.045) * np.maximum(x - zcb(r, 0.25), 0))
    right = mc_forward(400_000, seed=14)
    assert abs(wrong - caplet_closed_form()) > 5 * right["se"] and abs(right["price"] - caplet_closed_form()) < 3 * right["se"]
    assert mc_risk_neutral(1000, seed=1)["normals"] == 260
