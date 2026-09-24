"""Acceptance tests of the Book 5, Chapter 22 build (finite-difference engine and trinomial tree)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "barrier"))
from firm_barrier import barrier
from firm_bs import bs
from firm_fdpricer import american_put, solve, stretched_grid, trinomial, uniform_grid, value_at

S, K, T, R, Q, VOL = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2


def test_european_against_black_scholes():
    for grid in ("stretched", "uniform"):
        x = stretched_grid(S, K, VOL, T, 200) if grid == "stretched" else uniform_grid(S, VOL, T, 200)
        v = solve(lambda s: np.maximum(K - s, 0.0), x, T, R, Q, VOL, 200, smoothing=True,
                  lower=lambda tau, s: K * math.exp(-R * tau) - s, upper=lambda tau, s: 0.0)
        val, delta, _ = value_at(x, v, S)
        assert abs(val - bs(S, K, T, R, Q, VOL, "P")) < 1e-3
        d1 = (math.log(S / K) + (R + 0.5 * VOL * VOL) * T) / (VOL * math.sqrt(T))
        assert abs(delta - (0.5 * math.erfc(-d1 / math.sqrt(2)) - 1)) < 2e-3


def test_american_put_converges_at_second_order():
    ref = 6.0903534672
    errs = [abs(american_put(S, K, T, R, Q, VOL, m, m) - ref) for m in (50, 100, 200)]
    assert errs[0] > errs[1] > errs[2] and errs[2] < 1e-3
    assert errs[0] / errs[1] > 2.5 and errs[1] / errs[2] > 2.5
    assert american_put(S, K, T, R, Q, VOL, 200, 200) > bs(S, K, T, R, Q, VOL, "P")


def test_trinomial_converges():
    ref = 6.0903534672
    e1, e2 = abs(trinomial(S, K, T, R, Q, VOL, 200) - ref), abs(trinomial(S, K, T, R, Q, VOL, 800) - ref)
    assert e2 < e1 / 3
    assert abs(trinomial(S, K, T, R, Q, VOL, 800, american=False) - bs(S, K, T, R, Q, VOL, "P")) < 3e-3


def test_dividend_jump_condition_against_simulation():
    d, td = 3.0, 0.5
    x = stretched_grid(S, K, VOL, T, 300)
    v = solve(lambda s: np.maximum(K - s, 0.0), x, T, R, Q, VOL, 300, dividends=[(td, d)], smoothing=True,
              lower=lambda tau, s: K * math.exp(-R * tau) - s, upper=lambda tau, s: 0.0)
    fd = value_at(x, v, S)[0]
    rng = np.random.default_rng(1)
    z1, z2 = rng.standard_normal(400_000), rng.standard_normal(400_000)
    s_half = S * np.exp((R - 0.5 * VOL * VOL) * td + VOL * math.sqrt(td) * z1) - d
    s_end = np.maximum(s_half, 1e-8) * np.exp((R - 0.5 * VOL * VOL) * (T - td) + VOL * math.sqrt(T - td) * z2)
    pay = math.exp(-R * T) * np.maximum(K - s_end, 0.0)
    assert abs(fd - pay.mean()) < 4 * pay.std() / math.sqrt(len(pay)) + 2e-3


def test_barrier_on_a_node():
    x = stretched_grid(S, K, VOL, T, 200, lower=math.log(90.0))
    assert abs(x[0] - math.log(90.0)) < 1e-12
    v = solve(lambda s: np.maximum(s - K, 0.0), x, T, R, Q, VOL, 200, smoothing=True,
              lower=lambda tau, s: 0.0, upper=lambda tau, s: s - K * math.exp(-R * tau))
    assert abs(value_at(x, v, S)[0] - barrier(S, K, 90.0, T, R, Q, VOL, "down-out", "C")) < 1e-3
