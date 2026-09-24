"""Book 4, chapter 17: linear time series (teaching module).

The 2s10s Treasury spread (FRED DGS10 - DGS2, daily, 1976-2026): autocorrelations, an AR(1) half-life, its
small-sample bias, the Dickey-Fuller test, spurious regression, and long memory.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "tsa"))
from firm_tsa import acf, adf, ar1, frac_diff, hurst_gph, hurst_rs, mackinnon_crit, pacf, yule_walker  # noqa: E402

DATA = ROOT / "data" / "methods" / "ust_2y10y_daily_1976_2026.csv"


def load() -> dict:
    d = np.genfromtxt(DATA, delimiter=",", names=True, dtype=None, encoding=None)
    dates = np.array(d["date"], dtype=str)
    s = 100 * (np.array(d["dgs10"], dtype=float) - np.array(d["dgs2"], dtype=float))
    return {"dates": dates, "spread": np.round(s, 6)}


def _norm_sf(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2))


def aic_ar(x, max_p: int = 10) -> list[tuple[int, float]]:
    """AIC of AR(p) fits by OLS on a common sample, p = 0..max_p (x demeaned)."""
    x = np.asarray(x, dtype=float) - np.mean(x)
    y = x[max_p:]
    out = []
    for p in range(max_p + 1):
        if p == 0:
            e = y
        else:
            X = np.column_stack([x[max_p - k: x.size - k] for k in range(1, p + 1)])
            e = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
        out.append((p, y.size * math.log(float(e @ e) / y.size) + 2 * p))
    return out


def problem() -> dict:
    d = load()
    s = d["spread"]
    a = ar1(s)
    t_df = adf(s, lags=0)
    t_adf = adf(s)
    ds = np.diff(s)
    aics = aic_ar(ds)
    p_best = min(aics, key=lambda t: t[1])[0]
    return {"n": s.size, "start": d["dates"][0], "end": d["dates"][-1], "mean": float(s.mean()), "last": float(s[-1]),
            "min": float(s.min()), "max": float(s.max()), "acf1": float(acf(s, 1)[1]), **a,
            "p_normal": _norm_sf(-a["t_unit"]), "tau_df": t_df["tau"], "tau_adf": t_adf["tau"],
            "adf_lags": t_adf["lags"],
            "crit": mackinnon_crit("c", s.size), "acf_changes": acf(ds, 5)[1:], "pacf_changes": pacf(ds, 5)[1:],
            "p_aic": p_best, "yw_changes": yule_walker(ds, p_best)[0], "sd_changes": float(ds.std()),
            "half_life_years": a["half_life"] / 252, "half_life_kendall_years": a["half_life_kendall"] / 252}


def df_distribution(n: int = 500, reps: int = 20_000, seed: int = 1) -> np.ndarray:
    """Dickey-Fuller tau (with constant) for pure random walks of length n."""
    rng = np.random.default_rng(seed)
    return _ols_rho(np.cumsum(rng.standard_normal((reps, n)), axis=1))[1]


def _ar1_paths(rho: float, n: int, reps: int, rng, burn: int = 200) -> np.ndarray:
    """reps AR(1) paths of length n (unit innovations), simulated together; stationary start."""
    x = rng.standard_normal(reps) / math.sqrt(1 - rho**2)
    out = np.empty((reps, n))
    for t in range(burn + n):
        x = rho * x + rng.standard_normal(reps)
        if t >= burn:
            out[:, t - burn] = x
    return out


def _ols_rho(paths: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Row-wise OLS AR(1) coefficient with intercept, and its t-statistic against one."""
    y, x = paths[:, 1:], paths[:, :-1]
    xc = x - x.mean(1, keepdims=True)
    yc = y - y.mean(1, keepdims=True)
    rho = np.sum(xc * yc, 1) / np.sum(xc * xc, 1)
    e = yc - rho[:, None] * xc
    se = np.sqrt(np.sum(e * e, 1) / (y.shape[1] - 2) / np.sum(xc * xc, 1))
    return rho, (rho - 1) / se


def kendall_curve(n: int, rhos, reps: int = 4000, seed: int = 2) -> list[tuple[float, float, float]]:
    """Mean bias of the OLS AR(1) coefficient (with intercept) against Kendall's -(1 + 3 rho)/n."""
    rng = np.random.default_rng(seed)
    out = []
    for rho in rhos:
        r, _ = _ols_rho(_ar1_paths(rho, n, reps, rng))
        out.append((float(rho), float(np.mean(r - rho)), -(1 + 3 * rho) / n))
    return out


def half_life_mc(rho: float, n: int, reps: int = 2000, seed: int = 3) -> dict:
    """Sampling distribution of the estimated half-life (days) when the true AR(1) coefficient is rho, and how often
    the Dickey-Fuller test fails to reject the unit root at 5%."""
    rng = np.random.default_rng(seed)
    r, t = _ols_rho(_ar1_paths(rho, n, reps, rng))
    hl = np.where((r > 0) & (r < 1), np.log(0.5) / np.log(np.clip(r, 1e-12, 1 - 1e-15)), np.inf)
    return {"median": float(np.median(hl)), "q10": float(np.quantile(hl, 0.1)), "q90": float(np.quantile(hl, 0.9)),
            "true": math.log(0.5) / math.log(rho), "p_not_reject": float(np.mean(t > mackinnon_crit("c", n)[1])),
            "mean_rho": float(np.mean(r)), "share_rho_ge1": float(np.mean(r >= 1))}


def spurious(n: int = 500, reps: int = 5000, seed: int = 4) -> dict:
    """Regress one independent random walk on another: share of |t| > 1.96 and median R^2."""
    rng = np.random.default_rng(seed)

    def t_and_r2(y, x):
        X = np.column_stack([np.ones(y.size), x])
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        e = y - X @ b
        se = math.sqrt(float(e @ e) / (y.size - 2) / float((x - x.mean()) @ (x - x.mean())))
        return b[1] / se, 1 - float(e @ e) / float((y - y.mean()) @ (y - y.mean()))
    hits = hits_d = 0
    r2 = []
    for _ in range(reps):
        dy, dx = rng.standard_normal(n), rng.standard_normal(n)
        t, r = t_and_r2(np.cumsum(dy), np.cumsum(dx))
        hits += int(abs(t) > 1.96)
        r2.append(r)
        hits_d += int(abs(t_and_r2(dy, dx)[0]) > 1.96)
    return {"share": hits / reps, "median_r2": float(np.median(r2)), "share_diff": hits_d / reps}


def long_memory(n: int = 20_000, d: float = 0.3, seed: int = 5) -> dict:
    """ARFIMA(0, d, 0) by fractional integration of white noise, against an AR(1) with the same lag-1
    autocorrelation."""
    rng = np.random.default_rng(seed)
    e = rng.standard_normal(n + 2000)
    x = frac_diff(e, -d, k=2000)[-n:]
    r = acf(x, 200)
    rho = r[1]
    return {"acf": r, "acf_ar1": rho ** np.arange(201), "rho1": float(rho), "rho1_theory": d / (1 - d),
            "h_rs": hurst_rs(x), "h_gph": hurst_gph(x), "h_true": d + 0.5,
            "h_rs_white": hurst_rs(e[:n]), "h_gph_white": hurst_gph(e[:n])}


def spread_memory() -> dict:
    ds = np.diff(load()["spread"])
    return {"h_gph_changes": hurst_gph(ds), "h_gph_abs": hurst_gph(np.abs(ds)), "h_rs_changes": hurst_rs(ds),
            "h_rs_abs": hurst_rs(np.abs(ds))}
