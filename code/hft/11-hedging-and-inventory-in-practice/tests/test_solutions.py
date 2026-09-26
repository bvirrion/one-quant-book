"""Numbers gate: every numerical answer printed in Book 11, chapter 11 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_hedging as h  # noqa: E402

mh = h.mh


def r(x, d=0):
    return round(float(x), d)


def test_frontier():
    f = h.frontier()
    none, zero, b250, stk = f["none"], f["future, zero"], f["future, band 250,000"], f["stocks"]
    assert [r(none["risk"], -1), r(zero["risk"], -1), r(b250["risk"], -1), r(stk["risk"])] == [8540, 4410, 4760, 2525]
    assert [r(zero["cost"], -2), r(b250["cost"], -1), r(stk["cost"], -1)] == [6700, 1880, 12760]
    assert r(zero["contracts"]) == 2682 and r(100 * zero["cost"] / zero["spread"]) == 14 and r(none["spread"], -2) == 46800
    assert [r(none["objective"], -1), r(zero["objective"], -1), r(b250["objective"], -1)] == [39640, 38260, 42570]
    assert max(f, key=lambda k: f[k]["objective"]) == "future, band 250,000"


def test_band():
    b = h.band()
    assert r(b["sigma_D"] / 1e4) == 248
    assert [r(v, -3) for v in b["bands"].values()] == [613000, 425000, 284000]
    d = h.frontier(1e-4)
    assert max(d, key=lambda k: d[k]["objective"]) == "future, band 500,000"
    assert [r(d[k]["objective"], -1) for k in ("future, band 500,000", "future, band 250,000", "future, band 1,000,000",
                                                 "future, zero")] == [41540, 40680, 40490, 31560]
    assert r(h.band(1e-4)["bands"][1e-4], -3) == 358000


def test_ten_to_four():
    t = h.ten_to_four()
    assert r(t["gross"] / 1e4) == 157 and r(t["D"]) == 833747 and r(t["flatten"]) == 438 and r(t["future"]) == 83
    assert [r(t[k]) for k in ("future_sd", "future_var99", "future_es99", "keep_sd", "keep_var99", "keep_es99")] == [
        3086, 7358, 8813, 5879, 14776, 19795]
    c = t["choice"]
    assert (r(c["stocks"]), r(c["future"]), r(c["none"]), c["best"]) == (438, 1035, 3454, "stocks")


def test_eod():
    e = h.eod()
    n, s = e["normal"], e["skew from 15:00"]
    assert r(n["gross"], -4) == 1320000 and r(s["gross"], -4) == 670000 and n["spread"] == s["spread"]
    assert (r(n["flatten"]), r(s["flatten"])) == (381, 163)


def test_exercises():
    import numpy as np
    assert mh.delta_equivalent([1000, -500], [50, 100], [1.2, 0.8]) == 20000
    H, _, k = mh.hedge_future(np.array([20000.0]), "zero")
    assert k == 0
    assert round(mh.partial_hedge(833747.0, 5e-5, 1e-4, 1e-4)) == 831247
    assert round(2 * 5e-5 * 833747) == 83
