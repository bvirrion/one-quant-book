"""Asians, lookbacks, cliquets and forward starts (Book 5, Chapter 16): where the Asian discount comes from,
the geometric control variate, discrete lookbacks, and forward smiles and cliquets under local volatility and
Heston fitted to the same surface (chapter 9's market; chapters 9 and 10's calibrations). Zero rates for the
model comparisons; r = 3%, q = 1% for the Black-Scholes examples."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "localvol", "heston", "pathdep"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
for ch in ("09-local-volatility", "10-stochastic-volatility"):
    sys.path.insert(0, str(ROOT / f"code/derivatives/{ch}/python"))
from dv_heston import calibration  # noqa: E402
from dv_localvol import grid as lv_grid  # noqa: E402
from firm_bs import bs, implied_vol  # noqa: E402
from firm_heston import simulate_paths  # noqa: E402
from firm_localvol import simulate as lv_simulate  # noqa: E402
from firm_pathdep import (  # noqa: E402
    asian_mc,
    asian_payoff,
    cliquet_payoff,
    forward_smile_from_paths,
    gbm_paths,
    lookback_floating_call,
    lookback_payoff,
    lookback_shifted,
    reverse_cliquet_payoff,
)
from firm_svi import ssvi  # noqa: E402

S, R, Q, VOL, T = 100.0, 0.03, 0.01, 0.20, 1.0


# ---------------------------------------------------------------- Asians
def asian_example(n: int = 12) -> dict:
    out = asian_mc(S, 100.0, T, R, Q, VOL, n)
    out["vanilla"] = bs(S, 100.0, T, R, Q, VOL, "C")
    out["discount"] = 1 - out["cv"] / out["vanilla"]
    out["var_factor"] = (n + 1) * (2 * n + 1) / (6 * n * n)
    out["reduction"] = (out["plain_se"] / out["cv_se"]) ** 2
    return out


def asian_by_fixings(ns=(1, 2, 4, 12, 52, 252)) -> list[tuple[int, float, float]]:
    """(n, Asian / vanilla, volatility of the geometric average in units of sigma)."""
    van = bs(S, 100.0, T, R, Q, VOL, "C")
    return [(n, asian_mc(S, 100.0, T, R, Q, VOL, n, n_paths=40_000)["cv"] / van,
             math.sqrt((n + 1) * (2 * n + 1) / (6 * n * n))) for n in ns]


def asian_scatter(n: int = 12, m: int = 400) -> tuple[np.ndarray, np.ndarray]:
    p = gbm_paths(S, T * np.arange(1, n + 1) / n, R, Q, VOL, m, 7)
    return asian_payoff(p, 100.0, geometric=True), asian_payoff(p, 100.0)


# ---------------------------------------------------------------- lookbacks
def lookback_table(counts=(12, 52, 252)) -> dict:
    cont = lookback_floating_call(S, S, T, R, Q, VOL)
    rows = []
    for n in counts:
        p = gbm_paths(S, T * np.arange(1, n + 1) / n, R, Q, VOL, 100_000, 3)
        x = math.exp(-R * T) * lookback_payoff(p)
        rows.append({"n": n, "mc": float(x.mean()), "se": float(x.std() / math.sqrt(len(x))),
                     "shifted": lookback_shifted(S, T, R, Q, VOL, n)})
    return {"cont": cont, "vanilla": bs(S, 100.0, T, R, Q, VOL, "C"), "rows": rows}


# ---------------------------------------------------------------- the two models on the same surface
MONTHS = np.arange(1, 13) / 12


def market_vol(k: float, t: float) -> float:
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    return math.sqrt(float(ssvi(k, theta, -0.6, 1.0, 0.45)) / t)


def model_paths(n: int = 100_000, seed: int = 16) -> dict[str, np.ndarray]:
    """Monthly spots over one year (zero rates) under chapter 9's local volatility, chapter 10's Heston and
    Black-Scholes at the one-year at-the-money volatility."""
    _, rec = lv_simulate(lv_grid(), 100.0, 1.0, 252, n, seed, record=tuple(MONTHS))
    lv = np.column_stack([np.full(len(rec[MONTHS[0]]), 100.0)] + [rec[m] for m in MONTHS])
    hs = simulate_paths(calibration()[0], 100.0, MONTHS, 252, n, seed)
    bsp = gbm_paths(100.0, MONTHS, 0.0, 0.0, market_vol(0.0, 1.0), n, seed)
    return {"lv": lv, "heston": hs, "bs": bsp}


FWD_KS = np.array([0.94, 0.96, 0.98, 1.0, 1.02, 1.04, 1.06])


def forward_smiles(paths=None) -> dict:
    """One-month smile starting in six months (month 6 to month 7), against today's one-month smile."""
    paths = model_paths() if paths is None else paths
    out = {"today": np.array([market_vol(math.log(k), 1 / 12) for k in FWD_KS])}
    for name in ("lv", "heston"):
        out[name] = forward_smile_from_paths(paths[name], 6, 7, 1 / 12, FWD_KS)
    return out


def cliquets(paths=None) -> dict:
    """Prices under each model (zero rates) of: a monthly cliquet with local floor -1%, local cap +1% and global
    floor 0 (per unit notional); and a reverse cliquet max(0, 25% + sum of negative monthly returns)."""
    paths = model_paths() if paths is None else paths
    out = {}
    for name, p in paths.items():
        c = cliquet_payoff(p, local_floor=-0.01, local_cap=0.01, global_floor=0.0)
        rc = reverse_cliquet_payoff(p, 0.25)
        out[name] = {"cliquet": float(c.mean()), "cliquet_se": float(c.std() / math.sqrt(len(c))),
                     "reverse": float(rc.mean()), "reverse_se": float(rc.std() / math.sqrt(len(rc)))}
    return out


def repricing_check(paths=None) -> dict[str, float]:
    """Both models must reprice the one-year at-the-money call of the surface: implied volatility of each
    model's simulated call against the market's."""
    paths = model_paths() if paths is None else paths
    out = {"market": market_vol(0.0, 1.0)}
    for name, p in paths.items():
        c = float(np.maximum(p[:, -1] - 100.0, 0).mean())
        out[name] = implied_vol(c, 100.0, 100.0, 1.0, 1.0, "C")
    return out


def cliquet_by_cap(paths=None, caps=(0.005, 0.01, 0.015, 0.02, 0.03, 0.05)) -> list[tuple[float, float, float, float]]:
    paths = model_paths() if paths is None else paths
    rows = []
    for cap in caps:
        vals = [float(cliquet_payoff(paths[m], -cap, cap, 0.0).mean()) for m in ("lv", "heston", "bs")]
        rows.append((cap, *vals))
    return rows


def asians_by_model(paths=None) -> dict[str, tuple[float, float]]:
    """At-the-money twelve-fixing Asian call (zero rates) under each model: (price, standard error)."""
    paths = model_paths() if paths is None else paths
    out = {}
    for name, p in paths.items():
        a = asian_payoff(p, 100.0)
        out[name] = (float(a.mean()), float(a.std() / math.sqrt(len(a))))
    return out


def reverse_by_coupon(paths=None, coupons=(0.15, 0.25, 0.35)) -> dict[float, dict[str, float]]:
    paths = model_paths() if paths is None else paths
    return {c: {name: float(reverse_cliquet_payoff(p, c).mean()) for name, p in paths.items()} for c in coupons}
