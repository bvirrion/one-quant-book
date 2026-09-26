"""Numbers gate: every numerical answer printed in Book 12, chapter 6 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_importance as m  # noqa: E402
from firm_featimp import false_selection_bound  # noqa: E402


def pct(x, d=2):
    return round(100 * float(x), d)


def test_importances():
    imp = m.importances()
    assert (pct(imp["test_r2"]), pct(imp["truth_r2"])) == (2.67, 4.01)
    assert list(m.ranks(imp["gain"])[:5]) == [4, 1, 2, 3, 5] and list(m.ranks(imp["perm"])[:5]) == [4, 1, 2, 3, 5]
    assert list(m.ranks(imp["drop"])[:4]) == [4, 1, 3, 2] and list(m.ranks(imp["shap"])[:5]) == [2, 1, 4, 5, 3]
    share = {}
    for k in ("gain", "perm", "drop", "shap"):
        v = np.clip(imp[k], 0, None)
        share[k] = 100 * v / v.sum()
    assert (round(share["gain"][0], 1), round(share["gain"][4], 1), round(share["gain"][5:].max(), 1)) == (9.5, 8.1, 5.4)
    assert round(share["perm"][5:].max(), 1) == 0.2 and share["shap"][4] > max(share["shap"][2], share["shap"][3])
    assert (pct(imp["perm"][0]), pct(imp["perm"][4])) == (0.76, 0.41)
    g = [i for i, grp in enumerate(imp["groups"]) if len(grp) > 1]
    assert len(g) == 1 and sorted(imp["groups"][g[0]]) == [0, 4] and pct(imp["perm_cluster"][g[0]]) == 2.72
    assert (pct(imp["drop"][0]), pct(imp["drop"][4])) == (0.09, -0.02)


def test_twins():
    t = m.twins()
    assert (pct(t["all"]), pct(t["no_x1"]), pct(t["no_x1b"]), pct(t["no_both"])) == (2.67, 2.58, 2.68, 1.61)
    assert pct(t["all"] - t["no_both"]) == 1.05 and round((t["all"] - t["no_both"]) / t["all"], 1) == 0.4


def test_stability():
    s = m.stability()
    assert list(s["lasso"]["chosen"]) == [0] and list(s["boosting"]["chosen"]) == [0, 1]
    assert s["lasso"]["false"] == 0 == s["boosting"]["false"]
    assert (round(s["lasso"]["q"], 1), round(s["lasso"]["bound"], 1)) == (6.7, 2.3)
    assert (round(s["boosting"]["q"], 1), round(s["boosting"]["bound"], 1)) == (6.0, 1.8)
    assert max(s["lasso"]["freq"][2:4].max(), s["boosting"]["freq"][2:4].max()) < 0.1


def test_heavy_tail_and_exercises():
    h = m.heavy_tail()
    assert (pct(h["raw"]), pct(h["winsorised"]), pct(h["ranked"]), pct(h["truth"])) == (0.13, 1.27, 1.96, 2.17)
    h5 = m.heavy_tail(df=5.0)
    assert (pct(h5["raw"]), pct(h5["winsorised"]), pct(h5["ranked"]), pct(h5["truth"])) == (1.36, 1.49, 1.57, 1.79)
    assert (round(false_selection_bound(10, 200, 0.6), 3), false_selection_bound(10, 200, 0.9)) == (2.5, 0.625)
    # Shapley values of the three-player game of exercise 2
    import itertools
    v = {(): 0, (1,): 1, (2,): 1, (3,): 0, (1, 2): 3, (1, 3): 1, (2, 3): 1, (1, 2, 3): 3}
    phi = {i: 0.0 for i in (1, 2, 3)}
    for order in itertools.permutations((1, 2, 3)):
        seen = []
        for i in order:
            phi[i] += v[tuple(sorted(seen + [i]))] - v[tuple(sorted(seen))]
            seen.append(i)
    assert {i: x / 6 for i, x in phi.items()} == {1: 1.5, 2: 1.5, 3: 0.0}
