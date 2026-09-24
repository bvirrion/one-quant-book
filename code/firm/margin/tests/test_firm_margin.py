"""Acceptance tests of the Chapter 20 build."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_margin import Market, Params, Position, black76, portfolio_margin, product_margin, risk_array, scenarios

P = Params(price_scan=345.0, vol_scan=0.04, multiplier=50.0, intermonth_charge=400.0, short_option_min=175.0)
MKT = Market({("ES", "Z"): 6000.0, ("ES", "H"): 6060.0, ("NQ", "Z"): 21000.0},
             {("ES", "Z"): 0.18, ("ES", "H"): 0.18, ("NQ", "Z"): 0.22},
             {("ES", "Z"): 0.25, ("ES", "H"): 0.5, ("NQ", "Z"): 0.25})


def test_sixteen_scenarios_and_a_future_s_risk_array():
    sc = scenarios(P)
    assert len(sc) == 16 and sc[0] == (0.0, 0.04, 1.0) and sc[10] == (345.0, 0.04, 1.0) and sc[15] == (-1035.0, 0.0, 0.30)
    arr = risk_array(Position("ES", "Z", 1), MKT, P)
    assert arr[0] == 0 and arr[2] == pytest.approx(-5750) and arr[12] == pytest.approx(17250)
    assert arr[15] == pytest.approx(15525)                        # 3 x 17,250 x 30%


def test_long_future_margin_is_the_price_scan_range():
    m = product_margin([Position("ES", "Z", 1)], MKT, P)
    assert m.scan_risk == pytest.approx(17250) and m.worst_scenario in (13, 14) and m.total == pytest.approx(17250)


def test_calendar_spread_pays_only_the_intermonth_charge():
    m = product_margin([Position("ES", "Z", 10), Position("ES", "H", -10)], MKT, P)
    assert m.scan_risk == pytest.approx(0.0, abs=1e-6) and m.intermonth == 4000 and m.total == 4000


def test_short_far_out_of_the_money_put_is_caught_by_the_extreme_scenario_or_the_minimum():
    pos = [Position("ES", "Z", -10, 4800.0, "P")]
    m = product_margin(pos, MKT, P)
    assert m.worst_scenario == 16 and m.scan_risk > 1750 and m.total == m.scan_risk
    tiny = product_margin([Position("ES", "Z", -10, 3000.0, "P")], MKT, P)
    assert tiny.scan_risk < 1750 and tiny.total == 1750           # the short option minimum binds


def test_put_call_parity_and_a_hedged_option():
    c, p = black76(6000, 6100, 0.18, 0.25, "C"), black76(6000, 6100, 0.18, 0.25, "P")
    assert c - p == pytest.approx(6000 - 6100)
    naked = product_margin([Position("ES", "Z", -10, 6000.0, "C")], MKT, P).total
    covered = product_margin([Position("ES", "Z", -10, 6000.0, "C"), Position("ES", "Z", 5)], MKT, P).total
    assert covered < 0.5 * naked


def test_inter_commodity_credit_needs_opposite_risks():
    pn = Params(price_scan=1300.0, vol_scan=0.04, multiplier=20.0)
    params = {"ES": P, "NQ": pn}
    hedged = {"ES": [Position("ES", "Z", 10)], "NQ": [Position("NQ", "Z", -7)]}
    total, res = portfolio_margin(hedged, MKT, params, {("ES", "NQ"): 0.35})
    gross = res["ES"].total + res["NQ"].total
    assert total == pytest.approx(gross - 2 * 0.35 * min(res["ES"].scan_risk, res["NQ"].scan_risk))
    same = {"ES": [Position("ES", "Z", 10)], "NQ": [Position("NQ", "Z", 7)]}
    total2, res2 = portfolio_margin(same, MKT, params, {("ES", "NQ"): 0.35})
    assert total2 == pytest.approx(res2["ES"].total + res2["NQ"].total)
