import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_algowheel import (  # noqa: E402
    Thompson,
    evaluate,
    months_needed,
    random_allocation,
    scorecard,
    stratified_allocation,
)


def test_allocations_balance():
    rng = np.random.default_rng(0)
    d = rng.lognormal(2.0, 1.0, 6000)
    s = stratified_allocation(d, 6, 10, rng)
    r = random_allocation(6000, 6, rng)
    assert np.ptp(np.bincount(s)) <= 20 and set(np.unique(r)) == set(range(6))
    assert np.ptp([d[s == j].mean() for j in range(6)]) < np.ptp([d[r == j].mean() for j in range(6)])


def test_evaluation_recovers_effects_and_power_formula():
    rng = np.random.default_rng(1)
    n, k = 20_000, 3
    b = rng.integers(0, k, n)
    d = rng.lognormal(2.0, 0.8, n) + 5.0 * (b == 2)                  # broker 2 gets harder orders
    y = np.array([0.0, 2.0, 1.0])[b] + d + rng.normal(0, 10, n)
    ev = evaluate(y, b, d, k)
    assert np.allclose(ev["mean"] - ev["mean"][0], [0, 2, 1], atol=0.5)
    raw = evaluate(y, b, d, k, adjust=False)
    assert raw["mean"][2] - raw["mean"][0] > 5
    assert np.isclose(months_needed(3.0, 30.0, 600, 6), 2 * 900 * (1.959964 + 0.841621) ** 2 / 9 * 6 / 600, rtol=1e-4)
    card = scorecard(y, b, d, k, ["a", "b", "c"])
    assert [c[5] for c in card] == [1, 3, 2]


def test_thompson_concentrates_on_the_best():
    rng = np.random.default_rng(2)
    t = Thompson(3, 10.0, 10.0, 5.0)
    true = np.array([5.0, 8.0, 12.0])
    picks = []
    for _ in range(2000):
        j = t.choose(rng)
        t.update(j, true[j] + rng.normal(0, 5.0))
        picks.append(j)
    assert np.mean(np.array(picks[-500:]) == 0) > 0.8 and abs(t.m[0] - 5.0) < 0.5
