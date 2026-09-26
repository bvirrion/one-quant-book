"""Numbers gate: every numerical answer printed in Book 12, chapter 22 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import ml_e2e as m  # noqa: E402


def test_main():
    s = m.summary(m.results())
    got = {k: (round(s[k]["net"], 2), round(s[k]["net sd"], 2), round(s[k]["gross"], 2), round(s[k]["turnover"], 2))
           for k in m.METHODS}
    assert got == {"predict then optimise": (0.19, 0.09, 0.60, 2.95), "least squares, tradeable names": (1.52, 0.23, 1.92, 1.59),
                   "decision-focused": (1.51, 0.22, 1.92, 2.75), "parametric policy": (1.49, 0.23, 1.92, 2.90),
                   "true coefficients": (1.57, 0.24, 1.97, 1.50)}
    assert tuple(round(x, 2) for x in s["gap"]) == (1.33, 0.18)
    B = {k: np.mean([r[k]["b"][:2] for r in m.results()], 0) * 1e3 for k in m.METHODS}
    assert tuple(np.round(B["predict then optimise"], 2)) == (1.51, 0.43)
    assert round(B["least squares, tradeable names"][1], 2) == 0.83 and round(B["decision-focused"][1], 2) == 1.43
    r0 = m.results()[0]
    assert tuple(np.round(r0["decision-focused"]["b"][2:] * 1e3, 2)) == (-0.44, 0.20)
    assert tuple(np.round(r0["least squares, tradeable names"]["b"][2:] * 1e3, 2)) == (-0.22, 0.13)


def test_forecast_errors():
    e = {k: tuple(round(x, 3) for x in v) for k, v in m.forecast_errors().items()}
    assert e == {"all names": (9.007, 8.987), "tradeable names": (9.031, 8.962)}


def test_overfit():
    s = m.summary(m.overfit())
    got = {k: round(s[k]["net"], 2) for k in m.METHODS}
    assert got == {"predict then optimise": 0.09, "least squares, tradeable names": 1.04, "decision-focused": 0.89,
                   "parametric policy": 0.87, "true coefficients": 1.51}
    assert (round(s["decision-focused"]["turnover"], 2), round(s["least squares, tradeable names"]["turnover"], 2)) == (3.49,
                                                                                                                  1.88)


def test_exercises():
    assert round(20 * 0.03**2 / (20 * 0.03**2 + 2 * 0.0005), 3) == 0.947
    r = m.early_stopping()
    assert sum(1 for b, _ in r if b == 0) == 3 and round(float(np.mean([x for _, x in r])), 2) == 1.04
