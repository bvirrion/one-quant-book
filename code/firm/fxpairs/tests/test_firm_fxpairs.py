"""Acceptance tests of the Book 2, Chapter 14 build (pairs, spot dates, crosses)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fxpairs import Quote, arbitrage, cross_via_usd, pair_name, pip, spot_date, spread_pips

TUE = dt.date(2026, 10, 6)
WED, THU, FRI = (TUE + dt.timedelta(days=k) for k in (1, 2, 3))


def test_pair_names_and_pips():
    assert pair_name("USD", "EUR") == "EURUSD" and pair_name("JPY", "USD") == "USDJPY"
    assert pair_name("GBP", "EUR") == "EURGBP" and pair_name("JPY", "AUD") == "AUDJPY"
    assert pip("USDJPY") == 0.01 and pip("EURUSD") == 0.0001


def test_spot_dates_follow_the_published_example():
    # Chaboud and Wright (2003): Tuesday dollar-yen trade
    assert spot_date(TUE, "USDJPY", {}) == THU
    assert spot_date(TUE, "USDJPY", {"JPY": {WED}}) == FRI
    assert spot_date(TUE, "USDJPY", {"USD": {WED}}) == THU
    assert spot_date(TUE, "USDJPY", {"USD": {THU}}) == FRI
    assert spot_date(TUE, "USDCAD", {}) == WED
    assert spot_date(dt.date(2026, 10, 9), "EURUSD", {}) == dt.date(2026, 10, 13)   # Friday -> Tuesday


def test_crosses():
    eurusd, usdjpy, gbpusd = Quote(1.1462, 1.1464), Quote(156.86, 156.88), Quote(1.3371, 1.3373)
    eurjpy = cross_via_usd(("EURUSD", eurusd), ("USDJPY", usdjpy), "EURJPY")
    assert math.isclose(eurjpy.bid, 1.1462 * 156.86) and math.isclose(eurjpy.ask, 1.1464 * 156.88)
    eurgbp = cross_via_usd(("EURUSD", eurusd), ("GBPUSD", gbpusd), "EURGBP")
    assert math.isclose(eurgbp.bid, 1.1462 / 1.3373) and math.isclose(eurgbp.ask, 1.1464 / 1.3371)
    assert spread_pips(eurgbp, "EURGBP") > 0
    assert arbitrage(Quote(eurjpy.ask + 0.01, eurjpy.ask + 0.03), eurjpy) == "sell direct, buy synthetic"
    assert arbitrage(Quote(eurjpy.bid, eurjpy.ask), eurjpy) is None
