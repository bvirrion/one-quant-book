"""Numbers gate: every numerical answer printed in Book 5, Chapter 27 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_reserves import concentration, day_one_study, exercises, fair_coupon, rho_curve, stress


def r3(x):
    return round(x, 3)


def test_note_and_reserves():
    assert round(fair_coupon(), 2) == 7.95
    s = day_one_study()
    r0 = s["r0"]
    assert r3(r0["value"]) == 98.0
    assert [r3(v) for v in r0["vega"]] == [-0.533, -0.693] and [r3(v) for v in r0["delta"]] == [0.143, 0.279]
    b = r0["bid_offer"]
    assert (r3(b["vega 1"]), r3(b["vega 2"]), r3(b["delta 1"] + b["delta 2"]), r3(b["total"])) == (0.266, 0.346, 0.008, 0.621)
    assert [round(-v, 2) for v in r0["models"].values()] == [98.00, 94.33, 98.62, 97.98]
    assert r3(r0["model_reserve"]) == 0.621
    p = r0["param"]
    assert (round(-p["best"], 2), round(-p["worst"], 2), round(-p["prudent"], 2), r3(p["reserve"])) == (97.64, 98.50, 98.43, 0.433)
    assert r3(s["aggregated"]) == 0.838 and round(concentration()) == 69
    assert round(-r0["models"]["flat ATM"] + r0["models"]["flat at the knock-in strike"], 1) == 3.7


def test_day_one_named_result():
    s = day_one_study()
    d = s["day_one"]
    assert (r3(d.margin), r3(d.charged), r3(d.deferred), r3(d.recognised)) == (2.0, 0.621, 1.054, 0.325)
    assert r3(d.margin - d.charged) == 1.379
    assert (r3(s["r1"]["param"]["reserve"]), r3(s["r1"]["model_reserve"])) == (0.071, 0.559)
    rel = [r3(x[2]) for x in s["schedule"]]
    assert rel == [0.0, 0.424, 0.336, 0.295] and [r3(x[1]) for x in s["schedule"]][1:3] == [0.630, 0.295]
    assert r3(s["r0"]["param"]["reserve"] - s["r1"]["param"]["reserve"]) == 0.362


def test_rho_and_stress():
    c = dict((round(r, 2), v) for r, v in rho_curve())
    assert c[0.2] < c[0.5] < c[0.8]
    st = stress()
    assert [[round(x, 2) for x in row] for row in st["grid"]] == [[7.02, -2.27, -6.31, -5.89, -2.85], [13.09, 5.63, 1.31, 0.0, 0.96],
                                                                  [18.21, 12.15, 8.08, 6.08, 5.83]]


def test_exercises():
    e = exercises()
    w = e["wide"]
    assert (round(-w["best"], 2), round(-w["worst"], 2), round(-w["prudent"], 2), r3(w["reserve"])) == (97.33, 99.12, 98.93, 0.935)
    assert (r3(e["d_wide"].deferred), r3(e["d_wide"].recognised)) == (1.556, -0.177)
    low = e["low"]
    assert (round(low["value"], 2), r3(low["model_reserve"]), r3(low["param"]["reserve"]), r3(e["release_low"])) == (86.99, 0.649, 0.202, 0.203)
