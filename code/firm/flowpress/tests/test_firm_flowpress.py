import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_flowpress import FlowConfig, fit, flow_rule, simulate_flows  # noqa: E402


def test_fit_by_hand():
    own = np.array([[0.1, 0.0, 0.05], [0.0, 0.2, 0.05]])
    assert np.allclose(fit(own, [0.1, -0.2]), [0.01, -0.04, -0.005])


def test_flows_chase_returns():
    rng = np.random.default_rng(0)
    f = flow_rule(np.arange(100.0), 0.05, 0.0, rng)
    assert np.all(np.diff(f) > 0) and abs(f.mean()) < 1e-12


def test_pressure_is_planted_and_decays():
    rng = np.random.default_rng(1)
    T, N = 63 * 12, 300
    R = 0.01 * rng.standard_normal((T, N))
    style = rng.standard_normal((N, 3))
    cfg = FlowConfig(funds=40, holdings=30, impact=1.5, half_life=126.0)
    out = simulate_flows(R, np.ones((T, N), bool), style, cfg)
    q = 3
    t0 = out["quarters"][q]
    lvl_end = out["pressure"][t0 + 62]
    fitq = out["fit"][q]
    assert np.corrcoef(lvl_end, fitq)[0, 1] > 0.5                    # the quarter's push follows its FIT
    extra = np.log1p(out["R"]) - np.log1p(R)
    assert np.allclose(np.cumsum(extra, axis=0)[-1], out["pressure"][-1], atol=1e-10)
