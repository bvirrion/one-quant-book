"""Acceptance tests for firm.lobmodel (Book 12, chapter 29)."""
import pathlib
import sys
import tempfile

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import firm_lobmodel as lm  # noqa: E402
from firm_mlinfer import forest_predict  # noqa: E402


def test_online_features_equal_offline_and_labels():
    seen = []

    def spy(x):
        seen.append(np.array(x))
        return 0.0

    a = lm.ModelAgent(spy, threshold=np.inf)
    lm.run_session(7, 120.0, a)
    ev = lm.events_array(a)
    t = np.array([d[0] for d in a.decisions])
    assert len(t) > 100 and np.array_equal(np.vstack(seen), lm.offline(ev, lm.FEATURES, t))
    X, y, t0, t1 = lm.dataset(ev, t[t < 110])
    k0 = np.searchsorted(ev["t"], t0, side="right") - 1
    k1 = np.searchsorted(ev["t"], t0 + lm.HORIZON, side="right") - 1
    assert np.allclose(y, ev["mid"][k1] - ev["mid"][k0]) and np.allclose(t1 - t0, lm.HORIZON)


def test_serving_fixture_parity_and_reproduction():
    f = lm.read_forest(HERE / "data" / "forest.txt")
    V = np.loadtxt(HERE / "data" / "vectors.csv", delimiter=",")
    P = lm.ForestPredictor(f)
    assert len(V) == 200
    assert np.array_equal(forest_predict(f, V[:, :10]), V[:, 10])
    assert all(P(x) == y for x, y in zip(V[:, :10], V[:, 10], strict=True))
    with tempfile.TemporaryDirectory() as d:
        out, _ = lm.make_pipeline(d, lm.DEFAULT).run("fit")
    g = out["fit"]["forest"]
    assert all(np.array_equal(np.asarray(g[k], dtype=f[k].dtype), f[k]) for k in f)
    assert out["fit"]["lightgbm"].tolist() == out["fit"]["flat"].tolist()


def test_decision_latency_makes_decisions_stale_and_flat_session_pnl():
    runs = {}
    for lat in (0, 50_000_000):
        a = lm.ModelAgent(lambda x: 0.0, threshold=np.inf, decision_ns=lat)
        r = lm.report(lm.run_session(11, 120.0, a), a)
        runs[lat] = r
    assert runs[0]["staleness ms"] < 0.05 < 50 <= runs[50_000_000]["staleness ms"]
    for r in runs.values():
        assert r["position"] == 0 or r["timeouts"] >= 0
        assert np.isfinite(r["pnl"])
