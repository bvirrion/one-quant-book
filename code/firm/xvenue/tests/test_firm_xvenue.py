import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_xvenue as xv  # noqa: E402


def _pair(n=20000, lag=3, seed=1):
    """A random walk, market 1 sees it at once, market 2 `lag` steps later, each with its own noise."""
    rng = np.random.default_rng(seed)
    w = np.cumsum(rng.normal(size=n + lag))
    return w[lag:] + 0.3 * rng.normal(size=n), w[:n] + 0.3 * rng.normal(size=n)


def test_leader_gets_the_larger_shares():
    p1, p2 = _pair()
    s = xv.shares(p1, p2, lags=5)
    assert s["component"] > 0.8 and s["is_low"] > 0.8 and s["is_low"] <= s["is_high"] <= 1.0
    s2 = xv.shares(p2, p1, lags=5)
    assert s2["component"] < 0.2


def test_lead_estimate_on_a_grid():
    p1, p2 = _pair(n=6000, lag=4, seed=2)
    t = np.arange(6000) * 0.1
    est, _ = xv.lead(t, p1, t, p2, np.arange(-10, 11) * 0.1)
    assert abs(est - 0.4) < 1e-9


def test_lead_edge_by_hand():
    lt = np.array([0.0, 2.0, 2.5])
    lm = np.array([100.0, 100.0, 102.0])                       # the leader jumps two ticks at 2.5
    ft = np.array([0.0, 3.0, 20.0])
    fb, fa = np.array([99.5, 101.5, 101.5]), np.array([100.5, 102.5, 102.5])   # the follower moves at 3.0
    early = xv.lead_edge(lt, lm, ft, fb, fa, latency=0.1, H=5.0)
    late = xv.lead_edge(lt, lm, ft, fb, fa, latency=1.0, H=5.0)
    assert early["trades"] == 1 and early["edge"] == 102.0 - 100.5 and late["edge"] == 102.0 - 102.5
