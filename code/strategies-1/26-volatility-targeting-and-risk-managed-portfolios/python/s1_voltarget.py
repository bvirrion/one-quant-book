"""Volatility targeting and risk-managed portfolios (One Quant Book 8, chapter 26).

Sharpe ratios: firm.synthmkt's market factor (GJR-GARCH with Student-t shocks, a constant 6% premium, ten years) on
twenty seeds, held at a constant exposure of one or managed by the previous month's realised variance, at 16% target
volatility (inverse volatility, and inverse variance as in Moreira and Muir), leverage capped at three; firm.synthfut's
four class indices (thirty years; volatility clustering independent of returns), targeted at 10% with an EWMA
forecast. Flows: a market with 12% volatility for 250 days, a 6% fall, twenty days at 40% and then 18%, in which funds
holding 0.2% of the market's value target 10% volatility (EWMA, centre of mass 20 days, leverage capped at two) and the
market trades 0.4% of its value a day; their flow as a share of each day's volume, with a linear impact of 0, 0.1 or
0.3 times that share fed back into the price and the forecast. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthmkt", "synthfut", "voltarget"):
    sys.path.insert(0, str(ROOT / "firm" / p))
from firm_synthfut import CLASSES, simulate_futures  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402
from firm_voltarget import ewma_var, realised_var, run, spike_flows, weights  # noqa: E402

SEEDS, START = tuple(range(1, 21)), 260
SHARE, TURNOVER, IMPACTS = 0.002, 0.004, (0.0, 0.1, 0.3)


def sr(x):
    x = np.asarray(x)[START:]
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252))


def maxdd(x):
    x = np.asarray(x)[START:] / (np.asarray(x)[START:].std() * math.sqrt(252))      # in annual volatilities
    c = np.cumsum(x)
    return float((np.maximum.accumulate(c) - c).max())


@functools.lru_cache(maxsize=1)
def seeds():
    out = []
    for seed in SEEDS:
        m = simulate(MarketConfig(seed=seed)).mkt
        v = realised_var(m, 21)
        rows = [run(m, np.ones(len(m))), run(m, weights(v, 0.16, 3.0, 1)), run(m, weights(v, 0.16, 3.0, 2))]
        out.append(([sr(x) for x in rows], [maxdd(x) for x in rows]))
    return out


def summary():
    s = np.array([a for a, _ in seeds()])
    d = np.array([b for _, b in seeds()])
    return {"mean": s.mean(0).tolist(), "better_vol": int((s[:, 1] > s[:, 0]).sum()),
            "better_var": int((s[:, 2] > s[:, 0]).sum()), "gain_vol": float((s[:, 1] - s[:, 0]).mean()),
            "gain_sd": float((s[:, 1] - s[:, 0]).std(ddof=1)), "dd": d.mean(0).tolist()}


@functools.lru_cache(maxsize=1)
def classes():
    F = simulate_futures()
    out = {}
    for k, name in enumerate(CLASSES):
        x = F["r"][:, F["cls"] == k].mean(1)
        managed = run(x, weights(ewma_var(x, 20.0), 0.10, 3.0, 1))
        out[name] = (sr(x), sr(managed), maxdd(x), maxdd(managed))
    return out


def base_path():
    rng = np.random.default_rng(26)
    b = np.zeros(320)
    b[:250] = 0.12 / math.sqrt(252) * rng.standard_normal(250)
    b[250] = -0.06
    b[251:271] = 0.40 / math.sqrt(252) * rng.standard_normal(20)
    b[271:] = 0.18 / math.sqrt(252) * rng.standard_normal(49)
    return b


@functools.lru_cache(maxsize=3)
def spike(impact: float = 0.0):
    b = base_path()
    o = spike_flows(b, SHARE, TURNOVER, impact, 0.10, 20.0, 2.0)
    return {"next_day": float(o["flow"][251]), "twenty": float(o["flow"][250:271].sum()),
            "exposure": (float(o["exposure"][249]), float(o["exposure"][270])),
            "ret": float(o["r"][250:271].sum()), "base": float(b[250:271].sum()), "flow": o["flow"],
            "exp": o["exposure"]}
