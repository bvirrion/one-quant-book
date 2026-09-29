"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 8 (text and solutions)."""
import csv
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "pyscale"))
import pl_pyscale as P
from firm_pyscale import chunks, rolling_sum_kernel, run

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/08-python-at-scale"


def rows(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs(tmp_path):
    a = P.agree(5_000, tmp_path / "h.flat")
    assert all(v < 1e-9 for v in a.values())
    _, rec = P.flat_open(P.history(tmp_path / "h.flat", 5_000))
    assert P.stream_max(rec, 777) == P.whole_max(rec)


@pytest.mark.reference
def test_memory_representations():
    m = P.symbol_memory()
    assert (m["object"], m["arrow string"], m["numpy fixed width"]) == (61_000_000, 8_000_000, 16_000_000)
    assert round(m["category"] / 1e6, 1) == 1.0 and round(m["object"] / m["category"]) == 61
    assert round(3 * m["object"] / 1e6) == 183 and round(3 * m["category"] / 1e6) == 3


def test_measured_numbers_in_text():
    ns = {r["method"]: float(r["ns_per_event"]) for r in rows("measured_methods.csv")}
    rec, lst, arr = ns["loop over records"], ns["loop over lists"], ns["array expression"]
    assert (round(rec, -1), round(lst), round(arr)) == (960, 145, 14)
    assert (round(rec / arr, -1), round(lst / arr)) == (70, 11)
    assert (round(rec * 2e8 / 1e9, -1), round(lst * 2e8 / 1e9), round(arr * 2e8 / 1e9, 1)) == (190, 29, 2.7)
    year = 250 * 2e8
    assert (round(rec * year / 3.6e12), round(lst * year / 3.6e12), round(arr * year / 6e10)) == (13, 2, 11)
    ch = {int(r["chunk"]): (float(r["seconds"]), float(r["peak_mb"])) for r in rows("measured_chunks.csv")}
    assert round(ch[1000][0], 3) == 0.048 and round(ch[10000][0], 3) == 0.025 and round(ch[10000][1], 2) == 0.31
    assert min(ch, key=lambda k: ch[k][0]) == 100000 and round(ch[100000][0], 3) == 0.023
    assert round(ch[2_000_000][0], 3) == 0.028 and max(ch[k][0] for k in ch if k >= 10000) < 1.25 * ch[100000][0]
    whole = ch[2_000_000][1] * 1e6 / 2e6
    assert round(whole) == 16 and round(1.5e9 / whole / 1e6) == 94 and round(ch[2_000_000][1]) == 32
    par = {r["task"]: float(r["seconds"]) for r in rows("measured_parallel.csv")}
    assert (round(par["pickled through a pipe"], 2), round(par["shared memory"], 2)) == (0.14, 0.03)
    assert (round(par["python loop; 2 threads"], 2), round(par["python loop; 1 thread"], 2)) == (0.20, 0.11)
    assert (round(par["numpy sort; 2 threads"], 3), round(par["numpy sort; 1 thread"], 3)) == (0.094, 0.086)


def test_exercise_7():
    x = np.random.default_rng(5).standard_normal(100_000)
    c = np.concatenate([[0.0], np.cumsum(x)])
    i = np.arange(1, len(x) + 1)
    ref = c[i] - c[np.maximum(i - 50, 0)]
    worst = max(float(np.max(np.abs(run(chunks(x, s), rolling_sum_kernel(50))[0] - ref)))
                for s in (1, 7, 50, 1000, len(x)))
    assert worst < 1e-11
