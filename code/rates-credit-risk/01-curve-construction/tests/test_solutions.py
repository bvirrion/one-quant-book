"""Numbers gate: every numerical answer printed in Book 6, chapter 1 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_curves as m
from firm_curvebuild import Swap, calibrate, swap_pv, with_quote

CURVES = m.curves()
SWITCH = m.interpolation_switch()


def test_text():
    c = CURVES["linear_zero"].curve
    i = c.labels.index("2Y")
    assert round(c.zeros[i] * 100, 4) == 3.2883
    assert (round(c.fwd_t(c.times[i] - 1e-4) * 100, 3), round(c.fwd_t(c.times[i] + 1e-4) * 100, 3)) == (2.964, 3.331)
    p = m.ECB_2026_09_22
    assert [round(p[k], 4) for k in ("b0", "b1", "b2", "b3", "tau1", "tau2")] == [
        1.6306, 0.6958, 2.5849, 6.6622, 1.0632, 14.4456]
    assert round(m.svensson(10, **p), 4) == 3.4527 and round(m.svensson(1e-9, **p), 2) == 2.33
    peak = max((m.svensson_forward(t / 10, **p), t / 10) for t in range(1, 301))
    assert round(peak[0], 2) == 4.08 and 13 <= peak[1] <= 15
    b = m.off_pillar_buckets(8)
    lab = [x.label for x in m.instruments()]
    ff, cs = dict(zip(lab, b["flat_forward"], strict=True)), dict(zip(lab, b["cubic_zero"], strict=True))
    assert (round(ff["7Y"], -2), round(ff["10Y"], -2)) == (40_400, 29_200)
    assert [round(cs[k], -2) for k in ("7Y", "5Y", "4Y", "12Y")] == [62_100, -22_200, 11_000, -9_500]
    assert all(round(sum(v), -2) == 69_600 for v in b.values())
    assert round(-SWITCH["pnl"], -3) == 90_000
    assert sum(q for _, q, _ in m.BOOK) == 5.0e9
    assert round(583_281 / 346_584 - 1, 2) == 0.68        # "grown by two thirds"


def test_exercises():
    assert round((3.30 * 3 - 3.25 * 2) / 1, 2) == 3.40
    assert round((100 - 96.72) - 0.006, 3) == 3.274
    t0, z0, t1, z1, t2, z2 = 1.2110, 3.4165, 2.0027, 3.2883, 3.0027, 3.3095
    assert (round(z1 + t1 * (z1 - z0) / (t1 - t0), 3), round(z1 + t1 * (z2 - z1) / (t2 - t1), 3)) == (2.964, 3.331)
    p = m.ECB_2026_09_22
    assert round(m.svensson_forward(10, **p), 4) == 3.9407 and round(p["b0"] + p["b1"], 4) == 2.3264
    one = m.off_pillar_buckets(8, bump=1e-4)["monotone_convex"]
    lab = [x.label for x in m.instruments()]
    d = dict(zip(lab, one, strict=True))
    assert [round(d[k]) for k in ("5Y", "7Y", "10Y", "12Y")] == [-5_663, 50_916, 33_188, -7_232]
    assert round(sum(one)) == 71_216
    assert round(sum(m.off_pillar_buckets(8)["monotone_convex"])) == 69_610
    ins = m.instruments()
    c = calibrate(m.SPOT, ins, "monotone_convex").curve
    k = Swap(m.SPOT, 8, 0.0).model(c)
    up = calibrate(m.SPOT, [with_quote(i, i.quote() + 1e-4) for i in ins], "monotone_convex").curve
    assert round(swap_pv(up, m.SPOT, 8, k, 1e8) - swap_pv(c, m.SPOT, 8, k, 1e8)) == 69_579


def test_problem():
    old, new = SWITCH["par_old"], SWITCH["par_new"]
    assert (round(old[17] * 100, 4), round(new[17] * 100, 4)) == (3.9975, 4.0074)
    assert (round(old[6] * 100, 4), round(new[6] * 100, 4)) == (3.5005, 3.5007)
    assert round(SWITCH["pnl"]) == -90_062
    cn = CURVES["monotone_convex"].curve
    per = {n: round(swap_pv(cn, m.SPOT, n, old[n], q, pay)) for n, q, pay in m.BOOK}
    assert per == {6: 5_462, 8: -135_555, 9: 150_433, 11: -159_817, 13: 234_745, 17: -863_596, 22: 678_267}
    lab = [x.label for x in m.instruments()]
    bo, bn = dict(zip(lab, SWITCH["buckets_old"], strict=True)), dict(zip(lab, SWITCH["buckets_new"], strict=True))
    assert (round(bo["15Y"]), round(bn["15Y"]), round(bo["20Y"]), round(bn["20Y"])) == (
        -346_584, -583_281, 345_841, 465_177)
    assert round(bn["12Y"]) == -77_741
    assert (round(sum(SWITCH["buckets_old"])), round(sum(SWITCH["buckets_new"]))) == (555_270, 557_510)
    dv15 = swap_pv(cn.bumped(None, 1e-4), m.SPOT, 15, Swap(m.SPOT, 15, 0).model(cn), 1e9)
    dv20 = swap_pv(cn.bumped(None, 1e-4), m.SPOT, 20, Swap(m.SPOT, 20, 0).model(cn), 1e9)
    assert (round(dv15), round(dv20)) == (1_149_075, 1_388_775)
    assert (round(346_584 / dv15, 4), round(583_281 / dv15, 4)) == (0.3016, 0.5076)
    assert (round(345_841 / dv20, 4), round(465_177 / dv20, 4)) == (0.2490, 0.3350)


def test_exercise_3_one_year_swap():
    k, cal = m.with_one_year_swap()
    c0, c1 = CURVES["flat_forward"].curve, cal.curve
    assert round(k * 100, 4) == 3.4639 and round((k + 2e-4) * 100, 4) == 3.4839 and cal.max_error < 1e-12
    assert (round(c0.fwd_t(0.98) * 100, 3), round(c1.fwd_t(0.98) * 100, 3), round(c1.fwd_t(1.1) * 100, 3)) == (
        3.242, 3.753, 3.150)
    assert round((c1.fwd_t(0.98) - c0.fwd_t(0.98)) * 1e4) == 51
