"""Numbers gate: every numerical answer printed in Book 3, Chapter 9 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/cot"))
from firm_cot import crush_margin, limit_path, variable_limit
from m3_ags import cocoa_stats, mm_stats, monthly_mm_vs_maize, report_day

MS = mm_stats()
R = report_day()


def test_text():
    assert round(1.8 / 15.0 * 100, 1) == 12.0 and round(1.5 / 15.0 * 100, 1) == 10.0
    assert variable_limit(4.50) == (0.30, 0.45)
    assert MS["max"][0] == "2022-03-22" and round(MS["max"][1] * 100, 1) == 24.4
    assert MS["min"][0] == "2024-07-09" and round(MS["min"][1] * 100, 1) == -22.8
    assert MS["short_weeks"] == 300 and MS["n"] == 559
    assert MS["last"][0] == "2026-09-15" and round(MS["last"][1] * 100, 1) == 22.5 and round(MS["last"][2], 2) == 2.26
    x = monthly_mm_vs_maize()
    assert round(float(np.corrcoef([a for _, a, _ in x], [b for _, _, b in x])[0, 1]), 2) == 0.68
    c = cocoa_stats()
    assert round(c["mean_2022"]) == 2369 and c["peak"] == ("2025-01", 10710.35) and round(c["last"][1]) == 5619
    assert c["peak"][1] / c["mean_2022"] > 4


def test_exercises():
    assert round(1.2 / 14.8 * 100, 1) == 8.1
    assert variable_limit(4.00) == (0.30, 0.45) and variable_limit(6.00) == (0.40, 0.60)
    assert round(crush_margin(10.00, 300.0, 50.0), 2) == 2.10
    p = limit_path(4.50, 3.90, 0.30, 0.45)
    assert [d.locked for d in p[:2]] == [True, False] and round((4.50 - 3.90) * 5000) == 3000


def test_problem():
    assert R["limits"] == (0.3, 0.45) and [d.settle for d in R["path"][:3]] == [4.20, 3.75, 3.70]
    assert round(50 * 0.30 * 5000) == 75000 and round(50 * 0.45 * 5000) == 112500
    assert R["margin_per_contract"] == 3750 and R["margin_total"] == 187500 and round(R["loss_total"]) == 200000
