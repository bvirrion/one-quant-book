"""Numbers gate: every number printed in Book 14, chapter 3 (text and solutions). Measured numbers are checked against
the committed CSV (they come from the laptop, not from this run)."""
import csv
import pathlib
import sys

import pytest
from scipy.optimize import brentq

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "nicring"))
import firm_nicring as nr  # noqa: E402
import nw_nic as n  # noqa: E402

FIG = ROOT / "figdata/networks/03-network-cards-and-kernel-bypass"


def measured():
    return {(int(r["mode"]), r["stage"]): r for r in csv.DictReader(open(FIG / "measured_rx.csv"))}


def test_measured_table():
    m = measured()
    us = lambda mode, st, q="p50_ns": float(m[(mode, st)][q]) / 1000  # noqa: E731
    assert (round(us(0, "to_kernel"), 2), round(us(0, "kernel_to_application"), 1), round(us(0, "total"), 1)) == (0.75, 15.4, 16.2)
    assert round(us(0, "total", "p99_ns")) == 215
    assert (round(us(1, "to_kernel"), 2), round(us(1, "kernel_to_application"), 2), round(us(1, "total"), 1)) == (0.62, 0.92, 1.5)
    assert round(us(1, "total", "p99_ns")) == 3457
    assert (round(us(2, "to_kernel"), 2), round(us(2, "kernel_to_application"), 1), round(us(2, "total"), 1)) == (0.45, 21.4, 22.0)
    assert round(us(2, "total", "p99_ns")) == 75
    assert round(us(0, "total") / us(1, "total")) == 11 and round(us(1, "total", "p99_ns") / us(0, "total", "p99_ns")) == 16
    assert round(us(0, "kernel_to_application") / us(0, "total"), 2) == 0.95                     # exercise 3
    q = {float(r["q"]): r for r in csv.DictReader(open(FIG / "measured_rx_q.csv"))}
    assert float(q[0.95]["busy"]) > max(float(q[0.95]["blocking"]), float(q[0.95]["batched"]))
    assert float(q[0.9]["busy"]) < float(q[0.9]["blocking"])


def test_model_numbers():
    assert round(n.crossover(0, 1) * 1e6, -3) == 435_000 and round(n.crossover(0, 16), 2) == 2.35
    a, t, p = n.coalesce(0.1, 0, 1), n.coalesce(0.1, 8, 10_000), n.poll(0.1)
    assert (round(a["mean_us"], 1), round(100 * a["cpu"])) == (5.6, 23)
    assert (round(t["mean_us"], 1), round(100 * t["cpu"])) == (11.7, 14) and round(p["mean_us"], 1) == 0.4
    assert n.coalesce(0.5, 0, 1)["cpu"] > 1                                                        # saturated
    # problem
    one, tim, pol = n.coalesce(0.2, 0, 1), n.coalesce(0.2, 10, 10_000), n.poll(0.2)
    assert round(0.2 * 2.3, 2) == 0.46 and round(3 + 2 + 0.3, 1) == 5.3 and round(one["mean_us"], 1) == 6.3
    assert round(tim["mean_us"], 1) == 12.4 and round(100 * tim["cpu"]) == 19            # analytic 19.3, below
    assert round(1 / (10 + 1 / 0.2) * 1e6) == 66_667 and round(100 * (66_667 * 2e-6 + 0.06), 1) == 19.3
    assert abs(tim["irq_rate"] - 1 / 15) < 0.002 and round(pol["mean_us"], 2) == 0.41
    assert round(brentq(lambda x: x * (2 / (1 + 10 * x) + 0.3) - 0.25, 1e-6, 5) * 1e6, -3) == 324_000
    assert round(1024 / 200_000 * 1e3, 1) == 5.1


def test_ring_numbers():
    assert max(0, 1.5e6 * 400e-6 - (512 - 40)) == 128                                           # exercise 1
    assert 1 + 0.2 * 20 == 5 and 200_000 / 5 == 40_000                                           # exercise 2
    ev = [tuple(int(x) if x.isdigit() else x for x in line.split())
          for line in (ROOT / "code/firm/nicring/data/events.txt").read_text().splitlines()]
    assert nr.Ring(64, 32).run(ev).drops == 36 and nr.Ring(128, 32).run(ev).drops == 0         # exercise 7


def test_small_runs():
    a = n.coalesce(0.2, 4, 10_000, n=5000)
    b = n.coalesce(0.2, 16, 10_000, n=5000)
    assert a["mean_us"] < b["mean_us"] and a["cpu"] > b["cpu"]
    assert n.poll(0.2, n=5000)["mean_us"] < a["mean_us"]
    with pytest.raises(ValueError):
        nr.Ring(100)
