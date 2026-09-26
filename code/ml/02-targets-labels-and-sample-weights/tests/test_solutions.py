"""Numbers gate: every numerical answer printed in Book 12, chapter 2 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_labels as m  # noqa: E402
from firm_labeling import average_uniqueness, concurrency, time_decay  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_label_stats():
    s = m.label_stats()
    assert s["n"] == 48980 and s["fh_conc"] == 10.0 and r(s["fh_u"], 3) == 0.100 and r(s["tb_u"], 3) == 0.123
    assert (round(s["fh_eff"]), round(s["tb_eff"])) == (4916, 6040)
    assert [r(100 * s[k], 1) for k in ("profit_hit", "stopped", "time_hit", "stopped_then_up", "disagree")] == [
        22.7, 20.3, 57.0, 5.3, 1.9]
    assert r(s["tb_len"], 1) == 8.3 and (r(s["t_naive"], 1), r(s["t_adjusted"], 1)) == (9.4, 3.3)
    assert r(s["t_naive"] / s["t_adjusted"]) == r(np.sqrt(1 / s["tb_u"])) == 2.85
    assert 20 * 2458 / 10 == 4916


def test_example_path():
    import csv

    here = pathlib.Path(__file__).resolve()
    rows = list(csv.DictReader(open(here.parents[4] / "figdata/ml" / here.parents[1].name / "path.csv")))
    assert (float(rows[3]["ret"]), float(rows[10]["ret"]), float(rows[0]["up"])) == (-5.0382, 1.8359, 4.8687)


def test_bagging_and_bootstrap():
    t = m.bagging_table()
    assert [r(x, 3) for x in t["plain"]] == [0.504, 0.517, 0.509] and r(t["plain"].mean(), 3) == 0.510
    assert [r(x, 3) for x in t["small"]] == [0.511, 0.512, 0.506] and r(t["small"].mean(), 3) == 0.510
    assert [r(x, 3) for x in t["weighted"]] == [0.506, 0.511, 0.510] and r(t["weighted"].mean(), 3) == 0.509
    d = np.concatenate([t["small"] - t["plain"], t["weighted"] - t["plain"]])
    assert r(np.abs(d).max(), 3) == 0.007 and r((t["weighted"] - t["plain"]).mean(), 3) == -0.001
    assert tuple(r(x) for x in m.bootstrap_uniqueness()) == (0.65, 0.69)


def test_meta():
    q = m.meta()
    assert (r(100 * q["primary"]["hit"], 1), r(q["primary"]["mean"], 3), r(q["primary"]["t"])) == (53.0, 0.064, 3.48)
    assert (r(100 * q["meta"]["share"], 1), r(100 * q["meta"]["hit"], 1), r(q["meta"]["mean"], 3), r(q["meta"]["t"])) == (
        33.8, 54.5, 0.097, 3.19)


def test_exercises():
    t0, t1 = np.array([0, 1, 2, 6]), np.array([2, 4, 4, 8])
    assert list(concurrency(t0, t1, 9)[1:]) == [1, 2, 2, 2, 0, 0, 1, 1]
    assert [r(x) for x in average_uniqueness(t0, t1, 9)] == [0.75, 0.5, 0.5, 1.0]
    assert r(1.5 * 1.2 * 4, 1) == 7.2 and r(6.1 / np.sqrt(20)) == 1.36
    s = m.label_stats(k=2.0)
    assert [r(100 * s[k], 1) for k in ("profit_hit", "stopped", "time_hit")] == [4.0, 3.3, 92.7]
    assert r(s["tb_u"], 4) == 0.1025 and r(s["tb_len"], 1) == 9.8
    assert r(time_decay(np.full(1001, 0.1))[500]) == 0.75 and r(time_decay(np.full(1000, 0.1)).mean()) == 0.75
