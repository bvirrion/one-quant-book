import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_crossimpact import estimate, explained_by_other, fair_pricing, liquidation, llob, symmetric_psd  # noqa: E402


def test_llob_square_root_when_fast():
    # a fast metaorder on a linear latent book moves the price by about sqrt(2 Q / L)
    t, p = llob(8.0, 0.5, L=1.0, D=0.2, dt=0.001, width=20.0, dx=0.05)
    assert abs(p[-1] - np.sqrt(2 * 8.0)) < 0.25
    f = fair_pricing(t, p, 0.5)
    assert f["average"] < f["peak"]


def test_cross_impact_estimation_and_projection():
    rng = np.random.default_rng(1)
    lam = np.array([[1.0, 0.3], [0.3, 0.8]])
    z = rng.standard_normal((5000, 2))
    q = z @ np.array([[1.0, 0.0], [0.5, 0.9]]).T
    r = q @ lam.T + 0.5 * rng.standard_normal((5000, 2))
    est = estimate(r, q)
    assert np.allclose(est, lam, atol=0.03)
    p = symmetric_psd(np.array([[1.0, 0.5], [-0.1, -0.2]]))
    assert np.allclose(p, p.T) and np.all(np.linalg.eigvalsh(p) >= -1e-12)
    share = explained_by_other(r, q)
    assert all(0 < s < 1 for s in share)


def test_joint_liquidation_is_cheaper():
    lam = np.array([[1.0, 0.6], [0.6, 1.0]])
    t = np.linspace(0, 1, 11)
    _, c_joint = liquidation(lam, 3.0, t, np.array([1.0, 1.0]))
    q, c_naive = liquidation(lam, 3.0, t, np.array([1.0, 1.0]), joint=False)
    assert c_joint <= c_naive + 1e-12 and np.isclose(q.sum(axis=1), 1.0).all()
