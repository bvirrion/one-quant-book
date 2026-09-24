"""Acceptance tests of the Book 5, Chapter 15 build (barriers and digitals)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_barrier import (
    barrier,
    bgk_shift,
    calendar_hedge,
    call_spread,
    digital,
    digital_smile,
    double_no_touch,
    hit_probability,
    mc_barrier,
    no_touch,
    one_touch,
    symmetry_down_in_call,
)
from firm_bs import bs

S, R, Q, V, T = 100.0, 0.03, 0.01, 0.25, 1.0


def test_in_out_parity_every_case():
    for h, kinds in ((90.0, ("down-in", "down-out")), (112.0, ("up-in", "up-out"))):
        for right in "CP":
            for k in (80.0, 95.0, 100.0, 105.0, 120.0):
                total = barrier(S, k, h, T, R, Q, V, kinds[0], right) + barrier(S, k, h, T, R, Q, V, kinds[1], right)
                assert abs(total - bs(S, k, T, R, Q, V, right)) < 1e-10


def test_far_barrier_and_positivity():
    assert abs(barrier(S, 100.0, 1e-3, T, R, Q, V, "down-out", "C") - bs(S, 100.0, T, R, Q, V, "C")) < 1e-10
    for kind in ("down-out", "down-in"):
        for right in "CP":
            assert barrier(S, 100.0, 85.0, T, R, Q, V, kind, right) >= 0


def test_discrete_monitoring_against_monte_carlo():
    for kind, h, right in (("down-out", 90.0, "C"), ("up-out", 120.0, "C"), ("down-in", 90.0, "P")):
        mc, se = mc_barrier(S, 100.0, h, T, R, Q, V, kind, right, 252)
        shifted = barrier(S, 100.0, bgk_shift(h, S, V, T / 252), T, R, Q, V, kind, right)
        assert abs(mc - shifted) < 3 * se + 0.01


def test_touches():
    p = hit_probability(S, 90.0, T, R, Q, V)
    assert abs(one_touch(S, 90.0, T, R, Q, V, False) - math.exp(-R * T) * p) < 1e-14
    assert abs(one_touch(S, 90.0, T, R, Q, V, False) + no_touch(S, 90.0, T, R, Q, V) - math.exp(-R * T)) < 1e-14
    assert one_touch(S, 90.0, T, R, Q, V, True) > one_touch(S, 90.0, T, R, Q, V, False)
    # double no-touch: tends to the single no-touch when the other barrier is far, and matches a simulation
    assert abs(double_no_touch(S, 90.0, 1e4, T, R, Q, V) - no_touch(S, 90.0, T, R, Q, V)) < 1e-6
    rng = np.random.default_rng(3)
    n, steps = 20_000, 2000
    dt = T / steps
    x = np.full(n, math.log(S))
    alive = np.ones(n, bool)
    for _ in range(steps):
        x += (R - Q - 0.5 * V * V) * dt + V * math.sqrt(dt) * rng.standard_normal(n)
        alive &= (x > math.log(80.0)) & (x < math.log(125.0))
    mc = math.exp(-R * T) * alive.mean()
    dnt = double_no_touch(S, bgk_shift(80.0, S, V, dt), bgk_shift(125.0, S, V, dt), T, R, Q, V)
    assert abs(mc - dnt) < 4 * math.sqrt(mc * (1 - mc) / n)


def test_digitals_and_overhedge():
    flat = digital(S, 100.0, T, R, Q, V)
    assert abs(digital_smile(S, 100.0, T, R, Q, lambda k: V) - flat) < 1e-6
    skew = digital_smile(S, 100.0, T, R, Q, lambda k: V - 0.002 * (k - 100.0))
    assert skew > flat                                      # a downside skew makes the up-digital dearer
    for w in (1.0, 5.0, 20.0):
        assert call_spread(S, 100.0, T, R, Q, lambda k: V, w, below=True) > flat
        assert call_spread(S, 100.0, T, R, Q, lambda k: V, w, below=False) < flat


def test_static_hedges():
    assert abs(symmetry_down_in_call(100.0, 90.0, 100.0, 1.0, 0.2)
               - barrier(100.0, 100.0, 90.0, 1.0, 0.0, 0.0, 0.2, "down-in", "C")) < 1e-10
    uoc = barrier(100.0, 100.0, 120.0, 1.0, 0.0, 0.0, 0.2, "up-out", "C")
    errs = [calendar_hedge(100.0, 100.0, 120.0, 1.0, 0.0, 0.0, 0.2, n)[1] - uoc for n in (8, 16, 32)]
    assert errs[0] > errs[1] > errs[2] > 0 and errs[2] < 0.1
