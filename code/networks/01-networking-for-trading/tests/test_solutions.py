"""Numbers gate: every number printed in Book 14, chapter 1 (text and solutions)."""
import csv
import functools
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
import nw_wire as w  # noqa: E402

ns = w.ns
FIG = ROOT / "figdata/networks/01-networking-for-trading"


def test_frames_and_table():
    e = w.mold_example()
    assert (e["payload"], e["frame"], e["wire"]) == (58, 104, 124)
    assert round(e["ns_10g"], 1) == 99.2 and round(e["ns_25g"], 1) == 39.7 and round(100 * e["useful_share"]) == 29
    t = w.frame_table()
    printed = {64: (672.0, 67.2, 26.9, 6.7), 128: (1184.0, 118.4, 47.4, 11.8), 256: (2208.0, 220.8, 88.3, 22.1),
               512: (4256.0, 425.6, 170.2, 42.6), 1024: (8352.0, 835.2, 334.1, 83.5), 1518: (12304.0, 1230.4, 492.2, 123.0)}
    for f, row in printed.items():
        assert tuple(round(t[(f, r)], 1) for r in w.RATES) == row
    assert round(1 - 10 / 25, 2) == 0.6
    assert round(1230.4 / ns.prop_ns(1.0)) == 252                                           # bits in flight
    assert 66 == 104 - 58 + 20                                                              # fixed overhead per packet


def test_opra_figures():
    c = w.opra_curve()
    j = dict(c["2026-07"])
    assert round(j[0.001] / j[1.0], 1) == 5.5 and round(j[1.0], 1) == 63.9 and round(j[0.001]) == 350
    jan = dict(c["2024-01"])
    assert round(jan[0.001] / jan[1.0], 1) == 1.9 and round(j[0.001] / j[1.0], 1) == 5.5         # exercise 6
    assert jan[0.001] / j[0.001] < 0.25                                                          # 80 against 350
    cap = w.opra_capacity()
    assert round(cap["gbps_100ms"], 1) == 44.0 and round(cap["gbps_10ms"], 1) == 50.1
    assert round(cap["bytes_per_packet"]) == 352 and round(cap["msgs_per_packet"], 1) == 8.7
    assert round(2 * 1.1 * 50.1, 1) == 110.2 and round(110.2 / 25, 1) == 4.4                    # exercise 3


def test_exercises_by_hand():
    assert round(ns.ser_ns(256, 25), 1) == 88.3 and round(1e10 / 672 / 1e6, 2) == 14.88
    assert ns.mcast_mac("233.54.12.111") == "01:00:5e:36:0c:6f"
    assert ns.mcast_mac("224.54.12.111") == ns.mcast_mac("233.182.12.111") == "01:00:5e:36:0c:6f"
    b = w.burst_queue(4, 6, 10, 50e-6)
    assert b == pytest.approx(87_500) and b * 8 / 10 == pytest.approx(70_000)


def test_problem():
    assert 8 * 0.6 == pytest.approx(4.8) and round(4.8e9 / 1760 / 1e6, 2) == 2.73
    b = w.burst_queue(8, 2.5, 10, 1e-3)
    assert b == pytest.approx(1.25e6) and round(b / 220) == 5682 and b * 8 / 1e10 == pytest.approx(1e-3)
    assert round(b * 8 / 5.2e9 * 1e3, 2) == 1.92
    share = 6e6 / 16
    assert share == 375_000 and round((b - share) / 220) == 3977
    burst = 20e9 * 1e-3 / 1760
    assert round(burst) == 11364 and round(100 * 3977 / burst) == 35
    assert 6e6 * 8 / 1e10 == pytest.approx(4.8e-3)
    assert 1e-3 / 60 < 2e-5                                                                     # < 0.002%


@functools.lru_cache
def zero(share):
    return w.zero_loss_buffer(share=share)


@pytest.mark.reference
def test_simulation_numbers():
    assert round(w.load_gbps(share=0.0), 1) == 5.2 and round(w.load_gbps(share=0.3), 1) == 5.2
    z0, z3 = zero(0.0), zero(0.3)
    assert (round(z0.min() / 1e3), round(z0.max() / 1e3), round(z0.mean() / 1e3)) == (21, 31, 26)
    assert (round(z3.min() / 1e6, 2), round(z3.max() / 1e6, 1), round(z3.mean() / 1e6, 1)) == (0.44, 2.4, 1.1)
    assert round(zero(0.1).mean() / 1e6, 2) == 0.32 and round(zero(0.5).mean() / 1e6, 2) == 1.98   # exercise 7
    rows = list(csv.DictReader(open(FIG / "peak.csv")))
    by = {float(r["window_us"]): r for r in rows}
    assert round(float(by[100.0]["independent"]), 1) == 9.1 and round(float(by[100.0]["common"])) == 68
    assert round(float(by[1000.0]["common"])) == 16 and float(by[100.0]["independent"]) < 10
    fan = {float(r["buffer_kb"]): r for r in csv.DictReader(open(FIG / "fanin.csv"))}
    assert round(float(fan[500.0]["f8_common"]), 1) == 2.6


def test_small_runs():
    """Machine-independent properties at reduced size (CI)."""
    small = dict(seconds=0.01)
    lo = w.zero_loss_buffer(share=0.0, seeds=range(1, 4), **small)
    hi = w.zero_loss_buffer(share=0.3, seeds=range(1, 4), **small)
    assert hi.mean() > 5 * lo.mean()                                   # the correlation, not the load, fills the buffer
    d = w.fanin((10_000, 100_000, 1_000_000), share=0.3, **small)
    assert d[0] >= d[1] >= d[2]
    p = w.peak_by_window((1_000, 1_000_000), share=0.3, **small)
    assert p[0] > p[1]
