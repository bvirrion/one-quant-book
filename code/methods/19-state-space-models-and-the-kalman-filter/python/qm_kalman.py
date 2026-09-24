"""Book 4, chapter 19: state-space models and the Kalman filter (teaching module).

The hedge ratio of daily Brent price changes on WTI price changes (EIA spot prices via FRED, 2010-2026) as a
hidden random walk, against a 60-day rolling regression; EM; a particle filter.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "kalman"))
from firm_kalman import em, fit_mle, kalman_filter, local_level_gain, particle_filter, rts_smoother  # noqa: E402

DATA = ROOT / "data" / "methods" / "wti_brent_daily_2010_2026.csv"
BAD = ("2020-04-20", "2020-04-21")     # WTI spot -36.98 on 20 April 2020: both changes treated as missing
WINDOW = 60


def load() -> dict:
    d = np.genfromtxt(DATA, delimiter=",", names=True, dtype=None, encoding=None)
    dates = np.array(d["date"], dtype=str)
    w, b = np.array(d["wti"], dtype=float), np.array(d["brent"], dtype=float)
    dw, db = np.diff(w), np.diff(b)
    bad = np.isin(dates[1:], BAD)
    dw, db = dw.copy(), db.copy()
    dw[bad], db[bad] = np.nan, np.nan
    return {"dates": dates[1:], "dw": dw, "db": db, "wti": w, "brent": b, "bad": bad}


def rolling_ratio(dw, db, window: int = WINDOW) -> np.ndarray:
    """Ratio used on day t: OLS slope through the origin over the previous `window` valid days."""
    out = np.full(dw.size, np.nan)
    for t in range(window, dw.size):
        x, y = dw[t - window: t], db[t - window: t]
        m = ~np.isnan(x)
        out[t] = float(x[m] @ y[m]) / float(x[m] @ x[m])
    return out


def vol_scale(dw, lam: float = 0.94, warm: int = WINDOW) -> np.ndarray:
    """EWMA volatility of the WTI change known before each day (the scale s_t of the observation noise)."""
    s = np.empty(dw.size)
    v = float(np.nanmean(dw[:warm] ** 2))
    for t in range(dw.size):
        s[t] = math.sqrt(v)
        if not np.isnan(dw[t]):
            v = lam * v + (1 - lam) * dw[t] ** 2
    return s


_CACHE: dict = {}


def fit(d: dict | None = None) -> dict:
    """Maximum likelihood for y_t = beta_t x_t + e_t, beta_{t+1} = beta_t + u_t, with Var(e_t) = h s_t^2: the model is
    fitted to the scaled observations y_t / s_t = beta_t x_t / s_t + e_t / s_t."""
    if d is None and "fit" in _CACHE:
        return _CACHE["fit"]
    dd = load() if d is None else d
    s = vol_scale(dd["dw"])
    x, y = dd["dw"] / s, dd["db"] / s
    h, Q, ll = fit_mle(y, x[:, None], [[1.0]], [0.7], [[1.0]], 1.0, [1e-4])
    q = float(Q[0, 0])
    out = {"h": h, "q": q, "snr": q / h, "loglik": ll, "x": x, "y": y, "mean_x2": float(np.nanmean(x * x))}
    if d is None:
        _CACHE["fit"] = out
    return out


def run_filter(f: dict, q: float | None = None) -> dict:
    return kalman_filter(f["y"], f["x"][:, None], [[1.0]], f["h"], [[f["q"] if q is None else q]], [0.7], [[1.0]])


def half_response(snr: float, mean_x2: float) -> float:
    """Days for the filter to cover half of a shift in the ratio, in steady state: the ratio estimate is an
    exponential average with daily weight about sqrt(snr * E[x^2])."""
    return math.log(2) / math.sqrt(snr * mean_x2)


def compare(d: dict | None = None, start: int = WINDOW) -> dict:
    if d is None and start == WINDOW and "compare" in _CACHE:
        return _CACHE["compare"]
    cache = d is None and start == WINDOW
    d = load() if d is None else d
    dw, db = d["dw"], d["db"]
    f = fit(None if cache else d)
    kf = run_filter(f)
    k_pred = kf["a_pred"][:, 0]
    roll = rolling_ratio(dw, db)
    ok = ~np.isnan(dw)
    ok[:start] = False

    def var(ratio):
        return float(np.mean((db[ok] - ratio[ok] * dw[ok]) ** 2))
    static = float(np.nansum(dw[:start] * db[:start]) / np.nansum(dw[:start] ** 2))
    sm = rts_smoother(kf, [[1.0]])
    raw = fit_mle(db, dw[:, None], [[1.0]], [0.7], [[1.0]], 1.0, [1e-4])
    kr = kalman_filter(db, dw[:, None], [[1.0]], raw[0], raw[1], [0.7], [[1.0]])["a_pred"][:, 0]
    out = {**{k: v for k, v in f.items() if k not in ("x", "y")},
            "var_kalman": var(k_pred), "var_roll": var(roll), "var_static": var(np.full(dw.size, static)),
            "var_unhedged": float(np.mean(db[ok] ** 2)), "reduction": 1 - var(k_pred) / var(roll),
            "reduction_unscaled": 1 - var(kr) / var(roll), "q_unscaled": float(raw[1][0, 0]), "h_unscaled": raw[0],
            "k_pred": k_pred, "k_filt": kf["a_filt"][:, 0], "k_smooth": sm["a_smooth"][:, 0], "roll": roll,
            "k_sd": np.sqrt(kf["P_filt"][:, 0, 0]), "n_eval": int(ok.sum()), "static": static,
            "half_days": half_response(f["snr"], f["mean_x2"]), "ok": ok}
    if cache:
        _CACHE["compare"] = out
    return out


def tradeoff(mults=(0.1, 0.3, 1, 3, 10, 30, 100), d: dict | None = None) -> list[tuple[float, float, float]]:
    """Hedge-error variance relative to the 60-day regression, and the half-response time, when q is scaled."""
    c, f = compare(d), fit(d)
    d = load() if d is None else d
    out = []
    for m in mults:
        kp = run_filter(f, f["q"] * m)["a_pred"][:, 0]
        ok = c["ok"]
        v = float(np.mean((d["db"][ok] - kp[ok] * d["dw"][ok]) ** 2))
        out.append((float(m), v / c["var_roll"], half_response(f["snr"] * m, f["mean_x2"])))
    return out


def jump_response(snr_mult: float = 1.0, jump: float = 0.3, n: int = 400, seed: int = 6) -> dict:
    """Simulated: the ratio jumps from 0.7 to 1.0 on day 200; x and noise with the fitted scales. Days until each
    estimate has covered half the jump."""
    f = fit()
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n) * math.sqrt(f["mean_x2"])
    beta = np.where(np.arange(n) < 200, 0.7, 0.7 + jump)
    y = beta * x + math.sqrt(f["h"]) * rng.standard_normal(n)
    kf = kalman_filter(y, x[:, None], [[1.0]], f["h"], [[f["q"] * snr_mult]], [0.7], [[0.01]])
    kp = kf["a_pred"][:, 0]
    roll = rolling_ratio(x, y)

    def days(est):
        after = np.flatnonzero(est[200:] >= 0.7 + jump / 2)
        return int(after[0]) if after.size else None
    return {"kalman": days(kp), "roll": days(roll)}


def em_path(n_iter: int = 30) -> dict:
    """EM on the scaled hedge model from a deliberately poor start (h = 1, q = 0.01)."""
    f = fit()
    H, Q, lls = em(f["y"], f["x"][:, None], [[1.0]], 1.0, [[1e-2]], [0.7], [[1.0]], n_iter)
    return {"h": H, "q": float(Q[0, 0]), "lls": lls}


def gain_curve(qs) -> list[tuple[float, float]]:
    return [(float(q), local_level_gain(q)) for q in qs]


def local_level_check(q: float = 0.01, n: int = 400, seed: int = 3) -> dict:
    """Simulated local level: the filter's gain converges to the steady-state formula."""
    rng = np.random.default_rng(seed)
    mu = np.cumsum(math.sqrt(q) * rng.standard_normal(n))
    y = mu + rng.standard_normal(n)
    kf = kalman_filter(y, [1.0], [[1.0]], 1.0, [[q]], [0.0], [[10.0]])
    return {"gain_last": float(kf["K"][-1, 0]), "gain_theory": local_level_gain(q)}


# --- particle filter: validation on the linear model, then stochastic volatility -------------------------------

def pf_vs_kalman(n_part: int = 2000, seed: int = 4, n: int = 500) -> dict:
    """Bootstrap filter on the local-level model, whose exact answer the Kalman filter gives."""
    rng = np.random.default_rng(seed)
    q = 0.05
    mu = np.cumsum(math.sqrt(q) * rng.standard_normal(n))
    y = mu + rng.standard_normal(n)
    kf = kalman_filter(y, [1.0], [[1.0]], 1.0, [[q]], [0.0], [[1.0]])
    pf = particle_filter(y, n_part, lambda m, g: g.standard_normal(m),
                         lambda x, g: x + math.sqrt(q) * g.standard_normal(x.size),
                         lambda yt, x: -0.5 * (yt - x) ** 2 - 0.5 * math.log(2 * math.pi),
                         np.random.default_rng(seed + 1))
    return {"ll_kf": kf["loglik"], "ll_pf": pf["loglik"],
            "max_mean_gap": float(np.max(np.abs(pf["mean"] - kf["a_filt"][:, 0]))),
            "sd_filter": float(np.sqrt(kf["P_filt"][-1, 0, 0])), "ess_mean": float(pf["ess"].mean())}


def sv_filter(returns, phi: float = 0.98, sigma_eta: float = 0.15, mu: float | None = None, n_part: int = 5000,
              seed: int = 5) -> dict:
    """Log-volatility x_t = mu + phi (x_{t-1} - mu) + sigma_eta u_t, r_t = exp(x_t / 2) z_t: filtered volatility."""
    r = np.asarray(returns, dtype=float)
    mu = math.log(np.var(r)) if mu is None else mu
    s0 = sigma_eta / math.sqrt(1 - phi**2)
    pf = particle_filter(r, n_part, lambda m, g: mu + s0 * g.standard_normal(m),
                         lambda x, g: mu + phi * (x - mu) + sigma_eta * g.standard_normal(x.size),
                         lambda rt, x: -0.5 * (math.log(2 * math.pi) + x + rt * rt / np.exp(x)),
                         np.random.default_rng(seed))
    return {"logvar_mean": pf["mean"], "ess": pf["ess"], "loglik": pf["loglik"]}


EURUSD = ROOT / "data" / "methods" / "eur_fx_ecb_1999_2026.csv"


def eurusd_returns(last: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    d = np.genfromtxt(EURUSD, delimiter=",", names=True, dtype=None, encoding=None)
    dates = np.array(d["date"], dtype=str)
    r = 100 * np.diff(np.log(np.array(d["usd_per_eur"], dtype=float)))
    return dates[1:][-last:], r[-last:]


def sv_grid(phis=(0.8, 0.9, 0.95, 0.98), sigmas=(0.2, 0.3, 0.4, 0.5), last: int = 1000) -> dict:
    """Particle-filter log-likelihood of the stochastic-volatility model on EUR/USD over a grid (same seed for every
    point: common random numbers), and the best point."""
    _, r = eurusd_returns(last)
    grid = {(p, s): sv_filter(r, p, s, n_part=5000, seed=5)["loglik"] for p in phis for s in sigmas}
    best = max(grid, key=grid.get)
    return {"grid": grid, "phi": best[0], "sigma": best[1], "loglik": grid[best]}
