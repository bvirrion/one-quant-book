"""Numbers gate: every numerical answer printed in Book 12, chapter 17 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_rl as m  # noqa: E402
from firm_rlcore import liquidation_mdp, rollouts  # noqa: E402


def test_exact_problem():
    mm = m.mdp()
    assert mm.n_states == 242
    b = {k: round(float(v), 2) for k, v in m.benchmarks().items()}
    assert b == {"optimal": 2.59, "desk": 3.27, "TWAP": 6.76}
    _, pi = m.optimum()
    assert [int(pi[mm.idx(0, 10, liq)]) for liq in (0, 1)] == [5, 2] and int(m.desk()[mm.idx(0, 10, 0)]) == 3
    V, _ = m.optimum()
    assert (V[mm.idx(9, 3, 1)], V[mm.idx(9, 3, 0)]) == (-18.0, -4.5)
    assert round(0.2 * sum(k * k for k in range(1, 10))) == 57


def test_learning_curves():
    lc = {k: [round(float(x), 3) for x in v] for k, v in m.learning_curves().items()}
    assert (lc["Q-learning"][2], lc["Q-learning"][4]) == (1.408, 0.044)
    assert (lc["SARSA"][2], lc["SARSA"][4]) == (0.284, 0.051)
    assert (lc["REINFORCE"][2], lc["REINFORCE"][4]) == (0.311, 0.067)
    assert (lc["actor-critic"][2], lc["actor-critic"][4]) == (0.106, 0.009)
    assert round(lc["Q-learning"][2], 2) == 1.41 and round(lc["SARSA"][2], 2) == 0.28


def test_bandits():
    b = {k: (round(float(v[0][-1])), round(100 * v[1])) for k, v in m.bandits().items()}
    assert b == {"epsilon 0.1": (1727, 78), "epsilon 0.01": (2026, 65), "UCB, c = 1.41": (1325, 83),
                 "UCB, c = 1": (944, 87)}


def test_off_policy():
    o = m.off_policy()
    assert (round(o["truth"], 2), round(o["behaviour"], 2)) == (2.77, 3.80)
    r = {k: (round(o[k][0], 2), round(o[k][1], 2), round(float(np.hypot(*o[k])), 2)) for k in ("IS", "WIS", "model", "DR")}
    assert r == {"IS": (0.20, 1.75, 1.76), "WIS": (0.49, 0.63, 0.80), "model": (0.30, 0.0, 0.30),
                 "DR": (-0.03, 0.29, 0.29)}


def test_sim_to_real():
    s = {k: round(float(v), 2) for k, v in m.sim_to_real().items()}
    assert s == {"agent in simulator": 2.77, "desk in simulator": 3.66, "agent in market": 3.83,
                 "desk in market": 3.27, "optimal in market": 2.59}
    assert round(s["desk in simulator"] - s["agent in simulator"], 1) == 0.9
    assert round(s["agent in market"] - s["desk in market"], 1) == 0.6


def test_exercises():
    assert round((2 * 5 * 2**0.5 / 0.3) ** 2, -2) == 2200
    assert round(-10 + 0.1 * (-3 - 5 + 10), 2) == -9.8 and round(-10 + 0.1 * (-3 - 8 + 10), 2) == -10.1
    Pb, Pe = m.behaviour_and_target()
    eps = rollouts(m.mdp(), Pb, 2000, seed=5)
    w = np.array([np.prod([Pe[s, u] / pb for s, u, _, pb in ep]) for ep in eps])
    assert (f"{np.median(w):.1e}", round(float(np.percentile(w, 99)), 2), round(float(w.max())),
            round(100 * float(w.max() / w.sum()))) == ("2.8e-05", 1.56, 797, 78)
    t = liquidation_mdp(drain=0.1)
    V, pi = t.solve()
    assert (round(-V[t.start] / 10, 2), [int(pi[t.idx(0, 10, liq)]) for liq in (0, 1)]) == (3.01, [5, 3])
