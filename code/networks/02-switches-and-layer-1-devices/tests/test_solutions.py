"""Numbers gate: every number printed in Book 14, chapter 2 (text and solutions)."""
import csv
import math
import pathlib
import sys

import pytest
from scipy.stats import norm

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
import nw_cage as c  # noqa: E402

ns = c.ns
FIG = ROOT / "figdata/networks/02-switches-and-layer-1-devices"


def test_device_tolls():
    assert ns.forward_ns(1518, 10, "store-and-forward", 0) == pytest.approx(1214.4)          # hook: 1.2 us
    assert ns.forward_ns(100, 10, "store-and-forward", 500) == pytest.approx(580)
    assert ns.forward_ns(100, 10, "cut-through", 0) == pytest.approx(51.2)
    assert ns.forward_ns(1518, 10, "store-and-forward", 500) == pytest.approx(1714.4)
    rows = {int(r["frame"]): r for r in csv.DictReader(open(FIG / "forwarding.csv"))}
    assert float(rows[1518]["store_forward"]) == 1714.4 and float(rows[64]["cut_through"]) == 250.0
    # exercise 1
    assert round(ns.forward_ns(512, 25, "store-and-forward", 300), 1) == 463.8
    assert round(ns.forward_ns(512, 25, "cut-through", 300), 1) == 320.5
    assert round(1 - 10 / 12, 3) == pytest.approx(0.167, abs=1e-3)                              # exercise 3


def test_designs():
    t = c.design_table()
    assert (round(t["commodity"]["feed"], 1), round(t["commodity"]["order"], 1)) == (1439.8, 1430.2)
    assert (round(t["cut-through"]["feed"], 1), round(t["cut-through"]["order"], 1)) == (560.0, 556.8)
    assert (round(t["layer-1"]["feed"], 1), round(t["layer-1"]["order"], 1)) == (262.8, 294.6)
    tot = {k: v["feed"] + v["order"] for k, v in t.items()}
    assert (round(tot["commodity"], 1), round(tot["cut-through"], 1), round(tot["layer-1"], 1)) == (2870.0, 1116.7, 557.3)
    assert round(tot["commodity"] - tot["cut-through"], 1) == 1753.3 and round(tot["cut-through"] - tot["layer-1"], 1) == 559.4
    assert round(60_000 / (tot["commodity"] - tot["cut-through"]), 1) == 34.2
    assert round(90_000 / (tot["cut-through"] - tot["layer-1"]), 1) == 160.9
    assert sorted(t["commodity"]["spof"]) == sorted(["sw1", "sw2", "sw1-sw2", "sw2-s1", "sw2-s2"])
    assert t["cut-through"]["spof"] == [] and t["layer-1"]["spof"] == []
    cage = c.design("layer-1")
    b = cage.breakdown(cage.path("A", "s1"), 104, 10.0)
    assert (round(b["serialisation"], 1), round(b["propagation"], 1), b["devices"]) == (83.2, 175.6, 4.0)
    assert round(ns.prop_ns(36), 1) == 175.6 and round(2 * 83.2, 1) == 166.4


def test_contention_closed_form():
    s = ns.ser_ns(100, 10)
    assert s == 96.0
    p50 = 2 * norm.cdf(s / (50 * math.sqrt(2))) - 1
    p100 = 2 * norm.cdf(s / (100 * math.sqrt(2))) - 1
    assert round(p50, 2) == 0.83 and round(p100, 2) == 0.50 and round(s / (100 * math.sqrt(2)), 3) == 0.679
    r = c.mux_contention(2, 50)
    assert abs(2 * r["p_wait"] - p50) < 0.01                      # simulation agrees with the proposition


def test_contention_simulation():
    r4 = c.mux_contention(4, 50)
    assert round(r4["mean"], 1) == 93.2 and round(r4["last"], 1) == 186.1
    assert round(c.mux_contention(4, 1000)["mean"]) == 6
    assert round(c.mux_contention(2, 50)["mean"], 1) == 22.7                                    # exercise 7
    assert round(294.6 + 186.1, 1) == 480.7 < 556.8


def test_small_runs():
    a = c.mux_contention(4, 50, n_events=2000)
    b = c.mux_contention(4, 800, n_events=2000)
    assert a["mean"] > b["mean"] > 0 and a["last"] >= a["mean"]
    assert c.mirror_load(6, 10) == (12, pytest.approx(1 / 6))
