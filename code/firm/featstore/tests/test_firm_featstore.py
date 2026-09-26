import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_featstore import FeatureDef, OnlineEngine, freshness, offline, parity, stream  # noqa: E402

rng = np.random.default_rng(0)
N = 2000
EV = {"t": np.sort(rng.uniform(0, 600, N)), "x": rng.integers(-5, 6, N).astype(float), "one": np.ones(N),
      "p": np.cumsum(rng.integers(-1, 2, N)).astype(float)}
DEFS = (FeatureDef("x last", "x", "last"), FeatureDef("x sum 10", "x", "sum", 10.0), FeatureDef("n 30", "one", "count", 30.0),
        FeatureDef("dp 20", "p", "change", 20.0))
TIMES = np.sort(rng.choice(EV["t"], 300, replace=False))


def brute(t):
    k = EV["t"] <= t
    last = EV["x"][k][-1]
    s10 = EV["x"][k & (EV["t"] > t - 10)].sum()
    n30 = (k & (EV["t"] > t - 30)).sum()
    before = EV["t"] <= t - 20
    base = EV["p"][before][-1] if before.any() else EV["p"][0]
    return [last, s10, n30, EV["p"][k][-1] - base]


def test_offline_matches_brute_force_and_online():
    off = offline(EV, DEFS, TIMES)
    assert np.allclose(off, np.array([brute(t) for t in TIMES]))
    assert parity(off, stream(EV, DEFS, TIMES))["mismatch share"] == 0.0


def test_lookahead_flagged_and_freshness():
    off = offline(EV, DEFS, TIMES, lag_events=1)
    assert parity(off, stream(EV, DEFS, TIMES), sample=20, seed=0)["flagged"]
    eng = OnlineEngine(DEFS)
    for i in range(100):
        eng.on(i, EV)
    assert abs(freshness(eng, EV["t"][99] + 3.0) - 3.0) < 1e-12
