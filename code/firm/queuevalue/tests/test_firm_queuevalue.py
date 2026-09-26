import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_queuevalue import (  # noqa: E402
    ENTRY,
    empirical,
    eta_hat,
    expected_time_to_fill,
    fill_probability,
    implicit_spread,
    slot_value,
)


def test_birth_death_against_simulation():
    rng = np.random.default_rng(1)
    n, mu, theta, nu = 4, 1.0, 0.2, 0.1
    filled = 0
    for _ in range(20_000):
        k = n
        while True:
            u = rng.random() * (mu + k * theta + nu)
            if u < nu:
                break
            if u < nu + mu and k == 0:
                filled += 1
                break
            k -= 1
    assert abs(filled / 20_000 - fill_probability(n, mu, theta, nu)) < 0.01
    assert math.isclose(expected_time_to_fill(0, 2.0, 0.5), 0.5)
    assert math.isclose(expected_time_to_fill(1, 1.0, 1.0), 1.5)
    assert math.isclose(slot_value(0, 1.0, 0.0, 1.0, 0.5, 0.3), 0.1)


def test_empirical_buckets_by_hand():
    e = np.zeros(3, ENTRY)
    e["ahead"] = [0, 0, 2000]
    e["qty"] = 100
    e["filled"] = [100, 0, 100]
    e["t"] = [0.0, 0.0, 1.0]
    e["t_fill"] = [2.0, np.nan, 11.0]
    e["capture"] = [50.0, 0.0, 50.0]
    e["adverse"] = [-20.0, 0.0, -80.0]
    front, back = empirical(e)
    assert (front["orders"], front["fill"], front["t_fill"]) == (2, 0.5, 2.0)
    assert (front["capture"], front["adverse"], front["value"]) == (0.5, 0.2, 0.15)
    assert (back["fill"], back["t_fill"], round(back["value"], 6)) == (1.0, 10.0, -0.3)


def test_uncertainty_zone():
    # up, up (continuation), down (alternation), down (continuation), up (alternation), up two ticks (ignored)
    p = [0, 1, 2, 1, 0, 1, 3]
    got = eta_hat(p)
    assert (got["continuations"], got["alternations"], got["eta"]) == (2, 2, 0.5)
    assert implicit_spread(0.25, 0.05) == 0.025
    # a pure bounce: all alternations, eta = 0
    assert eta_hat([0, 1, 0, 1, 0, 1])["eta"] == 0.0
