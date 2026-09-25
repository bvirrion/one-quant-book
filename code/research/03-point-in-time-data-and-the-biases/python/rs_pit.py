"""Point-in-time data and the biases (One Quant Book 7, chapter 3).

Real-time US payrolls (Philadelphia Fed vintages, data/research/): how large the revisions are, how the
2008 recession looked as it was reported, and a bitemporal store of the 2008-2009 vintages; and a simulated
equity universe in which dropping the names that delisted inflates the equal-weighted return. NumPy only.
"""
from __future__ import annotations

import csv
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
DATA = HERE.parents[4] / "data" / "research"
sys.path.insert(0, str(HERE.parents[3] / "firm" / "pit"))
from firm_pit import Guard, Store  # noqa: E402


def _num(x):
    return float(x) if x != "" else math.nan


def payrolls():
    rows = list(csv.DictReader(open(DATA / "payrolls_realtime.csv")))
    text = ("month", "first_vintage", "latest_vintage")
    return {k: [r[k] for r in rows] if k in text else np.array([_num(r[k]) for r in rows]) for k in rows[0]}


def revision_stats(p=None):
    p = p or payrolls()
    ok = ~np.isnan(p["first"]) & ~np.isnan(p["latest"])
    rev = (p["latest"] - p["first"])[ok]
    months = [m for m, k in zip(p["month"], ok, strict=True) if k]
    i = int(np.argmax(np.abs(rev)))
    no2020 = np.array([not m.startswith("2020") for m in months])
    flips = int(np.sum(np.sign(p["first"][ok]) * np.sign(p["latest"][ok]) < 0))
    return {"n": int(ok.sum()), "mean_abs": float(np.abs(rev).mean()), "share_100": float((np.abs(rev) > 100).mean()),
            "mean_abs_ex2020": float(np.abs(rev[no2020]).mean()), "largest_month": months[i],
            "largest": float(rev[i]), "sign_flips": flips, "sd_rev": float(rev.std(ddof=1)),
            "mean_rev": float(rev.mean())}


def year_totals(year: str, p=None):
    """Sum of the monthly changes of a year: first releases, and today's vintage (thousand jobs)."""
    p = p or payrolls()
    k = np.array([m.startswith(year) for m in p["month"]])
    return float(np.nansum(p["first"][k])), float(np.nansum(p["latest"][k]))


def vintage_store() -> Store:
    s = Store()
    for r in csv.DictReader(open(DATA / "payrolls_vintages_2008_2009.csv")):
        s.put("US", "payrolls_change", r["month"], r["vintage"], float(r["change"]))
    return s


def real_time_view(month: str, decision: str, store: Store | None = None):
    """What a desk could know on `decision` (a vintage month) about `month`, through the guard."""
    return Guard(store or vintage_store(), decision).asof("US", "payrolls_change", month)


# ------------------------------------------------------------------------------ survivorship

def universe(n: int = 2000, years: int = 20, mu: float = 0.08, sigma: float = 0.40, barrier: float = -1.6,
             delist_return: float = -0.30, seed: int = 11):
    """Monthly log-value random walks, drift mu and volatility sigma a year. A stock is delisted in the
    first month its cumulative log return falls below `barrier`; that month's return is replaced by the
    delisting return, and a new listing takes its place the next month (so the universe keeps n names)."""
    rng = np.random.default_rng(seed)
    T, dt = 12 * years, 1.0 / 12
    ret = np.exp(rng.normal((mu - 0.5 * sigma**2) * dt, sigma * math.sqrt(dt), (T, n))) - 1.0
    cum = np.zeros(n)
    delisted = np.zeros((T, n), bool)
    start = np.zeros(n, int)                     # month in which the name now in each slot listed
    spells = []                                  # (slot, first month, last month or None if still listed)
    for t in range(T):
        cum += np.log1p(ret[t])
        hit = cum < barrier
        if hit.any():
            delisted[t] = hit
            ret[t, hit] = delist_return
            spells += [(int(j), int(start[j]), t) for j in np.flatnonzero(hit)]
            cum[hit] = 0.0
            start[hit] = t + 1
    spells += [(j, int(start[j]), None) for j in range(n)]
    return {"ret": ret, "delisted": delisted, "spells": spells, "T": T, "n": n}


def survivorship(**kw):
    """Annualised equal-weighted return of the full universe (with delisting returns) against the universe
    of the names still listed at the end, each over its own history (today's constituents, backfilled)."""
    u = universe(**kw)
    ret, T, n = u["ret"], u["T"], u["n"]
    full = ret.mean(axis=1)
    surv_mask = np.zeros((T, n), bool)
    for j, s, e in u["spells"]:
        if e is None:
            surv_mask[s:, j] = True
    counts = surv_mask.sum(axis=1)
    surv = np.where(counts > 0, (ret * surv_mask).sum(axis=1) / np.maximum(counts, 1), np.nan)
    rate = u["delisted"].sum() / (n * T / 12)
    fail_mask = ~surv_mask                          # name-months of names that delisted before the end
    w = float(fail_mask.mean())
    r_fail, r_surv = float(ret[fail_mask].mean() * 12), float(ret[surv_mask].mean() * 12)

    def ann(r):
        return float(np.nanmean(r) * 12)

    return {"full": ann(full), "survivors": ann(surv), "bias": ann(surv) - ann(full), "delist_rate": float(rate),
            "fail_share": w, "r_fail": r_fail, "r_surv_pooled": r_surv, "identity": w * (r_surv - r_fail),
            "cum_full": np.cumprod(1 + full), "cum_surv": np.cumprod(1 + np.nan_to_num(surv)),
            "first_full_month": int(np.argmax(counts > 0))}


def bias_approximation(h: float, r_survivor: float, loss: float) -> float:
    """Survivor minus true equal-weighted annual return when a fraction h of names fails each year, a
    failing name losing `loss` in its last year while survivors return r_survivor: h (r_survivor + loss)."""
    return h * (r_survivor + loss)
