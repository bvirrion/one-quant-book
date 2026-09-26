import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mlsynth import PanelConfig, ceiling, months_to_detect, panel, r2_oos, task


def test_task_bayes_r2():
    for kind in ("linear", "friedman"):
        d = task(40000, p=10, snr=1.0, kind=kind, seed=2)
        r2 = 1 - np.mean((d["y"] - d["f"]) ** 2) / np.var(d["y"])
        assert abs(r2 - d["bayes_r2"]) < 0.02                          # the truth scores the Bayes R-squared


def test_panel_shapes_ranks_and_ceiling():
    cfgs = [PanelConfig(n=200, months=120, seed=s, ceiling=0.01) for s in range(1, 5)]
    cs = []
    for cfg in cfgs:
        P = panel(cfg)
        assert P.X.shape == (120, 200, 20) and P.r.shape == P.mu.shape == (120, 200)
        assert P.X.min() > -1 and P.X.max() < 1 and abs(P.X[5, :, 3].mean()) < 1e-12   # ranks, centred
        cs.append(ceiling(P, np.arange(120)))
    assert abs(np.mean(cs) - 0.01) < 0.002                              # the ceiling is hit on average over seeds


def test_signal_lives_in_first_six_characteristics():
    P = panel(PanelConfig(n=300, months=60, seed=3))
    X, _, mu, _ = P.flat(np.arange(60))
    c = [abs(np.corrcoef(X[:, j], mu)[0, 1]) for j in range(20)]
    assert max(c[6:]) < 0.06 < 0.2 < min(c[:3])                        # noise characteristics carry (almost) nothing


def test_decay_and_flip():
    P0 = panel(PanelConfig(n=300, months=200, seed=4))
    P1 = panel(PanelConfig(n=300, months=200, seed=4, decay_from=100, decay_half_life=12.0, regime_at=150))
    late = np.arange(180, 200)
    X, _, mu0, _ = P0.flat(late)
    _, _, mu1, _ = P1.flat(late)
    inter = X[:, 0] * X[:, 3]
    assert np.corrcoef(inter, mu0)[0, 1] > 0.1 and np.corrcoef(inter, mu1)[0, 1] < -0.1
    assert abs(np.corrcoef(X[:, 0], mu1)[0, 1]) < abs(np.corrcoef(X[:, 0], mu0)[0, 1])


def test_r2_and_detection():
    y = np.array([1.0, -1.0, 2.0])
    assert r2_oos(y, np.zeros(3)) == 0.0 and r2_oos(y, y) == 1.0
    assert abs(months_to_detect([0.01, 0.03, 0.02]) - (2 * 0.01 / 0.02) ** 2) < 1e-12
