import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_spreaddecomp import (  # noqa: E402
    abdi_ranaldo,
    corwin_schultz,
    decompose,
    glosten_harris,
    hasbrouck_var,
    huang_stoll,
    mid_at,
    mrr,
    quoted_spread,
)

TRD = np.dtype([("t", "f8"), ("price", "f8"), ("qty", "i8"), ("sign", "i1")])


def test_identity_and_quoted():
    times, mids = np.array([0.0, 5.0]), np.array([100.0, 100.02])
    tr = np.array([(1.0, 100.01, 100, 1), (2.0, 99.99, 100, -1)], dtype=TRD)
    d = decompose(tr, times, mids, 10.0)
    assert math.isclose(d["effective"], d["realised"] + d["impact"])
    assert math.isclose(d["effective"], 0.01) and math.isclose(d["impact"], 0.0)            # +0.02 and -0.02 cancel
    assert math.isclose(quoted_spread([0, 1], [99, 99], [101, 100], 2.0), 1.5)
    assert mid_at(times, mids, [4.9, 5.0]).tolist() == [100.0, 100.02]


def _market(n=60_000, half=0.5, theta=0.3, rho=0.0, seed=1):
    """MRR's model: value moves theta per unit surprise; price = value + (phi) x with phi = half - theta."""
    rng = np.random.default_rng(seed)
    x = np.empty(n)
    x[0] = 1.0
    for t in range(1, n):
        x[t] = x[t - 1] if rng.random() < (1 + rho) / 2 else -x[t - 1]
    surprise = x - rho * np.concatenate([[0.0], x[:-1]])
    v = np.cumsum(theta * surprise + 0.05 * rng.standard_normal(n))
    return v + (half - theta) * x, x, v


def test_structural_estimators_recover_a_planted_model():
    p, x, _ = _market(theta=0.3, rho=0.0)
    m = mrr(p, x)
    assert abs(m["theta"] - 0.3) < 0.01 and abs(m["phi"] - 0.2) < 0.01
    hs = huang_stoll(p, x)
    assert abs(hs["spread"] - 1.0) < 0.02 and abs(hs["lam"] - 0.6) < 0.03                 # lam = theta / (S/2)
    p2, x2, _ = _market(theta=0.3, rho=0.4, seed=2)
    assert abs(mrr(p2, x2)["theta"] - 0.3) < 0.02 and abs(mrr(p2, x2)["rho"] - 0.4) < 0.02


def test_var_and_low_frequency():
    rng = np.random.default_rng(3)
    n = 40_000
    x = rng.choice([-1.0, 1.0], n)
    r = 0.2 * x + 0.05 * rng.standard_normal(n)                                            # permanent 0.2 at once
    assert abs(hasbrouck_var(r, x)["permanent"] - 0.2) < 0.01
    # a random walk quoted with relative spread 1%: daily high/low/close of 390 minutes
    ret = 0.0005 * rng.standard_normal(390 * 400)
    mid = 100 * np.exp(np.cumsum(ret)).reshape(400, 390)
    side = rng.choice([-1.0, 1.0], mid.shape)
    px = mid * (1 + 0.005 * side)
    cs = corwin_schultz(px.max(1), px.min(1))
    ar = abdi_ranaldo(px[:, -1], px.max(1), px.min(1))
    assert 0.005 < cs < 0.02 and 0.005 < ar < 0.015


def test_glosten_harris_recovers_size_dependent_components():
    rng = np.random.default_rng(4)
    n = 50_000
    e = rng.choice([-1.0, 1.0], n)
    v = rng.integers(1, 6, n).astype(float)
    m = np.cumsum(e * (0.1 + 0.05 * v) + 0.05 * rng.standard_normal(n))
    p = m + e * (0.2 + 0.01 * v)
    g = glosten_harris(p, e, v)
    assert abs(g["z0"] - 0.1) < 0.01 and abs(g["z1"] - 0.05) < 0.005
    assert abs(g["c0"] - 0.2) < 0.01 and abs(g["c1"] - 0.01) < 0.005
