"""Numbers gate: every numerical answer printed in Book 5, Chapter 26 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_optmm import dividend_study, hedge_study, limits_by_seed, play_spread, stale_table, toy_mm, width_study


def test_stale():
    t = stale_table()
    m1, m3 = 1 / 12, 0.25
    assert [round(t[(d, m1)], 4) for d in (1, 10)] == [0.0023, 0.0072]
    assert [round(t[(d, m1)], 3) for d in (60, 300)] == [0.018, 0.039]
    assert [round(t[(d, m3)], 4) for d in (1, 10)] == [0.0013, 0.0042]
    assert [round(t[(d, m3)], 3) for d in (60, 300)] == [0.010, 0.023]


def test_widths():
    w = width_study()
    assert [round(w[r]["w_star"], 2) for r in (0.0, 2.0, 5.0, 10.0, 20.0)] == [0.30, 0.35, 0.42, 0.55, 0.78]
    assert [round(w[r]["profit"], 2) for r in (0.0, 2.0, 5.0, 10.0, 20.0)] == [2.21, 1.89, 1.51, 1.07, 0.65]
    assert (round(w["vega_1m"], 3), round(w["vega_3m"], 3)) == (0.115, 0.199)
    assert (round(100 * 0.42 * w["vega_1m"], 1), round(100 * 0.42 * w["vega_3m"], 1)) == (4.8, 8.4)
    assert (round(100 * 0.42 * w["vega_1m"], 2), round(100 * 0.42 * w["vega_3m"], 2)) == (4.83, 8.37)


def test_hedging():
    h = hedge_study()
    assert tuple(round(x, 3) for x in h["time"][1][:2]) == (0.525, 0.321)
    assert tuple(round(x, 3) for x in h["time"][13][:2]) == (0.142, 0.855)
    assert tuple(round(x, 3) for x in h["time"][3][:2]) == (0.302, 0.434)
    assert tuple(round(x, 3) for x in h["band"][1.0][:2]) == (0.140, 0.505)
    assert tuple(round(x, 3) for x in h["band"][0.25][:2]) == (0.313, 0.313)
    assert round(100 * (1 - h["band"][1.0][1] / h["time"][13][1])) == 41


def test_dividend_play_named_result():
    d = dividend_study()
    assert d["exercise"] and d["gain"] == 48.0
    r = d[0.3]
    assert (round(d[0.3]["q"]), round(r["res"]["unassigned"]), round(100 * r["res"]["captured"])) == (32_947, 2_605, 87)
    assert (round(r["res"]["gross"]), round(r["res"]["cost"]), round(r["res"]["net"])) == (125_026, 16_474, 108_553)
    assert (round(d[0.1]["q"]), round(d[0.1]["res"]["net"]), round(d[0.5]["q"]), round(d[0.5]["res"]["net"])) == \
        (16_909, 28_591, 43_990, 193_510)
    assert round(d["no_fee"]["net"], -2) == 144_000 and round(d[0.1]["res"]["cost"], -2) == 8_500
    assert round(math.sqrt(2 * 0.3 * 10_000 * 48 * 10_000 / 0.5)) == 75_895
    assert round(2 * 32_947 * 3_000 / 75_894) == 2_605


def test_spread_and_seeds():
    p = play_spread()
    assert (round(p["mean"]), round(p["sd"], -1), round(p["sd_exact"]), round(p["p01"])) == (108_552, 870, 871, 106_502)
    s = limits_by_seed()
    assert (round(s["mean"]), round(s["sd"]), round(s["se"]), s["n"] - s["positive"]) == (9_585, 11_597, 2_593, 6)


def test_toy():
    on, off = toy_mm(limits=True), toy_mm(limits=False)
    assert [round(on[k]) for k in ("edge", "selection", "hedge_cost", "inventory", "total")] == [36_280, -8_720, -9_815, -6_605, 11_141]
    assert (round(off["inventory"]), round(off["total"])) == (-15_240, -607)
    assert round(min(x["6m"] for x in on["vega_path"])) == -3_369 and round(min(x["6m"] for x in off["vega_path"])) == -5_033
    assert round(on["total"] - off["total"], -2) == 11_700
