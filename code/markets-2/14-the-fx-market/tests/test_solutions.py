"""Numbers gate: every numerical answer printed in Book 2, Chapter 14 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from fx_demo import LEGS, crosses, relative_spread_bp, spot_examples, spread_pips, the_cross

C = crosses()
P = the_cross()


def test_text():
    assert (round(C["EURJPY"].bid, 4), round(C["EURJPY"].ask, 4)) == (179.7929, 179.8472)
    assert round(spread_pips(C["EURJPY"], "EURJPY"), 2) == 5.43 and round(relative_spread_bp(C["EURJPY"]), 2) == 3.02
    assert (round(relative_spread_bp(LEGS["EURUSD"]), 2), round(relative_spread_bp(LEGS["USDJPY"]), 2)) == (1.74, 1.27)
    assert (round(C["EURGBP"].bid, 5), round(C["EURGBP"].ask, 5)) == (0.85710, 0.85738)
    assert round(spread_pips(C["EURGBP"], "EURGBP"), 2) == 2.78
    assert (round(C["GBPJPY"].bid, 4), round(C["GBPJPY"].ask, 4)) == (209.7375, 209.7956)
    assert round(spread_pips(C["GBPJPY"], "GBPJPY"), 2) == 5.81
    assert round(46 + 50) == 96


def test_exercises():
    assert round(5e6 * LEGS["EURUSD"].bid) == 5_731_000 and round(spread_pips(LEGS["EURUSD"], "EURUSD")) == 2
    d = {(p, h): v for p, h, v in spot_examples()}
    assert d[("USDJPY", "none")] == dt.date(2026, 10, 8) and d[("USDJPY", "Japan Wednesday")] == dt.date(2026, 10, 9)
    assert d[("USDJPY", "US Wednesday")] == dt.date(2026, 10, 8) and d[("USDJPY", "US Thursday")] == dt.date(2026, 10, 9)
    assert d[("USDCAD", "none")] == dt.date(2026, 10, 7)
    g = [round(relative_spread_bp(x), 3) for x in (C["GBPJPY"], LEGS["GBPUSD"], LEGS["USDJPY"])]
    assert g == [2.771, 1.496, 1.275]


def test_problem():
    assert round(P["pips"], 2) == 5.43 and round(P["rel_bp"], 2) == 3.02
    assert (round(P["leg1_bp"], 3), round(P["leg2_bp"], 3), round(P["leg1_bp"] + P["leg2_bp"], 2)) == (1.745, 1.275, 3.02)
    assert round(P["usd_leg"]) == 11_464_000
    assert P["tight_ok"] and P["crossed"] == "sell direct, buy synthetic"
    assert round(P["profit_jpy"]) == 27_680 and round(P["profit_usd"]) == 176
    d = {(p, h): v for p, h, v in spot_examples()}
    assert d[("EURJPY", "Japan Wednesday")] == dt.date(2026, 10, 9)
