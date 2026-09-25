import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_xasset import detect, diffuse, lead_scan, lead_trades, signal, simulate_pair  # noqa: E402


def test_diffuse_and_signal_by_hand():
    lead = np.array([[1.0], [2.0], [3.0], [4.0]])
    out = diffuse(np.zeros((4, 1)), lead, [(0, 0)], 0.5, 2)
    assert np.allclose(out[:, 0], [0.0, 0.5 * 1 / 2, 0.5 * 3 / 2, 0.5 * 5 / 2])
    assert np.allclose(signal(lead, [(0, 0)], 2, 1)[:, 0], [0, 0, 5, 7])


def test_scan_finds_a_planted_lag():
    rng = np.random.default_rng(0)
    lead = rng.standard_normal((5000, 2))
    fol = rng.standard_normal((5000, 2))
    fol[3:, 1] += 0.2 * lead[:-3, 0]
    t = lead_scan(lead, fol, range(1, 6))
    hits, thr = detect(t, t.size)
    assert (2, 0, 1) in hits and len(hits) == 1 and thr > 3


def test_pair_lead_and_trades():
    t1, x1, t2, x2 = simulate_pair(2000, 2, 1e-4, 0.0, 5.0, np.random.default_rng(1))
    assert t1.min() >= 0 and t2.max() <= 2000
    g1 = np.cumsum(np.r_[0.0, np.ones(20) * 1e-4])
    g2 = np.r_[0.0, 0.0, g1[:-2]]
    tr = lead_trades(g1, g2, 2, 0, 2, 1.5e-4, 0.25e-4)
    assert len(tr) > 0 and math.isclose(tr[0], 2e-4 - 0.5e-4)
