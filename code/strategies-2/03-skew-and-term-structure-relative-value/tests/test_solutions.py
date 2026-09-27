"""Numbers gate: every numerical answer printed in Book 9, chapter 3 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_volrv import books, bucket_sr, carry_link, fit, real, seeds, static, table, worst, zscore  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_features():
    f = fit()
    assert (r(f["corr_skew"]), r(f["corr_slope"]), r(f["beta_skew"]), r(f["beta_slope"]), r(f["corr_raw_skew_level"]),
            r(f["corr_raw_slope_level"])) == (0.97, 0.92, -0.46, -0.2, -0.63, -0.83)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_books():
    t = table()
    got = {k: (r(v["sr"]), r(v["skewness"]), r(v["worst_sd"], 1), r(100 * v["share_up"], 0)) for k, v in t.items()}
    assert got == {"skew raw": (1.13, 1.91, -4.6, 63), "skew residual": (0.75, 1.48, -4.5, 55),
                   "calendar raw": (0.07, 4.74, -1.7, 45), "calendar residual": (0.64, 1.43, -2.4, 51)}
    shares = {k: tuple(r(100 * v[c], 0) for c in ("spot_time", "level", "skew", "slope", "cost")) for k, v in t.items()}
    assert shares == {"skew raw": (94, 5, 9, 0, -8), "skew residual": (73, 24, 16, 0, -13),
                      "calendar raw": (-31, 160, 2, 155, -186), "calendar residual": (97, -16, 1, 51, -32)}
    assert len(books()["skew raw"]["total"]) == 227


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_buckets_and_worst_month():
    b = bucket_sr()
    assert (r(b["skew raw"]["skew"]), r(b["skew residual"]["skew"]), r(b["calendar raw"]["slope"]),
            r(b["calendar residual"]["slope"]), r(b["calendar raw"]["level"])) == (0.95, 1.01, 0.84, 1.51, 0.42)
    for name in ("skew raw", "skew residual"):
        w = worst(name)
        assert (w["start"], r(w["start"] / 252, 1), w["pos"], r(100 * w["ret"], 1), r(100 * w["atm_start"], 1),
                r(100 * w["atm_end"], 1), r(w["spot_time"], 0), r(w["level"], 0), r(w["total"], 0)) == (
                    1470, 5.8, 2.0, 4.5, 15.2, 9.7, -119, -157, -289)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_seeds():
    s = seeds(8)
    assert {k: (r(np.mean(v)), r(min(v)), r(max(v))) for k, v in s.items()} == {
        "skew raw": (0.9, 0.47, 1.26), "skew residual": (0.39, 0.12, 0.75), "calendar raw": (-0.07, -0.43, 0.29),
        "calendar residual": (0.38, -0.1, 0.75)}


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_real():
    x = real()
    s, k, rv, vn = x["slope"], x["skew"], x["rvx"], x["vxn"]
    assert (s["first"], s["last"], r(float(s["mean"])), r(100 * float(s["share_below_zero"]), 1), r(float(s["min"])),
            s["min_at"], r(float(s["mar_2020"])), r(float(s["phi"])), r(float(s["half_life"]), 1),
            r(float(s["corr_with_vix"]))) == ("2009-09-18", "2026-09-22", 1.93, 7.6, -18.23, "2020-03-12", -7.98, 0.9,
                                             6.5, -0.54)
    assert (k["first"], r(float(k["mean"]), 1), r(float(k["p05"]), 1), r(float(k["p95"]), 1), r(float(k["max"])),
            k["max_at"], r(float(k["min"])), k["min_at"], r(float(k["corr_changes_vix"])),
            r(float(k["corr_levels_vix"]))) == ("1990-01-02", 123.2, 110.0, 147.3, 183.12, "2025-02-18", 101.23,
                                                "1991-03-19", -0.13, -0.17)
    assert (r(float(rv["mean"]), 1), r(float(rv["sd"]), 1), r(float(rv["half_life"]), 1), r(float(vn["mean"]), 1),
            r(float(vn["sd"]), 1), r(float(vn["half_life"]), 1)) == (5.2, 2.3, 15.7, 3.0, 2.3, 15.3)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_static_and_carry():
    st = static()
    assert {k: tuple(r(v[c], 1) for c in ("spot_time", "level", "total")) for k, v in st.items()} == {
        "skew": (12.0, -15.9, -6.2), "calendar": (9.6, -3.2, 4.7)}
    c = carry_link()
    assert (r(c["skew residual"]), r(c["calendar residual"])) == (0.25, 0.14)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercise_7_no_noise():
    t = table(0, 0.0)
    assert {k: (r(v["sr"]), r(v["worst_sd"], 1)) for k, v in t.items()} == {
        "skew raw": (1.08, -2.8), "skew residual": (-0.41, -11.7), "calendar raw": (-0.12, -1.7),
        "calendar residual": (-0.11, -2.1)}


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_small_answers():
    import math
    assert (100 - 10 * -2.3, r(0.4 / 20 * 100), r(math.log(0.5) / math.log(0.98), 1)) == (123.0, 2.0, 34.3)
    assert r(math.log(0.5) / math.log(0.98), 0) == 34
    from s2_volrv import market
    assert market()[1]["crashes"][0][0] - (1470 + 21) == 9
    assert r(100 * (math.exp(0.152 * math.sqrt(21 / 252)) - 1), 1) == 4.5    # the call's strike, 4.5% above spot


def test_small_runs():
    # One seed's books instead of the tables across seeds: the z-score is zero in its warm-up, clipped, and uses no
    # future data; each book's P&L buckets are finite.
    import numpy as np

    x = np.random.default_rng(0).standard_normal(600)
    z = zscore(x)
    y = x.copy()
    y[400:] += 10.0
    assert (z[:252] == 0).all() and np.abs(z).max() <= 2.0 and np.array_equal(zscore(y)[:400], z[:400])
    b = books(0)
    assert set(b) == {"skew raw", "skew residual", "calendar raw", "calendar residual"}
    assert all(np.isfinite(v).all() for book in b.values() for v in book.values())
