"""Numbers gate: every numerical answer printed in Book 3, Chapter 8 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from m3_metals import NICKEL, calendar, nickel_moves, short_squeeze

P = {k: v for k, _, v in NICKEL}
M = nickel_moves()
S = short_squeeze()


def test_text():
    assert round(M["fri"] * 100, 1) == 6.8 and round(M["mon"] * 100) == 66
    assert (S["monday"], S["tuesday_peak"], S["total"]) == (-191_590_000, -532_870_000, -724_460_000)
    assert round(10_000 * P["4 Mar close"] / 1e6) == 289
    c = calendar()
    assert (c["daily"], c["weekly"], c["monthly"]) == (65, 14, 21)


def test_exercises():
    s = short_squeeze(2_000)
    assert round(-s["monday"] / 1e6, 2) == 38.32 and round(-s["tuesday_peak"] / 1e6, 2) == 106.57
    assert round(M["mon"] * 100, 1) == 66.3 and round(M["tue"] * 100, 1) == 110.8
    assert round(P["8 Mar 06:08, peak"] / P["4 Mar open"], 2) == 3.74 and round(M["total"] * 100) == 274


def test_problem():
    assert round(10_000 * P["4 Mar close"] / 1e6, 2) == 289.19
    fri = 10_000 * (P["4 Mar close"] - P["4 Mar open"])
    assert round(fri / 1e6, 2) == 18.39
    assert round((fri - S["total"]) / 1e6, 2) == 742.85


def test_carry_example():
    assert round(80 / 9800 * 100, 2) == 0.82 and round(80 / 9800 * 365 / 91 * 100, 1) == 3.3
