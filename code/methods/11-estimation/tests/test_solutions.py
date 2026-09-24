"""Numbers gate: every numerical answer printed in Book 4, Chapter 11 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_estimation import SD_BP, coverage, misspecified_fit, problem, strategy_pnl

P = problem()
C = coverage()
M = misspecified_fit()


def test_text():
    assert (round(P["mean"], 1), round(P["se_iid"], 1), round(P["t_iid"], 1)) == (4.0, 1.2, 3.4)
    assert (round(P["se_nw"], 1), round(P["t_nw"], 1)) == (2.3, 1.7)
    assert round(2 / math.sqrt(100) * 1, 1) == 0.2
    assert (round(M["logsd_se_hessian"], 4), round(M["logsd_se_sandwich"], 4), round(M["logsd_se_true"], 4)) == (0.0158, 0.0230, 0.0237)
    assert round(math.sqrt(1 / 5), 2) == 0.45 and round(P["sr"], 2) == 1.51 and round(P["sr_se_hac"], 2) == 0.87
    assert P["lrv_factor"] == 5.0 and round(math.sqrt(5), 2) == 2.24
    assert (round(P["se_nw"], 2), round(P["t_nw"], 2), round(P["se_true"], 2)) == (2.32, 1.73, 2.65)
    assert (round(C["pct"]["iid"], 1), round(C["pct"]["nw"], 1), round(C["pct"]["nw20"], 1)) == (62.5, 92.2, 93.5)
    assert (round(P["se_iid"], 2), round(P["t_iid"], 2)) == (1.19, 3.38)


def test_exercises():
    sr1 = 1 / math.sqrt(252)
    assert round(math.sqrt((1 + sr1**2 / 2) / 1008) * math.sqrt(252), 2) == 0.50
    assert round(math.sqrt(1.2 / 0.8), 2) == 1.22
    se = math.sqrt(0.55 * 0.45 / 200)
    assert (round(se, 3), round(0.05 / se, 2)) == (0.035, 1.42)
    assert round(1 / math.sqrt(4000), 4) == 0.0158
    assert round(3 * 252 / 20) == 38


def test_problem():
    assert (round(P["mean"], 2), round(P["sd"], 1), P["lags"]) == (4.03, 42.3, 7)
    assert [round(a, 2) for a in P["ac"][:4]] == [0.80, 0.59, 0.37, 0.16]
    assert round(P["se_nw20"], 2) == 2.33 and round(P["sr_se_iid"], 2) == 0.45
    assert round(P["sd"] * math.sqrt(5 / 1260), 2) == 2.66 and round(P["t_true_expected"], 2) == 1.51
    n = (3 * SD_BP * math.sqrt(5) / 4) ** 2
    assert round(n, -1) == 4960 and round(n / 252) == 20


def test_time_step_and_ablation():
    """WRITING section 9. The coverage result must be stable when the number of simulated histories is
    quadrupled-ish (independent seeds), and the mechanism credited (overlap) is ablated: with one-day
    holding the P&L is independent and the iid interval covers about 95%."""
    c2 = coverage(n_rep=2000, seed0=50_000)
    assert abs(c2["iid"] - C["iid"]) < 0.03 and abs(c2["nw"] - C["nw"]) < 0.02
    import numpy as np
    from qm_estimation import MU_BP, mean_se
    hits = []
    for k in range(1000):
        x = strategy_pnl(seed=70_000 + k, hold=1)
        hits.append(abs(x.mean() - MU_BP) <= 1.96 * mean_se(x, "iid"))
    assert abs(np.mean(hits) - 0.95) < 0.02


def test_years_for_t():
    """Section 5: the wait for t = 2 is 4 / SR^2 years, m times longer with long-run variance factor m."""
    from qm_estimation import lrv_factor, years_for_t
    assert abs(years_for_t(1.0) - 4.0) < 0.01 and abs(years_for_t(2.0) - 1.0) < 0.01
    assert round(years_for_t(1.51), 1) == 1.8 and round(years_for_t(1.51, lrv_factor()), 1) == 8.8
    assert abs(lrv_factor() - 5.0) < 1e-12
    # the honest Sharpe ratio 1.51 / sqrt(5) = 0.68 reaches t = 1.52 after five years, short of 2
    assert round(1.51 / 5**0.5, 2) == 0.68 and 1.51 / 5**0.5 * 5**0.5 < 2
