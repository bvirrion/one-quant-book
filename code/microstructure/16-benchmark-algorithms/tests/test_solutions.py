"""Numbers gate: every numerical answer printed in Book 10, chapter 16 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_algos import (  # noqa: E402
    QTY,
    benchmark_study,
    example_days,
    flow,
    forecast_study,
    pov_study,
    vwap_study,
)


def r(x, d=1):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_panel_and_forecasts():
    v = flow()
    (j, _), (j1, d1) = example_days()
    typ = v[j].sum(axis=0)
    assert (r(100 * typ[0] / typ.sum(), 2), r(100 * typ[-1] / typ.sum(), 2)) == (5.50, 9.38)
    assert int(np.argmax(v[j1, d1][:-1])) + 1 == 21                   # the news day's surge
    f = forecast_study()
    assert (f["n"], f["n_high"], r(100 * f["high_share"])) == (3800, 331, 8.7)
    assert [r(f[n]["l1"], 3) for n in ("static curve", "level + AR dynamic")] == [0.324, 0.306]
    assert [(r(f[n]["normal"]), r(f[n]["high"])) for n in ("static curve", "level + AR dynamic", "PCA-ARMA",
                                                          "PCA-ARMA dynamic")] == [
        (13.7, 17.7), (13.3, 17.2), (14.6, 18.3), (12.7, 20.6)]


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_vwap_named_result():
    s = vwap_study()
    hs, hd, ns, nd = s[("high", "static")], s[("high", "dynamic")], s[("normal", "static")], s[("normal", "dynamic")]
    assert (r(100 * hs["explained"]), r(100 * hd["explained"])) == (99.1, 98.6)
    assert (r(100 * ns["explained"]), r(100 * nd["explained"])) == (73.9, 68.5)
    assert (r(hs["sd"], 2), r(hd["sd"], 2), r(hs["sched_sd"], 2), r(hd["sched_sd"], 2)) == (2.24, 1.75, 2.17, 1.71)
    assert (r(hs["exec_sd"], 2), r(hd["exec_sd"], 2), r(hs["exec_mean"], 2), r(hd["exec_mean"], 2)) == (0.21, 0.20, 0.66, 0.73)
    assert (r(ns["sd"], 2), r(nd["sd"], 2), r(ns["sched_sd"], 2), r(ns["exec_sd"], 2)) == (0.48, 0.41, 0.48, 0.24)
    assert (r(nd["exec_sd"], 2), r(hs["exec_mean"] + 0.05, 1)) == (0.23, 0.7)
    p = s[("high", "paired")]
    assert (r(p["mean"]), r(p["se"]), p["better"]) == (1.5, 1.8, 7)
    top = s[("high", "static")]["rows"][:, 0].argmax()
    assert (r(s[("high", "static")]["rows"][top, 0]), r(s[("high", "dynamic")]["rows"][top, 0])) == (7.5, 5.4)
    assert (r(100 * ns["part"], 2), r(100 * hs["part"])) == (4.95, 2.5) and r(ns["part"], 2) == 0.05
    assert max(x["identity"] for k, x in s.items() if k[1] != "paired") < 1e-9          # the split adds up
    assert min(x["done"] for k, x in s.items() if k[1] != "paired") == QTY


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_participation():
    p = pov_study()
    rows = [(p[k]["minutes"], p[k]["part"], p[k]["pace"], p[k]["induced"], p[k]["induced_se"], p[k]["cost"], p[k]["cost_se"])
            for k in (("normal", "one"), ("normal", "two"), ("thin", "one"), ("thin", "two"))]
    assert [(r(m), r(100 * a), r(100 * b), r(i, 2), r(ie, 2), r(c), r(ce)) for m, a, b, i, ie, c, ce in rows] == [
        (5.2, 17.0, 21.1, 0.12, 0.10, 6.4, 0.7), (4.6, 15.9, 24.6, 0.12, 0.04, 10.0, 0.9),
        (11.6, 19.7, 24.9, 0.04, 0.06, 5.4, 0.8), (9.5, 19.2, 29.4, -0.05, 0.04, 5.7, 0.6)]
    assert all(p[k]["done"] == 1.0 for k in p)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_benchmarks():
    b = benchmark_study()
    got = [(r(x["bench"]), r(x["bench_sd"]), r(x["moved"]), r(x["impact"]), r(x["impact_se"]), r(x["arrival"]), r(x["arrival_se"]))
           for x in (b[n] for n in ("VWAP", "TWAP", "POV", "IS", "close"))]
    assert got == [(0.6, 0.2, 2.0, 2.7, 0.4, 3.0, 2.1), (0.8, 0.5, 2.1, 2.9, 0.2, 3.3, 2.2), (1.5, 0.7, 3.2, 4.7, 0.6, 5.3, 1.7),
                   (2.9, 5.1, 0.0, 2.9, 0.5, 2.9, 1.8), (-5.9, 3.6, 12.6, 6.8, 1.1, 7.3, 2.3)]
    assert 5.0 < np.mean([b[n]["arrival_sd"] for n in b]) < 7.0                         # "about six ticks"
    assert (int(0.3 * QTY), min(b[n]["done"] for n in b)) == (4500, QTY)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_is_schedule_and_exercises():
    from firm_algos import decompose, shortfall
    assert r(100 * shortfall(QTY, 26, 4.0)[:13].sum() / QTY, 0) == 87
    # 1: shares of a 15,000-share static VWAP in the first and last bins
    assert (round(QTY * 0.0550), round(QTY * 0.0938)) == (825, 1407)
    # 2: following only the others at 10%
    assert (r(100 * 0.1 / 1.1, 2), r(100 * 0.1 / 0.9)) == (9.09, 11.1)
    # 3: the split
    ex, sch = decompose([2, 2], [10.10, 11.00], [1, 3], [10.00, 11.00])
    assert (r(ex, 2), r(sch, 2), r(ex + sch, 2), r((10.10 + 11.00) / 2, 2), r((10.0 + 33.0) / 4, 2)) == (0.05, -0.25, -0.2, 10.55, 10.75)
    # 6: three followers
    assert (0.2 / (1 - 3 * 0.2), 1 / (1 - 3 * 0.2), 0.25 / (1 - 3 * 0.25), 1 / (1 - 3 * 0.25)) == (0.5000000000000001, 2.5000000000000004, 1.0, 4.0)
    assert (r(0.2 / 0.8 * 100), r(0.2 / 0.6 * 100)) == (25.0, 33.3)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercise_7_more_news():
    f = forecast_study(16, 0.2)
    assert (f["n_high"], r(100 * f["high_share"])) == (382, 10.1)
    assert (r(f["static curve"]["high"]), r(f["level + AR dynamic"]["high"])) == (20.0, 18.9)


def test_small_runs():
    # One seed of the participation study instead of eight (the VWAP panels need the 30-second forecast study):
    # each child order completes, at a participation rate inside (0, 1).
    p = pov_study(seeds=(1,))
    assert set(p) == {("normal", "one"), ("normal", "two"), ("thin", "one"), ("thin", "two")}
    assert all(x["done"] == 1.0 and 0 < x["part"] < 1 and x["minutes"] > 0 for x in p.values())
