"""Monte Carlo pricers in practice (Book 5, Chapter 23): Bermudan bounds for a three-asset max-call, the inner-path
bias of the dual bound, Greeks by pathwise, likelihood-ratio and adjoint methods, Heston by Euler and QE, and
quasi-random numbers with the Brownian bridge."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "heston", "jumps", "american", "mcpricer"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_american import bermudan_put  # noqa: E402
from firm_bs import greeks  # noqa: E402
from firm_heston import Heston  # noqa: E402
from firm_jumps import call_prices  # noqa: E402
from firm_mcpricer import (  # noqa: E402
    asian_adjoint,
    brownian_bridge,
    call_greeks,
    dual_upper,
    gbm_paths,
    halton,
    heston_terminal,
    lsm_fit,
    lsm_price,
    max_call_basis,
    norm_inv,
    small_basis,
)

# ---------------------------------------------------------------- the three-asset Bermudan max-call
S, K, T, R, Q, VOL = 100.0, 100.0, 3.0, 0.05, 0.10, 0.20
TIMES = np.arange(1, 10) / 3
EX = list(range(1, 10))
DT = 1 / 3
DISC = math.exp(-R * DT)
CORR = np.eye(3)


def payoff(s):
    return np.maximum(s.max(axis=1) - K, 0.0)


def step(s, n, rng):
    z = rng.standard_normal(s.shape)
    return s * np.exp((R - Q - 0.5 * VOL * VOL) * DT + VOL * math.sqrt(DT) * z)


@functools.cache
def bounds(n_inner: int = 1000) -> dict:
    train = gbm_paths([S] * 3, [VOL] * 3, CORR, TIMES, R, Q, 200_000, 1)
    test = gbm_paths([S] * 3, [VOL] * 3, CORR, TIMES, R, Q, 200_000, 2)
    outer = gbm_paths([S] * 3, [VOL] * 3, CORR, TIMES, R, Q, 1000, 3)
    out = {}
    for name, basis in (("full", max_call_basis), ("small", small_basis)):
        coefs = lsm_fit(train, EX, payoff, basis, K, DISC)
        lo = lsm_price(test, EX, coefs, payoff, basis, K, DISC)
        up = dual_upper(outer, EX, coefs, payoff, basis, K, DISC, step, n_inner, 4)
        out[name] = {"lower": lo, "upper": up, "gap": up[0] - lo[0]}
    return out


# ---------------------------------------------------------------- the inner-path bias, on a one-asset Bermudan put
@functools.cache
def put_bias(inners=(100, 400, 1600)) -> dict:
    s, k, t, r, v = 100.0, 100.0, 1.0, 0.05, 0.2
    times, ex, disc = np.arange(1, 11) / 10, list(range(1, 11)), math.exp(-0.05 * 0.1)

    def put(x):
        return np.maximum(k - x[:, 0], 0.0)

    def basis(x, kk):
        return np.column_stack([np.ones(len(x)), x[:, 0] / kk, (x[:, 0] / kk) ** 2, (x[:, 0] / kk) ** 3])

    def one_step(x, n, rng):
        return x * np.exp((r - 0.5 * v * v) * 0.1 + v * math.sqrt(0.1) * rng.standard_normal(x.shape))
    coefs = lsm_fit(gbm_paths([s], [v], [[1]], times, r, 0.0, 100_000, 1), ex, put, basis, k, disc)
    lo = lsm_price(gbm_paths([s], [v], [[1]], times, r, 0.0, 100_000, 2), ex, coefs, put, basis, k, disc)
    outer = gbm_paths([s], [v], [[1]], times, r, 0.0, 1000, 3)
    ups = {n: dual_upper(outer, ex, coefs, put, basis, k, disc, one_step, n, 4) for n in inners}
    return {"tree": bermudan_put(s, k, t, r, v, 10), "lower": lo, "upper": ups}


# ---------------------------------------------------------------- Greeks
def greek_table(n: int = 200_000) -> dict:
    exact = greeks(100.0, 100.0, 1.0, 0.05, 0.0, 0.2, "C")
    d2 = (math.log(1.0) + (0.05 - 0.02)) / 0.2

    def dig(s, v):
        z = (math.log(s / 100) + (0.05 - 0.5 * v * v)) / v
        return math.exp(-0.05) * 0.5 * math.erfc(-z / math.sqrt(2))
    return {"call": call_greeks(100.0, 100.0, 1.0, 0.05, 0.2, n, 5),
            "digital": call_greeks(100.0, 100.0, 1.0, 0.05, 0.2, n, 5, digital=True),
            "digital_smooth": call_greeks(100.0, 100.0, 1.0, 0.05, 0.2, n, 5, digital=True, smooth=1.0),
            "exact_call": (exact["delta"], exact["vega"]),
            "exact_digital": ((dig(100.01, 0.2) - dig(99.99, 0.2)) / 0.02,
                              (dig(100, 0.2001) - dig(100, 0.1999)) / 0.0002),
            "d2": d2}


@functools.cache
def adjoint() -> dict:
    a = asian_adjoint(100.0, 100.0, 1.0, 0.05, 0.2, 48, 12, 100_000, 6)
    # check the first bucket by bumping with the same draws
    def bumped(h):
        n, steps, dt = 100_000, 48, 1 / 48
        z = np.random.default_rng(6).standard_normal((n, steps))
        sig = np.full(steps, 0.2)
        sig[:4] *= 1 + h
        s, tot = np.full(n, 100.0), np.zeros(n)
        for i in range(steps):
            s = s * np.exp((0.05 - 0.5 * sig[i] ** 2) * dt + sig[i] * math.sqrt(dt) * z[:, i])
            tot += s
        return math.exp(-0.05) * np.maximum(tot / steps - 100, 0).mean()
    a["bump_first"] = (bumped(1e-4) - bumped(-1e-4)) / (2e-4 * 0.2)
    return a


# ---------------------------------------------------------------- Heston: Euler against QE
@functools.cache
def heston_bias(steps_list=(4, 8, 16, 32), n: int = 400_000) -> dict:
    m = Heston(0.04, 1.5, 0.04, 0.6, -0.7)
    exact = float(call_prices(m, 100.0, [100.0], 1.0)[0])
    rows = {}
    for steps in steps_list:
        e = heston_terminal(0.04, 1.5, 0.04, 0.6, -0.7, 100.0, 1.0, steps, n, 7, scheme="euler")
        q = heston_terminal(0.04, 1.5, 0.04, 0.6, -0.7, 100.0, 1.0, steps, n, 7, scheme="qe")
        pe, pq = np.maximum(e - 100, 0), np.maximum(q - 100, 0)
        rows[steps] = {"euler": float(pe.mean()) - exact, "qe": float(pq.mean()) - exact,
                       "se": float(pq.std() / math.sqrt(n))}
    return {"exact": exact, "rows": rows}


# ---------------------------------------------------------------- quasi-random numbers
def asian_estimate(z: np.ndarray, bridge: bool, steps: int = 16) -> float:
    dw = brownian_bridge(z, 1.0) if bridge else z * math.sqrt(1.0 / steps)
    logs = math.log(100.0) + np.cumsum((0.05 - 0.02) / steps + 0.2 * dw, axis=1)
    return math.exp(-0.05) * float(np.maximum(np.exp(logs).mean(axis=1) - 100.0, 0).mean())


@functools.cache
def qmc_study(sizes=(256, 1024, 4096), reps: int = 20) -> dict:
    """Error (standard deviation over random shifts) of a 16-date Asian call with Halton points, with and without the
    Brownian bridge, against plain Monte Carlo's standard error at the same number of paths."""
    big = np.random.default_rng(99).standard_normal((400_000, 16))
    pay = math.exp(-0.05) * np.maximum(np.exp(math.log(100.0) + np.cumsum((0.05 - 0.02) / 16 + 0.2 * big * 0.25,
                                                                               axis=1)).mean(axis=1) - 100, 0)
    sd = float(pay.std())
    rng = np.random.default_rng(1)
    out = {}
    for n in sizes:
        hb, hn = [], []
        for _ in range(reps):
            z = norm_inv(halton(n, 16, rng.uniform(size=16)))
            hb.append(asian_estimate(z, True))
            hn.append(asian_estimate(z, False))
        out[n] = {"mc": sd / math.sqrt(n), "halton": float(np.std(hn)), "bridge": float(np.std(hb))}
    return out


# ---------------------------------------------------------------- exercise 7 and the European max-call
@functools.cache
def in_sample(n_train: int = 2_000, reps: int = 40) -> dict:
    """Fit and price on the same paths against pricing the same policy on independent paths (rich basis), averaged
    over `reps` small training sets so that the in-sample bias shows above the noise; and the European max-call."""
    test = gbm_paths([S] * 3, [VOL] * 3, CORR, TIMES, R, Q, 100_000, 2)
    same, fresh = [], []
    for rep in range(reps):
        train = gbm_paths([S] * 3, [VOL] * 3, CORR, TIMES, R, Q, n_train, 100 + rep)
        coefs = lsm_fit(train, EX, payoff, max_call_basis, K, DISC)
        same.append(lsm_price(train, EX, coefs, payoff, max_call_basis, K, DISC)[0])
        fresh.append(lsm_price(test, EX, coefs, payoff, max_call_basis, K, DISC)[0])
    diff = np.array(same) - np.array(fresh)
    euro = math.exp(-R * T) * payoff(test[:, -1, :])
    return {"same": float(np.mean(same)), "fresh": float(np.mean(fresh)),
            "diff": (float(diff.mean()), float(diff.std() / math.sqrt(reps))),
            "european": (float(euro.mean()), float(euro.std() / math.sqrt(len(euro))))}
