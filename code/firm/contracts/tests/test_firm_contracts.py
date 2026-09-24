"""Acceptance tests of the Chapter 18 build."""
import datetime as dt
import pathlib
import sys
from fractions import Fraction

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_contracts import ContractMaster, ContractSpec, parse_thirty_seconds, third_friday

CSV = pathlib.Path(__file__).resolve().parents[4] / "data/markets-1/contracts_sample.csv"
TODAY = dt.date(2026, 9, 18)


def master():
    return ContractMaster.from_csv(str(CSV))


def test_tick_values_are_exact():
    m = master()
    got = {r: m.spec(r).tick_value for r in ("ES", "FESX", "ZN", "FGBL", "CL", "B")}
    assert got == {"ES": Fraction(25, 2), "FESX": 10, "ZN": Fraction(125, 8), "FGBL": 10, "CL": 10, "B": 10}


def test_prices_round_trip_through_integer_ticks():
    es = master().spec("ES")
    assert es.to_ticks("6000.25") == 24001 and es.from_ticks(24001) == Fraction("6000.25")
    assert es.notional("6000") == 300_000
    with pytest.raises(ValueError):
        es.to_ticks("6000.10")


def test_treasury_quotes():
    zn = master().spec("ZN")
    p = parse_thirty_seconds("112-165")
    assert p == Fraction(112) + Fraction(33, 64) and zn.to_ticks(p) == 112 * 64 + 33
    assert parse_thirty_seconds("112-16") == Fraction(225, 2) and zn.notional(p) == Fraction("112515.625")
    with pytest.raises(ValueError):
        parse_thirty_seconds("112-163")


def test_symbols_and_expiries():
    m = master()
    z6 = m.parse("ESZ6", TODAY)
    assert (z6.year, z6.month, z6.symbol) == (2026, 12, "ESZ6") and m.expiry(z6) == dt.date(2026, 12, 18)
    assert m.parse("ESH6", TODAY).year == 2036                       # March 2026 is in the past
    assert third_friday(2026, 9) == dt.date(2026, 9, 18)
    with pytest.raises(ValueError):
        m.parse("ESF7", TODAY)                                       # no January E-mini
    with pytest.raises(NotImplementedError):
        m.expiry(m.parse("CLX6", TODAY))


def test_validation():
    bad = ContractSpec("X", "x", "X", "USD", Fraction(0), Fraction(1), "decimal", "H", "cash", "third_friday")
    with pytest.raises(ValueError):
        ContractMaster([bad])
