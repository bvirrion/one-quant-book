"""Acceptance tests of the Book 5, Chapter 20 build (FX volatility)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "fxsmile"))
from firm_fxsmile import gk
from firm_fxvol import (
    SLV,
    calibrate_leverage,
    one_touch_bs,
    one_touch_vv,
    simulate_slv,
    tarf_client_pnl,
    vv_implied,
    vv_price,
)

S, T, RD, RF = 1.10, 1.0, 0.04, 0.02
PILLARS = (1.02, 1.12, 1.24)


def test_vanna_volga_reproduces_pillars_and_flat_smile():
    vols = (0.105, 0.09, 0.10)
    for k, v in zip(PILLARS, vols, strict=True):
        assert abs(vv_implied(k, PILLARS, vols, S, T, RD, RF) - v) < 1e-8
    flat = (0.09, 0.09, 0.09)
    for k in (0.95, 1.1, 1.3):
        assert abs(vv_price(k, PILLARS, flat, S, T, RD, RF) - gk(S, k, T, RD, RF, 0.09)) < 1e-12
    assert abs(one_touch_vv(S, 1.25, T, RD, RF, PILLARS, flat) - one_touch_bs(S, 1.25, T, RD, RF, 0.09)) < 1e-9


def test_one_touch_against_simulation():
    rng = np.random.default_rng(2)
    n, steps, vol = 100_000, 2000, 0.1
    dt = T / steps
    x = np.full(n, math.log(S))
    hit = np.zeros(n, bool)
    for _ in range(steps):
        x += (RD - RF - 0.5 * vol * vol) * dt + vol * math.sqrt(dt) * rng.standard_normal(n)
        hit |= x >= math.log(1.25 * math.exp(-0.5826 * vol * math.sqrt(dt)))   # discrete paths, barrier moved in
    mc = math.exp(-RD * T) * hit.mean()
    assert abs(mc - one_touch_bs(S, 1.25, T, RD, RF, vol)) < 4 * math.sqrt(mc * (1 - mc) / n) + 1e-3


def test_slv_reduces_to_local_volatility():
    model = SLV(0.01, 1.5, 0.02, 0.4, -0.3, 0.0)                # no volatility of variance
    lev = calibrate_leverage(model, lambda t, s: np.full_like(s, 0.12), S, RD, RF, 0.5, n=20_000)
    p = simulate_slv(model, lev, S, RD, RF, 0.5, n=100_000)
    call = math.exp(-RD * 0.5) * np.maximum(p[:, -1] - S, 0).mean()
    assert abs(call - gk(S, S, 0.5, RD, RF, 0.12)) < 0.002
    assert abs(p[:, -1].mean() - S * math.exp((RD - RF) * 0.5)) < 0.002


def test_tarf_on_hand_paths():
    fx = np.array([[6.9, 6.9, 6.9, 6.9], [7.5, 7.5, 7.5, 7.5], [7.1, 7.6, 6.8, 6.8]])
    r = tarf_client_pnl(fx, 7.2, 0.5, notional=1.0)
    assert np.allclose(r["pnl"], [0.5, -2 * 0.3 * 4, 0.1 - 0.8 + 0.4])
    assert list(r["fixings"]) == [2, 4, 3] and list(r["redeemed"]) == [True, False, True]
