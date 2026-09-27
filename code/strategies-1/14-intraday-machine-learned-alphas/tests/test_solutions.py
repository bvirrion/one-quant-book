"""Numbers gate: every numerical answer printed in Book 8, chapter 14 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_intraml import naive, scores, trading, without_own_returns  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_scores():
    got = {h: scores(h) for h in (5, 30, 120)}
    f = lambda s: (r(100 * s["r2_ridge"], 1), r(100 * s["r2_gbm"], 1), r(s["ic_ridge"]), r(s["ic_gbm"]),  # noqa: E731
                   r(100 * s["r2_gbm_train"], 1), r(s["sd_move"]))
    assert f(got[5]) == (21.1, 24.6, 0.33, 0.34, 23.3, 0.69)
    assert f(got[30]) == (5.1, 5.1, 0.23, 0.28, 9.2, 2.19)
    assert f(got[120]) == (-0.4, -1.5, 0.07, 0.07, 3.2, 4.47)
    assert got[5]["n_test"] == 21396


def test_trading():
    t = {h: trading(h) for h in (5, 30, 120)}
    n = {h: naive(h) for h in (5, 30, 120)}
    assert [(r(n[h]["agg_mean"]), r(n[h]["pas_mean"])) for h in (5, 30, 120)] == [(-0.6, 0.37), (-0.48, 0.33), (-0.87, -0.02)]
    assert [(r(t[h]["agg_mean"]), t[h]["agg_n"], r(t[h]["pas_mean"]), r(t[h]["coupled"])) for h in (5, 30, 120)] == \
        [(0.13, 324, 0.35, 0.33), (0.3, 2411, 0.18, 0.22), (-0.5, 3139, -0.09, -0.24)]
    assert (n[5]["agg_n"], n[5]["pas_n"], r(t[5]["spread"])) == (6142, 3203, 1.07)


def test_exercises():
    w = without_own_returns(5)
    assert (r(100 * w['r2_ridge'], 1), r(100 * w['r2_gbm'], 1)) == (18.6, 24.4)
    assert r(math.sqrt(0.25) * 0.69, 2) == 0.34 and r(0.01 * 100, 2) == 1.0
    assert r(0.35 * 3000 * 100 * 0.01, 0) == 1050
