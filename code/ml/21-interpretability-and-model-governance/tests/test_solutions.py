"""Numbers gate: every numerical answer printed in Book 12, chapter 21 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_explain as m  # noqa: E402
from firm_featimp import shap_values  # noqa: E402
from firm_gbdt import make  # noqa: E402
from firm_modelval import binomial_tail  # noqa: E402


def test_effects():
    e = {k: (round(v["PD"], 3), round(v["ALE"], 3), round(v["corr"], 2)) for k, v in m.effects().items()}
    assert e == {"independent": (0.027, 0.028, -0.01), "correlation 0.9": (0.134, 0.044, 0.92),
                 "correlation 0.99": (0.229, 0.11, 0.99)}
    assert (round(0.134 / 0.027), round(0.229 / 0.027)) == (5, 8)


def test_ice_surrogate_counterfactual():
    _, pd_slope, slopes, x4 = m.ice_x3()
    assert (round(pd_slope, 3), round(float(np.std(slopes)), 2), round(float(np.corrcoef(slopes, x4)[0, 1]), 2)) == (
        0.009, 0.91, 0.98)
    tree, fid = m.surrogate()
    assert round(fid, 2) == 0.48 and set(tree.tree_.feature[tree.tree_.feature >= 0]) == {0, 1}
    x1, pred, v = m.counterfactual_example()
    assert (round(x1, 2), round(pred, 2), round(v, 2)) == (0.46, 0.82, -0.44)


def test_stability():
    a, b, r2, rk = m.stability(1.0)
    assert (round(a, 2), round(b, 2), round(r2, 2)) == (0.22, 0.89, 0.66)
    assert all(set(r[:3]) == {0, 1, 2} for r in rk)
    a, b, r2, rk = m.stability(6.0)
    assert (a, round(b, 2), round(r2, 2)) == (0.0, 0.78, 0.05)
    assert any(any(f >= 8 for f in r[:5]) for r in rk)                   # a null feature in someone's top five
    a, b, _, _ = m.stability(1.0, disjoint=True)
    assert (a, b) == (1.0, 1.0)
    X, y = m.stability_data(1.0)
    assert np.abs(shap_values(make(seed=1).fit(X[:400], y[:400]), X[:1000])).max() == 0.0


def test_validation_and_card():
    v = m.validation()
    assert (round(v["r2"], 3), round(v["ridge r2"], 3), v["exceptions"], round(v["tail"], 2)) == (0.860, 0.349, 27, 0.37)
    assert v["parity"]["failures"] == 0 and v["parity"]["max_abs"] == 0.0 and v["parity"]["points"] == 200
    passed = [k for k, ok, _ in v["checklist"] if ok]
    assert passed == ["out-of-sample performance", "challenger comparison", "implementation parity", "outcomes analysis"]
    c = m.card()
    assert c.missing() == ["monitoring", "approvals"] and len(c.fields) == 15 and "MISSING" in c.render()
    assert round(binomial_tail(250, 27, 0.1), 2) == 0.37 and 0.1 * 250 == 25
