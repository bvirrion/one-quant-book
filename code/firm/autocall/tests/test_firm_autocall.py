"""Acceptance tests of the Book 5, Chapter 18 build (autocallables)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_autocall import TermSheet, hedge_across_ki, price, snowball_tail


def flat(v):
    return lambda t, s: np.full_like(s, v)


OBS = tuple(np.arange(1, 5) / 4)


def test_deterministic_limits():
    ts = TermSheet(OBS, trigger=0.999, coupon=2.0, coupon_barrier=0.7)       # no volatility: called at once
    r = price(ts, flat(1e-8), n_paths=2000)
    assert abs(r["price"] - 102.0) < 1e-6 and abs(r["call_probs"][0] - 1.0) < 1e-12
    never = TermSheet(OBS, trigger=1e9, coupon=2.0, coupon_barrier=0.0, protection=0.0)
    assert abs(price(never, flat(0.3), n_paths=20_000)["price"] - 108.0) < 1e-9


def test_protection_and_monitoring():
    eur = TermSheet(OBS, trigger=1e9, protection=0.7, ki_daily=False)
    day = TermSheet(OBS, trigger=1e9, protection=0.7, ki_daily=True)
    pe, pd = price(eur, flat(0.3), n_paths=50_000), price(day, flat(0.3), n_paths=50_000)
    assert pd["ki_prob"] > pe["ki_prob"] and pd["price"] < pe["price"] < 100.0


def test_worst_of_reduces_to_single():
    ts = TermSheet(OBS, trigger=1.0, coupon=1.0, protection=0.6)
    single = price(ts, flat(0.25), n_paths=40_000, seed=3)
    corr = np.full((3, 3), 0.999999) + 0.000001 * np.eye(3)
    wo = price(ts, flat(0.25), n_paths=40_000, seed=3, corr=corr, n_assets=3)
    assert abs(single["price"] - wo["price"]) < 0.05


def test_snowball_tail_and_cliff():
    s, tau, vol = 0.80, 1 / 12, 0.25
    rng = np.random.default_rng(1)
    n, steps = 200_000, 21
    x = np.full(n, math.log(s))
    mn = np.full(n, s)
    for _ in range(steps):
        x += -0.5 * vol * vol * tau / steps + vol * math.sqrt(tau / steps) * rng.standard_normal(n)
        mn = np.minimum(mn, np.exp(x))
    pay = np.where(mn < 0.75, 100 * np.minimum(np.exp(x), 1), 130.0)
    assert abs(pay.mean() - snowball_tail(s, 0.75, tau, vol, 30.0, False)) < 4 * pay.std() / math.sqrt(n) + 0.1
    one, twelve = hedge_across_ki(0.75, 1 / 12, vol, 30.0), hedge_across_ki(0.75, 1.0, vol, 30.0)
    assert abs(one["delta_after"] - 1.0) < 1e-3 and one["sold"] > twelve["sold"] > 0
