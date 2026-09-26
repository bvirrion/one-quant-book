import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_modelcard import (  # noqa: E402
    CARD_FIELDS,
    ModelCard,
    ale,
    counterfactual,
    global_surrogate,
    ice,
    partial_dependence,
    rank_stability,
    validation_checklist,
)

rng = np.random.default_rng(0)
X = rng.uniform(-1, 1, (3000, 2))


def f_add(Z):
    return Z[:, 0] ** 3 + Z[:, 1]


def test_pd_and_ale_recover_additive_effect():
    g = np.linspace(-0.9, 0.9, 7)
    pd = partial_dependence(f_add, X, 0, g)
    assert np.allclose(pd - pd.mean(), g**3 - (g**3).mean(), atol=1e-9)
    edges, a = ale(f_add, X, 0, bins=30)
    t = edges**3
    assert np.max(np.abs((a - a.mean()) - (t - t.mean()))) < 0.05


def test_ale_right_pd_wrong_off_manifold():
    x1 = rng.uniform(-1, 1, 3000)
    Z = np.column_stack([x1, x1 + 0.01 * rng.standard_normal(3000)])

    def trap(W):                                                       # agrees with x1 on the data, explodes off it
        return W[:, 0] + 10 * (W[:, 1] - W[:, 0]) ** 2
    g = np.linspace(-0.9, 0.9, 9)
    pd = partial_dependence(trap, Z, 0, g)
    edges, a = ale(trap, Z, 0, bins=20)
    assert np.max(np.abs((pd - pd.mean()) - (g - g.mean()))) > 0.5
    assert np.max(np.abs(np.interp(g, edges, a) - np.interp(g, edges, a).mean() - (g - g.mean()))) < 0.1


def test_ice_slopes_recover_interaction():
    C = ice(lambda Z: Z[:, 0] * Z[:, 1], X, 0, np.linspace(-1, 1, 5), list(range(50)))
    slopes = np.polyfit(np.linspace(-1, 1, 5), C.T, 1)[0]
    assert np.allclose(slopes, X[:50, 1])


def test_surrogate_counterfactual_stability_card():
    tree, fid = global_surrogate(lambda Z: (Z[:, 0] > 0).astype(float), X, depth=1)
    assert fid == 1.0
    v = counterfactual(lambda Z: Z[:, 0], np.array([0.5, 0.0]), 0, 0.0, np.linspace(-1, 1, 201))
    assert v is not None and v < 0 and abs(v) < 0.02
    r = [np.arange(10)] * 4
    assert rank_stability(r, 5) == (1.0, 1.0)
    assert rank_stability([np.arange(10), np.r_[1, 0, 2, 3, 4, 5, 6, 7, 8, 9]], 5)[1] < 1.0
    c = ModelCard({"name": "x"})
    assert set(c.missing()) == set(CARD_FIELDS) - {"name"} and "MISSING" in c.render()
    cl = validation_checklist({"implementation parity": (True, "exact")})
    assert len(cl) == 9 and [x for x in cl if x[1]] == [("implementation parity", True, "exact")]
