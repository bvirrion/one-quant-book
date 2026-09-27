"""Numbers gate: every numerical answer printed in Book 12, chapter 5 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_trees as m  # noqa: E402


def pct(x, d=2):
    return round(100 * float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_family():
    f = m.family()
    assert (pct(f["ceiling"]), pct(f["tree_2"]), pct(f["tree_5"]), pct(f["tree_10"])) == (0.77, 0.24, -0.20, -3.42)
    assert (pct(f["forest"]), pct(f["forest_oob"]), pct(f["forest_train"])) == (0.20, 0.42, 2.76)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_early_stopping():
    e = m.early()
    assert (e[0.1]["best"], pct(e[0.1]["test_best"]), pct(e[0.1]["test_full"])) == (34, 0.05, -3.38)
    assert (e[0.01]["best"], pct(e[0.01]["test_best"]), pct(e[0.01]["test_full"])) == (233, 0.26, 0.03)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_tuning():
    t = m.tuning()
    s = t["scores"]
    assert (pct(s.min()), pct(s.max())) == (-0.54, 0.39) and int(np.sum(s >= s.max() - 0.0004)) == 6
    b = t["best_config"]
    assert (b["num_leaves"], b["learning_rate"], b["n_estimators"], b["min_child_samples"]) == (4, 0.02, 200, 20)
    assert (pct(t["best_seeds"].min()), pct(t["best_seeds"].max())) == (0.36, 0.39)
    assert (round(100 * np.std(t["best_seeds"], ddof=1), 3), round(100 * t["seed_sd"], 2)) == (0.014, 0.07)
    d = t["default_seeds"]
    assert (pct(d.min()), pct(d.max()), pct(d.mean())) == (-0.00, 0.17, 0.09)
    assert [pct(x) for x in d] == [0.17, 0.11, 0.09, -0.00]
    assert (pct(t["test"]["best"]), pct(t["test"]["defaults"]), pct(t["test"]["plateau"])) == (0.32, -0.19, 0.31)
    p = t["plateau_config"]
    assert (p["num_leaves"], p["min_child_samples"], p["subsample"], pct(s[t["plateau"]])) == (4, 1000, 1.0, 0.35)
    assert round(10 ** (-0.2959 - 0.5536), 2) == 0.14                  # about a seventh as flexible


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_monotone():
    a = m.monotone()
    assert (round(a["free"], 3), round(a["mono"], 3), a["n_train"]) == (0.333, 0.364, 912)
    assert (round(100 * a["viol"], 1), a["viol_mono"]) == (7.0, 0.0)
    w = m.monotone(ofi5_sign=-1)
    assert (round(w["mono"], 3), round(100 * w["viol_mono"])) == (0.305, 95)


def test_exercises():
    assert round(0.3 + 0.7 / 50, 3) == 0.314
    assert round(400 * 0.18**2 + 600 * 0.12**2, 2) == 21.6
    assert (round(1 - 0.1 * 0.8, 2), round(0.9**10, 3)) == (0.92, 0.349)


def test_small_runs():
    # A 60-name panel instead of 300: a shallow tree and the chapter's boosted trees fit, and neither beats the
    # panel's own ceiling (the R-squared of the true expected returns) out of sample.
    from firm_mlsynth import PanelConfig, ceiling, panel
    from sklearn.tree import DecisionTreeRegressor

    P = panel(PanelConfig(n=60, months=m.T, k=10, seed=1, style_vol=0.02))
    top = ceiling(P, m.TEST)
    for model in (DecisionTreeRegressor(max_depth=3, min_samples_leaf=100, random_state=0), m.make()):
        score = m._score(m.fit(model, P.X, P.r, m.TRAIN), P)
        assert np.isfinite(score) and score < top
