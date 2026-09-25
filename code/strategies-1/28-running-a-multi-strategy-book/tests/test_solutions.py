"""Numbers gate: every numerical answer printed in Book 8, chapter 28 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_multistrat import LIMITS, correlations, limits, net_savings, overlap, stop_rate  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_overlap():
    c = correlations()
    assert (r(c["same_factor"]), r(c["other"], 3), [r(x, 1) for x in c["crash_pod_loss"]]) == \
        (0.22, -0.004, [-2.4, -2.4, -2.6])
    got = {cap: (r(overlap(cap)["sr"]), r(100 * overlap(cap)["mdd"], 1), [r(100 * x, 1) for x in overlap(cap)["crash"]])
           for cap in (None, 1.0, 0.5)}
    assert got == {None: (1.45, 43.5, [-31.5, -31.7, -33.6]), 1.0: (1.52, 42.8, [-30.1, -30.1, -32.3]),
                   0.5: (1.7, 35.7, [-21.6, -20.7, -22.9])}


def test_limits():
    got = {lim: (r(100 * limits(lim)["per_pod_year"], 1), limits(lim)["dead_days"], r(100 * limits(lim)["paths"], 1))
           for lim in LIMITS}
    assert got == {0.05: (85.8, 98, 91.6), 0.1: (38.9, 307, 34.5), 0.15: (22.1, 979, 8.9), 0.2: (14.7, None, 2.1),
                   0.3: (5.8, None, 0.0)}


def test_netting_and_exercises():
    assert [r(x, 3) for x in net_savings()] == [0.346, 0.685]
    assert r(1 - 1 / math.sqrt(10), 3) == 0.684 and r(0.4 * 6, 1) == 2.4
    assert r(100 * stop_rate(0.7, 0.05, 0.05, 1.0, 20_000, np.random.default_rng(1)), 1) == 34.5


def test_strict_cap_and_brownian():
    from statistics import NormalDist
    o = overlap(0.25)
    assert (r(o["sr"]), r(100 * o["mdd"], 1), [r(100 * x, 1) for x in o["crash"]]) == (1.72, 28.0, [-12.2, -11.1, -13.0])
    assert r(2 * (1 - NormalDist().cdf(0.5)), 3) == 0.617
