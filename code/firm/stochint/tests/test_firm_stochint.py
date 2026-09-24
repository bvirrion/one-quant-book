"""Acceptance tests of firm.stochint."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_stochint import covariation, gains, lookahead_test, riemann_sums, same_bar_gains


def _walk(n, seed):
    rng = np.random.default_rng(seed)
    return np.concatenate([[0.0], np.cumsum(rng.standard_normal(n))])


def test_adapted_gains_have_mean_zero_for_any_rule():
    means = []
    for seed in range(200):
        s = _walk(500, seed)
        c = np.cumsum(np.concatenate([[0.0], s]))
        ma = np.concatenate([s[:9], (c[10:] - c[:-10]) / 10])                 # trailing 10-step average
        theta = np.tanh(s - ma)                                                # reads the current price
        means.append(gains(theta, s)[-1] / 500)
    assert abs(np.mean(means)) < 3 * np.std(means) / math.sqrt(len(means))


def test_identity_and_detection():
    s = _walk(5000, 1)
    theta = s - np.concatenate([[0.0], s[:-1]])          # position = latest increment: blatant look-ahead
    r = lookahead_test(theta, s)
    assert r["identity_error"] < 1e-9 and r["t"] > 20
    assert np.allclose(same_bar_gains(theta, s) - gains(theta, s), covariation(theta, s))


def test_quadratic_variation_and_riemann_sums():
    rng = np.random.default_rng(2)
    n = 2**16
    w = np.concatenate([[0.0], np.cumsum(rng.standard_normal(n) / math.sqrt(n))])
    assert abs(covariation(w, w)[-1] - 1) < 0.02
    left, right, mid = (riemann_sums(lambda x: x, w, p) for p in ("left", "right", "mid"))
    assert abs(left - (w[-1] ** 2 - 1) / 2) < 0.02 and abs(right - (w[-1] ** 2 + 1) / 2) < 0.02
    assert abs(mid - w[-1] ** 2 / 2) < 1e-9


def test_alignment_is_checked():
    try:
        gains(np.zeros(3), np.zeros(4))
    except ValueError:
        return
    raise AssertionError("misaligned inputs accepted")
