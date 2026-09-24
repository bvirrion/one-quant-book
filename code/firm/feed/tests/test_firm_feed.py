"""Acceptance tests of the Chapter 28 build (Python side)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_feed import Book, Msg, decode, encode, summary
from make_sample import build

ROOT = pathlib.Path(__file__).resolve().parents[1]
T0 = 34_200_000_000_000


def test_lengths_and_round_trip():
    msgs = [Msg("A", 7, 0, T0, 1, "B", 300, "XYZ", 999_900), Msg("E", 7, 0, T0 + 5, 1, shares=100, match=9),
            Msg("X", 7, 0, T0 + 6, 1, shares=100), Msg("D", 7, 0, T0 + 7, 1),
            Msg("P", 7, 0, T0 + 8, 0, "B", 100, "XYZ", 1_000_000, 10)]
    buf = b"".join(encode(m) for m in msgs)
    assert len(buf) == sum(2 + n for n in (36, 31, 23, 19, 44)) and list(decode(buf)) == msgs
    assert buf[2:3] == b"A" and buf[2 + 32:2 + 36] == (999_900).to_bytes(4, "big")


def test_decoder_refuses_garbage():
    good = encode(Msg("D", 7, 0, T0, 1))
    with pytest.raises(ValueError):
        list(decode(good[:-1]))
    with pytest.raises(ValueError):
        list(decode(b"\x00\x13" + b"A" + good[3:]))              # an 'A' cannot be 19 bytes long


def test_book_by_hand():
    b = Book()
    for m in (Msg("A", 7, 0, T0, 1, "B", 300, "XYZ", 999_900), Msg("A", 7, 0, T0 + 1, 2, "B", 200, "XYZ", 999_900),
              Msg("A", 7, 0, T0 + 2, 3, "S", 500, "XYZ", 1_000_100), Msg("A", 7, 0, T0 + 3, 4, "B", 100, "XYZ", 999_800)):
        b.apply(m)
    assert b.best(7) == (999_900, 500, 1_000_100, 500) and b.depth(7, "B", 2) == [(999_900, 500), (999_800, 100)]
    b.apply(Msg("E", 7, 0, T0 + 4, 1, shares=300, match=1))        # a seller hits the first bid in full
    b.apply(Msg("X", 7, 0, T0 + 5, 2, shares=100))
    assert b.best(7)[:2] == (999_900, 100) and len(b.orders) == 3
    t = b.trades[0]
    assert (t.price, t.shares, t.aggressor) == (999_900, 300, "S")
    b.apply(Msg("D", 7, 0, T0 + 6, 2))
    assert b.best(7)[:2] == (999_800, 100) and not b.errors


def test_errors_are_recorded_not_swallowed():
    b = Book()
    b.apply(Msg("E", 7, 0, T0, 99, shares=100, match=1))
    b.apply(Msg("A", 7, 0, T0 - 1, 1, "B", 100, "XYZ", 999_900))
    assert len(b.errors) == 2 and not b.trades


def test_sample_file_is_reproducible_and_clean():
    data = build()
    assert data == (ROOT / "data/sample.itch").read_bytes()
    b = Book()
    for m in decode(data):
        b.apply(m)
    assert not b.errors
    s = summary(b, 7)
    assert s == tuple(int(x) for x in (ROOT / "data/sample.expected").read_text().split())
