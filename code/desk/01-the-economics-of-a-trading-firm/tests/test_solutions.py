"""Numbers gate: every numerical answer printed in Book 16, chapter 1 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_econ as e  # noqa: E402

fe = e.fe


def r(x, d=1):
    return round(float(x), d)


def test_hook():
    h = e.hook()
    assert r(h["rev_ratio"], 2) == 2.13 and r(100 * h["comp_change"]) == 2.6 and r(100 * h["comm_change"]) == 2.1
    assert h["pretax"] == (-116.0, 1382.8)


def test_lines_2025():
    v = e.table("virtu")[-1]
    assert r(v["nr"]) == 2145.3 and r(v["volume"]) == 1417.2 and r(v["fixed"]) == 411.5 and r(v["profit"]) == 1205.7
    assert r(100 * v["volume"] / (v["nr"] + v["volume"])) == 39.8 and r(100 * v["operating_margin"]) == 56.2
    assert r(e.table("virtu")[-2]["nr"]) == 1597.7
    m, g = e.table("man")[-1], e.table("gsgbm")[-1]
    assert r(m["profit"], 0) == 428 and r(100 * m["operating_margin"]) == 32.3 and r(100 * m["comp_ratio"]) == 50.9
    assert r(g["profit"], 0) == 17574 and r(100 * g["operating_margin"]) == 42.8 and r(100 * g["comp_ratio"]) == 26.8
    assert (r(v["revenue_per_head"], 2), r(v["comp_per_head"], 2)) == (2.09, 0.51)
    assert (r(m["revenue_per_head"], 2), r(m["comp_per_head"], 2)) == (0.77, 0.39)
    assert r(100 * v["comp_ratio"]) == 24.6 and r(m["nr"], 0) == 1325 and r(g["nr"], 0) == 41075


def test_shares_figure():
    s = e.latest_shares()
    assert [r(100 * s["virtu"][k]) for k in ("volume", "comp", "fixed", "profit")] == [39.8, 14.8, 11.6, 33.8]
    assert r(100 * s["man"]["volume"]) == 5.2 and r(100 * s["man"]["comp"]) == 48.3


def test_small_firm_and_ex4_iq4():
    s = e.small_firm()
    assert s["profit"] == 20 and r(100 * s["fall_flex"]) == 28.6 and r(100 * s["fall_rigid"]) == 20.0
    assert r(s["lev_flex"], 2) == 3.5 and r(s["lev_rigid"], 2) == 5.0
    assert r(fe.profit(fe.CostStructure(50, 0.3), 75), 2) == 2.5 and r(fe.profit(fe.CostStructure(80, 0), 75), 2) == -5.0
    assert r(fe.profit(fe.CostStructure(50, 0.2), 60), 2) == -2.0


def test_pay_fits():
    a, b, sb = e.pay_fit("virtu")
    assert (r(b, 3), r(sb, 3)) == (0.048, 0.045)
    a, b, sb = e.pay_fit("man")
    assert (r(b, 2), r(sb, 3)) == (0.29, 0.094)
    assert r(e.pay_fit("gsgbm")[1], 2) == 0.20
    s = e.sts("man")[1:]
    _, b, _, sb = fe.fit_line([x.net_revenue for x in s], [x.comp for x in s])
    assert (r(b, 2), r(sb, 2)) == (0.13, 0.13)
    assert r(100 * e.man_reported_comp_ratio(2025)) == 48.3 and r(100 * e.man_reported_comp_ratio(2022)) == 40.0


def test_breakeven_table():
    want = {"virtu": (59.0, 1.69, 56.2, 1.78, 836.8), "man": (45.6, 2.19, 32.3, 3.10, 510.8),
            "gsgbm": (53.3, 1.88, 42.8, 2.34, 15399.9)}
    for f, (xf, lf, xr, lr, cfix) in want.items():
        s, t = e.structure(f), e.structure(f, flex=False)
        assert (r(100 * s["fall"]), r(s["lev"], 2), r(100 * t["fall"]), r(t["lev"], 2)) == (xf, lf, xr, lr)
        assert r(s["cs"].fixed) == cfix
    ch, c = e.profit_curves()
    i = list(ch).index(-0.3)
    assert [r(100 * c[f][i]) for f in ("virtu", "man", "gsgbm")] == [49.2, 34.2, 43.7]
    assert r(100 * e.breakeven_in("virtu", 2019)) == 22.9 and r(100 * e.table("virtu")[0]["operating_margin"]) == 21.8


def test_cycle_and_roe():
    b, sb, rho = e.vix_fit("virtu")
    assert (r(b, 0), r(sb, 0), r(rho, 2)) == (52, 33, 0.58)
    b, sb, rho = e.vix_fit("man")
    assert (r(b, 0), r(sb, 0), r(rho, 2)) == (-13, 23, -0.27)
    assert r(100 * e.virtu_roe(2025)) == 52.7 and r(100 * e.virtu_roe(2023)) == 17.3
    assert r(100 * e.gs_roe(2025)[0]) == 16.4
    t = e.table("virtu")
    assert r(100 * (t[1]["nr"] / t[0]["nr"] - 1)) == 133.0 and r(100 * (t[1]["profit"] / t[0]["profit"] - 1)) == 607.5
    assert r((t[1]["profit"] / t[0]["profit"] - 1) / (t[1]["nr"] / t[0]["nr"] - 1), 2) == 4.57
    assert r(1 / e.breakeven_in("virtu", 2019), 2) == 4.37
    mx = max(e.table("virtu"), key=lambda d: d["comp"] - (e.pay_fit("virtu")[0] + e.pay_fit("virtu")[1] * d["nr"]))
    assert mx["year"] == 2025
