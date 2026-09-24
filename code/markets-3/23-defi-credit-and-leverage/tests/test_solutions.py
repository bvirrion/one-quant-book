"""Numbers in the solutions of Book 3, Chapter 23."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_defi as m


def smallest_paying(**kw):
    return next(k / 100 for k in range(100, 6_000) if m.pump_attack(k / 100, **kw) > 0)


def test_exercises():
    assert round(100 * m.MODEL.borrow_rate(0.5), 2) == 2.22 and round(100 * m.MODEL.borrow_rate(0.5) * 0.5 * 0.9, 2) == 1.0
    assert round(100 * m.MODEL.borrow_rate(0.95), 2) == 34.0 and round(100 * m.MODEL.borrow_rate(0.95) * 0.95 * 0.9, 2) == 29.07
    assert round(100_000 / (50 * 0.825), 2) == 2_424.24
    assert round(50_000 / 2_500 * 1.05, 2) == 21.0
    assert round(0.825 * 1.1, 4) == 0.9075
    assert (smallest_paying(), smallest_paying(residual=1.0)) == (1.93, 1.72)


def test_problem():
    assert 0.6 * 5e6 == 3e6
    assert round(m.pump_needed(50e6, 5e6, 0.6), 2) == 16.67
    assert round(m.pump_attack(50 / 3) / 1e6, 2) == 38.84 and round(m.pump_attack(50 / 3, residual=1.0) / 1e6, 2) == 40.35
    assert max(m.pump_attack(k / 10, depth_usd=20e6, depth_tokens=20e6) for k in range(10, 600)) < 0
    assert round(m.pump_needed(50e6, 5e6, 0.3), 2) == 33.33 and smallest_paying(ltv=0.3) == 4.98

    def best(cap):
        return max(min(cap, 3e6 * k / 10) - 5e6 - 2e6 * (math.sqrt(k / 10) - 1) for k in range(10, 2_000))
    assert best(5.8e6) <= 0 < best(5.9e6)
