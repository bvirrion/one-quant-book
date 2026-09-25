"""Numbers gate: every numerical answer printed in Book 9, chapter 28 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_sphedge import exposures, margin, profile, recycling, table  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_values_and_margin():
    v, m = exposures()["value"], margin()
    assert (r(v["single A"]), r(v["worst-of A, B"]), r(m["total"] / 1e6)) == (99.12, 99.29, 8.31)
    assert r(m["single A"]["money"] / 1e6) == 3.52                                          # exercise 1


def test_exposures():
    t = table()
    by = {k: [r(t[k]["by_note"].get(n, 0.0) / 1e6) for n in ("single A", "single B", "worst-of A, B")] for k in t}
    assert by == {"vega": [3.22, 2.42, 4.02], "skew": [1.47, 1.1, 1.86], "dividends": [0.51, 0.38, 0.55],
                  "correlation": [0.0, 0.0, -1.05]}
    assert [r(t[k]["total"] / 1e6) for k in t] == [9.66, 4.42, 1.43, -1.05]


def test_profile():
    p = profile()
    at = dict(zip(p["spot"], zip(p["vega"], p["delta"], strict=True), strict=True))
    assert (r(at[1.0][0] / 1e6), r(-at[1.0][1] / 0.01 / 1e6, 0), r(max(p["vega"]) / 1e6), p["spot"][p["vega"].index(max(p["vega"]))]) == (
        3.22, 106, 4.45, 0.8)
    assert (r(-at[0.55][1] / 0.01 / 1e6, 0), r(-at[0.4][1] / 0.01 / 1e6, 0)) == (334, 246)
    v50, v55 = at[0.5][0], at[0.55][0]
    assert r(100 * (0.5 + 0.05 * -v50 / (v55 - v50)), 0) == 52
    assert r(334 - 106, 0) == 228                                                             # exercise 3


def test_recycling():
    rc = recycling()
    got = [(r(rc[d]["move"]), r(rc[d]["seller_cost"] / 1e6), r(rc[d]["buyer_gain"] / 1e6)) for d in (5e6, 10e6, 20e6)]
    assert got == [(-1.93, 9.33, 18.67), (-0.97, 4.67, 9.33), (-0.48, 2.33, 4.67)]
