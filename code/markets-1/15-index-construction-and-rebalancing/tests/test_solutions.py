"""Numbers gate: every numerical answer printed in the Chapter 15 text and solutions."""
import datetime
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from index_recon import adv_multiple, passive_demand, simulate_turnover


def test_text():
    fc = 400e6 * 50 * 0.65
    assert fc == pytest.approx(13e9) and fc / 5e12 * 100 == pytest.approx(0.26)
    d = passive_demand(2e12, 5e12, fc)
    assert d == pytest.approx(5.2e9) and adv_multiple(d, 400e6) == pytest.approx(13.0)
    assert 10e12 * 0.015 == pytest.approx(150e9) and 10e12 * 0.06 * 0.015 == pytest.approx(9e9)
    assert datetime.date(2020, 12, 18).weekday() == 4 and 15 <= 18 <= 21          # third Friday
    assert datetime.date(2026, 6, 26).weekday() == 4 and datetime.date(2026, 12, 11).weekday() == 4
    none, wide = simulate_turnover(600, 200, 0, 20, 3), simulate_turnover(600, 200, 30, 20, 3)
    assert wide[0] < 0.6 * none[0]                                               # 'halves', roughly


def test_exercises():
    assert round(0.06 * (1 - 0.015) * 100, 2) == 5.91
    assert round(0.7 * 0.025 * math.sqrt(13) * 100, 1) == 6.3
    assert round(0.7 * 0.025 * math.sqrt(13 / 20) * 100, 1) == 1.4
    a, b = simulate_turnover(600, 200, 0, 20, 1), simulate_turnover(600, 200, 30, 20, 1)
    assert (a[0], round(a[1] * 100, 2)) == (18.5, 1.92) and (b[0], round(b[1] * 100, 2)) == (9.2, 1.18)
    assert round(2 * (a[1] - b[1]) * 15, 2) == 0.22                               # bp of assets a year


def test_problem():
    own_s, own_l = 200 / 3000, 4000 / 50000
    assert round(own_s * 100, 2) == 6.67 and own_l == pytest.approx(0.08)
    dem = own_s * 1.2e9
    sh = dem / 24
    assert dem == pytest.approx(80e6) and round(sh) == 3_333_333 and round(sh / 0.9e6, 1) == 3.7
    sell, buy = own_s * 9e9, own_l * 9e9
    assert (sell, buy, buy - sell) == pytest.approx((600e6, 720e6, 120e6))
    assert sell / 60 / 2.5e6 == pytest.approx(4.0) and (buy - sell) / 60 / 2.5e6 == pytest.approx(0.8)
    assert 0.6 * sh == pytest.approx(2e6) and 0.08 * 0.9e6 == pytest.approx(72_000) and round(0.6 * sh / 72_000) == 28
    assert round(0.7 * 0.03 * math.sqrt(sh / 0.9e6) * 100, 1) == 4.0
    assert round(0.7 * 0.03 * math.sqrt(sh / 20 / 0.9e6) * 100, 1) == 0.9
    p, up, dn, cost, pos, n = 0.8, 0.03, -0.02, 0.004, 5e6, 25
    e = p * up + (1 - p) * dn - cost
    sd = math.sqrt(p * (1 - p)) * (up - dn)
    assert e == pytest.approx(0.016) and e * pos == pytest.approx(80_000) and sd * pos == pytest.approx(100_000)
    assert n * e * pos == pytest.approx(2e6) and math.sqrt(n) * sd * pos == pytest.approx(500_000)
    corr = sd * pos * math.sqrt(n + n * (n - 1) * 0.3)
    assert round(corr / 1e6, 2) == 1.43 and round(2e6 / corr, 1) == 1.4
    assert (cost - dn) / (up - dn) == pytest.approx(0.48)
