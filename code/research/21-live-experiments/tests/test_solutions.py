"""Numbers gate: every numerical answer printed in Book 7, chapter 21 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "abtest"))
from firm_abtest import mde, power, sample_size, srm_pvalue
from rs_abtest import (
    EFFECT,
    ORDERS,
    SPILL,
    calibration,
    canary,
    days_needed,
    hook,
    peeking,
    rollout,
    simulated_power,
    stopping,
    world,
)


def r(x, d=2):
    return round(float(x), d)


def test_world_and_hook():
    w = world()
    assert (r(w["sd"], 1), r(w["mean"], 1), r(w["pre_sd"], 1)) == (23.1, 11.7, 6.9)
    assert (r(w["r2_pre"]), r(w["r2_both"]), r(100 * w["with_siblings"], 0)) == (0.09, 0.51, 88)
    assert r(rollout()) == -0.08 and r(EFFECT + SPILL * w["with_siblings"], 3) == r(rollout(), 3)
    d, se, nt, p = hook()
    assert (r(d), r(se), nt, r(p)) == (-0.55, 0.48, 2485, 0.07)
    assert (r(d - 1.959964 * se), r(d + 1.959964 * se)) == (-1.49, 0.39)
    assert r((nt - 2400) / math.sqrt(24000 * 0.1 * 0.9)) == 1.83 and r(srm_pvalue(nt, 24000 - nt, 0.1)) == 0.07


def test_designs_table():
    c = calibration()
    rows = [(r(m), r(s, 3), r(e, 3), r(d, 0)) for m, s, e, d in c.values()]
    assert rows == [(-0.30, 0.123, 0.122, 77), (-0.30, 0.119, 0.117, 72), (-0.30, 0.121, 0.116, 70),
                    (-0.29, 0.095, 0.085, 38), (-0.16, 0.656, 0.788, 3253), (-0.09, 0.235, 0.235, 290),
                    (-0.09, 0.188, 0.184, 178), (-0.08, 0.093, 0.082, 35)]
    se = c["by stock-day, within day + CUPED"][2]
    assert r(days_needed(se, effect=abs(rollout())), 0) == 503


def test_power_and_sequential():
    w = world()
    sd, sdc = w["sd"], w["sd"] * math.sqrt(1 - w["r2_both"])
    assert r(sdc, 1) == 16.2
    assert (r(sample_size(0.3, sd) / ORDERS, 1), r(sample_size(0.3, sdc) / ORDERS, 1)) == (77.7, 38.2)
    assert r(sample_size(0.3, sd), -2) == 186500
    assert simulated_power(80)[0] == 0.78 and simulated_power(40)[1] == 0.76
    pk = peeking(sdc, horizons=(1, 23, 38, 60, 120))
    assert [r(100 * pk[h][0], 0) for h in (1, 23, 38, 60, 120)] == [5, 25, 29, 33, 38]
    assert [round(4000 * pk[h][1]) for h in (38, 60, 120)] == [46, 62, 82]
    st = stopping(sdc)
    assert (np.median(st), r(100 * np.mean(st <= 10), 0), r(100 * np.mean(st <= 120), 0)) == (38.0, 4, 98)
    assert np.median(stopping(sdc, effect=1.0)) == 6.0
    assert (np.median(stopping(sdc, tau=0.1)), np.median(stopping(sdc, tau=1.0))) == (56.0, 44.0)


def test_exercises():
    assert r(mde(0.085)) == 0.24 and r(mde(1.0)) == 2.80
    assert r(power(0.3, 0.085)) == 0.94
    assert r(1 - 0.51, 2) == 0.49 and r(77 * 0.49, 0) == 38
    n1, d1 = canary(5.0, world()["sd"], 0.01)
    n10, d10 = canary(5.0, world()["sd"], 0.10)
    n50, d50 = canary(5.0, world()["sd"], 0.50)
    assert (r(n1, 0), r(d1, 1), r(n10, 0), r(d10), r(n50, 0), r(d50)) == (194, 8.1, 214, 0.89, 385, 0.32)
    assert r(-0.30 + 0.25 * 0.883, 3) == -0.079
    assert r(6.5 * 60 * d10, 0) == 348
    assert r(math.sqrt(24000 * 0.1 * 0.9), 1) == 46.5 and r((1 / 0.1 + 1 / 0.9) / 4, 1) == 2.8 and r(3253 / 77, 0) == 42 and 20 * 0.05 == 1.0
