"""Acceptance tests of the Chapter 21 build."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fairvalue import ArbCosts, Dividend, arbitrage_band, fair_value, implied_rate, roll_richness_bp

TODAY, DEC, MAR = dt.date(2026, 9, 18), dt.date(2026, 12, 18), dt.date(2027, 3, 19)
DIVS = [Dividend(dt.date(2026, 10, 15), 6.0), Dividend(dt.date(2026, 11, 16), 9.5), Dividend(dt.date(2026, 12, 10), 5.5),
        Dividend(dt.date(2027, 1, 15), 6.0), Dividend(dt.date(2027, 2, 15), 9.5), Dividend(dt.date(2027, 3, 10), 5.5)]


def test_no_dividends_is_simple_interest():
    assert fair_value(6000.0, 0.042, TODAY, DEC, []) == pytest.approx(6000 * (1 + 0.042 * 91 / 360))


def test_dividends_by_hand():
    carry = 6000 * 0.042 * 91 / 360
    divs = 6.0 * (1 + 0.042 * 64 / 360) + 9.5 * (1 + 0.042 * 32 / 360) + 5.5 * (1 + 0.042 * 8 / 360)
    assert fair_value(6000.0, 0.042, TODAY, DEC, DIVS) == pytest.approx(6000 + carry - divs)
    assert fair_value(6000.0, 0.042, TODAY, DEC, DIVS) == pytest.approx(6042.62, abs=0.01)


def test_implied_rate_round_trip():
    f = fair_value(6000.0, 0.0455, TODAY, DEC, DIVS)
    assert implied_rate(f, 6000.0, TODAY, DEC, DIVS) == pytest.approx(0.0455, abs=1e-9)


def test_band_is_wider_below_when_borrow_is_dear():
    lo, hi = arbitrage_band(6000.0, 0.042, TODAY, DEC, DIVS, ArbCosts(3.0, 0.5, 40.0, 15.0))
    fv = fair_value(6000.0, 0.042, TODAY, DEC, DIVS)
    assert hi - fv == pytest.approx(2 * 3.5e-4 * 6000 + 15e-4 * 91 / 360 * 6000)
    assert fv - lo == pytest.approx(2 * 3.5e-4 * 6000 + 40e-4 * 91 / 360 * 6000) and fv - lo > hi - fv


def test_roll_richness():
    fair = fair_value(6000.0, 0.042, TODAY, MAR, DIVS) - fair_value(6000.0, 0.042, TODAY, DEC, DIVS)
    assert roll_richness_bp(fair, 6000.0, 0.042, TODAY, DEC, MAR, DIVS) == pytest.approx(0.0, abs=1e-9)
    assert roll_richness_bp(fair + 4.55, 6000.0, 0.042, TODAY, DEC, MAR, DIVS) == pytest.approx(30.0, abs=0.01)
