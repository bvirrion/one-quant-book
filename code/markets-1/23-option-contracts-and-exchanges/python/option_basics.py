"""Payoffs, the size of a chain, and what a book turns into at expiry (Chapter 23). Illustrative."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/chain"))
from firm_chain import Series, expiry_shares

EXP = dt.date(2026, 12, 18)


def count_series(weekly: int, monthly: int, quarterly_leaps: int, strikes_near: int, strikes_far: int) -> int:
    """Series listed on one underlying: near expiries carry more strikes than far ones; calls and puts."""
    return 2 * ((weekly + monthly) * strikes_near + quarterly_leaps * strikes_far)


def example_book() -> dict[Series, int]:
    """A small market-making book in one expiry: contracts held (+) or written (-)."""
    return {
        Series("XYZ", EXP, "P", 47_500): -40,
        Series("XYZ", EXP, "P", 50_000): -10,
        Series("XYZ", EXP, "C", 50_000): 25,
        Series("XYZ", EXP, "C", 52_500): -60,
    }


def shares_by_close(book: dict[Series, int], closes: list[float]) -> list[int]:
    return [expiry_shares(book, c) for c in closes]
