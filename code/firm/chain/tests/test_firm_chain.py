"""Acceptance tests of the Chapter 23 build."""
import datetime as dt
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_chain import Chain, Series, exercised_by_exception, expiry_shares, parse_osi

EXP = dt.date(2026, 12, 18)


def test_osi_round_trip():
    s = parse_osi("XYZ   261218C00052500")
    assert (s.root, s.expiry, s.right, s.strike_milli, s.strike) == ("XYZ", EXP, "C", 52_500, 52.5)
    assert s.osi == "XYZ   261218C00052500"
    assert parse_osi("SPXW  260918P06000000", style="european", settlement="cash").strike == 6000.0
    for bad in ("XYZ261218C00052500", "XYZ   261218X00052500", "XYZ   2612AAC00052500"):
        with pytest.raises(ValueError):
            parse_osi(bad)


def test_chain_lookup_and_atm():
    series = [Series("XYZ", EXP, r, k) for k in (45_000, 47_500, 50_000, 52_500, 55_000) for r in "CP"]
    ch = Chain(series)
    assert len(ch) == 10 and ch.expiries() == [EXP] and ch.strikes(EXP)[0] == 45_000
    assert ch.atm_strike(EXP, 51.30) == 52_500 and ch.atm_strike(EXP, 51.20) == 50_000
    assert ch.atm_strike(EXP, 51.25) == 50_000                  # a tie goes to the lower strike
    with pytest.raises(ValueError):
        Chain(series + [Series("XYZ", EXP, "C", 50_000)])


def test_payoffs():
    call = Series("XYZ", EXP, "C", 50_000)
    assert call.payoff(56.0, 2.40, 10) == pytest.approx(3_600) and call.payoff(48.0, 2.40, 10) == pytest.approx(-2_400)
    assert call.payoff(56.0, 2.40, -10) == pytest.approx(-3_600)


def test_exercise_by_exception_and_net_shares():
    c50, p50, c55 = Series("XYZ", EXP, "C", 50_000), Series("XYZ", EXP, "P", 50_000), Series("XYZ", EXP, "C", 55_000)
    assert exercised_by_exception(c50, 50.01) and not exercised_by_exception(c50, 50.00)
    book = {c50: 20, p50: -15, c55: -30}
    assert expiry_shares(book, 52.00) == 2_000                 # long calls exercised; short puts and 55 calls expire
    assert expiry_shares(book, 49.00) == 1_500                 # short puts assigned: the book must BUY 1,500 shares
    assert expiry_shares(book, 56.00) == 2_000 - 3_000
    assert expiry_shares(book, 50.01, overrides={c50: False}) == 0
    cash = Series("SPX", EXP, "C", 6_000_000, style="european", settlement="cash")
    assert expiry_shares({cash: 5}, 6_100.0) == 0
