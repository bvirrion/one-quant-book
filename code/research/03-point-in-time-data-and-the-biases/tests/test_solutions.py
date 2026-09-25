"""Numbers gate: every numerical answer printed in Book 7, chapter 3 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "pit"))
from firm_pit import Guard, LookAheadError, asof_join
from rs_pit import payrolls, real_time_view, revision_stats, survivorship, vintage_store, year_totals


def r(x, d=1):
    return round(float(x), d)


def test_payroll_revisions():
    s = revision_stats()
    assert s["n"] == 318 and round(s["mean_abs"]) == 74 and r(100 * s["share_100"], 0) == 24
    assert round(s["mean_rev"]) == -3 and round(s["sd_rev"]) == 106 and s["sign_flips"] == 18
    p = payrolls()
    i = p["month"].index("2020-03")
    assert (p["first"][i], p["latest"][i]) == (-701, -1398) and s["largest_month"] == "2020-03"


def test_life_of_september_2008():
    life = [v for _, v in vintage_store().vintages("US", "payrolls_change", "2008-09")]
    distinct = [life[0]] + [b for a, b in zip(life, life[1:], strict=False) if b != a]
    assert distinct == [-159, -284, -403, -321, -458, -434]
    p = payrolls()
    assert p["latest"][p["month"].index("2008-09")] == -451
    whens = [k for (k, v), (_, prev) in zip(vintage_store().vintages("US", "payrolls_change", "2008-09")[1:],
                                            vintage_store().vintages("US", "payrolls_change", "2008-09"), strict=False)
             if v != prev]
    assert [w for w in whens if w.endswith("-02")] == ["2009-02", "2010-02", "2011-02"] and len(whens) == 5


def test_the_2008_recession():
    first, latest = year_totals("2008")
    assert (first, latest) == (-1882, -3548) and r((first - latest) / 1000) == 1.7
    s = vintage_store()
    assert sum(s.asof("US", "payrolls_change", f"2008-{m:02d}", "2009-01") for m in range(1, 13)) == -2589


def test_survivorship():
    s = survivorship()
    assert (r(100 * s["delist_rate"]), r(100 * s["full"]), r(100 * s["survivors"]), r(100 * s["bias"])) == (
        2.2, 7.7, 12.9, 5.2)
    assert (r(100 * s["fail_share"]), r(100 * s["r_fail"]), r(100 * s["r_surv_pooled"]), r(100 * s["identity"])) == (
        20.9, -11.1, 12.6, 5.0)
    assert r(s["cum_full"][-1]) == 4.6 and r(s["cum_surv"][-1]) == 12.9
    assert r(100 * survivorship(delist_return=0.0)["bias"]) == 4.5
    assert r(100 * survivorship(delist_return=-1.0)["bias"]) == 6.7
    lo, hi = survivorship(barrier=-1.2), survivorship(barrier=-2.0)
    assert (r(100 * lo["delist_rate"]), r(100 * lo["bias"]), r(100 * hi["delist_rate"]), r(100 * hi["bias"])) == (
        3.5, 7.0, 1.4, 3.8)
    assert r(100 * (s["bias"] - survivorship(delist_return=0.0)["bias"])) == 0.7


def test_tutorial_and_exercises():
    assert real_time_view("2008-09", "2008-10") == -159 and real_time_view("2008-09", "2011-09") == -434
    assert real_time_view("2008-09", "2009-01") == -403 and real_time_view("2008-09", "2009-06") == -321
    with pytest.raises(LookAheadError):
        Guard(vintage_store(), "2008-11").asof("US", "payrolls_change", "2008-09", known="2008-12")
    assert r(0.15 * (0.10 + 0.20), 3) == 0.045
    d = np.array([0.0, 1.0, 2.0])
    q = np.array([-0.5, 1.0, 1.8])
    assert list(asof_join(d, q, [1, 2, 3])) == [1.0, 2.0, 3.0]
    assert list(asof_join(d, q + 0.3, [1, 2, 3])) == [1.0, 1.0, 2.0]
    assert 90**2 + 106**2 == 19336 and round(100 * 106**2 / 19336) == 58
    assert r(100 * (1 - math.exp(-1.6))) == 79.8
