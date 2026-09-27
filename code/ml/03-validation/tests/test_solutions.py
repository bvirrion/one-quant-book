"""Numbers gate: every numerical answer printed in Book 12, chapter 3 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_validation as v  # noqa: E402


def pct(x, d=2):
    return round(100 * float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_leaks_table():
    L = v.leaks()
    assert (pct(L["clean"]), pct(L["period_join"]), pct(L["target_encoding"])) == (-0.19, 1.27, 8.97)
    assert (pct(L["screening"]), pct(L["screening_clean"])) == (0.13, -0.16)
    assert (pct(L["overlap_shuffled"]), pct(L["overlap_purged"])) == (3.47, -3.37)
    assert (pct(L["selection_best"]), pct(L["selection_fresh"]), pct(L["selection_median"])) == (-0.27, -0.20, -0.40)
    assert pct(L["selection_best"] - L["selection_median"]) == 0.13


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_selection_and_nested():
    s = v.selection()
    assert (pct(s["scores"].min()), pct(s["scores"].max()), pct(s["fresh_median"])) == (-0.60, -0.27, -0.19)
    assert round(float(np.corrcoef(s["scores"], s["fresh_scores"])[0, 1]), 2) == -0.16
    n = v.nested()
    assert (pct(n["flat_best"]), pct(n["nested"])) == (-0.62, -0.85)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_detectors():
    o = v.overlap_detectors()
    assert (o["shuffled"], o["purged"], round(o["adversarial_auc"], 2)) == (38080, 0, 0.71)
    d = v.detectors()
    assert (round(d["trunc_period"], 2), d["trunc_filing"], round(d["trunc_screening"], 2)) == (4.77, 0.0, 5.13)
    assert (pct(d["canary_te"][0]), pct(d["canary_te"][1])) == (4.03, 0.02)
    assert (pct(d["canary_screening"][0]), pct(d["canary_screening"][1])) == (0.17, 0.03)
    assert pct(d["canary_period"][0]) == -0.44


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    assert round(0.30 + 1.16 * 0.10, 2) == 0.42
    t0 = np.arange(200)
    t1 = t0 + 2
    te = np.arange(100, 140)
    a, b = t0[te].min(), t1[te].max()
    drop = [i for i in range(200) if i not in te and ((t1[i] >= a and t0[i] <= b) or (b < t0[i] <= b + 1))]
    assert (int(b), drop) == (141, [98, 99, 140, 141, 142])
    x = np.array([0.21, 0.15, 0.18])
    assert (round(x.mean(), 2), round(x.std(ddof=1) / math.sqrt(3), 3)) == (0.18, 0.017)
    p, f = v.announcement_effect(0.04)
    assert (pct(p), pct(f)) == (5.47, -0.14)


def test_small_runs():
    # The leak itself, on a small surprise array (the reference run scores models on the whole world): joining by the
    # fiscal period shows each quarter's surprise one month before it is filed; joining by filing date does not.
    rng = np.random.default_rng(0)
    s = np.where(rng.random((12, 6)) < 0.4, rng.standard_normal((12, 6)), np.nan)
    period, filing = v.surprise_known(s, "period"), v.surprise_known(s, "filing")
    assert np.array_equal(filing[1:], period[:-1]) and not np.array_equal(filing, period)
    assert np.allclose(v.xs(rng.standard_normal((5, 7))).mean(axis=1), 0)
