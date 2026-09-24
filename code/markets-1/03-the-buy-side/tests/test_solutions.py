"""Numbers gate: every numerical answer printed in the Chapter 3 text and solutions."""
import math
import pathlib
import sys
from statistics import NormalDist

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from buyside import gross_nav, run_fees, years_to_significance

PATH = [0.20, -0.15, 0.10, 0.25, -0.05, 0.08, 0.30, -0.20, 0.15, 0.12]


def test_text():
    assert round(math.sqrt(40 * (0.01 * 0.25) ** 2) * 100, 1) == 1.6
    assert years_to_significance(0.5) == 16 and years_to_significance(0.25) == 64
    assert round(years_to_significance(8) * 252) == 16          # about three weeks
    assert 5.6 / 147 < 0.04


def test_exercises():
    a = np.array([9.1, 3.4, -6.2, 12.0]) - np.array([8.0, 4.0, -7.0, 10.5])      # 1
    assert a.mean() == pytest.approx(0.70) and round(a.std(ddof=1), 2) == 0.91
    assert round(a.mean() / a.std(ddof=1), 2) == 0.77
    assert 4 / 0.4**2 == pytest.approx(25) and round(4 / 1.5**2, 1) == 1.8        # 2
    assert 4 / 36 * 252 == pytest.approx(28)
    assert 50e9 * 0.0004 == pytest.approx(20e6)                                   # 3
    assert 2e9 * 0.02 + 0.2 * (2e9 * 0.10 - 2e9 * 0.02) == pytest.approx(72e6)
    assert 9.5 + 3 * 6 + 2 * 5.5 == 38.5                                          # 4
    assert round(9.5 * 1.3 / (100 + 9.5 * 0.3) * 100, 1) == 12.0
    assert math.sqrt(100 * (0.005 * 0.30) ** 2) == pytest.approx(0.015)           # 5
    assert 0.03 / math.sqrt(100) / 0.30 == pytest.approx(0.01)
    r = run_fees([0.30, -0.20, 0.10])                                             # 6
    assert [round(x * 100, 2) for x in r.mgmt_fees] == [2.0, 2.45, 1.91]
    assert [round(x * 100, 2) for x in r.perf_fees] == [5.6, 0.0, 0.0]
    assert [round(x * 100, 2) for x in r.nav[1:]] == [122.4, 95.47, 103.11]
    a, b = run_fees(PATH, 0.02, 0.20), run_fees(PATH, 0.01, 0.30)                 # 7
    assert round((sum(a.mgmt_fees) + sum(a.perf_fees)) * 100, 1) == 35.9
    assert round((sum(b.mgmt_fees) + sum(b.perf_fees)) * 100, 1) == 33.2
    assert round(a.nav[-1] * 100, 1) == 145.2 and round(b.nav[-1] * 100, 1) == 149.8
    z = NormalDist().inv_cdf(1 - 20 / 400)                                        # 8
    assert round(z * 4 / math.sqrt(5), 1) == 2.9 and round(z / math.sqrt(5), 2) == 0.74


def test_problem():
    r, g = run_fees(PATH), gross_nav(PATH)
    assert [round(r.mgmt_fees[i] * 100, 2) for i in range(3)] == [2.0, 2.29, 1.90]
    assert [round(r.perf_fees[i] * 100, 2) for i in range(3)] == [3.6, 0.0, 0.0]
    assert [round(r.nav[i] * 100, 2) for i in (1, 2, 3)] == [114.4, 94.95, 102.55]
    assert round(sum(r.mgmt_fees[:3]) * 100 + sum(r.perf_fees[:3]) * 100, 2) == 9.79       # 4
    assert [i + 1 for i, p in enumerate(r.perf_fees) if p > 0] == [1, 4, 7]                 # 5
    assert round(sum(r.mgmt_fees) * 100, 1) == 23.4 and round(sum(r.perf_fees) * 100, 1) == 12.4
    assert round(r.nav[-1] * 100, 1) == 145.2 and round((r.nav[-1] ** 0.1 - 1) * 100, 1) == 3.8
    assert round(g[-1] * 100, 1) == 192.8 and round((g[-1] ** 0.1 - 1) * 100, 1) == 6.8
    fees = (sum(r.mgmt_fees) + sum(r.perf_fees)) * 100
    assert round((g[-1] - 1) * 100 - fees - (r.nav[-1] - 1) * 100, 1) == 11.7               # 9
    assert round(fees / ((g[-1] - 1) * 100) * 100) == 39                                    # 10 / 19
    assert round((r.nav[-1] - 1) / (g[-1] - 1) * 100) == 49
    assert round(100 * 1.0595**10, 1) == 178.2                                              # 11
    assert np.mean(PATH) == pytest.approx(0.08) and round(0.08 / 0.17, 2) == 0.47           # 13
    assert round(4 / (0.08 / 0.17) ** 2) == 18
    assert round((r.high_water[8] / r.nav[8] - 1) * 100) == 28                              # 14
    assert run_fees([0.15]).perf_fees[0] == pytest.approx(0.026)                            # 16


def test_interview():
    assert 4 / 1**2 == 4                                          # iq 2
    assert round(3.24 / math.sqrt(3), 1) == 1.9                   # iq 6
