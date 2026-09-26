import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_labeling import (
    attribution_weights,
    average_uniqueness,
    concurrency,
    fixed_horizon,
    meta_labels,
    sequential_bootstrap,
    time_decay,
    triple_barrier,
    vol_widths,
)


def test_fixed_horizon_by_hand():
    r = np.array([0.0, 0.01, -0.02, 0.03, 0.01])
    out = fixed_horizon(r, [0, 1], 2)
    assert np.allclose(out["ret"], [-0.01, 0.01]) and list(out["t1"]) == [2, 3] and list(out["label"]) == [-1, 1]


def test_triple_barrier_touches():
    r = np.array([0.0, 0.01, 0.01, -0.05, 0.02, 0.0, 0.0])
    up = triple_barrier(r, [0], 0.015, 0.03, 5)                         # +2% after bar 2: profit first
    assert up["hit"][0] == "up" and up["t1"][0] == 2 and up["label"][0] == 1
    dn = triple_barrier(r, [0], 0.05, 0.02, 5)                          # -3% after bar 3: stop first
    assert dn["hit"][0] == "down" and dn["t1"][0] == 3 and abs(dn["ret"][0] + 0.03) < 1e-12
    tm = triple_barrier(r, [0], np.inf, np.inf, 4)
    assert tm["hit"][0] == "time" and tm["t1"][0] == 4
    short = triple_barrier(r, [0], 0.02, 0.05, 5, side=[-1])           # a short gains 3% when the price falls
    assert short["hit"][0] == "up" and short["label"][0] == 1
    assert np.allclose(vol_widths([0.01, 0.02], [1], 4, 2.0), [0.08])
    assert list(meta_labels([1, -1, 1], [0.01, 0.02, -0.01])) == [1, 0, 0]


def test_concurrency_and_uniqueness():
    t0, t1 = np.array([0, 1, 5]), np.array([3, 4, 7])                   # spans (0,3], (1,4], (5,7]
    assert list(concurrency(t0, t1, 8)) == [0, 1, 2, 2, 1, 0, 1, 1]
    u = average_uniqueness(t0, t1, 8)
    assert np.allclose(u, [(1 + 0.5 + 0.5) / 3, (0.5 + 0.5 + 1) / 3, 1.0])
    w = attribution_weights(t0, t1, np.array([0, 0.03, 0.02, 0.02, 0.01, 0, 0.0, 0.0]), 8)
    assert abs(w.mean() - 1) < 1e-12 and w[2] == 0.0
    d = time_decay(np.ones(4), 0.5)
    assert np.allclose(d, [0.625, 0.75, 0.875, 1.0])


def test_sequential_bootstrap_raises_uniqueness():
    t0 = np.arange(200)
    t1 = t0 + 10
    rng = np.random.default_rng(3)
    plain = [average_uniqueness(t0[i], t1[i], 212).mean() for i in (rng.integers(0, 200, 20) for _ in range(40))]
    seq = [average_uniqueness(t0[i], t1[i], 212).mean() for i in (sequential_bootstrap(t0, t1, 212, 20, rng)
                                                                   for _ in range(40))]
    assert np.mean(seq) > np.mean(plain) + 0.03
