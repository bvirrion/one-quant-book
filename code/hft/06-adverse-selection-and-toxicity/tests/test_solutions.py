"""Numbers gate: every numerical answer printed in Book 11, chapter 6 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_toxicity as h  # noqa: E402


def r(x, d=3):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_classes_and_periods():
    c = h.by_class()
    assert (r(c["informed"], 2), r(c["se_informed"], 2), r(c["uninformed"], 2), r(c["se_uninformed"], 2)) == (
        -0.95, 0.14, 0.55, 0.1)
    assert (r(100 * c["share_informed"], 0), r(c["all"], 2), c["fills"]) == (32, 0.07, 920)
    p = h.by_period()
    assert [(r(p[k]["fills_per_min"], 2), r(100 * p[k]["informed"], 1), r(p[k]["markout"])) for k in
            ("before", "during", "after")] == [(6.97, 34.7, 0.025), (17.89, 23.6, 0.059), (6.69, 32.3, 0.132)]


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_score():
    q = h.fit_quality()
    assert [r(x) for x in q["coef"]] == [1.432, -0.029, -1.795, -0.072, 0.028] and q["n"] == 919
    assert (r(q["corr_in"], 2), r(q["corr_out"], 2)) == (0.19, 0.18)
    c = h.calibration()
    assert (r(c["real"][0], 2), r(c["real"][-1], 2), r(c["se"][0], 2), r(c["se"][-1], 2)) == (-0.86, 0.83, 0.12, 0.25)
    assert all(np.diff(c["pred"]) > 0)
    assert r(h.fitted().score(np.array([2, 0.8, math.log1p(0.5), 0])), 2) == 0.09


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_responses():
    rs = h.responses()
    got = [(round(v["shares"]), r(100 * v["informed"], 1), r(v["markout"]), r(v["se"]), round(v["messages"]), r(v["pnl"], 2),
            r(v["sd"], 2)) for v in rs.values()]
    assert got == [(19167, 29.4, -0.005, 0.096, 696, -75.0, 178.23), (6550, 18.3, 0.136, 0.199, 1012, 37.75, 134.3),
                   (6683, 20.0, 0.112, 0.222, 1513, -2.08, 105.59)]
    fs = h.fade_sweep()
    got = [(round(v["shares"]), r(100 * v["informed"], 1), r(v["markout"]), r(v["se"]), round(v["messages"])) for v in fs.values()]
    assert got == [(6550, 18.3, 0.136, 0.199, 1012), (10733, 17.9, 0.214, 0.146, 952), (15017, 24.1, 0.186, 0.123, 841),
                   (18017, 30.1, -0.06, 0.103, 740)]
    assert r(100 * (1 - 10733 / 19167), 0) == 44 and r(10733 / 6550 - 1, 2) == 0.64


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_hysteresis_and_exercises():
    y = h.hysteresis()
    assert (round(y["messages"]), round(y["shares"]), r(100 * y["informed"], 1), r(y["markout"])) == (716, 9767, 21.2, 0.102)
    assert r(0.32 * -0.95 + 0.68 * 0.55, 2) == 0.07 and r(0.2 * 10000 * 0.01, 2) == 20.0


def test_small_runs():
    # One calibration session instead of six: the base quoter's fills, their classes and mark-outs.
    c = h.by_class(seeds=h.CAL_SEEDS[:1])
    assert c["fills"] > 0 and 0 < c["share_informed"] < 1
    assert c["informed"] < 0 < c["uninformed"]          # informed flow costs the quoter, the rest pays it
    r, at_fill = h.run(h.CAL_SEEDS[0])
    assert len(at_fill) == len(r.fills["qty"]) and np.isfinite(h._markouts(r)).all()
