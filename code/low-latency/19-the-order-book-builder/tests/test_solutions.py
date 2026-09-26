"""Numbers gate, Book 13 chapter 19."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_book as L  # noqa: E402

FIG = L.ROOT / "figdata/low-latency/19-the-order-book-builder"


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def test_text_and_exercises():
    assert round(L.daily_sigma_ticks(100, 0.01, 1e-4)) == 10_000
    assert round(L.expected_recentrings(10_000, 4096)) == 95
    assert round(1 / L.expected_recentrings(10_000, 65536), 1) == 2.7                    # once every three days
    assert L.recentrings_trend(300_000, 4096) == 292 and round(300_000 / 1024) == 293
    base = 5000 - 2048                                                                   # exercise 1, in cents
    assert base == 2952 and 4973 - base == 2021 and base + 1024 == 3976 and base + 3071 == 6023
    assert 65536 * 16 * 2 == 2 * 2**20                                                   # exercise 2
    s = L.daily_sigma_ticks(40, 0.02, 0.01)                                              # exercise 5
    assert round(s) == 80 and round(L.expected_recentrings(s, 1024), 3) == 0.098
    assert round(L.expected_recentrings(s, 4096), 4) == 0.0061 and round(1 / L.expected_recentrings(s, 4096)) == 164


def test_problem():
    s = L.daily_sigma_ticks(100, 0.015, 1e-4)
    assert round(s) == 15_000
    assert round(L.expected_recentrings(s, 4096)) == 215 and round(L.expected_recentrings(s, 65536), 2) == 0.84
    assert 4 * 15_000 == 60_000
    w = {int(r["width"]): r for r in rows("measured_width.csv")}
    assert w[4096]["recentrings"] == "256" and w[65536]["recentrings"] == "15" and w[256]["recentrings"] == "19744"
    assert int(w[1048576]["recentrings"]) == 0
    tot = {k: float(r["total_ms"]) for k, r in w.items()}
    assert min(tot, key=tot.get) == 65536                                                # the day's minimum
    assert round(tot[65536]) == 4 and round(tot[4096]) == 13 and round(tot[256] / 1000, 1) == 0.7
    assert (round(tot[4096], 1), round(tot[65536], 1)) == (12.8, 4.4)
    per = (tot[4096] - tot[65536]) / (256 - 15) * 1000
    assert 15 < per < 60 and round(per) == 35
    q = {k: float(r["q50"]) for k, r in w.items()}
    assert round(q[65536]) == 29 and all(130 <= q[k] <= 140 for k in (1048576, 4194304))       # about 135
    assert all(25 < q[k] < 31 for k in (4096, 16384, 65536)) and round(q[262144]) == 36


def test_measured_update():
    r = {(x["regime"], x["structure"]): x for x in rows("measured_update.csv")}
    q = {k: float(v["q50"]) for k, v in r.items()}
    assert q[("small", "ladder")] < 0.6 * min(q[("small", "tree")], q[("small", "vector")])
    assert round(q[("large", "ladder")]) == 28 and round(q[("large", "vector")]) == 36 and round(q[("large", "tree")]) == 37
    assert round(q[("small", "ladder")]) == 31 and round(q[("small", "tree")]) == 72 and round(q[("small", "vector")]) == 65
    assert round(q[("small", "tree")], -1) == 70                                           # introduction: about 70
    assert round(float(r[("large", "ladder")]["q99"]), -1) == 150
