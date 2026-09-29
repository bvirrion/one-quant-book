"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 9 (text and solutions)."""
import csv
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "natext"))
import firm_natext as N
import pl_natext as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/09-native-extensions"


def test_small_runs():
    calls = P.per_call(20_000)
    assert set(calls) == {"python function", "C++ via pybind11", "Rust via ctypes"} and min(calls.values()) > 0
    rows = P.sweep((10, 1_000, 100_000))
    assert all(r["ewma_cpp"] < r["ewma_python"] for r in rows)
    assert rows[-1]["asof_cpp"] < rows[-1]["asof_numpy"]


def test_exercise_7_four_lookups_agree():
    rng = np.random.default_rng(7)
    left = np.sort(rng.integers(0, 10**9, 100_000)).astype(np.int64)
    right = np.sort(rng.integers(0, 10**9, 50_000)).astype(np.int64)
    left[0], left[-1] = -5, 2 * 10**9
    ref = N.asof_python(left, right)
    assert all((f(left, right) == ref).all() for f in (N.asof_numpy, N.asof_cpp, N.asof_rust))
    assert ref[0] == -1 and ref[-1] == 49_999


def test_measured_numbers_in_text():
    c = {r["route"]: float(r["ns_per_call"]) for r in csv.DictReader(open(FIG / "measured_calls.csv"))}
    assert (round(c["python function"]), round(c["C++ via pybind11"]), round(c["Rust via ctypes"])) == (60, 118, 337)
    s = {int(r["n"]): {k: float(v) for k, v in r.items() if k != "n"} for r in csv.DictReader(open(FIG / "measured_sweep.csv"))}
    m = s[1_000_000]
    assert (round(m["ewma_cpp"], 1), round(m["ewma_rust"], 1), round(m["ewma_numpy"], 1), round(m["asof_numpy"])) == (1.4, 1.5, 3.3, 21)
    assert round(m["asof_cpp"]) == 6 and round(m["asof_rust"]) == 6 and round(m["asof_numpy"] / m["asof_cpp"]) == 3
    long = [s[n] for n in (10_000, 100_000, 1_000_000, 10_000_000)]
    assert 1.2 < min(x[k] for x in long for k in ("ewma_cpp", "ewma_rust")) and max(
        x[k] for x in long for k in ("ewma_cpp", "ewma_rust")) < 2.0 and all(3.0 <= x["ewma_numpy"] < 3.7 for x in long)
    assert all(s[n]["ewma_cpp"] < s[n]["ewma_numpy"] and s[n]["ewma_rust"] < s[n]["ewma_numpy"] for n in s)
    assert P.break_even([dict(n=n, **v) for n, v in sorted(s.items())], "asof", "rust") == 1000
    assert 2 < m["ewma_numpy"] / m["ewma_cpp"] < 2.5
    # exercises 1 and 4
    assert (round(118 * 2e8 / 1e9, 1), round(60 * 2e8 / 1e9, 1), round(1.4 * 2e8 / 1e9, 2)) == (23.6, 12.0, 0.28)
    assert math.ceil(118 / (60 - 1.4)) == 3 and round(118 / 58.6) == 2 and round(3.3 * 0.2 - 0.28, 1) == 0.4
