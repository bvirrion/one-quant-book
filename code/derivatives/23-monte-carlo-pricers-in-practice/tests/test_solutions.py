"""Numbers gate: every numerical answer printed in Book 5, Chapter 23 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_mc import adjoint, bounds, greek_table, heston_bias, in_sample, put_bias, qmc_study


def test_max_call_bounds():
    b = bounds()
    f, s = b["full"], b["small"]
    assert (round(f["lower"][0], 3), round(f["lower"][1], 3), round(f["upper"][0], 3), round(f["upper"][1], 3)) == \
        (18.649, 0.039, 18.713, 0.019)
    assert round(f["gap"], 3) == 0.064 and round(100 * f["gap"] / f["lower"][0], 1) == 0.3
    assert (round(s["lower"][0], 3), round(s["upper"][0], 3), round(s["gap"], 3)) == (18.137, 18.805, 0.668)
    assert round(s["gap"] / f["gap"]) == 10
    # the reserve discussion: gap against two combined standard errors
    se = (f["lower"][1] ** 2 + f["upper"][1] ** 2) ** 0.5
    assert (round(se, 3), round(2 * se, 3)) == (0.043, 0.086) and round(f["gap"] + 2 * se, 2) == 0.15
    se_s = (s["lower"][1] ** 2 + s["upper"][1] ** 2) ** 0.5
    assert round(s["gap"] + 2 * se_s, 1) == 0.8


def test_put_inner_bias():
    p = put_bias()
    assert (round(p["tree"], 4), round(p["lower"][0], 4), round(p["lower"][1], 3)) == (6.0326, 6.0325, 0.023)
    assert [round(p["upper"][n][0], 3) for n in (100, 400, 1600)] == [6.134, 6.054, 6.037]
    ex = [p["upper"][n][0] - p["tree"] for n in (100, 400, 1600)]
    assert all(4.5 < ex[i] / ex[i + 1] < 5.5 for i in range(2))


def test_greeks():
    g = greek_table()
    c, d, sm = g["call"], g["digital"], g["digital_smooth"]
    assert (round(g["exact_call"][0], 4), round(g["exact_call"][1], 2)) == (0.6368, 37.52)
    assert (round(c["pw_delta"][0], 4), round(c["pw_delta"][1], 4), round(c["lr_delta"][0], 4), round(c["lr_delta"][1], 4)) \
        == (0.6384, 0.0013, 0.6413, 0.0033)
    assert (round(c["pw_vega"][0], 2), round(c["pw_vega"][1], 2), round(c["lr_vega"][0], 2), round(c["lr_vega"][1], 2)) \
        == (37.72, 0.17, 38.24, 0.62)
    assert round((c["lr_delta"][1] / c["pw_delta"][1]) ** 2, 1) == 6.5 and round((c["lr_vega"][1] / c["pw_vega"][1]) ** 2) == 13
    assert (round(g["exact_digital"][0], 5), round(g["exact_digital"][1], 3)) == (0.01876, -0.657)
    assert d["pw_delta"][0] == 0.0 and d["pw_vega"][0] == 0.0
    assert (round(d["lr_delta"][0], 5), round(d["lr_delta"][1], 5), round(d["lr_vega"][0], 3), round(d["lr_vega"][1], 3)) \
        == (0.01883, 0.00006, -0.648, 0.010)
    assert (round(sm["pw_delta"][0], 5), round(sm["pw_delta"][1], 5), round(sm["pw_vega"][0], 3), round(sm["pw_vega"][1], 3)) \
        == (0.01895, 0.00021, -0.663, 0.007)


def test_adjoint():
    a = adjoint()
    assert (round(a["price"], 3), round(a["delta"], 3), round(a["delta"], 4)) == (5.901, 0.593, 0.5928)
    assert (round(a["bucket_vega"][0], 3), round(a["bump_first"], 3)) == (5.064, 5.065)
    assert (round(a["bucket_vega"][0], 4), round(a["bump_first"], 4)) == (5.0645, 5.0647)
    assert round(a["bucket_vega"][-1], 3) == 0.016 and len(a["bucket_vega"]) == 12


def test_heston():
    h = heston_bias()
    assert round(h["exact"], 3) == 6.751
    assert [round(h["rows"][n]["euler"], 3) for n in (4, 8, 16, 32)] == [0.857, 0.373, 0.140, 0.041]
    assert all(abs(h["rows"][n]["qe"]) < h["rows"][n]["se"] for n in (4, 8, 16, 32))
    assert round(h["rows"][4]["se"], 3) == 0.014


def test_qmc():
    q = qmc_study()
    assert (round(q[4096]["mc"], 3), round(q[4096]["halton"], 3), round(q[4096]["bridge"], 4)) == (0.131, 0.027, 0.0092)
    assert round(q[4096]["mc"] / q[4096]["bridge"]) == 14 and round((q[4096]["mc"] / q[4096]["bridge"]) ** 2, -2) == 200
    assert (round(q[256]["mc"], 2), round(q[256]["halton"], 2), round(q[256]["bridge"], 2)) == (0.53, 0.34, 0.13)


def test_in_sample_and_european():
    r = in_sample()
    assert (round(r["same"], 2), round(r["fresh"], 2), round(r["diff"][0], 2), round(r["diff"][1], 2)) == (18.74, 18.50, 0.25, 0.06)
    assert (round(r["european"][0], 2), round(r["european"][1], 2)) == (15.57, 0.07)
    assert round(bounds()["full"]["lower"][0] - r["european"][0], 2) == 3.08


def test_dual_cost():
    inner = 1000 * 1000 * sum(range(1, 10))
    lower = 200_000 * 9
    assert (inner, lower, inner // lower) == (45_000_000, 1_800_000, 25)
