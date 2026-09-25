"""Seasonality and calendar effects (One Quant Book 8, chapter 23).

Calendar rules: firm.synthfut's equity class (the mean of ten index futures, thirty years) on firm.seasonal's stylised
calendar, with two planted effects, 8 basis points a day on the last day and first three days of each month and 15
basis points on the day before each of nine holidays a year; the 100 rules are tested and corrected four ways
(Bonferroni, Holm, Benjamini-Hochberg, Benjamini-Yekutieli; firm.multitest), and each discovery is classed as carrying
the turn-of-month effect, the pre-holiday effect, or neither. Same-month seasonality: firm.synthmkt's stocks (ten
years) receive a planted return in each calendar month, persistent across years (1% a month in cross-sectional
standard deviation); the signal is the stock's average return in the same calendar month of the previous five years,
tested by monthly rank IC and a decile long-short. Real data: WTI's rolled returns by calendar month (EIA, 1986-2024),
and the Henry Hub spot price's seasonal profile (EIA via FRED, monthly, 2000-2026). NumPy only.
"""
from __future__ import annotations

import csv
import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for p in ("synthfut", "synthmkt", "seasonal", "multitest", "bars"):
    sys.path.insert(0, str(ROOT / "firm" / p))
sys.path.insert(0, str(ROOT / "research" / "02-market-data-for-research" / "python"))
from firm_multitest import benjamini_hochberg, benjamini_yekutieli, bonferroni, holm  # noqa: E402
from firm_seasonal import DPM, calendar, profile, rules, same_month, score_rules  # noqa: E402
from firm_synthfut import FutConfig, simulate_futures  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

TOM, PRE, SEASON_SD = 0.0008, 0.0015, 0.01
GAS = ROOT.parent / "data" / "markets-3" / "gas_monthly.csv"
CORRECTIONS = (("none", lambda p: p), ("Bonferroni", bonferroni), ("Holm", holm),
               ("Benjamini-Hochberg", benjamini_hochberg), ("Benjamini-Yekutieli", benjamini_yekutieli))


@functools.lru_cache(maxsize=2)
def calendar_test(seed: int = 7):
    F = simulate_futures(FutConfig(seed=seed))
    eq = F["r"][:, F["cls"] == 0].mean(1)
    cal = calendar(30)
    tom = np.where((cal["dom"] >= DPM - 1) | (cal["dom"] < 3), TOM, 0.0)
    pre = np.where(cal["pre"], PRE, 0.0)
    R = rules(cal)
    names, t, p = score_rules(eq + tom + pre, R)
    e_tom = np.array([tom[m].mean() - tom[~m].mean() for _, m in R])
    e_pre = np.array([pre[m].mean() - pre[~m].mean() for _, m in R])
    family = np.where(np.abs(e_tom) >= 3e-4, "tom", np.where(np.abs(e_pre) >= 3e-4, "pre", "none"))
    out = {"n_rules": len(R), "family": family, "names": names, "t": t, "p": p}
    for label, fn in CORRECTIONS:
        k = fn(p) < 0.05
        out[label] = {f: int((k & (family == f)).sum()) for f in ("tom", "pre", "none")}
        out[label]["false"] = [names[i] for i in np.flatnonzero(k & (family == "none"))]
    return out


@functools.lru_cache(maxsize=1)
def same_month_test():
    P = simulate(MarketConfig())
    T, M = P.ret.shape
    rng = np.random.default_rng(23)
    s = SEASON_SD * rng.standard_normal((M, 12))                    # planted monthly seasonal return per listing
    moy = (np.arange(T) // DPM) % 12
    R = np.where(P.listed, P.ret + s[:, moy].T / DPM, np.nan)
    months = T // DPM
    Mret = np.array([np.sum(R[k * DPM:(k + 1) * DPM], axis=0) for k in range(months)])
    Mret[np.array([np.isnan(R[k * DPM:(k + 1) * DPM]).any(axis=0) for k in range(months)])] = np.nan
    sig = same_month(Mret, (1, 2, 3, 4, 5))
    ics, ls = [], []
    for k in range(12, months):
        m = ~np.isnan(sig[k]) & ~np.isnan(Mret[k])
        a, b = sig[k][m], Mret[k][m]
        ics.append(np.corrcoef(np.argsort(np.argsort(a)), np.argsort(np.argsort(b)))[0, 1])
        q = np.quantile(a, [0.1, 0.9])
        ls.append(b[a >= q[1]].mean() - b[a <= q[0]].mean())
    ics, ls = np.array(ics), np.array(ls)
    return {"ic": float(ics.mean()), "ic_t": float(ics.mean() / ics.std(ddof=1) * math.sqrt(len(ics))),
            "ls_month": float(ls.mean()), "ls_sr": float(ls.mean() / ls.std(ddof=1) * math.sqrt(12)),
            "months": len(ics)}


@functools.lru_cache(maxsize=1)
def wti_months():
    from rs_marketdata import wti_series
    s = wti_series(5, start="1986-01-02")
    r = np.diff(np.log(s["ratio"]))
    mo = np.array([d.month for d in s["dates"][1:]])
    out = []
    for m in range(1, 13):
        a, b = r[mo == m], r[mo != m]
        t = (a.mean() - b.mean()) / math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        out.append((m, float(a.mean() * 21), float(t), math.erfc(abs(t) / math.sqrt(2))))
    p = np.array([o[3] for o in out])
    return out, bonferroni(p), benjamini_hochberg(p)


@functools.lru_cache(maxsize=1)
def gas_profile():
    with open(GAS) as fh:
        rows = list(csv.DictReader(fh))
    x = np.log(np.array([float(r["hh"]) for r in rows]))
    trend = np.full(len(x), np.nan)
    for k in range(6, len(x) - 6):                                  # centred 12-month average (2x12)
        trend[k] = (0.5 * x[k - 6] + x[k - 5:k + 6].sum() + 0.5 * x[k + 6]) / 12
    first = int(rows[0]["month"][5:7]) - 1
    dev = np.roll(profile(x - trend, 12), first)                    # index 0 = January
    return {"dev": dev, "start": rows[0]["month"], "end": rows[-1]["month"], "n": len(rows)}
