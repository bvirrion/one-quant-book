"""Acceptance tests of the Book 3, Chapter 26 build (websocket book builder); the C++ and Rust twins have the
same cases."""
import pathlib
import sys
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_wsbook import Book, crc32


def book():
    b = Book()
    b.snapshot(100, [(999, 5), (998, 7)], [(1001, 4), (1002, 6)])
    return b


def test_sequence_rules():
    b = book()
    assert b.apply(95, 100, [(999, 1)], []) == "ignored"          # already in the snapshot
    assert b.apply(99, 101, [(999, 0)], [(1001, 9)]) == "applied"  # straddles the snapshot id
    assert b.bids == {998: 7} and b.asks[1001] == 9 and b.update_id == 101
    assert b.apply(103, 104, [], [(1003, 1)]) == "gap" and not b.synced
    assert b.apply(105, 105, [], []) == "gap"                     # stays unsynced until a snapshot


def test_checksum():
    b = book()
    s = "10014" + "10026" + "9995" + "9987"
    assert b.checksum() == zlib.crc32(s.encode())
    assert crc32(s.encode()) == zlib.crc32(s.encode())
    assert crc32(b"123456789") == 0xCBF43926                        # the standard check value
