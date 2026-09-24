"""Numbers in the solutions of Book 3, Chapter 26."""
import pathlib
import sys
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_data as m
from firm_wsbook import Book


def test_exercises():
    b = Book()
    b.snapshot(100, [], [])
    assert b.apply(95, 99, [], []) == "ignored" and b.apply(101, 103, [], []) == "applied"
    assert b.apply(105, 106, [], []) == "gap"
    s = "10014" + "10026" + "9995" + "9987"
    assert zlib.crc32(s.encode()) == 3_348_617_501
    r = m.simulate(0.001)
    assert round(100 * r["silent_wrong"], 1) == 1.9 and round(r["mean_error_msgs"]) == 21
    same = [(R, m.simulate(0.001, n=100_000, resync_msgs=R)) for R in (10, 20, 30)]
    assert [round(x["stale"] - x["silent_wrong"], 3) for _, x in same] == [-0.009, 0.0, 0.01]


def test_problem():
    r = m.simulate(0.001)
    assert round(100 * r["silent_wrong"], 2) == 1.90 and round(100 * r["stale"], 2) == 4.75
