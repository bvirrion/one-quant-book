"""Numbers gate: every numerical answer printed in Book 12, chapter 18 (text and solutions). Trains three deep
Q-networks and two tabular market makers (about ninety seconds on one core)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_rltrade as m  # noqa: E402


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_execution():
    e = m.execution()
    assert round(m.benchmark_twap(), 2) == 21.4
    assert {w: round(e[w]["optimum"], 2) for w in m.WORLDS} == {"model": 18.85, "impact x3": 40.36, "impact /3": 9.74}
    gaps = {w: {k: round(v, 2) for k, v in e[w].items() if k != "optimum"} for w in m.WORLDS}
    assert gaps["model"] == {"Almgren-Chriss (model)": 0.0, "TWAP": 2.55, "DQN": 0.44, "DQN, noisy reward": 2.55,
                             "DQN, randomised": 0.55}
    assert gaps["impact x3"] == {"Almgren-Chriss (model)": 2.2, "TWAP": 1.04, "DQN": 9.09, "DQN, noisy reward": 1.04,
                                 "DQN, randomised": 0.86}
    assert gaps["impact /3"] == {"Almgren-Chriss (model)": 1.21, "TWAP": 4.99, "DQN": 4.6, "DQN, noisy reward": 4.99,
                                 "DQN, randomised": 1.24}
    assert (round(e["grid"], 2), round(e["model"]["optimum"] + e["grid"], 2)) == (0.2, 19.05)
    assert round(e["model"]["optimum"] + e["model"]["DQN"], 2) == 19.29
    a = m.agents()
    assert np.allclose(a["DQN, noisy reward"](m.ETA), a["TWAP"](m.ETA))
    dr, ac = a["DQN, randomised"](m.ETA), a["Almgren-Chriss (model)"](m.ETA)
    assert dr[1] > ac[1]


def test_market_making():
    r = m.market_making()
    got = {k: (round(v["objective"], 2), round(v["se"], 2), round(v["pnl sd"], 2), round(v["abs q_T"], 2),
               round(v["fills"], 1)) for k, v in r.items() if k != "cj depths at t=0"}
    assert got == {"Cartea-Jaimungal optimum": (67.95, 0.12, 8.53, 2.67, 101.8),
                   "Avellaneda-Stoikov, gamma 0.1": (64.73, 0.09, 6.5, 2.26, 97.0),
                   "constant 1/k": (66.67, 0.17, 11.61, 5.03, 101.0),
                   "Q-learning, 2000 episodes": (62.34, 0.12, 8.31, 4.4, 91.7),
                   "Q-learning, 8000 episodes": (62.84, 0.12, 8.53, 4.38, 93.1)}
    b, a = r["cj depths at t=0"]
    assert (round(float(b[1]), 2), round(float(a[1]), 2), round(float(a[2]), 2), round(float(b[2]), 2)) == (0.68, 0.68, 0.57,
                                                                                                          0.79)
    assert (m.MM.n_time * (2 * m.MM.qmax + 1), len(m.MM.actions), 8000 * m.MM.n) == (420, 36, 1_600_000)


def test_exercises():
    impact = 10 * 0.001 * 0.1**2 / 0.1
    risk = 10 * 0.02**2 * 0.1 * sum((k / 10) ** 2 for k in range(1, 10))
    assert (round(impact, 6), round(risk, 6), round(1e4 * (impact + risk), 1)) == (0.001, 0.00114, 21.4)
    assert round(1 / m.MM.k, 2) == 0.67 and round(1e4 * 0.02 * math.sqrt(0.1)) == 63
    best, score = m.linear_policy_search()
    assert (round(best[0], 2), best[1], round(score, 2)) == (0.7, 0.03, 67.82)
