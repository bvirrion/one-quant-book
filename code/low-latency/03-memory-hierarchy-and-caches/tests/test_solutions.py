"""Numbers gate, Book 13 chapter 3."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_mem as m  # noqa: E402


def near(x, want, rel=0.2):
    return abs(x - want) <= rel * abs(want)


def test_geometry():
    assert m.cache_geometry(48 * 1024, 64, 12) == (64, 4096)
    assert 13 * 64 == 832
    assert m.split_address(0x7F3A12345E48)[1:] == (57, 8)                  # exercise 1
    assert m.cache_geometry(2 * 1024 * 1024, 64, 16) == (2048, 131072)      # exercise 2
    assert m.pages_needed(600 << 20, 4096) == 153_600 and m.pages_needed(600 << 20, 2 << 20) == 300
    assert m.tlb_reach(2048, 4096) == 8 << 20 and m.tlb_reach(2048, 2 << 20) == 4 << 30


def test_problem():
    per = 2 * 256 * 32 + 4096
    assert per == 20_480 and per // 64 == 320
    assert m.books_in(2 << 20, per, 0.75) == 76 and m.books_in(48 << 10, per) == 2
    miss = 1 - 76 / 300
    assert round(100 * miss, 1) == 74.7
    assert round(3 * ((1 - miss) * 5 + miss * 150)) == 340
    straddle = [k for k in range(4) if (48 * k) // 64 != (48 * k + 47) // 64]
    assert straddle == [1, 2]                                               # half of 48-byte levels straddle


def test_measured():
    assert near(m.at(32768), 1.1) and near(m.at(262144), 3.5)
    assert all(15 <= m.at(b) <= 23 for b in (3 << 20, 4 << 20, 6 << 20, 8 << 20))     # the third level
    assert 95 <= m.at(12 << 20) and all(100 <= m.at(b) <= 175 for b in (16 << 20, 32 << 20, 64 << 20, 256 << 20))
    assert round(m.at(256 << 20), -1) in (170, 180)
    assert all(r["sequential_ns"] < 2.5 for r in m.stairs() if r["bytes"] <= 1 << 20)
    assert all(r["sequential_ns"] < 12 for r in m.stairs())                 # six or seven ns from memory
    big = [r for r in m.stairs() if r["bytes"] >= 16 << 20]
    assert all(r["random_ns"] > 25 * r["sequential_ns"] for r in big)       # "some thirty times less"
    assert all(3.5 <= r["sequential_ns"] <= 5 for r in big)                 # four or five ns
    h = {r["pages"]: float(r["ns"]) for r in m.rows("measured_huge.csv")}
    assert round(h["4KiB"], -1) == 180 and round(h["huge"], -1) == 150
    f = {r["layout"]: float(r["ns_per_increment"]) for r in m.rows("measured_false.csv")}
    assert round(f["one thread"]) == 4 and near(f["padded"], f["one thread"], 0.15)
    assert round(f["same line"] / f["one thread"]) == 5                     # about five times
