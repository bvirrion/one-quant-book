"""Numbers gate, Book 13 chapter 11."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import ll_aba  # noqa: E402

FIG = HERE.parents[2] / "figdata/low-latency/11-lock-free-programming"


def rows(name):
    with open(FIG / name, newline="") as f:
        return list(csv.DictReader(f))


def test_aba_replay():
    ok, contents, pool = ll_aba.aba(tagged=False)
    assert ok and contents[0] == "B" and "B" in pool          # the head is a node back in the pool
    ok, contents, _ = ll_aba.aba(tagged=True)
    assert not ok and contents[0] == "A"                      # the tag makes the CAS fail


def test_arithmetic():
    assert round(2**32 / 1e8, 1) == 42.9                                                # exercise 3
    assert round(100_000 * 2e-6, 2) == 0.2                                              # exercise 6
    held = 50_000 * 3e-6                                                                 # problem
    assert round(held, 2) == 0.15 and round(20_000 * held * 1.5e-6 * 1e3, 1) == 4.5    # ms per second
    pre = 50_000 * 1e-4
    assert pre == 5 and round(pre * 3e-3, 3) == 0.015
    assert round(20_000 * 0.015) == 300 and round(300 * 1.5e-3 * 1e3) == 450
    assert round(4.5 + 450, 1) == 454.5


def test_measured():
    c = {int(r["threads"]): {k: float(v) for k, v in r.items() if k != "threads"} for r in rows("measured_counters.csv")}
    assert all(3 < c[1][k] < 16 for k in c[1])                                          # a few ns alone
    assert all(c[4]["per_thread"] < 2 * c[1]["per_thread"] for _ in [0])                # shares nothing: scales
    assert all(c[t][k] > 3 * c[1][k] for t in (2, 3, 4) for k in ("mutex", "CAS_loop", "fetch_add"))
    assert 30e6 < 4 / (c[4]["fetch_add"] * 1e-9) < 60e6 and 4 / (c[4]["per_thread"] * 1e-9) > 5e8   # exercise 1
    lit = {r["ordering"]: int(r["both_zero"]) for r in rows("measured_litmus.csv")}
    assert lit["seq_cst"] == 0 and lit["relaxed"] > 0 and lit["release-acquire"] > 0
    assert all(int(r["nodes_wrong"]) == 0 for r in rows("measured_aba.csv")) and len(rows("measured_aba.csv")) == 20
