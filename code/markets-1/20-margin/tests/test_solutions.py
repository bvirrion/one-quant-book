"""Numbers gate: every numerical answer printed in the Chapter 20 text and solutions."""
import csv
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/margin"))
from firm_margin import Market, Params, Position, product_margin, risk_array
from margin_demo import peak_to_trough, with_floor

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/markets-1/20-margin"
P = Params(price_scan=345.0, vol_scan=0.04, multiplier=50.0, intermonth_charge=400.0, short_option_min=175.0)
MKT = Market({("ES", "Z"): 6000.0}, {("ES", "Z"): 0.18}, {("ES", "Z"): 0.25})
BOOK = [Position("ES", "Z", 2), Position("ES", "Z", -10, 5600.0, "P"), Position("ES", "Z", -10, 6400.0, "C")]


def col(name, key):
    with open(FIG / name) as f:
        return np.array([float(r[key]) for r in csv.DictReader(f)])


def test_text():
    arr = risk_array(Position("ES", "Z", 1), MKT, P)
    assert [round(x) for x in arr] == [0, 0, -5750, -5750, 5750, 5750, -11500, -11500, 11500, 11500,
                                       -17250, -17250, 17250, 17250, -15525, 15525]
    m = product_margin(BOOK, MKT, P)
    assert m.worst_scenario == 16 and round(m.total / 1e3, 1) == 107.8
    legs = [product_margin([b], MKT, P).total for b in BOOK]
    assert round(sum(legs) / 1e3) == 213 and round(m.total / 1e3) == 108
    hs, fhs, fl = (col("procyclical.csv", k) for k in ("hs", "fhs", "floored"))
    assert [round(peak_to_trough(x, 10) * 100) for x in (hs, fhs, fl)] == [109, 203, 94]
    assert round(fl[:300].mean(), 1) == 4.5 and round(fhs[:300].mean(), 1) == 3.0


def test_exercises():
    assert 44.25 * 50 * 25 == 55_312.5
    assert 120_000 - 5 * 3_200 == 104_000 < 5 * 21_000 and 5 * 23_100 - 104_000 == 11_500
    assert round((sum(product_margin([b], MKT, P).total for b in BOOK) - product_margin(BOOK, MKT, P).total) / 1e3, 1) == 105.5
    assert round(1 - 107.77 / 213.25, 2) == 0.49 and round(105_480 * 0.05) == 5_274
    assert round(2.1 * math.sqrt(2), 2) == 2.97 and round(2.1 * math.sqrt(5), 2) == 4.70
    fhs = col("procyclical.csv", "fhs")
    w = next(x / 100 for x in range(25, 80) if peak_to_trough(with_floor(fhs, 9.0, x / 100), 10) <= 0.5)
    assert w == 0.47 and round(with_floor(fhs, 9.0, w)[:300].mean(), 1) == 5.8


def test_problem():
    assert 400 * 3300 * 50 == 66_000_000 and 66e6 * 0.045 == pytest.approx(2.97e6)
    assert 400 * 50 * 800 == 16_000_000 and 400 * 2500 * 50 * 0.09 == pytest.approx(4.5e6)
    assert 4.5e6 - 2.97e6 == pytest.approx(1.53e6) and round(17.53 / 66 * 100, 1) == 26.6
    p1 = 2750 * 0.905
    assert p1 == pytest.approx(2488.75) and 400 * 50 * (2750 - p1) == pytest.approx(5_225_000)
    assert 400 * 50 * 2750 * 0.06 == pytest.approx(3_300_000)
    assert 400 * 50 * p1 * 0.075 - 3_300_000 == pytest.approx(433_125)
    assert 5_225_000 + 433_125 == 5_658_125
