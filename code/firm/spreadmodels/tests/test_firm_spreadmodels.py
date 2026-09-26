import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_spreadmodels import (  # noqa: E402
    gm_path,
    gm_quotes,
    gm_update,
    inventory_quotes,
    kyle_one_period,
    kyle_simulate,
    pin,
    pin_fit,
    pin_loglik,
    roll_spread,
    simulate_days,
)


def test_glosten_milgrom():
    b, a = gm_quotes(0.5, 0.3)
    assert abs(a - 0.65) < 1e-12 and abs(b - 0.35) < 1e-12                  # spread = mu (v_high - v_low)
    d = gm_update(0.5, +1, 0.3)
    assert abs(d - a) < 1e-12                                               # the ask is the posterior after a buy
    p = gm_path(True, 0.3, 200, seed=3)
    assert p["delta"][-1] > 0.99 and (np.diff(p["ask"] - p["bid"])[50:] <= 1e-12).mean() > 0.5


def test_kyle():
    k = kyle_one_period(1.0, 2.0)
    assert (k["beta"], k["lambda"], k["posterior_var"], k["profit"]) == (2.0, 0.25, 0.5, 1.0)
    s = kyle_simulate(1.0, 2.0, 200_000, seed=5)
    assert abs(s["slope"] - 0.25) < 1e-9 and abs(s["posterior_var"] - 0.5) < 0.01 and abs(s["profit"] - 1.0) < 0.02


def test_inventory_and_roll():
    b, a = inventory_quotes(100.0, 0.0, 1.0, 0.1, 0.5, 1.0)
    assert abs((a - b) - 0.025) < 1e-12 and abs((a + b) / 2 - 100.0) < 1e-12
    b2, a2 = inventory_quotes(100.0, 2.0, 1.0, 0.1, 0.5, 1.0)
    assert a2 < 100.0 and abs((a2 + b2) / 2 - (100.0 - 0.05)) < 1e-12        # long inventory shades both quotes down
    rng = np.random.default_rng(1)
    v = np.cumsum(0.02 * rng.standard_normal(50_000))
    p = v + 0.5 * rng.choice([-1.0, 1.0], 50_000)                            # half-spread 0.5, random signs
    assert abs(roll_spread(p) - 1.0) < 0.03


def test_pin():
    th = (0.4, 0.5, 60.0, 100.0, 100.0)
    assert abs(pin(th) - 24 / 224) < 1e-12
    b, s = simulate_days(300, th, seed=7)
    f = pin_fit(b, s)
    assert abs(f["pin"] - pin(th)) < 0.02 and f["loglik"] >= pin_loglik(th, b, s) - 1e-6
