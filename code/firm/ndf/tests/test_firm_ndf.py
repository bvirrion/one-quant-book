"""Acceptance tests of the Book 2, Chapter 18 build (NDFs, bands, leverage)."""
import datetime as dt
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_ndf import band, fixing_date, implied_local_rate, leveraged_loss, ndf_settlement, onshore_offshore_basis


def test_ndf_settlement():
    assert ndf_settlement(10e6, 1400.0, 1400.0) == 0.0
    assert math.isclose(ndf_settlement(10e6, 1400.0, 1470.0), 10e6 * 70 / 1470)
    assert ndf_settlement(10e6, 1400.0, 1330.0) < 0 and ndf_settlement(10e6, 1400.0, 1330.0, buyer=False) > 0


def test_fixing_date_skips_weekends_and_holidays():
    settle = dt.date(2026, 10, 13)                                   # Tuesday
    assert fixing_date(settle, set()) == dt.date(2026, 10, 9)          # Friday
    assert fixing_date(settle, {dt.date(2026, 10, 9)}) == dt.date(2026, 10, 8)


def test_implied_rates_and_basis():
    f = 7.10 * (1 + 0.015 * 90 / 365) / (1 + 0.04 * 90 / 360)
    assert math.isclose(implied_local_rate(7.10, f, 0.04, 90), 0.015)
    assert math.isclose(onshore_offshore_basis(7.10, f, 7.10, f, 0.04, 90), 0.0, abs_tol=1e-15)


def test_band_and_leverage():
    lo, hi = band(7.10, 0.02)
    assert math.isclose(lo, 6.958) and math.isclose(hi, 7.242)
    assert math.isclose(leveraged_loss(0.144, 20), 2.88)
