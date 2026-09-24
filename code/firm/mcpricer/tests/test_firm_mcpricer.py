"""Acceptance tests of the Book 5, Chapter 23 build (Monte Carlo engine)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "american"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "bs"))
from firm_american import bermudan_put
from firm_bs import greeks
from firm_mcpricer import (
    asian_adjoint,
    brownian_bridge,
    call_greeks,
    dual_upper,
    gbm_paths,
    halton,
    heston_terminal,
    lsm_fit,
    lsm_price,
    norm_inv,
)

TIMES, EX, DISC = np.arange(1, 11) / 10, list(range(1, 11)), math.exp(-0.05 * 0.1)


def put(x):
    return np.maximum(100.0 - x[:, 0], 0.0)


def basis(x, k):
    return np.column_stack([np.ones(len(x)), x[:, 0] / k, (x[:, 0] / k) ** 2])


def test_bermudan_bounds_bracket_the_tree():
    coefs = lsm_fit(gbm_paths([100.0], [0.2], [[1]], TIMES, 0.05, 0.0, 50_000, 1), EX, put, basis, 100.0, DISC)
    lo, se = lsm_price(gbm_paths([100.0], [0.2], [[1]], TIMES, 0.05, 0.0, 50_000, 2), EX, coefs, put, basis, 100.0, DISC)
    tree = bermudan_put(100.0, 100.0, 1.0, 0.05, 0.2, 10)
    assert lo < tree + 3 * se

    def step(x, n, rng):
        return x * np.exp((0.05 - 0.02) * 0.1 + 0.2 * math.sqrt(0.1) * rng.standard_normal(x.shape))
    outer = gbm_paths([100.0], [0.2], [[1]], TIMES, 0.05, 0.0, 400, 3)
    up_small = dual_upper(outer, EX, coefs, put, basis, 100.0, DISC, step, 100, 4)[0]
    up_big = dual_upper(outer, EX, coefs, put, basis, 100.0, DISC, step, 800, 4)[0]
    assert up_big > tree - 0.03 and up_small > up_big


def test_greeks():
    g = greeks(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, "C")
    c = call_greeks(100.0, 100.0, 1.0, 0.05, 0.2, 200_000, 1)
    for key, exact in (("pw_delta", g["delta"]), ("lr_delta", g["delta"]), ("pw_vega", g["vega"]), ("lr_vega", g["vega"])):
        assert abs(c[key][0] - exact) < 4 * c[key][1]
    assert c["pw_delta"][1] < c["lr_delta"][1]
    d = call_greeks(100.0, 100.0, 1.0, 0.05, 0.2, 10_000, 1, digital=True)
    assert d["pw_delta"][0] == 0.0 and d["lr_delta"][0] > 0


def test_adjoint_matches_bumping():
    a = asian_adjoint(100.0, 100.0, 1.0, 0.05, 0.2, 12, 3, 20_000, 2)
    # the sum of bucket vegas is the parallel vega; check it against a bump with the same draws
    def price(vol):
        return asian_adjoint(100.0, 100.0, 1.0, 0.05, vol, 12, 3, 20_000, 2)["price"]
    parallel = (price(0.2 + 1e-5) - price(0.2 - 1e-5)) / 2e-5
    assert abs(a["bucket_vega"].sum() - parallel) < 1e-3
    delta = (asian_adjoint(100.0 + 1e-4, 100.0, 1.0, 0.05, 0.2, 12, 3, 20_000, 2)["price"]
             - asian_adjoint(100.0 - 1e-4, 100.0, 1.0, 0.05, 0.2, 12, 3, 20_000, 2)["price"]) / 2e-4
    assert abs(a["delta"] - delta) < 1e-4


def test_heston_qe_is_close_to_the_fourier_price():
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "jumps"))
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "heston"))
    from firm_heston import Heston
    from firm_jumps import call_prices
    exact = float(call_prices(Heston(0.04, 1.5, 0.04, 0.6, -0.7), 100.0, [100.0], 1.0)[0])
    st = heston_terminal(0.04, 1.5, 0.04, 0.6, -0.7, 100.0, 1.0, 8, 200_000, 3)
    pay = np.maximum(st - 100.0, 0.0)
    assert abs(pay.mean() - exact) < 4 * pay.std() / math.sqrt(len(pay))


def test_halton_bridge_and_inverse_normal():
    h = halton(8, 2)
    assert np.allclose(h[:4, 0], [0.5, 0.25, 0.75, 0.125]) and np.allclose(h[:3, 1], [1 / 3, 2 / 3, 1 / 9])
    u = np.array([0.001, 0.2, 0.5, 0.975])
    x = norm_inv(u)
    assert np.allclose([0.5 * (1 + math.erf(v / math.sqrt(2))) for v in x], u, atol=1e-12) and x[2] == 0.0
    z = np.random.default_rng(1).standard_normal((200_000, 8))
    dw = brownian_bridge(z, 2.0)
    assert np.allclose(dw.var(axis=0), 0.25, atol=0.005) and abs(dw.sum(axis=1).var() - 2.0) < 0.02
