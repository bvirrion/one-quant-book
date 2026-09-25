"""Numbers gate: every numerical answer printed in Book 9, chapter 2 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_dispersion import crashes, monthly, real, stats  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_correlations():
    m = monthly()
    assert (len(m["ic"]), r(m["ic"].mean(), 3), r(m["rc"].mean(), 3), r((m["ic"] > m["rc"]).mean()),
            r((m["ic"] - m["rc"]).mean(), 3), m["crash_periods"]) == (239, 0.311, 0.252, 0.77, 0.059, [71, 152, 209])


def test_books():
    m = monthly()
    got = {k: (r(stats(m[k])["sr"]), r(stats(m[k])["skew"]), r(stats(m[k])["worst_sd"], 1), r(100 * stats(m[k])["share_up"], 0))
           for k in ("weights", "vega", "corrswap")}
    assert got == {"weights": (-0.02, 2.67, -1.6, 36), "vega": (0.65, -5.87, -11.3, 70), "corrswap": (1.74, -1.67, -6.0, 77)}
    assert [tuple(r(v) for v in c) for c in crashes()] == [(0.12, 0.83, -11.26, -0.71), (0.12, 0.57, -2.98, -0.45),
                                                          (0.73, 0.84, -0.97, -0.11)]


def test_real():
    c, d = real()["COR1M"], real()["DSPX"]
    assert (c["first"], c["last"], r(float(c["mean"]), 1), r(float(c["p05"]), 1), r(float(c["p95"]), 1), r(float(c["max"]), 1),
            c["max_at"], r(float(c["min"]), 2), c["min_at"], r(float(c["oct_2008"]), 1), r(float(c["mar_2020"]), 1),
            r(float(c["last_value"]), 2)) == ("2006-01-03", "2026-09-22", 37.0, 10.8, 69.7, 96.6, "2008-10-24", 2.93,
                                              "2024-07-12", 70.4, 72.5, 7.59)
    assert (d["first"], r(float(d["mean"]), 1), r(float(d["max"]), 1), d["max_at"], r(float(d["mar_2020"]), 1),
            r(float(d["last_value"]), 1)) == ("2014-06-19", 25.5, 58.9, "2020-03-18", 36.9, 36.4)


def test_exercises():
    assert r(0.2**2 / 0.3**2, 3) == 0.444 and r(0.2 / 0.3, 3) == 0.667
    assert r(0.12 - 0.83, 2) == -0.71


def test_equal_premia():
    m = monthly(0.30)
    assert (r(m["ic"].mean(), 3), r(m["rc"].mean(), 3), r((m["ic"] - m["rc"]).mean(), 3)) == (0.258, 0.252, 0.006)
    assert [r(stats(m[k])["sr"]) for k in ("weights", "vega", "corrswap")] == [-17.3, -1.84, 0.17]
