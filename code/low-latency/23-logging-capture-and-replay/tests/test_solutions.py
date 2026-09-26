"""Numbers gate, Book 13 chapter 23."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = ROOT / "figdata/low-latency/23-logging-capture-and-replay"
sys.path.insert(0, str(HERE / "python"))
import ll_logging as L  # noqa: E402

bl = L.bl


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def journal():
    return {r["stream"]: r for r in rows("journal.csv")}


def test_exercises():
    w = bl.Writer()
    w.log(34_200_000_000_010, "fill {} of {} at {}, position {}", "uiii", 40, 100, 999_900, -200)
    assert len(w.recs) == 48
    sites, recs = bl.read(w.bytes())
    line = bl.text(sites, recs)[0]
    assert line == "34200000000010 fill 40 of 100 at 999900, position -200" and len(line) == 54
    assert bl.site_id("x {}", "i") != bl.site_id("x {}", "d")
    j = journal()["large tick (the open)"]
    assert int(j["raw_bytes"]) == 12 + 189_875 * 56 and round(int(j["zlib_bytes"]) / 189_875, 1) == 14.9
    assert 2_000_000 * 0.02 == 40_000 and 65_536 * 64 == 4 * 2**20


def test_journal_table():
    j = journal()
    big, small = j["large tick (the open)"], j["small tick (synthetic)"]
    assert (int(big["events"]), float(big["span_s"]), float(big["ratio"])) == (189_875, 120.0, 3.76)
    assert round(int(big["raw_bytes"]) / 1e6, 1) == 10.6 and round(int(big["zlib_bytes"]) / 1e6, 1) == 2.8
    assert (int(small["events"]), float(small["ratio"])) == (6_000, 3.96)
    assert round(int(small["raw_bytes"]) / 1e6, 2) == 0.34 and round(int(small["zlib_bytes"]) / 1e6, 2) == 0.08
    assert round(float(small["span_s"]) * 1000) == 6
    assert all(14 <= float(r["zlib_bytes_per_event"]) <= 15.5 for r in j.values())


def test_problem():
    rate = 189_875 / 120
    assert round(rate) == 1_582
    events = rate * 6.5 * 3600
    assert round(events / 1e6, 1) == 37.0
    raw = L.storage_per_day(rate, 6.5, 56)
    comp = L.storage_per_day(rate, 6.5, 56, 3.76)
    assert round(raw / 1e9, 2) == 2.07 and round(comp / 1e9, 2) == 0.55
    assert round(comp * 252 * 5 / 1e12, 1) == 0.7 and round(comp * 252 * 5 * 200 / 1e12) == 139
    r = rows("measured_replay.csv")[0]
    speed = float(r["speedup"])
    assert round(speed, -2) == 2_800 and float(r["replay_s"]) < 0.05              # about 2,800x; under 50 ms
    assert 23_400 / speed < 10 and round(23_400 / 2_800, 1) == 8.4 and 25 <= 200 * 23_400 / speed / 60 <= 35


def test_measured_calls():
    m = {(x["method"], float(x["quantile"])): float(x["ns"]) for x in rows("measured_logcall.csv")}
    b, s = m[("binlog", 0.5)], m[("snprintf", 0.5)]
    assert 3 <= b <= 8 and round(b) in (4, 5, 6)
    assert round(s, -1) == 100 and 85 <= m[("fprintf", 0.5)] <= 115
    assert round(m[("ostringstream", 0.5)], -1) == 210 and 15 <= s / b <= 30 and round(s / b, -1) == 20
    assert 5 * 5 == 25 and 5 * 100 == 500
