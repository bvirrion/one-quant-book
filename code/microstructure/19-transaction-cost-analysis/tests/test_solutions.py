"""Numbers gate: every numerical answer printed in Book 10, chapter 19 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_tca import DAYS, log, study  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_log_and_benchmarks():
    rows = log()
    assert DAYS == 100 and len(rows) == 400
    part = [x["part"] for x in rows if not x["urgent"]]
    assert (r(100 * min(part), 0), r(100 * max(part), 0)) == (2, 24)
    s = study()
    assert s["n_orders"] == 200
    assert [r(s["sigma"][v]) for v in (0.1, 0.2, 0.4)] == [7.6, 10.0, 11.5]
    for name, want in (("patient", (2.42, -0.29, 1.90, 2.51)), ("urgent", (3.66, 1.40, 3.39, 4.10))):
        b = s[name]["bench"]
        assert tuple(r(b[k], 2) for k in ("arrival", "interval_vwap", "day_vwap", "close")) == want


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_pretrade_and_attribution():
    s = study()
    p = s["pretrade"]
    assert (r(p["eta"], 2), r(p["se"], 2), r(p["pred"], 2), r(p["real"], 2), r(p["real_se"], 2), r(p["corr"], 2)) == (
        1.04, 0.18, 2.47, 2.73, 0.52, 0.25)
    assert p["n_train"] == 100
    a, u = s["patient"], s["urgent"]
    keys = ("delay", "spread", "impact", "timing", "opportunity", "fees", "total")
    assert tuple(r(a[k], 2) for k in keys) == (-0.35, -0.65, 2.41, 0.59, 0.10, -0.20, 1.90)
    assert tuple(r(u[k], 2) for k in keys) == (-0.15, 2.43, 1.13, -0.07, 0.16, 0.29, 3.79)
    assert (r(100 * a["filled"]), r(100 * u["filled"])) == (99.5, 98.0) and max(a["check"], u["check"]) < 1e-9
    assert (r(a["sd"], 2), r(u["sd"], 2)) == (5.98, 4.60)
    assert [r(-x, 2) for x in a["rev"]] == [1.37, 3.51] and [r(-x, 2) for x in u["rev"]] == [0.07, 1.06]


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_comparison_named_result():
    s = study()
    assert (r(s["true"][0], 2), r(s["true"][1], 2)) == (1.89, 0.25)
    assert r(100 * s["share_urgent"]) == 53.5 and [round(x) for x in s["urgent_big"]] == [7039, 4126]
    d = s["diff"]
    assert (r(d["raw"], 2), r(d["raw_se"], 2), r(d["adj"], 2), r(d["lo"], 2), r(d["hi"], 2)) == (3.36, 0.76, 2.00, 0.32, 3.68)
    assert r(d["raw"] - d["adj"]) == 1.4
    pp = {str(k): v for k, v in s["peer"].items()}
    assert (r(pp["patient"][0], 2), r(pp["patient"][1], 2), r(pp["urgent"][0], 2), r(pp["urgent"][1], 2)) == (
        -0.77, 0.56, 1.50, 0.46)
    lp = s["loop"]
    assert (r(lp["model"], 2), r(lp["observed"], 2), r(lp["urgent"], 2), lp["share_urgent"]) == (2.17, 3.24, 3.88, 0.0)
    dp = s["diff_part"]
    assert (r(dp["adj"], 2), r(dp["lo"], 2), r(dp["hi"], 2)) == (2.32, 0.79, 3.85)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    assert r((800 * 0.02 + 800 * 0.03 + 200 * 0.10 + 800 * 0.003) / 1000 * 100, 2) == 6.24
    assert r(-0.5 + 1.04 * 10.0 * math.sqrt(0.1), 2) == 2.79
    s = study()
    lam = (s["urgent"]["total"] - s["patient"]["total"]) / (s["patient"]["sd"] ** 2 - s["urgent"]["sd"] ** 2)
    assert (r(s["patient"]["sd"] ** 2 - s["urgent"]["sd"] ** 2), r(lam, 2)) == (14.6, 0.13)
    assert np.isclose(5.98**2 - 4.60**2, 14.6, atol=0.01)


def test_small_runs():
    # Two simulated days instead of a hundred: each order is worked patiently and urgently on the same day (common
    # random numbers), and the urgent version finishes no later.
    rows = log(days=2)
    assert len(rows) == 8 and all(0 < x["part"] < 1 and math.isfinite(x["cost"]) for x in rows)
    pairs = {}
    for x in rows:
        pairs.setdefault((x["day"], x["order"]), {})[x["urgent"]] = x
    for p in pairs.values():
        assert p[True]["qty"] == p[False]["qty"] and p[True]["side"] == p[False]["side"]
        assert p[True]["t_end"] <= p[False]["t_end"]
