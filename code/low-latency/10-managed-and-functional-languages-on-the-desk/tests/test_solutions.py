"""Numbers gate, Book 13 chapter 10."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_gc  # noqa: E402

FIG = HERE.parents[2] / "figdata/low-latency/10-managed-and-functional-languages-on-the-desk"
GIB = 1 << 30
SESSION = 6.5 * 3600


def test_budget():
    assert round(ll_gc.garbage_budget(2 * GIB, 200_000, SESSION), 3) == 0.459           # text and named result
    rate = 64 * 100_000                                                                   # exercise 1
    assert round(GIB / rate, 1) == 167.8 and int(rate * SESSION / GIB) == 139
    assert 0.001 * 200_000 == 200                                                        # exercise 2
    assert round(20e6 / 6e6, 2) == 3.33                                                   # exercise 6
    r = 48 * 200_000                                                                      # problem
    assert r == 9_600_000 and round(r * SESSION / 1e9, 2) == 224.64
    n = r * SESSION / (2 * GIB)
    assert round(2 * GIB / r, 1) == 223.7 and round(n) == 105 and round(n * 0.5) == 52
    assert 0.0005 * 200_000 == 100 and round(3 * n) == 314 and round(3 * n * 0.5) == 157


def test_collector_counts_are_deterministic():
    _, w = ll_gc.run(ll_gc.dict_book(), 200_000)
    assert w.collections == {0: 259, 1: 23, 2: 2}
    _, w = ll_gc.run(ll_gc.pooled_book(), 50_000)
    assert w.collections == {0: 0, 1: 0, 2: 0}


def test_measured():
    rows = {r["design"]: {k: float(v) for k, v in r.items() if k != "design"}
            for r in csv.DictReader(open(FIG / "measured_gc.csv"))}
    d, p = rows["dict book"], rows["pooled book"]
    assert (d["gen0"], d["gen1"], d["gen2"], p["gen0"] + p["gen1"] + p["gen2"]) == (259, 23, 2, 0)
    assert d["max"] / p["max"] > 20 and 12e6 < d["max"] < 30e6                   # twenty times; about eighteen ms
    assert abs(d["max"] - d["gc_max_ns"]) / d["max"] < 0.1                          # the worst message is the full collection
    assert p["p50"] > d["p50"]                                                       # not faster at the median
