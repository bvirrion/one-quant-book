"""Numbers gate: every numerical answer printed in Book 2, Chapter 6 (text and solutions)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/ctd"))
from firm_ctd import (
    carry_to_delivery,
    conversion_factor,
    gross_basis,
    implied_repo,
    invoice_price,
    net_basis,
    whole_months,
)
from futures_demo import (
    DAYS,
    DELIVERY,
    FIRST_DAY,
    REPO,
    bonds,
    deliverables,
    delivery_value_per_cf,
    fair_futures,
    switch_option_value,
)

F = fair_futures()
CTD = deliverables()[0]
SD = 0.0080 * math.sqrt(DAYS / 365)


def test_text():
    assert DAYS == 97 and F == 111 + 24.5 / 32
    assert conversion_factor(0.0375, dt.date(2008, 12, 1), dt.date(2018, 11, 15)) == 0.8357
    assert round(net_basis(CTD, F, REPO, DAYS) * 32, 2) == 0.65               # two thirds of a 32nd
    assert round((REPO - implied_repo(CTD, F, DAYS)) * 1e4) == 8
    low = min(v for _, v in delivery_value_per_cf(0.0))
    assert round(low, 3) == 111.793


def test_exercises():
    inv = invoice_price(F, CTD.cf, CTD.accrued_delivery)
    assert CTD.accrued_delivery == 1.453125 and round(inv, 6) == 100.589234 and round(inv * 1000, 2) == 100_589.23
    g = gross_basis(CTD, F)
    assert round(g, 3) == -0.004 and round(g * 32, 2) == -0.14
    assert whole_months(FIRST_DAY, dt.date(2033, 11, 15)) == 6 * 12 + 11
    assert conversion_factor(0.04, FIRST_DAY, dt.date(2033, 11, 15)) == 0.8902
    assert conversion_factor(0.06, FIRST_DAY, dt.date(2033, 11, 15)) == 0.9999
    cost = (CTD.clean + CTD.accrued_now) * 1e6
    irr = implied_repo(CTD, F, DAYS)
    assert round(cost) == 99_563_440 and round(irr * 100, 4) == 3.8238 and round((REPO - irr) * 1e4, 2) == 7.62
    assert round(cost * (REPO - irr) * DAYS / 360) == 20_451
    assert round(1000 * CTD.cf) == 887
    assert round(SD * 1e4) == 41 and round(3 * SD * 1e4) == 124
    assert round(switch_option_value(SD) * 64, 3) == 0.001 and round(switch_option_value(3 * SD) * 64, 2) == 3.07
    assert round(111.77 * 0.887, 2) == 99.14 and round(CTD.clean, 2) == 99.13


def test_problem():
    for n, b, _, _ in bonds():
        m = whole_months(FIRST_DAY, b.maturity)
        assert 78 <= m < 96, n
    assert [whole_months(FIRST_DAY, b.maturity) for _, b, _, _ in bonds()] == [80, 83, 86, 89, 92]
    c = carry_to_delivery(CTD, REPO, DAYS)
    assert round(c, 3) == -0.025 and round(net_basis(CTD, F, REPO, DAYS), 3) == 0.020
    assert round(CTD.accrued_delivery - CTD.accrued_now, 3) == 1.021
    assert round((CTD.clean + CTD.accrued_now) * REPO * DAYS / 360, 3) == 1.046
    vals = dict(delivery_value_per_cf(0.0))
    low = min(vals.values())
    assert [round(v - low, 3) for v in vals.values()] == [0.0, 0.270, 0.527, 0.742, 1.171]
    y = {n: yy for n, _, yy, _ in bonds()}
    assert round((y["3 7/8 Aug-33"] + 0.0147) * 100, 2) == 5.49 and round((y["4 Aug-34"] + 0.0147) * 100, 2) == 5.55
    dv = {}
    for n, b, yy, cf in bonds():
        r = b.risk(yy + 0.0147, DELIVERY)
        dv[n] = r["dirty"] * r["modified"] / cf
    assert (round(dv["3 7/8 Aug-33"]), round(dv["4 Aug-34"]), round((dv["4 Aug-34"] / dv["3 7/8 Aug-33"] - 1) * 100)) == (
        586, 658, 12)
    assert round(147 / (SD * 1e4), 1) == 3.6
