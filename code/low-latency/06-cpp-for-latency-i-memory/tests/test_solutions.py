"""Numbers gate, Book 13 chapter 6 (the allocation count itself, 9 and 0, is asserted by cpp/ll_alloc_test.cpp)."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_layout as lay  # noqa: E402


def near(x, want, rel=0.25):
    return abs(x - want) <= rel * want


def test_layouts():
    assert lay.layout(lay.LOOSE)[1:] == (40, 17) and lay.layout(lay.by_size(lay.LOOSE))[1:] == (24, 1)
    assert 8 * 24 == 3 * 64 and 8 * 40 == 5 * 64                                  # eight orders: three lines, not five
    ex1 = [("a", "char"), ("b", "int32"), ("c", "char"), ("d", "double"), ("e", "int16")]
    assert lay.layout(ex1)[1:] == (32, 16) and lay.layout(lay.by_size(ex1))[1:] == (16, 0)


def test_sizes():
    assert 50_000 * 64 == 3_200_000 and -(-3_200_000 // 4096) == 782               # exercise 2
    assert (512 << 20) // 4096 == 131_072
    assert 9 * 50_000 == 450_000                                                   # problem 1
    assert near(38_000 * 1.5, 57_000, 0.01) and 1 << 16 == 65_536                  # problem 19


def test_measured():
    f = lay.fault_cost()
    first, pre = f["first touch"], f["pre-faulted"]
    assert first[1] == 16_384 and pre[1] == 0                                      # 64 MiB of 4 KiB pages
    assert 0.9e3 < first[0] < 2.0e3 and 20 < pre[0] < 45 and first[0] / pre[0] > 30  # ~1.3 us, 30 ns, forty times
    assert near(131_072 * first[0] / 1e9, 0.17, 0.35)                              # exercise 3: ~0.17 s
    c = lay.churn()
    assert near(c["new/delete"]["p50"], 25) and c["pool"]["p50"] <= c["new/delete"]["p50"]
    assert c["pmr pool"]["p50"] > c["pool"]["p50"]
    assert all(v["max"] > 1e4 for v in c.values())                                 # tens of microseconds at the max
    pair = c["new/delete"]["p50"]
    assert near(9 * pair * 50_000 / 1e6, 12, 0.35)                                 # problem 6: ~12 ms a second
    assert 250 < 400_000 / first[0] < 450                                          # problem 7: ~300 faults
