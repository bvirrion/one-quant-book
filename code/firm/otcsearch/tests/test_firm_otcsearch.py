import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_otcsearch import (  # noqa: E402
    best_n,
    chase,
    core_periphery,
    dgp,
    intermediation,
    rfq_cost,
    rfq_simulate,
)


def test_dgp_steady_state_and_prices():
    m = dgp(2.0, 0.2, 50.0, 0.8, 0.05, 2.0, 0.8)
    ho, hn, lo, ln = m["mu"]
    assert np.isclose(ho + lo, 0.8) and np.isclose(ho + hn, 2.0 / 2.2) and np.isclose(sum(m["mu"]), 1.0)
    assert np.isclose(0.2 * ho, (2.0 + 50.0) * lo)                          # low owners: in = out
    assert m["ask"] > m["bid"] and np.isclose(m["spread"], 0.8 * (m["dV"][0] - m["dV"][1]))
    faster = dgp(2.0, 0.2, 500.0, 0.8, 0.05, 2.0, 0.8)
    assert faster["spread"] < m["spread"]                                  # easier access: tighter
    assert dgp(2.0, 0.2, 50.0, 0.8, 0.05, 2.0, 0.0)["spread"] == 0.0


def test_rfq_costs():
    assert np.isclose(rfq_cost(3, 10.0, 5.0, 0.0, 1.0), 10.0 - 5.0 * 0.846284 + 2.0, atol=1e-4)
    assert abs(rfq_simulate(4, 10.0, 5.0, 2.0, 0.5, 200_000) - rfq_cost(4, 10.0, 5.0, 2.0, 0.5)) < 0.03
    assert best_n(10.0, 5.0, 2.0, 0.0) == 20 and best_n(10.0, 5.0, 2.0, 5.0) == 1
    assert best_n(10.0, 5.0, 2.0, 0.5) > best_n(10.0, 5.0, 2.0, 2.0)


def test_chasing_and_network():
    c = chase(2.0, 1.0, 3.0)
    assert c["informed"] < c["uninformed"]
    adj = core_periphery(5, 40, 1, seed=3)
    assert all(len(adj[i]) >= 4 for i in range(5)) and all(len(adj[p]) == 1 for p in range(5, 45))
    r = intermediation(adj, 5, 3.0, 1.0, trials=4000, seed=2)
    assert r["periphery"]["hops"] > r["core"]["hops"]
