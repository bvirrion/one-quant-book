"""Acceptance tests of the Book 2, Chapter 5 build (repo book)."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_repo import RepoTrade, carry, fails_charge, margin_call, special_rate_floor, value_of_specialness

D = dt.date


def test_cash_interest_and_repurchase_price():
    t = RepoTrade("repo", "T 4.25 08/36", 100e6, 101.5, 0.02, 0.039, D(2026, 9, 25), D(2026, 9, 29))
    assert t.cash == pytest.approx(99.47e6)
    assert t.interest() == pytest.approx(99.47e6 * 0.039 * 4 / 360)
    assert t.repurchase_price() == pytest.approx(t.cash + t.interest())


def test_margin_call_sign():
    t = RepoTrade("repo", "X", 100e6, 100.0, 0.02, 0.04, D(2026, 9, 25), D(2026, 10, 25))
    assert margin_call(t, 100.0, D(2026, 9, 25)) == pytest.approx(0.0, abs=1e-6)
    assert margin_call(t, 98.5, D(2026, 9, 25)) == pytest.approx(1.5e6)      # price fell: post more
    assert margin_call(t, 101.0, D(2026, 9, 25)) < 0                          # price rose: may withdraw


def test_tmpg_example():
    assert fails_charge(100e6, 1.0) == pytest.approx(5555.56, abs=0.01)
    assert fails_charge(100e6, 1.0, days=5) == pytest.approx(27777.78, abs=0.01)
    assert fails_charge(100e6, 3.75) == 0.0


def test_special_floor():
    assert special_rate_floor(0.0025) == pytest.approx(-0.0275)
    assert special_rate_floor(0.0375) == 0.0


def test_specialness_value_and_carry():
    assert value_of_specialness(100.0, [(30, 0.004), (60, 0.002)]) == pytest.approx(100 * (30 * 0.004 + 60 * 0.002) / 360)
    assert carry(100e6, 4.25, 100.0, 0.0425 * 360 / 364, 182) == pytest.approx(0.0, abs=1e3)
