"""Numbers gate: every numerical answer printed in Book 12, chapter 24 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_featstore as m  # noqa: E402
from firm_featstore import parity  # noqa: E402


def test_counts_and_clean_parity():
    assert m.counts() == {"decisions": 7714, "messages": 313681}
    for s in m.SESSIONS:
        assert parity(m.research(s), m.production(s))["mismatch share"] == 0.0


def test_parity_table():
    p = {k: (round(100 * a), round(100 * b)) for k, (a, b) in m.parity_table().items()}
    assert p == {"none": (0, 0), "one event ahead": (100, 100), "one-second bars": (96, 100), "float32 storage": (92, 100),
                 "late trade prints": (100, 100)}
    q = m.parity_table(tol=1e-6)
    assert q["float32 storage"] == (0.0, 0.0) and min(q[k][0] for k in ("one event ahead", "one-second bars",
                                                                       "late trade prints")) > 0.955


def test_model_effects():
    e = {k: tuple(round(v[c], 3) for c in ("backtest IC", "live IC", "live P&L")) for k, v in m.model_effects(1.0).items()}
    assert e == {"none": (0.411, 0.411, 0.089), "one event ahead": (0.395, 0.418, 0.091),
                 "one-second bars": (0.438, 0.36, 0.078), "float32 storage": (0.411, 0.411, 0.089),
                 "late trade prints": (0.411, 0.411, 0.089)}
    f = m.model_effects(5.0)
    assert max(abs(f[k]["live IC"] - f["none"]["live IC"]) for k in f) < 0.01
    assert max(abs(f[k]["backtest IC"] - f["none"]["backtest IC"]) for k in f) < 0.01


def test_feature_skew():
    s = m.feature_skew()
    r = {k: [round(v[f.name][1], 2) for f in m.FEATURES] for k, v in s.items()}
    assert r["one event ahead"] == [0.38, 0.24, 0.11, 0.30, 0.03, 0.01, 0.01, 0.02, 0.02, 0.09, 0.03, 0.0]
    assert r["one-second bars"] == [0.92, 0.73, 0.41, 0.79, 0.24, 0.07, 0.07, 0.10, 0.18, 0.39, 0.13, 0.04]
    assert r["late trade prints"] == [0, 0, 0, 0, 0, 0, 0.07, 0.11, 0.17, 0, 0, 0]
    late = [round(100 * s["late trade prints"][n][0]) for n in ("volume 30 s", "signed volume 30 s", "trades 10 s")]
    assert late == [94, 93, 92]
    assert all(round(s["float32 storage"][f.name][1], 2) == 0.0 for f in m.FEATURES)


def test_exercises():
    assert math.ceil(math.log(0.05) / math.log(0.999)) == 2995 and round(math.log(0.05) / math.log(0.999)) == 2994
    t = m.train_on_production()
    assert (round(t["trained on production"], 3), round(t["trained on research"], 3)) == (0.411, 0.36)
