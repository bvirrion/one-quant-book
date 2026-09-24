"""Numbers gate: every numerical answer printed in the Chapter 28 text and solutions."""
import collections
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from feed_demo import SAMPLE, TRADES, clean, inversions, receive_times, replay, vwap

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/feed"))
from firm_feed import LENGTHS, Book, Msg, decode

T0 = 34_200_000_000_000


def test_text():
    data = SAMPLE.read_bytes()
    counts = collections.Counter(m.kind for m in decode(data))
    assert counts == {"A": 1102, "E": 311, "X": 114, "D": 473, "P": 20} and sum(counts.values()) == 2020
    assert len(data) == 65_842 == sum(n * (2 + LENGTHS[k.encode()]) for k, n in counts.items())
    ex = np.array([x[0] for x in replay()[1]], dtype=float)
    pct = [inversions(ex, receive_times(ex, 200_000.0, j * 1000.0, 28)) / (len(ex) - 1) * 100 for j in (100, 1000, 5000)]
    assert [round(p) for p in pct] == [1, 11, 32]
    kept, dropped = clean(TRADES)
    assert sorted(r[0] for r in dropped) == [6, 9] and round(vwap(TRADES), 2) == 98.40


def test_exercises():
    b = Book()
    for ref, side, shares, price in ((1001, "B", 300, 999_900), (1002, "B", 200, 999_900), (1004, "B", 100, 999_800),
                                     (1003, "S", 500, 1_000_100), (1005, "S", 100, 1_000_200)):
        b.apply(Msg("A", 7, 0, T0, ref, side, shares, "XYZ", price))
    assert b.depth(7, "B", 2) == [(999_900, 500), (999_800, 100)] and b.best(7) == (999_900, 500, 1_000_100, 500)
    b.apply(Msg("E", 7, 0, T0 + 1, 1001, shares=300, match=1))
    b.apply(Msg("X", 7, 0, T0 + 2, 1002, shares=100))
    assert b.depth(7, "B", 2) == [(999_900, 100), (999_800, 100)]
    assert (b.trades[0].price, b.trades[0].aggressor) == (999_900, "S")
    assert int.from_bytes(bytes.fromhex("000F41DC"), "big") == 999_900
    assert int.from_bytes(bytes.fromhex("000F41DC"), "little") == 3_695_251_200
    assert round(2**48 / 1e9 / 3600, 1) == 78.2 and round(2**32 / 1e9, 1) == 4.3 and 86_400e9 < 2**48


def test_problem():
    assert sum(r[3] for r in TRADES) == 22_650 and min(r[2] for r in TRADES) == 10.01
    assert round((vwap(TRADES) / 100.05 - 1) * 1e4) == -165
    good = [r for r in TRADES if r[0] not in (6, 9, 11)]
    assert len(TRADES) - len(good) == 3 and sum(r[3] for r in good) == 16_950 and round(vwap(good), 3) == 100.045
    cont = [r for r in good if r[4] != "open"]
    assert sum(r[3] for r in cont) == 4_950 and round(vwap(cont), 3) == 100.106
    assert (min(r[2] for r in good), max(r[2] for r in good)) == (100.02, 100.15)
    assert round((100.09 / vwap(good) - 1) * 1e4, 1) == 4.5 and round((100.09 / vwap(cont) - 1) * 1e4, 1) == -1.6
    assert pytest.approx(vwap([r for r in TRADES if r[0] not in (6, 9)]), abs=0.001) == 99.989
