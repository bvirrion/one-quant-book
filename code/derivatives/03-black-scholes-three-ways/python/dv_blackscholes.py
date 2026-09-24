"""Black-Scholes three ways: the formula, the tree limit, Monte Carlo, and replication along a path
(Book 5, Chapter 3)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/bs"))
sys.path.insert(0, str(ROOT / "code/firm/binomial"))
from firm_binomial import price as tree_price  # noqa: E402
from firm_bs import black, bs, greeks, implied_vol, ncdf  # noqa: E402

CASE = {"spot": 100.0, "strike": 100.0, "t": 1.0, "r": 0.05, "q": 0.0, "vol": 0.20}


def d1d2(spot, strike, t, r, q, vol):
    s = vol * math.sqrt(t)
    d1 = (math.log(spot / strike) + (r - q) * t) / s + 0.5 * s
    return d1, d1 - s


def mc_price(n_paths: int, seed: int = 2026, c: dict = CASE, antithetic: bool = False) -> tuple[float, float]:
    """Monte Carlo under Q: exact lognormal terminal draw. Returns (estimate, standard error)."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n_paths)
    if antithetic:
        z = np.concatenate([z, -z])
    s_t = c["spot"] * np.exp((c["r"] - c["q"] - 0.5 * c["vol"] ** 2) * c["t"] + c["vol"] * math.sqrt(c["t"]) * z)
    pay = math.exp(-c["r"] * c["t"]) * np.maximum(s_t - c["strike"], 0.0)
    if antithetic:
        pay = 0.5 * (pay[: n_paths] + pay[n_paths:])
    return float(pay.mean()), float(pay.std(ddof=1) / math.sqrt(len(pay)))


def three_ways(c: dict = CASE) -> dict[str, float]:
    f = bs(c["spot"], c["strike"], c["t"], c["r"], c["q"], c["vol"], "C")
    tr = tree_price(c["spot"], c["strike"], c["t"], c["r"], c["vol"], 1000, "C", q=c["q"], method="crr")
    mc, se = mc_price(1_000_000, c=c)
    return {"formula": f, "tree": tr, "tree_err": tr - f, "mc": mc, "mc_se": se, "mc_err": mc - f}


def pde_residual(c: dict = CASE) -> float:
    """Theta + (r-q) S Delta + 1/2 sigma^2 S^2 Gamma - r V for the call: zero if the formula solves the PDE."""
    g = greeks(c["spot"], c["strike"], c["t"], c["r"], c["q"], c["vol"], "C")
    v = bs(c["spot"], c["strike"], c["t"], c["r"], c["q"], c["vol"], "C")
    s = c["spot"]
    return g["theta"] + (c["r"] - c["q"]) * s * g["delta"] + 0.5 * c["vol"] ** 2 * s * s * g["gamma"] - c["r"] * v


def replicate_path(seed: int = 11, steps: int = 252, mu: float = 0.12, c: dict = CASE):
    """Sell the call at the formula, delta-hedge daily along one real-world path (drift mu).
    Returns times, spot path, option values and replicating-portfolio values."""
    rng = np.random.default_rng(seed)
    dt = c["t"] / steps
    s = np.empty(steps + 1)
    s[0] = c["spot"]
    z = rng.standard_normal(steps)
    for i in range(steps):
        s[i + 1] = s[i] * math.exp((mu - 0.5 * c["vol"] ** 2) * dt + c["vol"] * math.sqrt(dt) * z[i])
    opt, port = np.empty(steps + 1), np.empty(steps + 1)
    opt[0] = port[0] = bs(s[0], c["strike"], c["t"], c["r"], c["q"], c["vol"], "C")
    delta = greeks(s[0], c["strike"], c["t"], c["r"], c["q"], c["vol"], "C")["delta"]
    cash = port[0] - delta * s[0]
    for i in range(1, steps + 1):
        cash *= math.exp(c["r"] * dt)
        port[i] = cash + delta * s[i]
        tau = c["t"] - i * dt
        alive = tau > 1e-12
        opt[i] = bs(s[i], c["strike"], tau, c["r"], c["q"], c["vol"], "C") if alive else max(s[i] - c["strike"], 0.0)
        if alive:
            new = greeks(s[i], c["strike"], tau, c["r"], c["q"], c["vol"], "C")["delta"]
            cash -= (new - delta) * s[i]
            delta = new
    return np.linspace(0, c["t"], steps + 1), s, opt, port


def problem() -> dict[str, float]:
    c = CASE
    d1, d2 = d1d2(c["spot"], c["strike"], c["t"], c["r"], c["q"], c["vol"])
    g = greeks(c["spot"], c["strike"], c["t"], c["r"], c["q"], c["vol"], "C")
    mu = 0.12
    d2_real = d1d2(c["spot"], c["strike"], c["t"], mu, c["q"], c["vol"])[1]
    out = {"d1": d1, "d2": d2, "nd1": ncdf(d1), "nd2": ncdf(d2), "p_real": ncdf(d2_real),
           "delta": g["delta"], "gamma": g["gamma"], "theta": g["theta"], "pde": pde_residual(),
           "put": bs(c["spot"], c["strike"], c["t"], c["r"], c["q"], c["vol"], "P"),
           "atm_approx": 0.4 * c["spot"] * c["vol"] * math.sqrt(c["t"]),
           "digital": math.exp(-c["r"] * c["t"]) * ncdf(d2)}
    t, s, opt, port = replicate_path()
    out["hedge_error"] = port[-1] - opt[-1]
    out["final_spot"] = s[-1]
    out.update(three_ways())
    out["mc_10k"], out["mc_10k_se"] = mc_price(10_000, seed=11)
    out["iv_10"] = implied_vol(10.0, c["spot"] * math.exp(c["r"]), 100.0, 1.0, math.exp(-c["r"]), "C")
    out["black_fut"] = black(80.0, 85.0, 0.25, 0.99, 0.35, "C")
    return out
