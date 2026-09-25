import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_intraday import DayConfig, decompose, last_half_hour, simulate_days, volume_curve  # noqa: E402


def test_volume_and_decomposition():
    w = volume_curve(13, 1.5)
    assert abs(w.sum() - 1) < 1e-12 and w[0] == w[-1] and w[6] == w.min()
    on, day = decompose([100.0, 101.0, 99.0], [100.5, 100.0, 99.5])
    assert np.allclose(on, [math.log(101 / 100.5), math.log(99 / 100.0)]) and np.allclose(day[0], math.log(100.5 / 100))


def test_variance_split_and_gamma():
    d = simulate_days(20000, DayConfig(), np.random.default_rng(1))
    tot = d["overnight"] + d["bars"].sum(axis=1)
    assert abs(d["overnight"].var() / tot.var() - 0.25) < 0.03
    assert abs(last_half_hour(d["bars"], d["overnight"])[1]) < 3
    g = simulate_days(20000, DayConfig(gamma=0.05, imbalance_impact=0.0), np.random.default_rng(1))
    slope, t = last_half_hour(g["bars"], g["overnight"])
    assert abs(slope - 0.05) < 0.01 and t > 10
