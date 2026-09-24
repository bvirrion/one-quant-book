"""Book 4, chapter 21: high-frequency econometrics (teaching module).

A simulated stock: efficient log price with 25% annual volatility, traded every second at the bid or the ask
of a one-cent grid around a $36 price. The signature plot, noise-robust estimators, the Epps effect with
asynchronous trading, and jumps.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "hfvol"))
from firm_hfvol import (  # noqa: E402
    bipower,
    hayashi_yoshida,
    noise_variance,
    optimal_n,
    preaveraged,
    previous_tick,
    realised_kernel,
    refresh_times,
    roll_spread,
    rv,
    tsrv,
)

N = 23_400             # seconds in a 6.5-hour session
SIGMA = 0.25           # annual volatility of the efficient price
S0 = 36.0
TICK = 0.01
STEPS = (1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800)


def day(seed: int, sigma: float = SIGMA, s0: float = S0, tick: float = TICK, jump: float = 0.0) -> dict:
    """Efficient log price each second; trades at bid or ask (one-tick spread around the efficient price, floor to the
    grid); mid = bid + tick / 2."""
    rng = np.random.default_rng(seed)
    sd = sigma / math.sqrt(252)
    p = math.log(s0) + np.cumsum(sd / math.sqrt(N) * rng.standard_normal(N))
    if jump:
        p[N // 2:] += jump
    P = np.exp(p)
    bid = np.floor(P / tick) * tick
    buy = rng.random(N) < 0.5
    trade = np.where(buy, bid + tick, bid)
    return {"p": p, "trade": trade, "logtrade": np.log(trade), "logmid": np.log(bid + tick / 2), "iv": sd * sd,
            "side": np.where(buy, 1, -1)}


def ann(v: float) -> float:
    return math.sqrt(252 * v)


def signature(n_days: int = 30, steps=STEPS) -> dict:
    out = {s: [0.0, 0.0, 0.0] for s in steps}
    for k in range(n_days):
        d = day(k)
        for s in steps:
            out[s][0] += rv(d["logtrade"], s) / n_days
            out[s][1] += rv(d["logmid"], s) / n_days
            out[s][2] += rv(d["p"], s) / n_days
    return {s: tuple(ann(v) for v in vals) for s, vals in out.items()}


def estimators(n_days: int = 30) -> dict:
    """Average annualised volatility of each estimator on trade prices, with the day-to-day spread."""
    names = ("rv1", "rv300", "tsrv", "kernel", "preavg", "rv_opt")
    vals = {k: [] for k in names}
    noise, roll = [], []
    for k in range(n_days):
        d = day(k)
        x = d["logtrade"]
        om2 = noise_variance(x)
        noise.append(om2)
        roll.append(roll_spread(d["trade"]))
        nstar = optimal_n(d["iv"] ** 2, om2)
        vals["rv1"].append(rv(x))
        vals["rv300"].append(rv(x, 300))
        vals["tsrv"].append(tsrv(x, 300))
        vals["kernel"].append(realised_kernel(x, 60))
        vals["preavg"].append(preaveraged(x, 150))
        vals["rv_opt"].append(rv(x, max(1, round(N / nstar))))
    iv = day(0)["iv"]
    return {**{k: {"vol": ann(float(np.mean(v))), "sd_rel": float(np.std(np.array(v) / iv))} for k, v in vals.items()},
            "noise_var": float(np.mean(noise)), "noise_sd_bp": 1e4 * math.sqrt(float(np.mean(noise))),
            "roll": float(np.mean(roll)), "iv": iv}


def optimal_interval(n_days: int = 10) -> dict:
    """Bandi-Russell optimum with the true quarticity, using the noise variance a practitioner would estimate
    (RV of one-second returns over 2n) and the true one (variance of log trade price minus efficient log price)."""
    iv = (SIGMA / math.sqrt(252)) ** 2
    est, true, r1 = [], [], []
    for k in range(n_days):
        d = day(k)
        est.append(noise_variance(d["logtrade"]))
        true.append(float(np.var(d["logtrade"] - d["p"])))
        r1.append(rv(d["logtrade"]))
    om_est, om_true = float(np.mean(est)), float(np.mean(true))
    n_est, n_true = optimal_n(iv * iv, om_est), optimal_n(iv * iv, om_true)
    return {"n": n_est, "seconds": N / n_est, "seconds_true": N / n_true, "noise_to_signal": om_est / iv,
            "noise_sd_bp_est": 1e4 * math.sqrt(om_est), "noise_sd_bp_true": 1e4 * math.sqrt(om_true),
            "ratio_1s": float(np.mean(r1)) / iv, "vol_1s": ann(float(np.mean(r1))), "iv": iv, "omega2": om_est}


def mse_by_interval(n_days: int = 60, steps=STEPS) -> dict:
    """Root mean squared error of daily RV (relative to IV) against the sampling interval."""
    err = {s: [] for s in steps}
    for k in range(n_days):
        d = day(1000 + k)
        for s in steps:
            err[s].append(rv(d["logtrade"], s) / d["iv"] - 1)
    return {s: float(math.sqrt(np.mean(np.square(e)))) for s, e in err.items()}


# --- asynchronous trading and the Epps effect --------------------------------------------------------------

def two_assets(seed: int, rho: float = 0.6, rates=(1 / 5, 1 / 15)) -> dict:
    """Two efficient prices with correlation rho, each observed at its own Poisson trade times (no noise)."""
    rng = np.random.default_rng(seed)
    sd = SIGMA / math.sqrt(252) / math.sqrt(N)
    z1, z2 = rng.standard_normal(N), rng.standard_normal(N)
    p1 = np.cumsum(sd * z1)
    p2 = np.cumsum(sd * (rho * z1 + math.sqrt(1 - rho * rho) * z2))
    obs = []
    for p, lam in ((p1, rates[0]), (p2, rates[1])):
        t = np.flatnonzero(rng.random(N) < lam).astype(float)
        obs.append((t, p[t.astype(int)]))
    return {"p1": p1, "p2": p2, "obs": obs}


def epps(n_days: int = 40, steps=(1, 5, 10, 30, 60, 120, 300, 600, 1800), rho: float = 0.6) -> dict:
    corr = {s: [] for s in steps}
    hy, rt = [], []
    for k in range(n_days):
        a = two_assets(k, rho)
        (t1, x1), (t2, x2) = a["obs"]
        for s in steps:
            grid = np.arange(0, N, s)
            y1, y2 = np.diff(previous_tick(t1, x1, grid)), np.diff(previous_tick(t2, x2, grid))
            corr[s].append(float(y1 @ y2) / math.sqrt(float(y1 @ y1) * float(y2 @ y2)))
        c = hayashi_yoshida(t1, x1, t2, x2)
        v1, v2 = float(np.sum(np.diff(x1) ** 2)), float(np.sum(np.diff(x2) ** 2))
        hy.append(c / math.sqrt(v1 * v2))
        r = refresh_times(t1, t2)
        y1, y2 = np.diff(previous_tick(t1, x1, r)), np.diff(previous_tick(t2, x2, r))
        rt.append(float(y1 @ y2) / math.sqrt(float(y1 @ y1) * float(y2 @ y2)))
    return {"corr": {s: float(np.mean(v)) for s, v in corr.items()}, "hy": float(np.mean(hy)),
            "hy_sd": float(np.std(hy)),
            "refresh": float(np.mean(rt)), "rho": rho}


# --- jumps ----------------------------------------------------------------------------------------------

def jumps(n_days: int = 40, size: float = 0.01) -> dict:
    """RV and bipower variation of 5-minute efficient returns with and without a 1% jump at midday."""
    out = {"rv": [], "bv": [], "rv_j": [], "bv_j": []}
    for k in range(n_days):
        for tag, j in (("", 0.0), ("_j", size)):
            p = day(2000 + k, jump=j)["p"]
            out["rv" + tag].append(rv(p, 300))
            out["bv" + tag].append(bipower(p, 300))
    iv = (SIGMA / math.sqrt(252)) ** 2
    return {k: float(np.mean(v)) / iv for k, v in out.items()} | {"jump_share": size**2 / (iv + size**2)}
