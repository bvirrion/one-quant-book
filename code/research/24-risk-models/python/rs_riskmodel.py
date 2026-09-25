"""Risk models (One Quant Book 7, chapter 24).

firm.synthmkt (seed 1) as the market: its returns are a market factor times beta, ten industry factors, three style
factors (size, value, momentum) and specific shocks, all known. Three models are fitted day by day: a fundamental
model with a country factor, the industries and four styles (an estimated beta, size, value, momentum); the same
model without momentum (the omitted factor); a statistical model of 15 principal components refitted monthly on the
trailing year. Books held from the close of day t over day t + 1, rebuilt monthly: a market-neutral book whose signal
(a proprietary score) loads on the momentum exposure, 50 random market-neutral books, and the cap-weighted market.
Risk forecasts are compared with realised returns by bias statistics over years 3 to 10. NumPy only.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")                     # many small matrices: threads only cost
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("riskmodel", "synthmkt"):
    sys.path.insert(0, str(ROOT / c))
from firm_riskmodel import bias_stat, ewma_cov, factor_returns, pca_model, specific_var, vra  # noqa: E402
from firm_synthmkt import point_in_time_styles, simulate  # noqa: E402

YEAR, MONTH, START, WARM = 252, 21, 2 * 252, 252
HL_COV, HL_VRA, HL_SPEC, SHRINK = 90.0, 42.0, 90.0, 0.1
STYLE_NAMES = ("beta", "size", "value", "momentum")


@functools.lru_cache(maxsize=1)
def market():
    P = simulate()
    R = np.where(P.listed, P.ret, np.nan)
    cap = np.where(P.listed, P.price * P.shares, np.nan)
    cap_prev = np.vstack([cap[:1], cap[:-1]])
    w = np.nan_to_num(cap_prev)
    mkt = np.nansum(w * np.nan_to_num(R), axis=1) / np.maximum(w.sum(axis=1), 1e-12)
    return P, R, cap, mkt


@functools.lru_cache(maxsize=1)
def styles():
    return point_in_time_styles(market()[0])


@functools.lru_cache(maxsize=1)
def betas():
    """Trailing 252-day betas on the cap-weighted market up to the previous day, re-estimated monthly (1 before
    126 observations): row t is the beta in force on day t."""
    P, R, _, mkt = market()
    T, M = R.shape
    B = np.ones((T, M))
    cur = np.ones(M)
    for t in range(T):
        if t % MONTH == 0 and t >= 126:
            lo = max(0, t - YEAR)
            r, m = R[lo:t], mkt[lo:t, None]
            ok = np.isfinite(r)
            n = ok.sum(axis=0)
            mm = np.where(ok, m, 0.0)
            mu_m = mm.sum(axis=0) / np.maximum(n, 1)
            mu_r = np.nansum(r, axis=0) / np.maximum(n, 1)
            cov = (np.where(ok, (r - mu_r) * (m - mu_m), 0.0)).sum(axis=0) / np.maximum(n - 1, 1)
            var = (np.where(ok, (m - mu_m) ** 2, 0.0)).sum(axis=0) / np.maximum(n - 1, 1)
            cur = np.where(n >= 126, cov / np.maximum(var, 1e-12), 1.0)
        B[t] = cur
    return B


def _z(x, listed, cap):
    """Cap-weighted mean zero, unit equal-weighted standard deviation over the listed names."""
    x = np.where(listed, x, np.nan)
    w = np.where(listed, np.nan_to_num(cap), 0.0)
    mu = np.nansum(w * np.nan_to_num(x)) / w.sum()
    sd = np.nanstd(x)
    return np.nan_to_num((x - mu) / sd) if sd > 0 else np.zeros(len(x))


@functools.lru_cache(maxsize=4)
def exposures(t: int, omit: str = ""):
    """The exposures in force on day t, known at the close of day t - 1 (point in time): country, industries, the
    trailing beta, size, value (log book-to-price at the previous close; 0 where no book is filed yet) and the
    momentum score."""
    P, _, cap, _ = market()
    st = styles()
    listed = P.listed[t]
    c = np.nan_to_num(cap[t - 1] if t > 0 else cap[t])
    ind = np.eye(P.cfg.n_industries)[P.industry] * listed[:, None]
    lb = st["log_bp"][t - 1] if t > 0 else np.full(len(listed), np.nan)
    have = listed & np.isfinite(lb)
    value = np.where(have, _z(np.nan_to_num(lb), have, c), 0.0)
    raw = {"beta": betas()[t], "size": st["size"], "momentum": st["momentum"][t]}
    cols = [listed.astype(float), ind]
    for k in STYLE_NAMES:
        if k == omit:
            continue
        cols.append((value if k == "value" else _z(raw[k], listed, c))[:, None])
    return np.column_stack(cols)


def constraint(t: int, n_styles: int):
    P, _, cap, _ = market()
    c = np.nan_to_num(np.where(P.listed[t], cap[t], 0.0))
    cw = np.bincount(P.industry, weights=c, minlength=P.cfg.n_industries)
    return np.r_[0.0, cw / cw.sum(), np.zeros(n_styles)][None, :]


@functools.lru_cache(maxsize=2)
def fundamental(omit: str = ""):
    """Factor returns, residuals, covariance forecasts, VRA multipliers and specific-variance forecasts (raw and
    shrunk within size deciles)."""
    P, R, cap, _ = market()
    T = R.shape[0]
    ns = len([k for k in STYLE_NAMES if k != omit])
    W = np.sqrt(np.nan_to_num(np.vstack([cap[:1], cap[:-1]])))
    F, E = factor_returns(R[WARM:], lambda t: exposures(t + WARM, omit), W[WARM:], lambda t: constraint(t + WARM, ns))
    covs = ewma_cov(F, HL_COV)
    lam2 = vra(F, covs, HL_VRA)
    size = np.vstack([_decile(np.log(np.nan_to_num(cap[t], nan=1.0) + 1.0), P.listed[t]) for t in range(WARM, T)])
    raw = specific_var(E, HL_SPEC)
    shr = specific_var(E, HL_SPEC, groups=size, shrink=SHRINK)
    pad = lambda a, v: np.concatenate([np.full((WARM,) + a.shape[1:], v), a])  # noqa: E731
    return {"F": pad(F, 0.0), "E": pad(E, np.nan), "covs": pad(covs, np.nan), "lam2": pad(lam2, 1.0),
            "spec_raw": pad(raw, np.nan), "spec": pad(shr, np.nan)}


def _decile(x, listed):
    q = np.quantile(x[listed], np.linspace(0.1, 0.9, 9))
    return np.where(listed, np.digitize(x, q), -1)


def books(n_random: int = 50, load: float = 0.5, n_side: int = 100, seed: int = 24):
    """(T, M) weights for each book, rebuilt monthly from the close of the month's first day: the exposed book
    (score = load * z(momentum exposure) + sqrt(1 - load^2) * noise, long the top n_side, short the bottom, then
    neutralised to the country, industry, beta, size and value exposures, gross 2), random market-neutral books
    (long n_side, short n_side, 1/n_side each), and the cap-weighted market."""
    P, R, cap, _ = market()
    T, M = R.shape
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(M)
    rand = rng.standard_normal((n_random, M))
    mom = styles()["momentum"]
    out = {"exposed": np.zeros((T, M)), "market": np.zeros((T, M))}
    rnd = np.zeros((n_random, T, M))
    for t0 in range(0, T, MONTH):
        listed = P.listed[t0]
        sl = slice(t0, min(t0 + MONTH, T))
        nxt = min(t0 + 1, T - 1)                                         # held over day t0 + 1 onward
        m = mom[nxt]
        score = load * (m - m[listed].mean()) / (m[listed].std() + 1e-12) + math.sqrt(1 - load**2) * noise
        out["exposed"][sl] = _neutral(_long_short(score, listed, n_side), exposures(nxt, "momentum"), listed)
        c = np.where(listed, np.nan_to_num(cap[t0]), 0.0)
        out["market"][sl] = c / c.sum()
        for j in range(n_random):
            rnd[j, sl] = _long_short(rand[j], listed, n_side)
    return out, rnd


def _neutral(w, X, listed):
    """The book minus its projection on the columns of X (over the listed names), rescaled to gross 2: neutral to
    every factor in X."""
    Xl = X[listed]
    wl = w[listed] - Xl @ np.linalg.lstsq(Xl, w[listed], rcond=None)[0]
    out = np.zeros(len(w))
    out[listed] = wl * 2.0 / np.abs(wl).sum()
    return out


def _long_short(s, listed, n):
    s = np.where(listed, s, np.nan)
    order = np.argsort(np.where(np.isfinite(s), s, np.inf))
    k = int(np.isfinite(s).sum())
    w = np.zeros(len(s))
    w[order[:n]] = -1.0 / n
    w[order[k - n:k]] = 1.0 / n
    return w


def forecast(w, model, adjust: bool = True, shrunk: bool = True, omit: str = ""):
    """Predicted daily volatility of each day's book (made at the close of day t for day t + 1) and its realised
    return on day t + 1, for t from START - 1; `model` is the dict of `fundamental`."""
    P, R, _, _ = market()
    T = R.shape[0]
    spec = model["spec"] if shrunk else model["spec_raw"]
    pred, real = [], []
    for t in range(START - 1, T - 1):
        X = exposures(t + 1, omit)
        x = X.T @ w[t]
        C = model["covs"][t] * (model["lam2"][t] if adjust else 1.0)
        var = x @ C @ x + np.nansum(w[t] ** 2 * np.where(np.isfinite(spec[t]), spec[t], np.nanmedian(spec[t])))
        pred.append(math.sqrt(var))
        real.append(float(np.nansum(w[t] * np.nan_to_num(R[t + 1]))))
    return np.array(pred), np.array(real)


@functools.lru_cache(maxsize=1)
def statistical(k: int = 15):
    """Monthly PCA refits on the trailing year (names listed all year); forecasts held for the month."""
    P, R, _, _ = market()
    T, M = R.shape
    fits = {}
    for t0 in range(START - 1, T - 1, MONTH):
        win = R[t0 - YEAR + 1:t0 + 1]
        full = np.all(np.isfinite(win), axis=0)
        B, Fc, sp = pca_model(win[:, full], k)
        fits[t0] = (np.flatnonzero(full), B, Fc, sp)
    return fits


def forecast_pca(w, k: int = 15):
    P, R, _, _ = market()
    T = R.shape[0]
    fits = statistical(k)
    pred, real, cur = [], [], None
    for t in range(START - 1, T - 1):
        cur = fits.get(t, cur)
        idx, B, Fc, sp = cur
        wi = w[t][idx]
        out = w[t].copy()
        out[idx] = 0.0
        med = float(np.median(sp))
        x = B.T @ wi
        var = x @ Fc @ x + float(wi**2 @ sp) + float(np.sum(out**2)) * med   # names without a year: median risk
        pred.append(math.sqrt(var))
        real.append(float(np.nansum(w[t] * np.nan_to_num(R[t + 1]))))
    return np.array(pred), np.array(real)


def annual(x) -> float:
    return float(np.std(x, ddof=1) * math.sqrt(YEAR))


def summary(load: float = 0.5):
    """The exposed book under each model: predicted and realised annual volatility and the bias statistic."""
    b, _ = books(load=load)
    w = b["exposed"]
    out = {}
    for name, (p, r) in {"full": forecast(w, fundamental()), "no momentum": forecast(w, fundamental("momentum"),
                                                                                      omit="momentum"),
                         "statistical": forecast_pca(w)}.items():
        out[name] = (float(np.sqrt(np.mean(p**2)) * math.sqrt(YEAR)), annual(r), bias_stat(r, p))
    return out


def random_bias(adjust: bool = True):
    """Bias statistics of the random books under the full model."""
    _, rnd = books()
    m = fundamental()
    return np.array([bias_stat(*reversed(forecast(w, m, adjust=adjust))) for w in rnd])


def rolling_bias(p, r, window: int = YEAR):
    z = r / p
    return np.array([np.std(z[i - window:i], ddof=1) for i in range(window, len(z) + 1)])


def market_bias():
    """The cap-weighted market under the full model, with and without the volatility regime adjustment: overall bias
    and the rolling one-year bias statistics."""
    b, _ = books()
    m = fundamental()
    out = {}
    for adj in (False, True):
        p, r = forecast(b["market"], m, adjust=adj)
        out[adj] = (bias_stat(r, p), rolling_bias(p, r))
    return out


def specific_deciles():
    """Standardised next-day residuals by decile of the predicted specific volatility: the bias statistic per decile,
    for the raw and the shrunk forecasts."""
    m = fundamental()
    E = m["E"]
    out = {}
    for key in ("spec_raw", "spec"):
        S = m[key]
        pred = np.sqrt(S[START - 1:-1])
        e = E[START:]
        ok = np.isfinite(pred) & np.isfinite(e)
        rank = np.full(pred.shape, -1)
        for t in range(len(pred)):
            v = pred[t]
            q = np.nanquantile(v, np.linspace(0.1, 0.9, 9))
            rank[t] = np.where(np.isfinite(v), np.digitize(v, q), -1)
        out[key] = [float(np.std((e / pred)[ok & (rank == d)], ddof=1)) for d in range(10)]
    return out


def decomposition(t: int = 1500):
    """The exposed book's predicted annual variance on day t under the full model: factor and specific shares, and
    the momentum factor's share of the total."""
    b, _ = books()
    m = fundamental()
    X = exposures(t + 1)
    from firm_riskmodel import portfolio_risk
    rk = portfolio_risk(b["exposed"][t], X, m["covs"][t] * m["lam2"][t], np.nan_to_num(m["spec"][t]))
    return {"vol": math.sqrt(rk["total"] * YEAR), "factor": rk["factor"] / rk["total"],
            "momentum": float(rk["contrib"][-1] / rk["total"]), "exposure": float(rk["exposure"][-1])}


def fit_r2():
    """Average daily cross-sectional R^2 (cap-weighted) of the fundamental regression, years 3 to 10."""
    P, R, cap, _ = market()
    m = fundamental()
    out = []
    for t in range(START, R.shape[0]):
        r, e = R[t], m["E"][t]
        ok = np.isfinite(r) & np.isfinite(e)
        w = np.sqrt(np.nan_to_num(cap[t - 1]))[ok]
        out.append(1 - (w @ e[ok] ** 2) / (w @ (r[ok] - (w @ r[ok]) / w.sum()) ** 2))
    return float(np.mean(out))


def rms_exposure():
    """Root mean square of the exposed book's momentum exposure over the evaluation days (the full model's X)."""
    b, _ = books()
    w = b["exposed"]
    T = w.shape[0]
    x = [float(exposures(t + 1)[:, -1] @ w[t]) for t in range(START - 1, T - 1)]
    return math.sqrt(float(np.mean(np.square(x))))
