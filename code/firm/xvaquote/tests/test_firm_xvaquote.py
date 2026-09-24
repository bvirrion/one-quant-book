import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_xvaquote as f
from firm_cdscurve import HazardCurve

T = np.linspace(0.0, 5.0, 21)
C = HazardCurve([5.0], [0.03])


def test_euler_contributions_add_up_and_scale():
    rng = np.random.default_rng(2)
    vals = [rng.normal(0, 1e6, (2000, 21)).cumsum(axis=1) * 0.3, rng.normal(0, 1e6, (2000, 21)).cumsum(axis=1) * 0.2]
    D = np.ones((2000, 21))
    total = f.netting_cva(vals, D, T, C)
    alloc = f.euler_cva(vals, D, T, C)
    assert abs(sum(alloc) - total) < 1e-6 * total
    assert math.isclose(f.euler_cva([2 * v for v in vals], D, T, C)[0], 2 * alloc[0], rel_tol=1e-12)


def test_incremental_and_standalone():
    def adj(vs):
        return float(np.maximum(np.sum(vs, axis=0), 0).mean())

    a, b = np.array([[1.0, -2.0]]), np.array([[-1.0, 1.0]])
    r = f.incremental(adj, [a], b)
    assert r["incremental"] == r["with"] - r["base"] and r["standalone"] == 0.5


def test_proxy_recovers_a_multiplicative_table():
    peers = [(r, s, g, 0.01 * fr * fs * fg) for r, fr in (("A", 1.0), ("B", 2.0)) for s, fs in (("x", 1.0), ("y", 1.5))
             for g, fg in (("US", 1.0), ("EU", 1.2))]
    p = f.proxy_spread(peers[:-1], ("B", "y", "EU"))
    assert abs(p["spread"] - 0.01 * 2.0 * 1.5 * 1.2) < 1e-12 and p["rmse"] < 1e-12
    assert math.isclose(f.running_charge(1e6, 1e8, 8.0), 1e6 / 8e8)
