"""firm.impactfit -- measuring price impact (build of One Quant Book 10, chapter 11).

Trades are structured arrays (t, price, qty, sign) and quotes a mid-price path (times, mids), as firm.tape and
firm.exchsim's Result.tape() give them; metaorders are records (start, end, sign, Q, V, sigma) with a price path.

API (stable):
    orders(trades)                                   executions at the same time and sign merged into market orders
    response(trades, times, mids, lags, size_edges)   R(l) = E[eps_t (m_{t+l} - m_t)] after market order t (merged
                                                     executions), overall and by order-size bucket (lags in orders)
    aggregate(trades, times, mids, interval, edges)  mid change over each interval against its signed volume,
                                                     averaged within buckets of signed volume
    metaorder_path(times, mids, start, end, sign, grid)   eps (m(t) - m(start)) on a grid of fractions of the
                                                     execution (0..1) and of the time after it (1..)
    fit_power(impact, sigma, participation, bins, boot, clusters, seed)   Book 7's firm.tcost.fit_impact (binned
                                                     log-log fit of impact / sigma on Q / V) with a cluster
                                                     bootstrap: exponent, prefactor and 95% intervals
    decontaminate(impact, forecast)                  impact minus the forecast drift that timed the order, and the
                                                     regression coefficient of impact on the forecast
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tcost"))
from firm_tcost import fit_impact  # noqa: E402


def _mid_at(times, mids, t):
    i = np.searchsorted(times, np.asarray(t, float), side="right") - 1
    return np.asarray(mids)[np.clip(i, 0, len(times) - 1)]


def orders(trades) -> np.ndarray:
    """Executions with the same time and sign merged into one market order (t, qty, sign)."""
    t, s, q = trades["t"], trades["sign"], trades["qty"]
    new = np.concatenate([[True], (np.diff(t) != 0) | (np.diff(s) != 0)])
    k = np.cumsum(new) - 1
    out = np.zeros(int(k[-1]) + 1, dtype=[("t", "f8"), ("qty", "i8"), ("sign", "i1")])
    out["t"], out["sign"] = t[new], s[new]
    out["qty"] = np.bincount(k, weights=q)
    return out


def response(trades, times, mids, lags=(1, 2, 5, 10, 20, 50), size_edges=(0, 150, 350, 750, 10**9)) -> dict:
    trades = orders(trades)
    t, q, e = trades["t"], trades["qty"].astype(float), trades["sign"].astype(float)
    m0 = _mid_at(times, mids, t - 1e-9)
    out = {"lags": list(lags), "all": [], "by_size": {}}
    for lag in lags:
        m1 = np.concatenate([m0[lag:], np.full(lag, np.nan)])
        r = e * (m1 - m0)
        out["all"].append(float(np.nanmean(r)))
        for lo, hi in zip(size_edges[:-1], size_edges[1:], strict=True):
            sel = (q >= lo) & (q < hi)
            ok = sel & np.isfinite(r)
            out["by_size"].setdefault((lo, hi), []).append(float(r[ok].mean()) if ok.any() else np.nan)
    return out


def aggregate(trades, times, mids, interval: float, edges) -> dict:
    t = trades["t"]
    k = (t // interval).astype(int)
    n = int(k.max()) + 1
    flow = np.bincount(k, weights=trades["qty"] * trades["sign"], minlength=n)
    grid = np.arange(n + 1) * interval
    dm = np.diff(_mid_at(times, mids, grid))
    b = np.digitize(flow, edges) - 1
    means = [float(dm[b == i].mean()) if np.any(b == i) else np.nan for i in range(len(edges) - 1)]
    centres = [float(flow[b == i].mean()) if np.any(b == i) else np.nan for i in range(len(edges) - 1)]
    return {"flow": centres, "dm": means, "n": [int(np.sum(b == i)) for i in range(len(edges) - 1)],
            "slope": float(np.polyfit(flow, dm, 1)[0])}


def metaorder_path(times, mids, start: float, end: float, sign: int, grid=(0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)):
    m0 = float(_mid_at(times, mids, start - 1e-9))
    ts = [start + g * (end - start) for g in grid]
    return np.array([sign * (float(_mid_at(times, mids, x)) - m0) for x in ts])


def fit_power(impact, sigma, participation, bins: int = 20, boot: int = 200, clusters=None,
              seed: int = 1) -> dict:
    impact, sigma, participation = (np.asarray(a, float) for a in (impact, sigma, participation))
    base = fit_impact(impact, sigma, participation, 0.0, bins)
    rng = np.random.default_rng(seed)
    groups = np.unique(clusters) if clusters is not None else None
    ex, et = [], []
    for _ in range(boot):
        if groups is None:                            # resample orders
            idx = rng.integers(0, len(impact), len(impact))
        else:                                         # resample whole stocks
            pick = rng.choice(groups, len(groups))
            idx = np.concatenate([np.flatnonzero(clusters == g) for g in pick])
        f = fit_impact(impact[idx], sigma[idx], participation[idx], 0.0, bins)
        ex.append(f["exponent"])
        et.append(f["eta"])

    def ci(x):
        return tuple(np.percentile(x, [2.5, 97.5]))
    return {"exponent": base["exponent"], "prefactor": base["eta"], "exponent_ci": ci(ex),
            "prefactor_ci": ci(et), "prefactor_sqrt": base["eta_fixed"]}


def decontaminate(impact, forecast) -> dict:
    impact, forecast = np.asarray(impact, float), np.asarray(forecast, float)
    beta = float(np.polyfit(forecast, impact, 1)[0]) if np.ptp(forecast) > 0 else 0.0
    return {"clean": impact - forecast, "beta": beta}
