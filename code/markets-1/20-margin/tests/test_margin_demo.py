import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from margin_demo import ewma_vol, fhs_var, hs_var, peak_to_trough, simulate_returns, with_floor


def series():
    r = simulate_returns(900, 0.008, 0.035, 600, 25, 20)
    vol = ewma_vol(r)
    days = np.arange(300, 900)
    hs = np.array([hs_var(r, t, 250, 0.99, 2) for t in days])
    fhs = np.array([fhs_var(r, vol, t, 250, 0.99, 2) for t in days])
    return hs, fhs


def test_filtered_margin_reacts_faster_and_harder():
    hs, fhs = series()
    assert fhs[300:330].max() > hs[300:330].max()                 # days 600 to 630: the stress block
    assert peak_to_trough(fhs, 10) > peak_to_trough(hs, 10) > 0


def test_a_floor_damps_the_jump_and_costs_in_calm_times():
    _, fhs = series()
    floored = with_floor(fhs, 0.09, 0.25)
    assert peak_to_trough(floored, 10) < peak_to_trough(fhs, 10)
    assert floored[:250].mean() > fhs[:250].mean()


def test_ewma_uses_only_the_past():
    r = simulate_returns(200, 0.01, 0.01, 100, 1, 1)
    v1 = ewma_vol(r)
    r2 = r.copy()
    r2[150] = 0.5
    v2 = ewma_vol(r2)
    assert v1[150] == v2[150] and v2[151] > v1[151]
