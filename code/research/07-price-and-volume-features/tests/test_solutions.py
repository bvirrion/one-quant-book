"""Numbers gate: every numerical answer printed in Book 7, chapter 7 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_features import crossover_filter, half_life, ic_by_horizon, ic_table, lag_profile, range_race


def r(x, d=4):
    return round(float(x), d)


def test_ic_table():
    t = ic_table()
    printed = {
        "reversal 1d": [(0.0378, 16.2), (0.0150, 3.0), (-0.0058, -0.6)],
        "reversal 5d": [(0.0176, 8.1), (0.0085, 1.8), (-0.0162, -1.8)],
        "reversal 21d": [(0.0022, 1.0), (-0.0117, -2.6), (-0.0285, -2.9)],
        "momentum 12-1": [(0.0076, 1.4), (0.0167, 1.4), (0.0296, 1.2)],
        "momentum 12": [(0.0059, 1.1), (0.0177, 1.5), (0.0340, 1.4)],
        "momentum 6-1": [(0.0067, 1.8), (0.0140, 1.7), (0.0285, 1.6)],
        "low volatility": [(-0.0034, -2.5), (-0.0033, -1.1), (-0.0023, -0.5)],
        "volume surprise": [(0.0009, 1.3), (-0.0007, -0.5), (-0.0008, -0.3)],
        "Amihud illiquidity": [(-0.0004, -0.3), (-0.0023, -0.7), (-0.0055, -0.8)],
        "low turnover": [(0.0011, 1.5), (0.0026, 1.7), (0.0049, 1.7)],
        "crossover 5/20": [(0.0027, 1.2), (0.0133, 2.9), (0.0218, 2.4)],
        "crossover 50/200": [(0.0084, 2.0), (0.0173, 1.9), (0.0324, 1.7)],
    }
    for name, row in printed.items():
        got = [(r(t[name][h][0]), r(t[name][h][1], 1)) for h in (1, 5, 21)]
        assert got == row, name


def test_horizon_and_card():
    m = ic_by_horizon("momentum 12-1")
    assert 0.03 < m[63] < 0.045 and ic_by_horizon("reversal 1d")[10] < 0.01
    lp = lag_profile("momentum 12-1", (1, 21, 42, 63, 126, 189, 252))
    assert r(lp[1]) == 0.0076 and 0.0035 <= lp[126] <= 0.0045 and round(half_life(lp)) == 260


def test_race():
    base, drift, gaps = range_race(), range_race(drift=0.005), range_race(gap_share=0.3)
    assert [r(base[k]["efficiency"], 1) for k in ("Parkinson", "Garman-Klass", "Rogers-Satchell", "Yang-Zhang (20 days)")] == [
        5.2, 7.6, 5.7, 7.5]
    assert [r(base[k]["bias"], 2) for k in ("Parkinson", "Garman-Klass", "Rogers-Satchell", "Yang-Zhang (20 days)")] == [
        0.92, 0.90, 0.90, 0.91]
    assert (r(drift["close-to-close"]["bias"], 2), r(drift["Parkinson"]["bias"], 2), r(drift["Rogers-Satchell"]["bias"], 2)) == (
        1.25, 1.02, 0.90)
    assert (r(gaps["Parkinson"]["bias"], 2), r(gaps["Garman-Klass"]["bias"], 2), r(gaps["Rogers-Satchell"]["bias"], 2)) == (
        0.64, 0.63, 0.63)
    assert r(gaps["Yang-Zhang (20 days)"]["bias"], 2) == 0.93
    thin = range_race(steps=30)
    assert (r(thin["Parkinson"]["bias"], 2), r(thin["Garman-Klass"]["bias"], 2), r(thin["Rogers-Satchell"]["bias"], 2)) == (
        0.78, 0.70, 0.70)


def test_exercises_and_filter():
    assert r(math.sqrt(math.log(51.2 / 49.8) ** 2 / (4 * math.log(2))) * 100, 2) == 1.67
    assert (r(100 * (1.02 * 0.99 * 1.04 - 1), 2), r(100 * (1.02 * 0.99 * 1.04 * 1.03 - 1), 2)) == (5.02, 8.17)
    assert (r(1.2 / 40, 3), r(2.5 / 2, 2)) == (0.03, 1.25)
    w = crossover_filter(3, 6)
    assert [r(x, 4) for x in w] == [0.1667, 0.3333, 0.5, 0.3333, 0.1667] and r(w.sum(), 2) == 1.5
    assert r(crossover_filter(5, 20).sum(), 2) == 7.5 and r(crossover_filter(10, 50).sum(), 1) == 20.0
    assert r(60 / 5.2, 1) == 11.5 and r((math.sqrt(11) * 0.03 - 0.03) / math.sqrt(12), 3) == 0.020
    assert r(0.34 / (1.34 + 21 / 19), 3) == 0.139
