"""Numbers gate: every number printed in Book 14, chapter 15 (text and solutions)."""
import pathlib
import sys

import pytest
from scipy.optimize import brentq

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_buy as b  # noqa: E402

sm = b.sm


def test_prices_and_text():
    assert (9000 / 10, 44000 / 200, 11000 / 10) == (900, 220, 1100)
    assert 0.05 * 30 * 1440 == 2160 and 0.05 * 30 * 24 == 36
    assert 12 * 44000 > 500_000 and 2 * 12 * 15000 == 360_000
    assert sm.uptime_pct(240, 30) == pytest.approx(99.444, abs=1e-3)
    rows = b.price_rows()
    assert len(rows) == 8 and rows[0][1] == 2500


@pytest.mark.reference
def test_designs_table():
    r = b.results(1000)
    one, duct, div = r["one circuit"], r["two circuits in one duct"], r["two diverse circuits"]
    assert (round(100 * one["availability"], 4), round(one["expected_min"], 1), round(one["sim_p95_min"])) == (99.9088, 479.6, 1541)
    assert (round(100 * duct["availability"], 4), round(duct["expected_min"], 1), round(duct["sim_p95_min"])) == (99.9315, 360.4, 1992)
    assert (round(100 * div["availability"], 5), round(div["expected_min"], 1), round(div["sim_p95_min"])) == (99.99992, 0.4, 0)
    assert (one["annual_cost"], duct["annual_cost"], round(div["annual_cost"] / 1000, 1)) == (139_200, 278_400, 320.2)
    assert (round(one["loss"] / 1000), round(duct["loss"] / 1000), round(div["loss"] / 1000, 1)) == (959, 721, 0.9)
    assert round(div["annual_cost"] - duct["annual_cost"]) == 41_760 and round((one["loss"] - duct["loss"]) / 1000) == 238
    assert round((duct["loss"] - div["loss"]) / 1000) == 720 and round(1992 / 60) == 33
    assert round(100 * (1 - one["availability"]), 3) == 0.091 and round(div["expected_min"], 2) == 0.44


@pytest.mark.reference
def test_credits():
    d = b.designs()
    assert b.monthly_credits(d[0], "single connection") == pytest.approx(5.5)
    assert round(b.monthly_credits(d[1], "multi-site non-redundant"), -1) == 2560
    assert b.monthly_credits(d[2], "multi-site redundant") == 0
    assert round(100 * 2560 / 720_874, 1) == 0.4


def test_exercises():
    c = b._circuit()
    u = 1 - sm.availability(c.mtbf_h, c.mttr_h)
    assert (round(u, 5), f"{u * u:.1e}", round(6 / sm.HOURS_Y, 5)) == (0.00091, "8.3e-07", 0.00068)
    single = sm.Design("s", (c,))
    rate = brentq(lambda x: sm.design_availability(sm.Design("u", (c, c), x, 12.0)) - sm.design_availability(single), 0.01, 5)
    assert (round(rate, 2), round(rate * 12 / sm.HOURS_Y, 6)) == (0.67, 0.000911)
    assert round(0.0001 * 30 * 1440, 1) == 4.3


def test_small_runs():
    y = sm.simulate_year(b.designs()[1], seed=1)
    assert y["down_min"] >= 0 and len(sm.monthly_down_min(y["intervals"])) == 12
