"""Stylised facts of returns (One Quant Book 7, chapter 5).

The same statistics for a century of the US market's daily excess return (derived statistics of the Kenneth French
data library, data/research/ff_*.csv), for the market factor, an equal-weighted index and the single stocks of
firm.synthmkt, and for the intraday tape of firm.tape: a scorecard of how realistic the book's simulators are.
NumPy only.
"""
from __future__ import annotations

import csv
import functools
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
DATA = ROOT / "data" / "research"
for c in ("synthmkt", "robust", "covest", "tape"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_covest import mp_edges  # noqa: E402
from firm_robust import hill  # noqa: E402
from firm_synthmkt import MarketConfig, simulate  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402
from firm_tape import simulate as tape_simulate  # noqa: E402


def french_summary() -> dict:
    out = {}
    for r in csv.DictReader(open(DATA / "ff_summary.csv")):
        v = r["value"]
        try:
            out[r["key"]] = float(v) if not v.isdigit() else int(v)
        except ValueError:
            out[r["key"]] = v
    return out


def french_table(name: str) -> dict:
    rows = list(csv.DictReader(open(DATA / f"ff_{name}.csv")))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def kurtosis(x) -> float:
    x = np.asarray(x, float) - np.mean(x)
    return float((x**4).mean() / (x**2).mean() ** 2)


def acf(x, k: int) -> float:
    x = np.asarray(x, float) - np.mean(x)
    return float((x[:-k] * x[k:]).mean() / (x * x).mean())


def facts(r) -> dict:
    """The scorecard statistics of one daily return series."""
    r = np.asarray(r, float)
    lr = np.log1p(r)
    m = len(lr) // 21
    k = max(20, int(0.02 * len(r)))
    return {"kurtosis": kurtosis(r), "hill_left": hill(-r, k)[0], "acf_abs_1": acf(np.abs(r), 1),
            "acf_abs_20": acf(np.abs(r), 20), "acf_abs_100": acf(np.abs(r), 100), "acf_r_1": acf(r, 1),
            "leverage_1": float(np.corrcoef(r[:-1], r[1:] ** 2)[0, 1]),
            "kurtosis_21": kurtosis(lr[: m * 21].reshape(m, 21).sum(axis=1))}


@functools.lru_cache(maxsize=1)
def market():
    return simulate(MarketConfig())


def synth_series():
    p = market()
    ew = np.nanmean(p.ret, axis=1)
    full = p.listed.all(axis=0)
    stocks = [facts(p.ret[:, j]) for j in np.flatnonzero(full)[:200]]
    med = {k: float(np.median([s[k] for s in stocks])) for k in stocks[0]}
    return {"market": facts(p.mkt), "ew": facts(ew), "stock_median": med, "n_full": int(full.sum())}


def eigen(window: int = 252, names: int = 200):
    """Eigenvalues of the correlation matrix of the last `window` days of `names` stocks listed throughout, with the
    Marchenko-Pastur upper edge for pure noise of the same shape (q = names / window)."""
    p = market()
    x = p.ret[-window:]
    x = x[:, ~np.isnan(x).any(axis=0)][:, :names]
    ev = np.sort(np.linalg.eigvalsh(np.corrcoef(x.T)))[::-1]
    lo, hi = mp_edges(x.shape[1] / x.shape[0])
    return ev, float(hi), x.shape


def aggregated_kurtosis(r, horizons=(1, 5, 10, 21, 63)):
    lr = np.log1p(np.asarray(r, float))
    return [kurtosis(lr[: (len(lr) // h) * h].reshape(-1, h).sum(axis=1)) for h in horizons]


def correlation_asymmetry(threshold: float = 1.0):
    """Average pairwise correlation of stock returns (market beta included) on days when the market factor fell by
    more than `threshold` of its standard deviation, and on days it rose by as much: exceedance correlations."""
    p = market()
    full = np.flatnonzero(p.listed.all(axis=0))[:300]
    x = p.ret[:, full]
    z = (p.mkt - p.mkt.mean()) / p.mkt.std()

    def avg_corr(rows):
        c = np.corrcoef(x[rows].T)
        n = c.shape[0]
        return float((c.sum() - n) / (n * (n - 1)))

    mid = np.abs(z) <= threshold
    return avg_corr(z < -threshold), avg_corr(z > threshold), avg_corr(mid) if mid.sum() > 2 else float("nan")


def intraday_profile(window: float = 900.0):
    """Traded volume per quarter-hour in the book's simulated day (firm.tape, U-shaped profile)."""
    tp = tape_simulate(TapeConfig(seconds=23_400.0, u_shape=1.5, news_at=12_600.0, seed=3))
    edges = np.arange(0.0, 23_400.0 + 1e-9, window)
    vol = np.histogram(tp.trades["t"], bins=edges, weights=tp.trades["qty"])[0]
    return vol
