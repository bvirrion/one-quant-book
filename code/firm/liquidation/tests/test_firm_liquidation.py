"""Acceptance tests of the Book 3, Chapter 18 build (margin and liquidation engine)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_liquidation import (
    Account,
    Tier,
    adl_rank,
    bankruptcy_price_linear,
    cross_health,
    liq_price_inverse,
    liq_price_linear,
    liquidate,
    maintenance_margin,
    sell_into_book,
)

TIERS = [Tier(50_000, 0.004, 0), Tier(250_000, 0.005, 50), Tier(1e12, 0.01, 1_300)]


def test_tiers_are_continuous():
    assert maintenance_margin(50_000, TIERS) == 200
    assert round(maintenance_margin(50_000.01, TIERS), 2) == 200.0
    assert maintenance_margin(250_000, TIERS) == 1_200
    assert round(maintenance_margin(250_000.01, TIERS), 2) == 1_200.0


def test_linear_prices():
    # 1 BTC long at 60,000 with 10x (6,000 margin), mmr 0.5%
    p = liq_price_linear(1, 60_000, 6_000, 0.005)
    assert round(p, 2) == round(54_000 / 0.995, 2)
    assert bankruptcy_price_linear(1, 60_000, 6_000) == 54_000
    s = liq_price_linear(-1, 60_000, 6_000, 0.005)
    assert round(s, 2) == round(66_000 / 1.005, 2)
    assert bankruptcy_price_linear(-1, 60_000, 6_000) == 66_000


def test_inverse_prices():
    # long 60,000 contracts at 60,000 with 0.1 BTC margin (10x)
    assert round(liq_price_inverse(60_000, 60_000, 0.1, 0.005), 2) == round(60_000 * 1.005 / 1.1, 2)
    assert liq_price_inverse(-60_000, 60_000, 1.0, 0.005) == float("inf")


def test_cross_health():
    h = cross_health(10_000, [(1, 60_000, 58_000), (-10, 3_000, 3_100)], TIERS)
    assert round(h, 4) == round((10_000 - 2_000 - 1_000) / (58_000 * 0.005 - 50 + 31_000 * 0.004), 4)


def test_book_insurance_and_adl():
    avg, book = sell_into_book(3, [(100, 1), (99, 1), (98, 5)])
    assert avg == 99 and book == [(98, 4)]
    long = Account("L", 10, 100, 100)                # bankruptcy price 90
    shorts = [Account("S1", -5, 120, 100), Account("S2", -20, 105, 1_000)]
    fund, _, fills = liquidate(long, [(91, 100)], 0.0, shorts, 89.0)
    assert fund == 10 and fills == []                 # sold above bankruptcy: surplus to the fund
    fund, _, fills = liquidate(long, [(85, 100)], 20.0, shorts, 85.0)
    assert fund == 20 and fills == [("S1", 5), ("S2", 5)]
    assert [a.name for a in adl_rank(shorts, 85.0)] == ["S1", "S2"]
