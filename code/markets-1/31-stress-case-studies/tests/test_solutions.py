"""Numbers gate: every numerical answer printed in the Chapter 31 text and solutions."""
import csv
import math
import pathlib
import sys
from dataclasses import replace

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from withdrawal import Params, depth_needed, run, trough

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/31-stress-case-studies"
P = Params()


def pct(x):
    return round(x * 100, 1)


def test_text_and_captions():
    full = run(P, 75_000)
    assert pct(trough(full)) == 9.8 and pct(trough(run(replace(P, withdrawal=0.0, churn=0.0), 75_000))) == 2.2
    assert pct(trough(run(replace(P, pause_at=0.05), 75_000))) == 7.0
    falls = [1 - x[0] for x in full]
    assert round((falls[21] - falls[17]) * 100, 1) == 5.9        # minutes 19 to 22
    assert [i + 1 for i, x in enumerate(full) if x[2] == 0][0] == 23
    rows = {r["max_fall_pct"]: float(r["depth_k"]) for r in csv.DictReader(open(FIG / "depth_needed.csv"))}
    assert rows["5"] == 116.2 and rows["2"] == 161.2
    assert rows["2"] == pytest.approx(depth_needed(P, 75_000, 0.02) / 1e3, abs=0.06)
    assert round(1058 / 327, 1) == 3.2 and round(220 / 144, 1) == 1.5 and 1058 + 220 == 1278


def test_exercises():
    assert round(4.1e9 / 75_000 / 50) == 1093 and round(4.1e9 / 75_000) == 54_667
    assert round(35 / 75 * 100) == 47 and round(35_000 / 13, -2) == 2_700
    assert (40 * 0.95, 40 * 1.05, 40 * 0.90, 40 * 1.10) == pytest.approx((38, 42, 36, 44))
    assert round(75_000 / (0.09 * 20_000)) == 42 and round(75_000 / (0.09 * 60_000)) == 14
    assert pct(trough(run(replace(P, churn=0.0), 75_000))) == 4.0
    assert pct(trough(run(replace(P, withdrawal=0.0), 75_000))) == 2.2
    assert pct(trough(run(replace(P, participation=0.03), 75_000, minutes=200))) == 2.6


def test_problem():
    assert 0.09 * 20_000 == 1_800 and round(0.03 * 1_800 / 100_000 * 100, 3) == 0.054
    depth = 100_000 * (0.1 + 0.9 * math.exp(-1.5))
    assert round(depth, -2) == 30_100 and 20_000 * (1 + 100 * 0.01) == 40_000
    assert round(math.log(90) / 150 * 100, 1) == 3.0
    assert 0.09 * 40_000 == 3_600 and round(0.03 * 3_600 / depth * 100, 2) == 0.36
    assert round(0.36 / 0.054, 1) == 6.7
    assert round(9.8 / 2.2, 1) == 4.5
    assert round(75_000 * 54_667 * (0.098 - 0.022) / 2 / 1e6) == 156
    assert round(75_000 * 54_667 * (0.098 - 0.070) / 2 / 1e6) == 57
    assert round(161.2 / 100, 2) == 1.61 and round(116.2 / 100, 2) == 1.16
    assert round(0.0225 * 100, 2) == 2.25          # 3% x 75,000 / 100,000: the no-feedback first-order fall
