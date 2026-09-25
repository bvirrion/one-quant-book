import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_residarb import eigenportfolios, ou_fit, regress, s_score, speed_ok, step, volume_adjust  # noqa: E402


def test_regress_both_shapes():
    rng = np.random.default_rng(0)
    F = rng.standard_normal((60, 2))
    R = 0.001 + F @ np.array([[1.0, 0.5], [0.2, -1.0]]) + 0.01 * rng.standard_normal((60, 2))
    beta, e = regress(R, F)
    assert np.allclose(beta, [[1.0, 0.5], [0.2, -1.0]], atol=0.05) and np.allclose(e.sum(axis=0), 0, atol=1e-12)
    b1, e1 = regress(R, np.column_stack([F[:, 0], F[:, 0]]), per_name=True)
    assert abs(b1[0] - 1.0) < 0.05 and np.allclose(e1.sum(axis=0), 0, atol=1e-12)


def test_ou_fit_recovers_an_ar1():
    rng = np.random.default_rng(1)
    b, n = 0.9, 60
    fits = []
    for _ in range(400):
        x = np.zeros(n + 1)
        for t in range(n):
            x[t + 1] = 0.02 + b * x[t] + 0.01 * rng.standard_normal()
        fits.append(ou_fit(np.diff(x)[:, None]))
    bs = np.array([f["b"][0] for f in fits])
    assert abs(np.median(bs) - b) < 0.06                               # small-sample bias of the AR(1) slope
    f = fits[0]
    assert abs(f["kappa"][0] + math.log(f["b"][0]) * 252) < 1e-9


def test_s_score_and_rules():
    fit = {"m": np.array([0.02, -0.02, 0.0]), "sigma_eq": np.array([0.01, 0.01, 0.01])}
    assert np.allclose(s_score(fit, center=False), [-2.0, 2.0, 0.0])
    pos = step(np.array([0, 0, 1, -1, 1]), np.array([-1.5, 1.5, -0.4, 0.7, -2.0]), np.array([1, 1, 1, 1, 0], bool))
    assert pos.tolist() == [1, -1, 0, 0, 0]
    assert speed_ok([8.0, 9.0, np.nan]).tolist() == [False, True, False]


def test_eigenportfolios_and_volume():
    rng = np.random.default_rng(2)
    m = rng.standard_normal(252)
    R = 0.01 * (m[:, None] + 0.5 * rng.standard_normal((252, 20)))
    Q, share = eigenportfolios(R, 1)
    assert share > 0.7 and (np.sign(Q[0]) == np.sign(Q[0, 0])).all()
    assert np.allclose(volume_adjust([0.02, 0.02], [200.0, 50.0], [100.0, 100.0]), [0.01, 0.04])
