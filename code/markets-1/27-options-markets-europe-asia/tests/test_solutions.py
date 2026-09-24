"""Numbers gate: every numerical answer printed in the Chapter 27 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from counting import MARKETS, derive_2024, three_rankings

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/turnover"))
from firm_turnover import activity_kept, contracts_after_lot_change


def test_text():
    r = three_rankings()
    m1, m2 = MARKETS[0].name, MARKETS[1].name
    assert [round(r[k][m1] * 100) for k in ("contracts", "notional_usd", "premium_usd")] == [98, 48, 38]
    assert r["contracts"][m2] < 0.01 and round(r["premium_usd"][m2] * 100) == 55
    prev = derive_2024()
    total = sum(prev.values())
    assert round(prev["Asia-Pacific"]) == 170 and round(prev["Asia-Pacific"] / total * 100) == 82 and round(75.59 / 119.29 * 100) == 63
    assert all(prev[k] < v for k, v in (("North America", 24.5), ("Latin America", 11.39), ("Europe", 4.38), ("Other", 3.43)))
    assert 4843.57e7 == pytest.approx(48.4e9, rel=0.002) and 1.8e5 * 1e7 == 1.8e12


def test_exercises():
    assert 25 * 22_000 * 0.012 == pytest.approx(6_600) and 25 * 35 * 0.012 == pytest.approx(10.5)
    assert 100 * 5_600 == 560_000 and 100 * 16 == 1_600 and round(1_600 / 10.5) == 152
    assert contracts_after_lot_change(90e9, 25, 75) == pytest.approx(30e9) and activity_kept(90e9, 24e9, 25, 75) == pytest.approx(0.8)
    total = sum(derive_2024().values())
    assert round(total, 1) == 206.4 and round((1 - 119.29 / total) * 100, 1) == 42.2
    assert 945 * 0.04 * 0.25 == pytest.approx(9.45) and 1360 * 0.015 * 0.25 == pytest.approx(5.1)


def test_problem():
    m1, m2 = MARKETS[0], MARKETS[1]
    assert round(90e9 / 0.85e9) == 106
    assert (round(m1.notional_usd / 1e12), round(m2.notional_usd / 1e12)) == (594, 476)          # trillions
    assert (round(m1.premium_usd / 1e9), round(m2.premium_usd / 1e9)) == (945, 1360)
    assert round(m2.premium_usd / m1.premium_usd, 2) == 1.44
    assert (round(m1.premium_to_notional_bp, 1), round(m2.premium_to_notional_bp, 1)) == (15.9, 28.6)
    g1, g2 = m1.premium_usd * 0.01, m2.premium_usd * 0.00375
    c1 = m1.premium_usd * 0.0005 + m1.premium_usd * 0.5 * 0.001
    c2 = 0.85e9 * 0.50
    assert [round(x / 1e9, 2) for x in (g1, g2, c1, c2, g1 - c1, g2 - c2)] == [9.45, 5.10, 0.94, 0.42, 8.51, 4.67]
    p_new = 24e9 * 75 * 35 * 0.012
    assert round(p_new / 1e9) == 756 and round((p_new * 0.01 - p_new * 0.001) / 1e9, 1) == 6.8
