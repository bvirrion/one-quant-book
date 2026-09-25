"""Running a multi-strategy book (One Quant Book 8, chapter 28).

firm.multistrat's firm of ten pods over twenty years: each pod runs at 10% volatility with a Sharpe ratio of 0.5 to
1.0; pods 1-3 load 0.4 on a shared factor A and pods 4-5 on a factor B, factors that are quiet except in three
ten-day crashes of six pod volatilities; pod 10's edge dies after ten years. The firm allocates monthly by inverse
trailing volatility, without and with overlap detection (each shared factor's total exposure capped at 1.0 or 0.5
equal-weight pods); results are scaled to 10% firm volatility. Drawdown limits of 5% to 30% of a pod's capital, with
stopped pods restarted each year: the share of live pods stopped in a year (simulated and on 20,000 paths) and how
long the dead pod ran before a stop. Netting: ten pods trading 200 instruments independently. NumPy only.
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
sys.path.insert(0, str(ROOT / "firm" / "multistrat"))
from firm_multistrat import PodConfig, netting, run_firm, simulate_pods, stop_rate  # noqa: E402

START = 252
LIMITS = (0.05, 0.10, 0.15, 0.20, 0.30)


@functools.lru_cache(maxsize=1)
def pods():
    return simulate_pods(PodConfig(), np.random.default_rng(28))


def correlations():
    p = pods()["pnl"][START:]
    c = np.corrcoef(p.T)
    same = [c[i, j] for i in range(3) for j in range(3) if i < j]
    crash = np.zeros(len(pods()["pnl"]), bool)
    for s, n in PodConfig().crash_days:
        crash[s:s + n] = True
    cum = [float(pods()["pnl"][s:s + n, :3].sum(0).mean() / 0.10) for s, n in PodConfig().crash_days]
    return {"same_factor": float(np.mean(same)), "other": float(c[0, 5]), "crash_pod_loss": cum}


def _stats(f):
    x = f[START:] * 0.10 / (f[START:].std() * math.sqrt(252))
    c = np.cumsum(x)
    return {"sr": float(x.mean() / x.std(ddof=1) * math.sqrt(252)), "mdd": float((np.maximum.accumulate(c) - c).max()),
            "crash": [float(x[s - START:s - START + n].sum()) for s, n in PodConfig().crash_days]}


@functools.lru_cache(maxsize=4)
def overlap(cap: float | None = None):
    return _stats(run_firm(pods(), 21, cap, None)[0])


@functools.lru_cache(maxsize=8)
def limits(limit: float):
    f, stops = run_firm(pods(), 21, None, limit)
    pod, day = pods()["dead"]
    live = [s for s in stops if not (s[0] == pod and s[1] >= day)]
    dead = [d for i, d in stops if i == pod and d >= day]
    years = (len(pods()["pnl"]) - START) / 252
    return {"per_pod_year": len(live) / (10 * years), "dead_days": (dead[0] - day) if dead else None,
            "sr": _stats(f)["sr"], "paths": stop_rate(0.7, 0.10, limit, 1.0, 20_000, np.random.default_rng(1))}


def net_savings(share: float = 0.2, instruments: int = 200, pods_n: int = 10):
    rng = np.random.default_rng(30)
    trades = rng.standard_normal((pods_n, instruments)) * (rng.random((pods_n, instruments)) < share)
    return netting(trades), netting(rng.standard_normal((pods_n, instruments)))


def paths(step: int = 5):
    """Cumulative firm P&L at 10% volatility, without and with a factor cap of 0.5, every `step` days."""
    out = []
    for cap in (None, 0.5):
        f = run_firm(pods(), 21, cap, None)[0][START:]
        out.append(np.cumsum(f * 0.10 / (f.std() * math.sqrt(252))))
    return [((START + i) / 252, float(out[0][i]), float(out[1][i])) for i in range(0, len(out[0]), step)]
