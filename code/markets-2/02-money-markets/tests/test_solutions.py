"""Numbers gate: every numerical answer printed in Book 2, Chapter 2 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mmyield"))
from firm_mmyield import (
    discount_from_price,
    investment_rate,
    money_market_yield,
    price_from_discount,
    term_proceeds,
)
from money_market_demo import AMOUNT, NORMAL_ON, ON_RRP, WEEKS, one_week_by_start, problem_numbers

P = problem_numbers()
ROOT = pathlib.Path(__file__).resolve().parents[3]


def rrp(date):
    with open(ROOT.parent / "data/markets-2/rrp_ontsyd_2022h2.csv") as f:
        return {r["observation_date"]: r["RRPONTSYD"] for r in csv.DictReader(f)}[date]


def test_text():
    assert round(float(rrp("2022-12-29"))) == 2308 and round(float(rrp("2022-12-30"))) == 2554
    assert round(float(rrp("2022-12-30")) - float(rrp("2022-12-29"))) == 245
    assert round(float(rrp("2023-01-03"))) == 2188
    p = price_from_discount(0.0382, 91)
    assert p == 99.034389
    m, i = money_market_yield(p, 91), investment_rate(p, 91, 365)
    assert (round(m * 100, 4), round(i * 100, 4)) == (3.8572, 3.9108) and round((i - 0.0382) * 1e4) == 9
    # a one-night turn of 8 bp diluted over a week and a month
    assert round(8 / 7, 1) == 1.1 and round(8 / 30, 2) == 0.27
    rates = dict(one_week_by_start())
    spanning = rates[max(d for d in rates if d.month == 9)]
    plain = rates[min(rates)]
    assert round((spanning - plain) * 1e4, 1) == 1.1                  # Figure 2.4 caption


def test_exercises():
    assert price_from_discount(0.0375, 182) == 98.104167
    assert round(discount_from_price(99.04, 91) * 100, 4) == 3.7978
    assert round(money_market_yield(99.04, 91) * 100, 4) == 3.8346
    assert round(investment_rate(99.04, 91, 365) * 100, 4) == 3.8879
    assert round(term_proceeds(10e6, 0.04, 90)) == 10_100_000
    assert price_from_discount(0.0765, 364) == 92.265 and round(investment_rate(92.265, 364, 365) * 100, 3) == 8.237
    assert round(1.1 / 20 * 100, 1) == 5.5
    bey = [round(investment_rate(price_from_discount(0.038, 7 * w), 7 * w, 365) * 100, 4) for w in WEEKS]
    assert bey == [3.8642, 3.8699, 3.8757, 3.8901, 3.9018, 3.9282, 3.9675]
    b13 = investment_rate(price_from_discount(0.0380, 91), 91, 365)
    b52 = investment_rate(price_from_discount(0.0379, 364), 364, 365)
    assert (round(b13 * 100, 4), round(b52 * 100, 4), round((b52 - b13) * 1e4, 1)) == (3.8901, 3.9567, 6.7)


def test_problem():
    assert round(P["deposit"]) == 384_028 and round(P["deposit_bey"] * 100, 4) == 4.0049
    assert round(P["rrp"]) == 364_665
    assert round(AMOUNT * ((1 + NORMAL_ON / 360) ** 3 - 1)) == 161_684
    assert round(P["turn"] * 100, 4) == 4.0009 and round(P["premium_bp"], 2) == 12.09
    assert round(P["extra_cost"]) == 6_716 and round(P["rrp_shortfall"]) == 13_938
    assert round(P["two_week"] * 100, 4) == 3.9171
    f7 = ((1 + NORMAL_ON / 360) ** 7 - 1) * 360 / 7
    f14 = ((1 + NORMAL_ON / 360) ** 14 - 1) * 360 / 14
    assert round((0.0395 - f7) * 1e4, 1) == 6.9 and round((P["two_week"] - f14) * 1e4, 1) == 3.4
    assert ON_RRP == 0.0375 and round(P["premium_bp"], 1) == 12.1
