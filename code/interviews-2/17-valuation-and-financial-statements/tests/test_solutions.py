"""Valuation and Financial Statements: every printed number, from the accounting identities and exact arithmetic."""
from fractions import Fraction as F

import numpy as np
from scipy.optimize import brentq

NONNUMERIC = {}


def r(x, n=2):
    return round(float(x), n)


def test_q1():
    t = F(1, 4)
    dni = -10 * (1 - t)
    assert dni == F(-15, 2)
    cfo = dni + 10
    assert cfo == F(5, 2)
    dcash, dppe, dre = cfo, F(-10), dni
    assert dcash + dppe == dre  # assets change by exactly what equity changes by
    assert 10 * t == F(5, 2)
    # The follow-up: interest paid in cash. Cash falls by 7.5 whichever heading the interest goes under.
    assert -10 * (1 - t) == F(-15, 2)
    ni = -10 * (1 - t)
    in_operating = ni  # nothing to add back
    in_financing_cfo, in_financing_cff = ni + 10, F(-10)  # interest moved out of operating
    assert in_operating == F(-15, 2) and in_financing_cfo > in_operating
    assert in_financing_cfo + in_financing_cff == in_operating


def test_q2():
    t = F(1, 4)
    revenue, cost = 100, 60
    pretax = revenue - cost
    tax = pretax * t
    ni = pretax - tax
    assert (pretax, tax, ni) == (40, 10, 30)
    cfo = ni - 100 + 60  # receivables up 100; inventory bought and sold; payables up 60
    assert cfo == -10
    assets = 100 - 10
    liabilities = 60
    assert assets == liabilities + ni


def test_q3():
    ev = 1000 + 300 - 100 + 50 + 30
    assert ev == 1280
    assert F(ev, 160) == 8
    # Borrow 100 and hold it as cash; pay out 50 of cash; buy back 100 of stock with cash.
    assert (1000 + 400 - 200 + 50 + 30) == ev
    assert ((1000 - 50) + 300 - 50 + 50 + 30) == ev
    assert ((1000 - 100) + 300 - 0 + 50 + 30) == ev


def test_q4():
    nopat = 200 * F(3, 4)
    assert nopat == 150
    ufcf = nopat + 40 - 70 - 20
    assert ufcf == 100
    lfcf = ufcf - 20 * F(3, 4) + 10
    assert lfcf == 95
    # From the top down, with interest: net income + D&A - capex - dNWC + net borrowing.
    ni = (200 - 20) * F(3, 4)
    assert ni == 135 and ni + 40 - 70 - 20 + 10 == 95


def test_q5():
    assert r(F(100) / (F(9, 100) - F(3, 100)), 0) == 1667
    v = F(100) / F(6, 100)
    up = F(100) / F(5, 100)
    assert up == 2000 and r(up / v - 1, 2) == 0.2
    assert F(100) / (F(8, 100) - F(3, 100)) == 2000
    assert r(v / 100, 1) == 16.7
    # If the 100 is this year's flow, the next is 103.
    assert r(F(103) / F(6, 100), 0) == 1717
    assert F(100) / (F(9, 100) - F(2, 100)) < v
    assert r(F(100) / F(7, 100), 0) == 1429
    assert r((1 - F(100) / F(7, 100) / v) * 100, 0) == 14


def test_q6():
    price = F(25)
    options = 10 - 10 * F(10) / price
    assert options == 6
    assert 200 / F(20) == 10
    assert 20 < price
    total = 100 + options + 2 + 10
    assert total == 118
    assert total * price == 2950
    # With the convert treated as equity it is not also debt: 200 of debt falls out of the bridge.
    assert 100 * price == 2500
    assert 2950 - 2500 == 450
    assert F(118, 100) - 1 == F(18, 100)
    # At a price of 15 the convert is out of the money, and stays debt; options: 10 - 10 * 10 / 15.
    assert r(10 - F(100, 15), 2) == 3.33


def test_q7():
    def ebit(rev):
        return rev * F(4, 5) - 60

    assert ebit(100) == 20 and ebit(110) == 28
    assert F(28, 20) - 1 == F(2, 5)
    assert F(28 - 10, 20 - 10) - 1 == F(4, 5)
    assert F(80, 20) == 4 and F(20, 10) == 2
    assert ebit(75) == 0
    assert ebit(90) - 10 == 2
    assert ebit(F(175, 2)) - 10 == 0


def test_q8():
    re_ = F(4) + F(12, 10) * 5
    assert re_ == 10
    wacc = F(8, 10) * re_ + F(2, 10) * 5 * F(3, 4)
    assert wacc == F(35, 4) and float(wacc) == 8.75
    bu = F(12, 10) / (1 + F(3, 4) * F(200, 800))
    assert r(bu) == 1.01
    bl = bu * (1 + F(3, 4) * 1)
    assert r(bl) == 1.77
    re2 = 4 + bl * 5
    assert r(re2) == 12.84
    w2 = F(1, 2) * re2 + F(1, 2) * 6 * F(3, 4)
    assert r(w2) == 8.67
    assert F(1, 2) * 10 + F(1, 2) * 6 * F(3, 4) == F(29, 4)


def test_q9():
    t, ru, rd = F(1, 4), F(10, 100), F(5, 100)
    nopat = F(100)
    vu = nopat / ru
    d = F(500)
    vl = vu + t * d
    assert vu == 1000 and vl == 1125
    e = vl - d
    assert e == 625
    fcfe = nopat - d * rd * (1 - t)
    assert fcfe == F(325, 4) and float(fcfe) == 81.25
    re_ = fcfe / e
    assert re_ == F(13, 100)
    assert re_ == ru + (ru - rd) * (1 - t) * d / e
    wacc = e / vl * re_ + d / vl * rd * (1 - t)
    assert r(wacc * 100) == 8.89
    assert wacc == ru * (1 - t * d / vl)
    assert nopat / wacc == vl
    # Holding the cost of equity at 10% is the classic slip.
    wrong = e / vl * ru + d / vl * rd * (1 - t)
    assert r(wrong * 100) == 7.22
    assert r(nopat / wrong, 0) == 1385
    assert r(rd * (1 - t) * 100) == 3.75


def test_q10():
    rate, g = F(9, 100), F(3, 100)
    flows = [F(100) * F(11, 10) ** i for i in range(5)]
    assert [r(x, 1) for x in flows] == [100.0, 110.0, 121.0, 133.1, 146.4]
    pv = [x / (1 + rate) ** (i + 1) for i, x in enumerate(flows)]
    assert [r(x, 1) for x in pv] == [91.7, 92.6, 93.4, 94.3, 95.2]
    tv = flows[-1] * (1 + g) / (rate - g)
    assert r(tv, 0) == 2513
    pvtv = tv / (1 + rate) ** 5
    assert r(pvtv, 0) == 1634
    total = sum(pv) + pvtv
    assert r(sum(pv), 0) == 467 and r(total, 0) == 2101
    assert r(pvtv / total * 100, 0) == 78
    # Mid-year convention scales the whole value by (1 + r)^(1/2).
    assert r(1.09**0.5, 3) == 1.044
    assert r(float(total) * 1.09**0.5, 0) == 2193
    # WACC and growth up by one point in the terminal value only.
    alt = sum(pv) + flows[-1] * (1 + F(4, 100)) / (rate - F(4, 100)) / (1 + rate) ** 5
    assert r(alt, 0) == 2446
    tv4 = flows[-1] * F(104, 100) / F(5, 100)
    assert r(tv4, 0) == 3045 and r(tv4 / tv - 1, 2) == 0.21
    assert r(1.09**5, 3) == 1.539


def test_q11():
    tv, fcf, rate = F(1000), F(55), F(9, 100)
    g = (tv * rate - fcf) / (tv + fcf)
    assert r(g * 100) == 3.32
    assert fcf * (1 + g) / (rate - g) == tv
    assert F(1000, 100) == 10
    # What multiple does 2% imply?
    implied = fcf * F(102, 100) / F(7, 100)
    assert r(implied, 0) == 801 and r(implied / 100, 1) == 8.0
    # A 6% implied growth rate if the exit multiple were 18.
    g2 = (F(1800) * rate - fcf) / (F(1800) + fcf)
    assert r(g2 * 100, 1) == 5.8


def test_q12():
    def value(g, roic, nopat=F(100), w=F(10, 100)):
        return nopat * (1 - g / roic) / (w - g)

    g = F(5, 100)
    assert value(g, F(5, 100)) == 0
    assert value(g, F(10, 100)) == 1000
    assert value(g, F(20, 100)) == 1500
    assert F(100) / F(10, 100) == 1000
    # The check by flows, for roic 20%: reinvest a quarter, FCF 75, growing at 5%.
    assert F(100) * (1 - g / F(20, 100)) == 75
    assert 75 / (F(10, 100) - g) == 1500
    assert 100 * F(5, 100) / F(20, 100) == 25
    assert 100 * F(1, 4) * F(20, 100) == 5
    # The price-earnings form with ROE 15, cost of equity 10, growth 5.
    assert r((1 - F(5, 15)) / F(5, 100), 1) == 13.3


def test_q13():
    t = F(3, 4)
    ni_a = 100 * t
    assert ni_a == 75 and F(1200) / ni_a == 16
    assert F(1200, 120) == 10
    ni_b = (100 - 30) * t
    assert ni_b == F(105, 2) and r(F(600) / ni_b) == 11.43
    assert r(ni_a / 1200 * 100) == 6.25
    assert 5 * t == F(15, 4) and float(5 * t) == 3.75
    # At 12% the after-tax rate exceeds the earnings yield.
    ni_c = (100 - 72) * t
    assert ni_c == 21 and r(F(600) / ni_c, 1) == 28.6
    assert 12 * t == 9


def test_q14():
    # Year 1, no tax, revenue less other costs is 200.
    a = {"ebitda": 100, "ebit": 100, "cfo": 100, "cfi": 0}
    b = {"ebitda": 200, "ebit": 180, "cfo": 200, "cfi": -100}
    assert a["cfo"] + a["cfi"] == b["cfo"] + b["cfi"] == 100
    assert F(100, 5) == 20
    assert b["ebit"] - a["ebit"] == 80
    assert 200 - 20 == 180
    # Steady state: 100 a year for five years or more means 100 of amortisation.
    assert 5 * 20 == 100
    # With spending growing 20% a year, the gap in the sixth year.
    spend = [100 * 1.2**i for i in range(6)]
    am = sum(spend[1:6]) / 5
    assert r(spend[5]) == 248.83 and r(am, 1) == 178.6
    assert r(spend[5] - am, 0) == 70


def test_q15():
    rev, cogs = F(1000), F(600)
    ar, inv, ap = rev * 45 / 365, cogs * 60 / 365, cogs * 30 / 365
    assert (r(ar, 1), r(inv, 1), r(ap, 1)) == (123.3, 98.6, 49.3)
    nwc = ar + inv - ap
    assert r(nwc, 1) == 172.6
    assert 45 + 60 - 30 == 75
    assert r(nwc * F(20, 100), 1) == 34.5
    assert r(nwc / 1000 * 100, 0) == 17
    assert r(cogs * 15 / 365, 1) == 24.7


def test_q16():
    fcf, sbc, cap = F(150), F(50), F(3000)
    assert fcf / cap == F(5, 100)
    assert r((fcf - sbc) / cap * 100) == 3.33
    assert r(sbc / cap * 100) == 1.67
    assert F(30) * 100 == cap
    assert r(sbc / 30) == 1.67
    assert 20 * fcf == 3000 and 20 * (fcf - sbc) == 2000
    assert F(3000, 2000) - 1 == F(1, 2)


def test_q17():
    base = F(1)
    stock = F(120, 115)
    assert r(stock, 4) == 1.0435 and r((stock - 1) * 100, 1) == 4.3
    assert 300 / F(20) == 15
    assert 300 * F(6, 100) == 18 and 18 * F(3, 4) == F(27, 2)
    debt = (F(120) - F(27, 2)) / 100
    assert debt == F(1065, 1000) and r((debt - base) * 100, 1) == 6.5
    assert F(300, 20) == 15 and r(F(20, 300) * 100) == 6.67
    assert 6 * F(3, 4) == F(9, 2)
    high = F(120) / (100 + F(450, 20))
    assert r(high, 3) == 0.98 and F(450, 20) == F(45, 2)


def test_q18():
    ebitda = 100 * 1.05**5
    assert round(ebitda, 1) == 127.6
    ev = 10 * ebitda
    assert round(ev) == 1276
    eq = ev - 300
    assert round(eq) == 976
    moic = eq / 400
    assert round(moic, 2) == 2.44
    irr = moic ** (1 / 5) - 1
    assert round(irr * 100, 1) == 19.5
    assert round(ev - 1000) == 276 and round(eq - 400) == 576
    assert round((ev / 1000 - 1) * 100) == 28 and round((eq / 400 - 1) * 100) == 144
    assert round(1.15**5, 2) == 2.01
    # Exit at 9 times.
    eq9 = 9 * ebitda - 300
    assert round(eq9) == 849 and round(eq9 / 400, 2) == 2.12
    assert round(((eq9 / 400) ** 0.2 - 1) * 100, 1) == 16.2
    # Rule of 72: doubling in five years is 14 to 15%; 2.44 is a bit over 1.3 doublings, so about 19.
    assert round(72 / 5, 1) == 14.4


def test_q19():
    r6 = F(6, 100)
    pv = sum(F(100) / (1 + r6) ** i for i in range(1, 6))
    assert r(pv) == 421.24
    interest = pv * r6
    dep = pv / 5
    assert r(interest) == 25.27 and r(dep) == 84.25
    assert r(interest + dep) == 109.52
    assert r(interest + dep - 100) == 9.52
    assert r(100 - dep) == 15.75
    close = pv + interest - 100
    assert r(close) == 346.51
    assert r(100 - interest) == 74.73
    # Multiples.
    assert r(F(1000, 150)) == 6.67
    assert r((1000 + pv) / 250) == 5.68
    assert r(F(1000 + 0 + 421, 250)) == 5.68
    # Five-year total: same 500 under both.
    bal, totals = pv, []
    for _ in range(5):
        i = bal * r6
        totals.append(i + dep)
        bal = bal + i - 100
    assert bal == 0
    assert sum(totals) == 500
    assert r(totals[-1]) == 89.91
    assert totals == sorted(totals, reverse=True)


def test_q20():
    book, tax_dep, pre, t = 20, [50, 50, 0, 0, 0], 60, F(1, 4)
    dtl = F(0)
    rows = []
    for year in range(5):
        pretax = pre - book
        expense = pretax * t
        cash_tax = (pre - tax_dep[year]) * t
        dtl += expense - cash_tax
        ni = pretax - expense
        rows.append((ni, cash_tax, dtl, ni + book + (expense - cash_tax)))
    assert [float(x[0]) for x in rows] == [30.0] * 5
    assert [float(x[1]) for x in rows] == [2.5, 2.5, 15.0, 15.0, 15.0]
    assert [float(x[2]) for x in rows] == [7.5, 15.0, 10.0, 5.0, 0.0]
    assert [float(x[3]) for x in rows] == [57.5, 57.5, 45.0, 45.0, 45.0]
    assert sum(x[1] for x in rows) == 50 == 5 * 40 * t
    # The value of the deferral at 8%.
    d = sum(float(x[1]) / 1.08 ** (i + 1) for i, x in enumerate(rows))
    e = sum(10 / 1.08 ** (i + 1) for i in range(5))
    assert round(e - d, 1) == 2.3


def test_q21():
    t = F(1, 4)
    goodwill = 500 - (200 + 100 - 100 * t)
    assert goodwill == 225
    assert 100 * t == 25
    extra = F(100, 10)
    assert extra == 10 and extra * (1 - t) == F(15, 2)
    # Balance check of the acquirer: assets +200 of old book net + 100 + 225 - 500 cash = 25 of DTL.
    assert 200 + 100 + 225 - 500 == 25
    assert 500 - 200 == 300


def test_q22():
    g = (F(3000) * F(8, 100) - 60) / (3000 + 60)
    assert g == F(1, 17) and r(g * 100) == 5.88
    assert 60 * (1 + g) / (F(8, 100) - g) == 3000

    def value(x):
        total, f = 0.0, 60.0
        for i in range(1, 11):
            f *= 1 + x
            total += f / 1.08**i
        return total + f * 1.03 / 0.05 / 1.08**10

    x = brentq(lambda y: value(y) - 3000, 0, 0.3)
    assert round(x * 100, 1) == 14.3
    assert abs(value(x) - 3000) < 1e-6
    assert round(value(0.03)) == 1236
    assert round((3000 - 1236) / 3000 * 100) == 59
    # Terminal share at the solution, and how far the flow has to grow.
    f = 60 * (1 + x) ** 10
    assert round(f) == 228
    assert round(f * 1.03 / 0.05 / 1.08**10 / 3000 * 100) == 72
    assert round((1 + x) ** 10, 1) == 3.8


def test_q23():
    margin, flow, central = F(15, 100), F(30, 100), 12
    base_rev = 100 * F(2)
    base_store = base_rev * margin
    assert base_store == 30 and base_store - central == 18

    # The rule as a cost model of the existing stores: a variable cost of 70% of revenue, and a fixed cost set by the base year.
    fixed = base_rev * flow - base_store
    assert fixed == 30

    def operating_profit(same_store, new_stores):
        existing = base_rev * (1 + same_store)
        store = base_store + (existing - base_rev) * flow  # the stated flow-through
        by_costs = existing - existing * (1 - flow) - fixed  # second route: costs line by line
        assert store == by_costs
        new_rev = new_stores * (F(2) * F(7, 10)) * F(1, 2)
        return existing + new_rev, store + new_rev * F(5, 100) - central

    # Limit case: nothing changes, so the model must return last year's profit exactly.
    assert operating_profit(F(0), 0) == (200, 18)

    revenue, ebit = operating_profit(F(3, 100), 10)
    assert revenue == 213
    assert ebit == F(2015, 100)
    assert 30 + F(18, 10) + F(35, 100) == F(3215, 100)
    assert r(ebit / 18 - 1, 3) == 0.119
    # One point of same-store sales, by the model, not by the formula.
    point = operating_profit(F(4, 100), 10)[1] - ebit
    assert point == F(6, 10)
    assert r(point / ebit * 100, 1) == 3.0
    # Flat same-store sales: more than last year, by exactly what the new stores earn.
    flat = operating_profit(F(0), 10)[1]
    assert flat == F(1835, 100) and flat > 18
    assert r(flat / 18 - 1, 3) == 0.019
    # The split of the growth, and the wrong answer.
    assert r(F(18, 10) / (ebit - 18) * 100, 0) == 84
    assert 200 * F(3, 100) * margin == F(9, 10)
    assert 30 + F(9, 10) + F(35, 100) - 12 == F(1925, 100)


def test_q24():
    rev = (F(1000), F(1200))
    cogs = (F(600), F(720))
    ar = (F(120), F(210))
    inv = (F(100), F(170))
    dso = [ar[i] / rev[i] * 365 for i in (0, 1)]
    dio = [inv[i] / cogs[i] * 365 for i in (0, 1)]
    assert [r(x, 1) for x in dso] == [43.8, 63.9]
    assert [r(x, 1) for x in dio] == [60.8, 86.2]
    assert 100 - 110 == -10 and 130 - 60 == 70
    assert r(F(70) / F((1000 + 1250), 2) * 100, 1) == 6.2
    # Free cash flow: operating cash flow less capex and capitalised development.
    assert 110 - 40 - 20 == 50 and 60 - 40 - 70 == -50
    excess = ar[1] - rev[1] * ar[0] / rev[0]
    assert excess == 66
    assert r(excess / 1200 * 100, 1) == 5.5
    assert 60 - 80 == -20 and 1200 + (60 - 80) == 1180
    assert r(F(70, 1200) * 100, 1) == 5.8 and F(20, 1000) == F(2, 100)
    assert rev[1] * ar[0] / rev[0] == 144
    capit = F(70) - F(2, 100) * 1200
    assert capit == 46
    assert capit * F(3, 4) == F(69, 2)
    adj = 130 - capit * F(3, 4)
    assert float(adj) == 95.5
    inv_excess = inv[1] - cogs[1] * inv[0] / cogs[0]
    assert inv_excess == 50
    assert r((F(130) - 100) / 100 * 100, 0) == 30


def test_q25():
    bull, bear, p0 = 150, 60, 90
    q = F(p0 - bear, bull - bear)
    assert q == F(1, 3)
    ev = F(1, 2) * bull + F(1, 2) * bear
    assert ev == 105 and r((ev / p0 - 1) * 100, 1) == 16.7
    b2, s2, p2 = 120, 50, 63
    q2 = F(p2 - s2, b2 - s2)
    assert r(q2 * 100, 1) == 18.6
    need = (F(63) * F(115, 100) - s2) / (b2 - s2)
    assert r(need * 100) == 32.07
    ev2 = F(35, 100) * b2 + F(65, 100) * s2
    assert ev2 == F(149, 2) and float(ev2) == 74.5
    assert r((ev2 / p2 - 1) * 100, 1) == 18.3
    down1, down2 = F(p0 - bear, p0), F(p2 - s2, p2)
    assert r(down1 * 100, 1) == 33.3 and r(down2 * 100, 1) == 20.6
    assert r(F(1, 100) / down1 * 100, 1) == 3.0 and r(F(1, 100) / down2 * 100, 1) == 4.8
    assert r((F(b2) / p2 - 1) * 100, 1) == 90.5
    # Loss from 90 to 63 on the 3% position.
    assert F(3, 100) * F(27, 90) == F(9, 1000)
    rng = np.random.default_rng(25)
    x = np.where(rng.random(1_000_000) < 0.35, 120.0, 50.0)
    assert abs(x.mean() - 74.5) < 0.1
