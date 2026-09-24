"""Numbers gate: every numerical answer printed in the Chapter 10 text and solutions."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from execq import EXCHANGE, RETAIL, max_payment, simulate, stats


def test_text():
    assert round(20.02 - 20.018, 3) == 0.002 and round(20.018 - 20.010, 3) == 0.008
    assert round(20.018 - 20.013, 3) == 0.005 and round(20.013 - 20.010, 3) == 0.003
    assert max_payment(1.0, RETAIL, 0.10) == pytest.approx(0.55) and 1 - 1.05 < 0
    s, p, m = simulate(RETAIL, 400_000, 10)
    assert round(stats(s, p, m[300.0])["realised"], 2) == 0.65 and round(stats(s, p, m[300.0])["impact"], 2) == 0.15
    s, p, m = simulate(EXCHANGE, 400_000, 11)
    assert abs(stats(s, p, m[300.0])["realised"]) < 0.06 and round(stats(s, p, m[300.0])["impact"], 2) in (1.04, 1.05)


def test_exercises():
    assert round(35.405 - 35.40, 3) == 0.005 and round(0.005 * 200, 2) == 1.0 and round(35.42 - 35.405, 3) == 0.015
    assert round(35.412 - 35.405, 3) == 0.007 and round(35.42 - 35.412, 3) == 0.008
    assert round(0.0018 * 60e6 * 252 / 1e6, 1) == 27.2 and round(0.0018 * 60e6 * 252 / 12e6, 2) == 2.27
    assert round(1.5 * 0.85 - 0.04 * 4 - 0.12, 3) == 0.995 and round(1.5 * 0.85 - 0.20 * 4 - 0.12, 3) == 0.355
    assert round((1.5 * 0.85 - 0.12) / 4 * 100, 1) == 28.9
    assert round(0.30 - 0.10, 2) == 0.20 and 1 / 0.002 == 500
    assert round(0.75 - 0.70, 2) == 0.05 and round(0.75 - 0.20, 2) == 0.55
    s, p, m = simulate(RETAIL, 10_000, 77)
    real = s * p - s * m[300.0]
    sd = real.std(ddof=1)
    assert round(sd, 1) == 6.1 and round(sd / np.sqrt(10_000), 3) == 0.061
    assert round((2 * sd / 0.09) ** 2, -3) == 18_000


def test_problem():
    h, imp, cost, pay, vol = 1.2, 0.06 * 3.5, 0.11, 0.30, 40e6
    assert imp == pytest.approx(0.21) and h * 0.8 == pytest.approx(0.96) and h * 0.8 - imp == pytest.approx(0.75)
    pm = h * 0.8 - imp - cost
    assert pm == pytest.approx(0.64)
    assert (h * 0.8 - imp) * vol / 100 == pytest.approx(300_000) and (pm - pay) * vol / 100 == pytest.approx(136_000)
    assert round((pm - pay) * vol / 100 * 252 / 1e6, 1) == 34.3
    assert round((1 - (pay + cost + imp) / h) * 100, 1) == 48.3
    assert round((1 - (pay + 0.06 + imp) / h) * 100, 1) == 52.5
    assert round((1 - (pay + cost + imp - 0.08) / h) * 100, 1) == 55.0
    imp2 = 0.25 * 6
    assert round(h * 0.8 - imp2, 2) == -0.54
    tox = h * 0.8 - imp2 - cost - pay
    assert round(0.85 * vol * (pm - pay) / 100 + 0.15 * vol * tox / 100) == 58_600
    assert round(3 * 0.8 - imp2, 2) == 0.90 and round(3 * 0.8 - imp2 - cost - pay, 2) == 0.49
    assert round(pay * vol / 100 * 252 / 1e6, 1) == 30.2 and round(0.2 * h * vol / 100 * 252 / 1e6, 1) == 24.2
