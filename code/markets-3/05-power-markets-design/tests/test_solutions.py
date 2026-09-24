"""Numbers gate: every numerical answer printed in Book 3, Chapter 5 (text and solutions)."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/dayahead"))
from firm_dayahead import BUY, SELL, Order, clear, marginal_cost
from m3_power import day, hour, load_de, negative_stats, spreads_example, stack, to_berlin, two_zones

NS = negative_stats()
MAY = day(dt.date(2025, 5, 11))


def test_text():
    h13 = [r for r in MAY if r[0] == 13][0]
    assert round(h13[2]) == 44 and round(h13[3]) == 40 and round(h13[1], 2) == -250.32
    top = max(load_de(), key=lambda r: r[1])
    assert to_berlin(top[0]) == dt.datetime(2024, 12, 12, 17, 0) and round(top[1]) == 936
    assert (top[3] + top[4]) / 1000 < 1.5                        # windless: under 1.5 GW of wind
    s = {n: mc for n, _, mc in stack(10)}
    assert round(s["gas CCGT"], 2) == 89.35 and round(s["coal"], 2) == 89.68 and round(s["lignite"], 2) == 82.38
    assert round(hour(45, 10)["price"], 2) == 89.35 and hour(45, 10)["marginal"] == "gas CCGT"
    assert round(hour(60, 10)["price"], 2) == 89.68 and hour(60, 10)["marginal"] == "coal"
    assert round(hour(60, 30)["price"], 2) == 89.35 and hour(60, 55)["price"] == 10.0
    sp = spreads_example()
    assert round(sp["spark"], 2) == 36.36 and round(sp["dark"], 2) == 70.00
    z = two_zones(3)
    assert z["flow"] == 3 and round(z["price_a"], 2) == 82.38 and round(z["price_b"], 2) == 89.68
    assert round(z["rent"] * 1000) == 21890 and round(z["price_b"] - z["price_a"], 2) == 7.30
    assert round(z["rent"] * 1000, -2) == 21900 and round(z["price_b"] - z["price_a"], 3) == 7.297  # printed: about 21 900; 21 890 unrounded
    z20 = two_zones(20)
    assert round(z20["price_a"], 2) == round(z20["price_b"], 2) == 89.35
    assert NS["by_year"] == {2024: 457, 2025: 573} and sum(NS["by_hour"]) == 1030
    assert [h for h, p, s, ld in MAY if s > ld] == [11, 12, 13, 14, 15]


def test_exercises():
    r = clear([Order(SELL, 0, 300), Order(SELL, 40, 200), Order(SELL, 90, 200), Order(SELL, 150, 100),
               Order(BUY, 4000, 450)])
    assert r.price == 40 and r.fills[:4] == (300, 150, 0, 0)
    assert round(marginal_cost(30, 0.5, 0.202, 70), 2) == 88.28
    assert two_zones(13)["price_a"] < two_zones(13)["price_b"]
    assert round(two_zones(13.01)["price_a"], 2) == round(two_zones(13.01)["price_b"], 2) == 89.35
    assert [h for h, p, s, ld in MAY if p < -60] == [12, 13, 14, 15]
    assert NS["by_hour"].index(max(NS["by_hour"])) == 13 and max(NS["by_hour"]) == 171
    assert NS["low"] == (dt.datetime(2025, 5, 11, 13, 0), -250.32)


def test_problem():
    neg = [(h, p) for h, p, s, ld in MAY if p < 0]
    assert [h for h, _ in neg] == list(range(9, 18)) and round(sum(p for _, p in neg) / 9, 2) == -98.54
    mc = round({n: c for n, _, c in stack(0)}["lignite"], 2)          # the problem states 82.38
    assert round(400 * (mc + 250.32)) == 133080
    assert round(sum(400 * (mc - p) for _, p in neg)) == 651308
    assert [h for h, p in neg if p >= -60] == [9, 10, 11, 16, 17]
