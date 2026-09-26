"""Numbers gate, Book 13 chapter 20."""
import csv
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = ROOT / "figdata/low-latency/20-the-strategy-engine"


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def expected_distinct(k, n=100):
    return k * (1 - (1 - 1 / k) ** n)


def test_exercises():
    t = 34_200_012_345_000
    assert t // 100_000 == 342_000_123 and (t // 100_000) % 1024 == 507
    assert round(5e9 / (1024 * 100_000), 1) == 48.8
    assert sorted([(120, 7), (121, 3), (120, 9)]) == [(120, 7), (120, 9), (121, 3)]
    assert round(expected_distinct(700)) == 93 and round(expected_distinct(600)) == 92    # exercise 4
    assert round(2e6 * 53e-9, 2) == 0.11                                                 # exercise 6


def test_measured_nondeterminism():
    d = {r["key"]: int(r["distinct"]) for r in rows("measured_nondet.csv")}
    assert d["firm"] == 1 and d["none"] == 1                                            # deterministic
    assert d["wall_clock"] == 100 and d["all"] == 100
    assert 50 < d["hash_order"] < 100 and 20 < d["two_threads"] < 100
    assert d["hash_order"] == 93 and d["two_threads"] == 49


def test_measured_engine():
    e = {(r["regime"], float(r["quantile"])): float(r["ns"]) for r in rows("measured_engine.csv")}
    assert 20 < e[("large", 0.5)] < 120 and round(e[("large", 0.5)]) == 53
    assert round(e[("small", 0.5)]) == 57
    assert round(e[("large", 0.99)], -1) == 130 and round(e[("small", 0.99)], -1) == 200
