"""Numbers gate: every numerical answer printed in Book 4, Chapter 3 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/stochint"))
from firm_stochint import lookahead_test
from qm_ito import (
    SIG_D,
    backtest,
    gbm_quantiles,
    ito_check,
    sharpe_distribution,
    spurious_mean,
    spurious_sharpe_theory,
    sums_table,
)

B = backtest()
D = sharpe_distribution()


def test_text():
    assert (round(B["sr_cheat"], 1), round(B["sr_honest"], 2)) == (5.4, -0.04)
    w1, rows = sums_table()
    assert round(w1, 2) == 2.04 and round((w1**2 - 1) / 2, 2) == 1.58 and round((w1**2 + 1) / 2, 2) == 2.58
    assert round(w1**2 / 2, 2) == 2.08 and all(abs(r[3] - w1**2 / 2) < 1e-12 for r in rows)
    a = spurious_mean() / SIG_D
    assert round(a, 3) == 0.382 and round(1 + a * a, 3) == 1.146
    assert round(spurious_sharpe_theory(), 2) == 5.67
    assert round(D["cheat_mean"], 2) == 5.69 and round(D["honest_mean"], 2) == 0.00 and round(D["honest_sd"], 2) == 0.32
    assert (round(100 * B["cheat"][-1]), round(100 * B["cov"][-1]), round(100 * B["honest"][-1])) == (958, 965, -7)
    g = gbm_quantiles()
    assert round(math.exp(1), 2) == 2.72 and round(math.exp(0.2), 2) == 1.22 and round(g[10][5], 2) == 0.24
    c = ito_check()
    assert (round(c["log"], 5), round(c["ito"], 5), round(c["naive"], 5)) == (0.70040, 0.70039, 0.78179)


def test_exercises():
    assert round(math.sqrt(0.2) * 100, 1) == 44.7 and round(math.exp(2), 2) == 7.39
    assert round(2 / math.sqrt(5), 3) == 0.894
    assert round(spurious_mean(60) / SIG_D, 3) == 0.223 and round(spurious_sharpe_theory(60), 2) == 3.45
    s60 = np.mean([backtest(seed=1000 + i, L=60)["sr_cheat"] for i in range(100)])
    assert round(s60, 2) == 3.47


def test_problem():
    c = SIG_D * math.sqrt(sum((m / 20) ** 2 for m in range(1, 20)))
    assert round(c / SIG_D, 3) == 2.485 and round(c, 4) == 0.0248
    a = spurious_mean() / SIG_D
    assert round(a * SIG_D, 4) == 0.0038 and round(SIG_D * math.sqrt(1 + a * a), 4) == 0.0107
    assert (round(D["cheat_sd"], 2), round(D["honest_sd"], 2)) == (0.13, 0.32)
    r = lookahead_test(B["theta"], B["s"])
    assert round(r["gap"], 3) == 9.653 and r["identity_error"] < 1e-13 and round(r["t"], 1) == 34.9
    assert [round(spurious_sharpe_theory(L), 2) for L in (5, 10, 60)] == [9.36, 7.47, 3.45]
    assert round(spurious_sharpe_theory() * math.sqrt(78)) == 50


def test_time_step_and_ablation():
    """WRITING section 9. The named result is a per-bar identity: it must not depend on the length
    of the sample (a history four times longer gives the same Sharpe ratio, more precisely), and it
    must vanish when the mechanism credited, the same-bar credit, is removed."""
    longer = [backtest(days=4 * 2520, seed=2000 + i)["sr_cheat"] for i in range(50)]
    assert abs(np.mean(longer) - spurious_sharpe_theory()) < 0.05 and np.std(longer) < D["cheat_sd"]
    honest = np.mean([backtest(seed=3000 + i)["sr_honest"] for i in range(200)])
    assert abs(honest) < 0.06
