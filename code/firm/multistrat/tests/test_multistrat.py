import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_multistrat import PodConfig, allocate, netting, run_firm, simulate_pods, stop_rate  # noqa: E402


def test_pods_share_factors_and_crash():
    S = simulate_pods(PodConfig(days=252 * 10, crash_days=((1000, 10),), dead_day=2000), np.random.default_rng(1))
    c = np.corrcoef(S["pnl"].T)
    assert c[0, 1] > 0.1 and abs(c[0, 7]) < 0.1
    assert S["pnl"][1000:1010, 0].sum() < -0.1


def test_allocation_cap_and_netting():
    pnl = np.random.default_rng(0).standard_normal((300, 4)) * np.array([0.01, 0.01, 0.02, 0.02])
    load = np.array([[0.5, 0], [0.5, 0], [0, 0], [0, 0]])
    w = allocate(pnl, load, 300, 252, None)
    assert math.isclose(w.sum(), 1.0) and w[0] > w[2]
    wc = allocate(pnl, load, 300, 252, 0.5)
    assert wc[0] < w[0] and math.isclose(wc.sum(), 1.0)
    assert math.isclose(netting([[1.0, 2.0], [-1.0, 1.0]]), 1 - 3 / 5)


def test_stops():
    assert stop_rate(0.7, 0.10, 0.05, 1.0, 5000) > stop_rate(0.7, 0.10, 0.20, 1.0, 5000)
    S = simulate_pods(PodConfig(days=252 * 6, crash_days=(), dead_day=1000), np.random.default_rng(2))
    f, stops = run_firm(S, 21, None, 0.05)
    assert len(stops) > 0 and all(t >= 252 for _, t in stops)
