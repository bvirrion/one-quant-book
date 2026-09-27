"""Numbers gate: every numerical answer printed in Book 8, chapter 3 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_residarb import YEAR, panel, run, sharpe, stability  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def f(res):
    c = res["corr_truth"]
    return (r(res["sr_gross"]), r(res["sr_net"]), r(100 * res["ret_net"], 1), r(100 * res["cost"], 1),
            r(100 * res["vol"], 1), r(res["positions"], 0), r(100 * res["turnover"], 0), r(res["gross"]),
            r(100 * res["passed"], 1), None if math.isnan(c) else r(c, 3))


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_main_table():
    assert f(run(0.0, "etf")) == (1.04, 0.07, 0.9, 12.0, 12.3, 347, 37, 3.47, 99.1, None)
    assert f(run(0.0, "pca")) == (1.3, -0.06, -0.5, 9.8, 7.2, 343, 39, 3.43, 99.0, None)
    assert f(run(0.15, "etf")) == (1.92, 0.93, 11.5, 12.3, 12.4, 344, 37, 3.44, 99.2, -0.091)
    assert f(run(0.15, "pca")) == (2.56, 1.22, 9.0, 9.8, 7.3, 340, 39, 3.4, 99.0, -0.088)
    assert f(run(0.3, "etf")) == (3.15, 2.15, 26.0, 12.2, 12.1, 336, 37, 3.36, 99.3, -0.128)
    assert f(run(0.3, "pca")) == (4.34, 3.0, 22.4, 10.0, 7.5, 338, 40, 3.38, 99.1, -0.123)
    assert r(100 * run(0.3, "pca")["explained"], 1) == 45.7


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_speed_filter_and_thresholds():
    assert (r(run(0.3, "etf", 1.25, 0.0)["sr_net"]), r(run(0.3, "pca", 1.25, 0.0)["sr_net"])) == (2.16, 3.04)
    got = [(r(run(0.3, "etf", 1.25, YEAR / tau)["sr_net"]), r(100 * run(0.3, "etf", 1.25, YEAR / tau)["passed"], 1))
           for tau in (15, 10, 5)]
    assert got == [(2.03, 87.9), (1.81, 69.2), (0.74, 26.8)]
    assert [r(run(0.3, "etf", so)["sr_net"]) for so in (0.75, 1.0, 1.5, 2.0)] == [2.2, 2.3, 2.23, 1.87]
    assert [r(run(0.3, "etf", so)["positions"], 0) for so in (0.75, 2.0)] == [509, 101]
    v = run(0.3, "etf", volume=True)
    assert (r(v["sr_net"]), r(v["sr_gross"])) == (1.78, 2.88)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_stability():
    st = stability()[1:]
    assert (r(100 * np.mean([x["explained"] for x in st]), 1), r(np.mean([x["v1"] for x in st]), 3),
            r(np.mean([x["subspace"] for x in st])), r(np.mean([x["min_cos"] for x in st]))) == (45.7, 0.999, 0.89, 0.63)
    assert r(100 * np.mean([x["first"] for x in stability()]), 1) == 26.1


def test_exercises():
    k = -math.log(0.9) * 252
    assert (r(k, 1), r(252 / k, 1)) == (26.6, 9.5)
    s_eq = math.sqrt(1e-4 / (1 - 0.81))
    assert (r(100 * s_eq), r(-0.02 / s_eq)) == (2.29, -0.87)
    assert r(math.exp(-1 / 30), 4) == 0.9672
    assert r(2 * 0.37 * 0.0005 * 252 * 100, 1) == 9.3


def test_small_runs():
    # A 100-name, three-year universe instead of the full one: the panel's returns, industry returns and volumes line
    # up day by day, and the Sharpe ratio annualises as the chapter does.
    import numpy as np

    P, R, ind, vol = panel(n=100, days=3 * YEAR)
    assert R.shape == vol.shape and ind.shape == (R.shape[0], P.cfg.n_industries) and np.isfinite(ind).all()
    x = np.r_[0.01, -0.005, 0.02, 0.0]
    assert abs(sharpe(x) - x.mean() / x.std(ddof=1) * YEAR**0.5) < 1e-12 and sharpe(np.zeros(5)) == 0.0
