"""Numbers gate: every numerical answer printed in Book 5, Chapter 7 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_surface import (
    RATE,
    black,
    check,
    crash_probability,
    density,
    forward,
    index_surface,
    ncdf,
    regimes,
    skew_90_110,
    smile_vol,
)

T = 91 / 365
F = forward(T)
C = crash_probability()
R = regimes()


def test_text():
    assert (round(100 * smile_vol(math.log(90 / F), T), 2), round(100 * smile_vol(math.log(110 / F), T), 2)) == (20.47, 14.19)
    assert round(100 * smile_vol(math.log(80 / F), T)) == 27 and round(100 * smile_vol(0, T)) == 16
    assert (round(100 * C["flat"], 2), round(100 * C["skewed"], 2), round(C["ratio"])) == (0.31, 1.89, 6)
    assert round(1 / C["flat"]) in range(300, 340) and round(1 / C["skewed"]) in range(50, 56)
    sk = {d: round(100 * skew_90_110(d / 365), 1) for d in (30, 91, 365, 730)}
    assert sk == {30: 10.8, 91: 6.3, 365: 3.3, 730: 2.5}
    assert (round(R["put_sticky_strike"], 2), round(R["put_sticky_delta"], 2), round(R["put_before"], 2)) == (6.00, 5.78, 3.08)
    assert (round(100 * R["atm_sticky_strike"], 1), round(100 * R["atm_before"], 1), round(0.95 * F, 1)) == (18.1, 16.4, 95.4)
    assert check(index_surface())["butterfly"] == 0 and check(index_surface())["calendar"] == 0
    bad = check(index_surface((1, -0.1, 0.03)))
    assert bad["butterfly"] == 6 and round(bad["worst"], 2) == -2.06
    assert check(index_surface((2, 0.0, -0.07)))["calendar"] == 1
    assert (round(F, 2), round(100 * C["atm"], 2), round(100 * C["vol_at_80"], 1)) == (100.37, 16.36, 26.8)
    df = math.exp(-RATE * T)
    assert round(black(F, 80, T, df, C["atm"], "P"), 3) == 0.006 and round(black(F, 80, T, df, C["vol_at_80"], "P"), 3) == 0.219
    peak = max(density(), key=lambda x: x[1])[0]
    assert peak > F


def test_exercises():
    assert (round(math.log(90 / F), 4), round(0.2047 ** 2 * T, 4)) == (-0.1091, 0.0104)
    assert (round(0.2 ** 2 * 0.25, 4), round(0.13 ** 2 * 0.5, 4)) == (0.0100, 0.0085)
    from firm_bs import greeks
    vol = smile_vol(math.log(100 / F), T)
    g = greeks(100, 100, T, RATE, 0.015, vol, "C")
    slope = (smile_vol(math.log(100 / F) + 1e-5, T) - smile_vol(math.log(100 / F) - 1e-5, T)) / 2e-5 / 100
    d2 = (math.log(F / 100) - 0.5 * vol * vol * T) / (vol * math.sqrt(T))
    assert (round(g["vega"], 2), round(slope, 4)) == (19.77, -0.0031)
    assert round(math.exp(-RATE * T) * ncdf(d2), 4) == 0.4980
    assert round(math.exp(-RATE * T) * ncdf(d2) - g["vega"] * slope, 4) == 0.5584
    assert (round(g["delta"], 3), round(g["delta"] - g["vega"] * slope, 3)) == (0.533, 0.593)
    assert check(index_surface((2, 0.0, -0.06)))["calendar"] == 0 and check(index_surface((2, 0.0, -0.065)))["calendar"] == 1
    assert check(index_surface((2, 0.0, -0.08)))["calendar"] == 3


def test_problem():
    assert round(math.exp(-RATE * T), 5) == 0.99255 and round(100 * C["vol_at_80"], 2) == 26.78
    assert round(math.log(80 / F), 4) == -0.2269
    assert round(100 * smile_vol(math.log(80 / (0.95 * F)), T), 1) == 23.8
    assert round(4 * 0.219, 2) == 0.88
