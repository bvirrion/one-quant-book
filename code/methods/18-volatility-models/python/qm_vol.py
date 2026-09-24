"""Book 4, chapter 18: volatility models (teaching module).

Daily EUR/USD returns from the ECB reference rates, 1999-2026: GARCH, EWMA and the 250-day window, the ghost
of a large return leaving the window, forecast evaluation, and HAR on simulated realised variance.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "volfcst"))
from firm_volfcst import (  # noqa: E402
    diebold_mariano,
    ewma,
    garch_filter,
    garch_fit,
    har_fit,
    har_forecast,
    mincer_zarnowitz,
    mse,
    qlike,
    rolling_var,
)

DATA = ROOT / "data" / "methods" / "eur_fx_ecb_1999_2026.csv"
WINDOW = 250
SPLIT = "2015-01-01"


def load() -> dict:
    d = np.genfromtxt(DATA, delimiter=",", names=True, dtype=None, encoding=None)
    dates = np.array(d["date"], dtype=str)
    usd = np.array(d["usd_per_eur"], dtype=float)
    return {"dates": dates[1:], "r": 100 * np.diff(np.log(usd))}


def fits() -> dict:
    r = load()["r"]
    return {"normal": garch_fit(r, "normal"), "t": garch_fit(r, "t"), "gjr_t": garch_fit(r, "t", gjr=True)}


def ghost() -> dict:
    """The largest one-day relative fall of the 250-day volatility, the return that left the window then, and what the
    GARCH-t and EWMA volatilities did on the same day."""
    d = load()
    r, dates = d["r"], d["dates"]
    win = np.sqrt(rolling_var(r, WINDOW))                 # win[t] uses r[t-250:t], the forecast for day t
    rel = win[WINDOW + 1:] / win[WINDOW:-1] - 1           # change between the forecasts for days t and t + 1
    j = int(np.nanargmin(rel)) + WINDOW                   # forecasts for day j and j + 1: r[j - 250] left
    f = garch_fit(r, "t")
    g = np.sqrt(f["h"])
    e = np.sqrt(ewma(r))
    return {"exit_date": dates[j - WINDOW], "exit_return": float(r[j - WINDOW]), "day": dates[j],
            "day_return": float(r[j]), "win_before": float(win[j]), "win_after": float(win[j + 1]),
            "drop_pct": float(100 * rel[j - WINDOW]), "garch_before": float(g[j]), "garch_after": float(g[j + 1]),
            "ewma_before": float(e[j]), "ewma_after": float(e[j + 1]), "index": j}


def impulse(shock: float = 3.5, days: int = 300, base_sd: float = 0.5) -> dict:
    """Extra variance attributed to one return of `shock` percent over the following days, when every other return
    equals the base standard deviation: GARCH-t (fitted), EWMA 0.94 and the 250-day window."""
    f = garch_fit(load()["r"], "t")
    p, a = f["persistence"], f["alpha"]
    k = np.arange(1, days + 1)
    extra = shock**2 - base_sd**2
    return {"k": k, "garch": a * extra * p ** (k - 1), "ewma": 0.06 * extra * 0.94 ** (k - 1),
            "window": np.where(k <= WINDOW, extra / (WINDOW - 1), 0.0)}


def evaluate(split: str = SPLIT) -> dict:
    """One-day-ahead variance forecasts on the test period (from `split`): GARCH-t fitted on the earlier data and run
    forward with fixed parameters, EWMA 0.94, and the 250-day window; proxy r^2."""
    d = load()
    r, dates = d["r"], d["dates"]
    cut = int(np.searchsorted(dates, split))
    f = garch_fit(r[:cut], "t")
    h_g = garch_filter(r, f["omega"], f["alpha"], f["beta"], 0.0, float(np.var(r[:cut])))[:-1]
    h_e = ewma(r)[:-1]
    h_w = rolling_var(r, WINDOW)[:-1]
    y = r[cut:] ** 2
    out = {"n_test": int(r.size - cut), "fit_train": f}
    for name, h in (("garch", h_g), ("ewma", h_e), ("window", h_w)):
        hh = h[cut:]
        out[name] = {"qlike": float(np.mean(qlike(y, hh))), "mse": float(np.mean(mse(y, hh))),
                     "mz": mincer_zarnowitz(y, hh), "loss_q": qlike(y, hh), "loss_m": mse(y, hh)}
    out["dm_garch_ewma"] = diebold_mariano(out["garch"]["loss_q"], out["ewma"]["loss_q"])
    out["dm_garch_window"] = diebold_mariano(out["garch"]["loss_q"], out["window"]["loss_q"])
    out["dm_ewma_window"] = diebold_mariano(out["ewma"]["loss_q"], out["window"]["loss_q"])
    out["dm_mse_garch_window"] = diebold_mariano(out["garch"]["loss_m"], out["window"]["loss_m"])
    return out


# --- realised variance and HAR on a simulated market ------------------------------------------------------

def sv_days(n_days: int = 3000, m: int = 78, seed: int = 18) -> dict:
    """Three-component stochastic volatility (daily AR coefficients 0.3, 0.9, 0.99), constant within a day;
    m intraday returns per day. Returns realised variances and the integrated variances (percent^2)."""
    rng = np.random.default_rng(seed)
    phis, sds = (0.3, 0.9, 0.99), (0.3, 0.25, 0.2)
    comp = np.zeros(3)
    logv = np.empty(n_days)
    for t in range(n_days + 500):
        comp = np.array(phis) * comp + np.array(sds) * np.sqrt(1 - np.array(phis) ** 2) * rng.standard_normal(3)
        if t >= 500:
            logv[t - 500] = comp.sum()
    iv = 0.25 * np.exp(logv - 0.5 * np.var(logv))
    intraday = rng.standard_normal((n_days, m)) * np.sqrt(iv / m)[:, None]
    return {"iv": iv, "rv": np.sum(intraday**2, axis=1), "r": intraday.sum(axis=1), "m": m}


def rv_convergence(ms=(1, 6, 13, 26, 78, 390), n_days: int = 2000, seed: int = 19) -> list[tuple[int, float]]:
    """Relative error sd(RV / IV - 1) against the number of intraday returns; theory sqrt(2 / m)."""
    out = []
    for m in ms:
        s = sv_days(n_days, m, seed)
        out.append((m, float(np.std(s["rv"] / s["iv"] - 1))))
    return out


def har_vs_ar1(seed: int = 18, n_days: int = 3000, n_test: int = 1000) -> dict:
    s = sv_days(n_days, 78, seed)
    rv = s["rv"]
    train = rv[: n_days - n_test]
    fit = har_fit(train)
    fc = har_forecast(fit, rv)                           # forecasts of rv[t+1] for t = 21..n-1
    target = rv[22:]
    fc = fc[:-1]
    x, y = train[:-1], train[1:]
    b = np.polyfit(x, y, 1)
    ar = b[1] + b[0] * rv[21:-1]
    test = slice(n_days - n_test - 22, None)
    iv_next = s["iv"][22:]
    return {"beta": fit["beta"], "r2": fit["r2"], "ar_slope": float(b[0]),
            "q_har": float(np.mean(qlike(target[test], fc[test]))),
            "q_ar": float(np.mean(qlike(target[test], ar[test]))),
            "mse_har_iv": float(np.mean(mse(iv_next[test], fc[test]))),
            "mse_ar_iv": float(np.mean(mse(iv_next[test], ar[test]))),
            "dm": diebold_mariano(qlike(target[test], fc[test]), qlike(target[test], ar[test]))}
