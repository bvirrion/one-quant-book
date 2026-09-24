import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_modelval as f


def test_tiering_rule():
    assert f.ModelRecord("a", "x", "o", "capital", 3, 3, 3).tier == 1
    assert f.ModelRecord("b", "x", "o", "pricing", 2, 2, 2).tier == 2
    assert f.ModelRecord("c", "x", "o", "report", 1, 1, 2).tier == 3
    assert f.inventory_summary([f.ModelRecord("a", "x", "o", "u", 3, 3, 3)]) == {1: 1, 2: 0, 3: 0}


def test_benchmark_harness():
    res = f.benchmark(lambda a, b: a * b + (0.1 if a > 2 else 0.0), lambda a, b: a * b,
                      {"a": [1, 2, 3], "b": [1.0, 10.0]}, abs_tol=1e-9, rel_tol=0.02)
    s = f.summary(res)
    assert s["points"] == 6 and s["failures"] == 1 and s["failed"][0].params == {"a": 3, "b": 1.0}


def test_outcomes_and_relative_change():
    assert math.isclose(f.binomial_tail(10, 0, 0.3), 1.0)
    assert math.isclose(f.binomial_tail(250, 5, 0.01), 1 - 0.8922, abs_tol=5e-4)   # Basel table: 89.22% up to 4
    assert math.isclose(f.relative_change(110, 100), 10 / 105)
    assert math.isclose(f.relative_change(110, 100, error=True), 0.5 * f.relative_change(110, 100))
