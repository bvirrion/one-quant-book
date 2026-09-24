"""Numbers gate: every numerical answer printed in the Chapter 4 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from venue_econ import (
    ACCESS,
    CME_2025,
    CME_RATE_PER_CONTRACT,
    CME_TOTAL_2025,
    ICE_EXCHANGES_2025,
    AccessModel,
    breakeven_share,
    cheapest,
    crossover,
    monthly_cost,
    shares,
    venue_profit,
)


def test_text():
    s = shares(ICE_EXCHANGES_2025)
    assert ICE_EXCHANGES_2025["Data and connectivity services"] > ICE_EXCHANGES_2025[
        "Cash equities and equity options"]                                    # the hook
    assert round((1031 + 495) / 5411 * 100) == 28
    assert round(s["Cash equities and equity options"] * 100, 1) == 8.6 and round(s["Energy"] * 100) == 40
    assert round(CME_2025["Clearing and transaction fees"] / CME_TOTAL_2025 * 100) == 81
    assert round(CME_2025["Market data and information services"] / CME_TOTAL_2025 * 100) == 12
    sides = CME_2025["Clearing and transaction fees"] * 1e6 / CME_RATE_PER_CONTRACT
    assert round(sides / 1e9, 1) == 7.6 and round(sides / 252 / 1e6) == 30
    xs = [crossover(a, b) for a, b in zip(ACCESS[:-1], ACCESS[1:], strict=True)]
    assert [round(x / 1e6, 1) for x in xs] == [2.5, 33.3, 312.5]
    assert round(breakeven_share(10e9, 0.0003, 50e6, 40e6) * 100, 1) == 5.0
    assert round(venue_profit(0.10, 10e9, 0.0003, 50e6, 40e6) / 1e6, 1) == 40.6
    assert round(venue_profit(0.02, 10e9, 0.0003, 50e6, 40e6) / 1e6, 1) == -23.9
    assert [cheapest(v * 1e6).name for v in (1, 10, 100, 1000)] == [
        "broker algorithm", "direct market access", "sponsored access", "own membership"]


def test_exercises():
    s = shares(ICE_EXCHANGES_2025)                                                       # 1
    assert [round(s[k] * 100, 1) for k in ("Energy", "Cash equities and equity options",
            "Data and connectivity services", "Listings")] == [40.3, 8.6, 19.1, 9.1]
    assert 2 * 0.70 / 280_000 * 1e4 == pytest.approx(0.05)                               # 2
    assert [monthly_cost(m, 60e6) for m in ACCESS] == [180_000, 65_000, 49_000, 150_000]  # 4
    sp = AccessModel("s", 0.0006, 25_000.0)                                              # 5
    assert round(crossover(ACCESS[1], sp) / 1e6) == 50 and round(crossover(sp, ACCESS[3]) / 1e6) == 208
    assert round(breakeven_share(10e9, 0.0002, 50e6, 40e6) * 100, 1) == 7.2              # 6
    assert round(venue_profit(0.10, 10e9, 0.0002, 50e6, 40e6) / 1e6, 1) == 15.4
    assert monthly_cost(ACCESS[2], 5e6) == 27_000 and monthly_cost(cheapest(5e6), 5e6) == 10_000  # 7


def test_problem():
    m, d, p = 8e9, 252, 45.0
    nu = 0.0028 - 0.0025
    assert nu == pytest.approx(0.0003) and round(nu / p * 1e4, 3) == 0.067
    tr = m * d * nu
    assert round(tr / 1e6, 1) == 604.8 and round((tr + 60e6) / 100 / 1e6, 2) == 6.65
    xs = 38e6 / (tr + 60e6)
    assert round(xs * 100, 2) == 5.72 and round(xs * m / 1e6) == 457 and round(xs * m * p / 1e9, 1) == 20.6
    share = 0.12 / 3 * 0.5
    assert share == pytest.approx(0.02) and round((share * (tr + 60e6) - 38e6) / 1e6, 1) == -24.7
    nu2 = 0.0028 - 0.0032
    assert round(0.04 * m * d * nu2 / 1e6, 1) == -32.3
    loss = 0.04 * m * d * nu2 + 0.04 * 60e6 - 38e6
    assert round(loss / 1e6, 1) == -67.9
    profit = 0.06 * (tr + 60e6) - 38e6
    assert round(profit / 1e6, 1) == 1.9 and round(-loss / profit) == 36
    assert round(38e6 / (m * d * 0.0002 + 60e6) * 100, 1) == 8.2
