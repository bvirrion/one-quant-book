"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 13 (text and solutions)."""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_jobgraph as P

J = P.J
FIG = P.FIG


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    tasks = P.sweep(0.7, n=400, n_long=4)
    cl = J.Cluster(2, 8, slow=(1,), slowdown=4.0, fail_per_hour=0.002, seed=1)
    lb = J.lower_bound(tasks, cl.total)
    got = {n: J.simulate(tasks, cl, m()).makespan for n, m in (("FIFO", J.FIFO), ("LPT", J.LPT))}
    assert got["LPT"] <= got["FIFO"] and got["LPT"] >= lb


def test_calibration():
    x = np.array([float(r["seconds"]) for r in _csv("measured_backtests.csv")])
    assert len(x) == 24 and round(P.measured_sigma(), 2) == 0.76
    assert round(float(np.median(x)), 3) == 0.089 and round(float(x.max() / np.median(x)), 1) == 8.0


def test_sweep_and_hook():
    s = P.measured_sigma()
    tasks, cl = P.sweep(s), P.cluster()
    assert cl.total == 384 and round(sum(t.duration for t in tasks) / 3600) == 3649
    assert round(J.lower_bound(tasks, 384) / 3600, 2) == 9.50
    sc = J.simulate(tasks, cl, J.FIFO())
    last = max(sc.finish, key=sc.finish.get)
    run = next(r for r in sc.runs if r[0] == last and r[4] == "done")
    # the hook: the last task is one of the forty long ones, started after twelve hours on a normal node
    assert last >= P.N - P.LONG and run[1] // 16 != 5 and round(run[2] / 3600, 1) == 12.3
    assert round(run[3] / 3600, 2) == 19.79
    g, b = P.profile(s)["FIFO"]
    assert round(P.idle_after(g, b), 1) == 16.3


def test_named_result_numbers():
    rows = {(r["policy"], r["spec"]): r for r in _csv("policies.csv")}
    mk = {k: float(v["makespan_h"]) for k, v in rows.items()}
    assert (mk[("FIFO", "0")], mk[("FIFO", "1")]) == (19.79, 20.32)
    assert (mk[("LPT", "0")], mk[("LPT", "1")]) == (11.80, 10.02)
    assert (mk[("work stealing", "0")], mk[("work stealing", "1")]) == (16.33, 16.40)
    assert mk[("LPT (no slow node)", "0")] == 10.32 and float(rows[("LPT", "0")]["bound_h"]) == 9.50
    assert round(100 * (10.02 / 9.50 - 1), 1) == 5.5
    nh = {k: float(v["node_hours"]) for k, v in rows.items()}
    assert (nh[("FIFO", "0")], nh[("LPT", "0")], nh[("work stealing", "0")]) == (475.0, 283.3, 391.9)
    assert (round(nh[("FIFO", "0")]), round(nh[("LPT", "1")]), round(nh[("FIFO", "0")] - nh[("LPT", "1")])) == (475, 240, 235)
    assert [int(rows[(p, "1")]["backups"]) for p in ("FIFO", "LPT", "work stealing")] == [152, 105, 145]
    assert [round(float(rows[(p, "1")]["wasted_core_h"])) for p in ("FIFO", "LPT", "work stealing")] == [130, 91, 118]
    fs = {r["policy"]: r for r in _csv("fairshare.csv")}
    assert [float(fs["FIFO"][k]) for k in ("team_b_half_h", "team_b_done_h", "team_a_done_h")] == [8.28, 11.38, 19.79]
    assert [float(fs["fair share"][k]) for k in ("team_b_half_h", "team_b_done_h", "team_a_done_h")] \
        == [0.59, 2.64, 16.68]
    c = [(float(r["makespan_h"]), int(r["core_hours"])) for r in _csv("caching.csv")]
    assert c == [(19.34, 6922), (11.44, 3514), (10.27, 3475)]
    # exercises
    assert round(15 * 30 / 60, 1) == 7.5 and round(7.5 * 4) == 30
    assert round(np.exp(0.3 * 3.05), 2) == 2.5 and round(100 * (1 - 0.99886), 2) == 0.11


def test_exercise_7_long_tasks_first():
    r = {k: round(v, 2) for k, v in P.long_tasks_first(P.measured_sigma()).items()}
    assert r == {("FIFO", False): 14.41, ("FIFO", True): 13.69, ("LPT", False): 11.8, ("LPT", True): 10.02}
