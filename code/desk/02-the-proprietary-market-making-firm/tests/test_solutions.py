"""Numbers gate: every numerical answer printed in Book 16, chapter 2 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_partner as m  # noqa: E402

fp = m.fp


def r(x, d=1):
    return round(float(x), d)


def test_requirements():
    (req, which), fo, vol = m.regulatory()
    assert fo == 95.0 and vol == 10_000.0 and req == 23.75 and which == "fixed overheads"
    assert fp.own_funds_requirement(95.0, 10_000.0, 0.0, 0.0)[0] == 23.75
    assert math.isclose(0.001 * vol, 10.0) and math.isclose(0.0001 * vol, 1.0)
    assert fp.own_funds_requirement(95.0, 0.0, 10_000.0, 0.0) == (23.75, "fixed overheads")
    assert m.BASE.capital0 / req > 8 and r(m.BASE.capital0 / req, 1) == 8.4


def test_year1_and_allocation():
    y = m.year1()
    assert (y["volume"], y["revenue"], y["spend"], y["profit"]) == (10_000.0, 250.0, 35.0, 116.25)
    p = fp.Partnership([fp.Member(n, x) for n, x in (("a", 40), ("b", 30), ("c", 20), ("d", 10))])
    d = p.allocate(116.25, 0.8)
    assert [r(v, 2) for v in d.values()] == [37.2, 27.9, 18.6, 9.3]
    assert r(sum(d.values()), 2) == 93.0 and r(p.total_capital, 2) == 23.25 and r(p.members[0].capital, 2) == 9.3


def test_retention():
    v = m.retention_curve()
    grid = list(m.GRID)
    assert [r(v[grid.index(x)], 0) for x in (0.0, 0.2, 0.5, 0.8)] == [582, 939, 706, 296]
    best, val = m.best_retention()
    assert best == 0.2 and r(val, 0) == 939
    assert r(m.target_value(), 0) == 1210 and r(m.target_value() - val, 0) == 271
    assert [m.years_to_fill(retention=x) for x in (0.2, 0.5, 0.8)] == [6, 3, 2]
    s = fp.simulate(m.BASE, fp.target_capital(400.0))
    assert s["payout"][0] == 0 and s["payout"][1] == 0 and s["payout"][2] > 0


def test_departure():
    rows = m.accounts()
    full = m.BASE.market * m.BASE.margin
    first = next(x["year"] for x in rows if x["capital"] >= full)
    assert first == 8


def test_treadmill():
    assert r(fp.steady_spend_share(0.15, 0.20), 2) == 0.35 and r(35 * 1.15 ** 9, 0) == 123
    t = m.treadmill()
    assert r(t["lean"]["rel"][9], 2) == 0.44 and r(t["lean"]["capture"][9] * 1e4, 2) == 0.44
    assert m.profit_gone_year(t["steady"]) == 20 and m.profit_gone_year(t["lean"]) == 18
    assert t["lean"]["profit"][0] > t["steady"]["profit"][0] and t["lean"]["profit"][1] < t["steady"]["profit"][1]
    t_star = math.log((500 - 60) / 35) / math.log(1.15)
    assert r(t_star, 1) == 18.1 and math.ceil(t_star + 1) == 20
    assert m.profit_gone_year(m.growing_market(0.10, 60)) == 56
    assert r(fp.steady_spend_share(0.10, 0.25), 2) == 0.35
