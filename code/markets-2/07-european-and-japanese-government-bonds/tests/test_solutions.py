"""Numbers gate: every numerical answer printed in Book 2, Chapter 7 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from sovereign_demo import GILT, HOLDING, START, Y0, cushion_for_resilience, exhaustion_bp, fund, sales_to_relever

R = GILT.risk(Y0, START)
D, C = R["modified"], R["convexity"]


def test_text():
    assert (round(D, 1), round(C)) == (21.8, 589)
    assert round(D * D / (2 * C) * 100, 1) == 40.5
    assert round(exhaustion_bp()) == 351
    assert round(19.3, 1) == round(12.1 + 7.2, 1)
    assert round(fund(160)["cushion_pct"] * 100) == 43


def test_exercises():
    assert (round((3.633 - 3.18) * 100), round((3.986 - 3.18) * 100), round((4.00 - 3.18) * 100)) == (45, 81, 82)
    assert round(800 / 300, 2) == 2.67
    assert round(0.5 / D * 1e4) == 229
    assert round(D / C * 100, 1) == 3.7 and round(C / 2, 1) == 294.6
    assert D * D - 4 * (C / 2) * 0.5 < 0                                  # no real root
    assert round(sales_to_relever(100) / 1e6, 1) == 191.6 and round(sales_to_relever(160) / 1e6, 1) == 284.4
    assert round(fund(100)["value"] / 1e6, 1) == 808.4 and round(fund(160)["value"] / 1e6, 1) == 715.6
    assert round(cushion_for_resilience() * 100, 1) == 39.9


def test_problem():
    f0 = fund(0)
    assert round(f0["price0"], 2) == 63.41 and round(HOLDING / f0["price0"] * 100 / 1e9, 3) == 1.577
    dv01 = HOLDING * D * 1e-4
    assert round(D, 2) == 21.84 and round(dv01 / 1e6, 2) == 2.18 and round(dv01 / 5e8 * 100, 2) == 0.44
    assert round(5e6 / dv01, 1) == 2.3
    f1, f2 = fund(100), fund(160)
    assert (round(f1["cushion"] / 1e6, 1), round(f1["cushion_pct"] * 100), round(f1["leverage"], 2)) == (308.4, 62, 2.62)
    assert (round(f2["cushion"] / 1e6, 1), round(f2["cushion_pct"] * 100), round(f2["leverage"], 2)) == (215.6, 43, 3.32)
    assert round(cushion_for_resilience() * HOLDING / 1e6) == 399
    assert round((HOLDING - fund(100)["value"]) / HOLDING * 100, 1) == 19.2
    assert math.isfinite(exhaustion_bp())
