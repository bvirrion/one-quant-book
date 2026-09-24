"""Acceptance tests of the Book 5, Chapter 16 build (path-dependent payoffs)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_bs import bs
from firm_pathdep import (
    asian_mc,
    asian_payoff,
    cliquet_payoff,
    forward_smile_from_paths,
    forward_start_call,
    gbm_paths,
    geometric_asian,
    lookback_floating_call,
    lookback_payoff,
    lookback_shifted,
    period_returns,
    reverse_cliquet_payoff,
)


def test_geometric_asian():
    # one fixing at expiry: the vanilla
    assert abs(geometric_asian(100, 95, 1.0, 0.03, 0.01, 0.2, 1) - bs(100, 95, 1.0, 0.03, 0.01, 0.2, "C")) < 1e-12
    p = gbm_paths(100.0, np.arange(1, 13) / 12, 0.03, 0.01, 0.2, 200_000, 1)
    mc = math.exp(-0.03) * asian_payoff(p, 100.0, geometric=True)
    assert abs(mc.mean() - geometric_asian(100, 100, 1.0, 0.03, 0.01, 0.2, 12)) < 4 * mc.std() / math.sqrt(len(mc))
    put = geometric_asian(100, 100, 1.0, 0.03, 0.01, 0.2, 12, "P")
    assert put > 0


def test_control_variate():
    r = asian_mc(100, 100, 1.0, 0.03, 0.01, 0.2, 12, n_paths=50_000)
    assert r["cv_se"] < r["plain_se"] / 10 and abs(r["cv"] - r["plain"]) < 4 * r["plain_se"]
    assert r["geometric"] < r["cv"]                         # AM-GM: the arithmetic average is larger


def test_lookback():
    c = lookback_floating_call(100, 100, 1.0, 0.03, 0.01, 0.2)
    assert c > bs(100, 100, 1.0, 0.03, 0.01, 0.2, "C")
    p = gbm_paths(100.0, np.arange(1, 253) / 252, 0.03, 0.01, 0.2, 100_000, 2)
    mc = math.exp(-0.03) * lookback_payoff(p)
    assert abs(mc.mean() - lookback_shifted(100, 1.0, 0.03, 0.01, 0.2, 252)) < 4 * mc.std() / math.sqrt(len(mc))
    assert mc.mean() < c


def test_forward_start_and_smile():
    assert abs(forward_start_call(100, 1.0, 0.5, 1.0, 0.0, 0.0, 0.2) - 100 * bs(1, 1, 0.5, 0, 0, 0.2, "C")) < 1e-12
    p = gbm_paths(100.0, [0.5, 1.0], 0.0, 0.0, 0.2, 200_000, 5)
    fs = forward_smile_from_paths(p, 1, 2, 0.5, [0.9, 1.0, 1.1])
    assert np.allclose(fs, 0.2, atol=0.003)


def test_cliquets():
    p = np.array([[100.0, 110.0, 99.0, 99.0]])
    r = period_returns(p)
    assert np.allclose(r, [[0.1, -0.1, 0.0]])
    assert abs(cliquet_payoff(p, -0.05, 0.05)[0] - 0.0) < 1e-12
    assert abs(cliquet_payoff(p, -0.2, 0.02, 0.0)[0] - 0.0) < 1e-12
    assert abs(cliquet_payoff(p, -0.02, 0.2)[0] - 0.08) < 1e-12
    assert abs(reverse_cliquet_payoff(p, 0.25)[0] - 0.15) < 1e-12
    assert reverse_cliquet_payoff(p, 0.05)[0] == 0.0
