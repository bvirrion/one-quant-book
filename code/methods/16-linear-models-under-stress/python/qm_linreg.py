"""Book 4, chapter 16: linear models under stress (teaching module).

Collinear factor betas that flip month to month, regularised return prediction with time-ordered
cross-validation, a hedge ratio attenuated by noisy prices, and standard errors for panels.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "linreg"))
from firm_linreg import elastic_net, fama_macbeth, ols, ridge, time_series_folds, tls, vif  # noqa: E402

# --- collinearity: two factors with correlation 0.97 --------------------------------------------------------
RHO12 = 0.97
TRUE_B = np.array([0.6, 0.4, 0.3, 0.2, 0.1])
DAYS = 21


def factor_months(n_months: int = 24, seed: int = 16) -> dict:
    """Daily factor and stock returns (percent), month by month; OLS betas per month."""
    rng = np.random.default_rng(seed)
    n = n_months * DAYS
    f = rng.standard_normal((n, 5))
    f[:, 1] = RHO12 * f[:, 0] + math.sqrt(1 - RHO12**2) * f[:, 1]
    r = f @ TRUE_B + rng.standard_normal(n)
    betas, r2 = [], []
    for m in range(n_months):
        s = slice(m * DAYS, (m + 1) * DAYS)
        X = np.column_stack([np.ones(DAYS), f[s]])
        fit = ols(X, r[s])
        betas.append(fit["beta"][1:])
        r2.append(1 - float(fit["resid"] @ fit["resid"]) / float(np.sum((r[s] - r[s].mean()) ** 2)))
    b = np.array(betas)
    return {"f": f, "r": r, "betas": b, "r2": np.array(r2), "vif": vif(f)}


# --- regularised prediction ----------------------------------------------------------------------------
P = 30
N_OBS = 2000
N_TEST = 500


def predictors(seed: int = 7, n: int = N_OBS) -> dict:
    """Thirty predictors in three blocks of ten with within-block correlation 0.8; five true signals."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n, P))
    common = rng.standard_normal((n, 3))
    X = np.empty((n, P))
    for j in range(P):
        X[:, j] = math.sqrt(0.8) * common[:, j // 10] + math.sqrt(0.2) * z[:, j]
    beta = np.zeros(P)
    beta[[0, 3, 11, 12, 25]] = [0.12, -0.08, 0.10, 0.06, -0.10]
    y = X @ beta + rng.standard_normal(n)
    return {"X": X, "y": y, "beta": beta}


def _std(X_train, X):
    mu, sd = X_train.mean(0), X_train.std(0)
    return (X - mu) / sd


def cv_path(method: str, lams, d: dict, n_folds: int = 5, purge: int = 5, alpha: float = 0.5) -> np.ndarray:
    """Average out-of-fold mean squared error on the training period for each penalty."""
    X, y = d["X"][:-N_TEST], d["y"][:-N_TEST]
    errs = np.zeros(len(lams))
    folds = time_series_folds(len(y), n_folds, purge)
    for tr, te in folds:
        Xtr, Xte = _std(X[tr], X[tr]), _std(X[tr], X[te])
        ytr = y[tr] - y[tr].mean()
        b = None
        for i, lam in enumerate(lams):
            if method == "ridge":
                b = ridge(Xtr, ytr, lam * len(tr))
            else:
                b = elastic_net(Xtr, ytr, lam, 1.0 if method == "lasso" else alpha, beta0=b)
            pred = y[tr].mean() + Xte @ b
            errs[i] += float(np.mean((y[te] - pred) ** 2)) / len(folds)
    return errs


LAMS = np.geomspace(1.0, 1e-4, 41)


def fit_all(seed: int = 9) -> dict:
    d = predictors(seed)
    X, y = d["X"], d["y"]
    Xtr, Xte = _std(X[:-N_TEST], X[:-N_TEST]), _std(X[:-N_TEST], X[-N_TEST:])
    ytr, yte = y[:-N_TEST], y[-N_TEST:]
    base = float(np.mean((yte - ytr.mean()) ** 2))
    out = {"lams": LAMS}
    b_ols = np.linalg.lstsq(Xtr, ytr - ytr.mean(), rcond=None)[0]
    out["ols"] = {"beta": b_ols, "r2": 1 - float(np.mean((yte - ytr.mean() - Xte @ b_ols) ** 2)) / base}
    for m in ("ridge", "lasso", "enet"):
        cv = cv_path(m, LAMS, d)
        lam = float(LAMS[int(np.argmin(cv))])
        if m == "ridge":
            b = ridge(Xtr, ytr - ytr.mean(), lam * len(ytr))
        else:
            b = elastic_net(Xtr, ytr - ytr.mean(), lam, 1.0 if m == "lasso" else 0.5)
        out[m] = {"beta": b, "lam": lam, "cv": cv, "nonzero": int(np.sum(np.abs(b) > 1e-12)),
                  "r2": 1 - float(np.mean((yte - ytr.mean() - Xte @ b) ** 2)) / base}
    oracle = d["beta"] * X[:-N_TEST].std(0)
    out["oracle_r2"] = 1 - float(np.mean((yte - ytr.mean() - Xte @ oracle) ** 2)) / base
    out["true_nonzero"] = [0, 3, 11, 12, 25]
    return out


def lasso_path(seed: int = 9, lams=None) -> np.ndarray:
    lams = LAMS if lams is None else lams
    d = predictors(seed)
    Xtr = _std(d["X"][:-N_TEST], d["X"][:-N_TEST])
    ytr = d["y"][:-N_TEST] - d["y"][:-N_TEST].mean()
    b, path = None, []
    for lam in lams:
        b = elastic_net(Xtr, ytr, lam, 1.0, beta0=b)
        path.append(b.copy())
    return np.array(path)


# --- the hedge ratio that shrank --------------------------------------------------------------------------
H_TRUE = 0.85          # bond price change per unit of the future's (true, synchronous) change
SD_FUT = 0.40          # daily sd of the future's true price change (points)
SD_LEVEL = 0.14        # sd of the error in the future's recorded daily price (last trade, stale, bid-ask)
SD_BASIS = 0.05        # daily sd of the bond's unhedgeable residual


def hedge_data(seed: int = 2026, n: int = 500) -> dict:
    rng = np.random.default_rng(seed)
    x = SD_FUT * rng.standard_normal(n)
    e = SD_LEVEL * rng.standard_normal(n + 1)
    xo = x + e[1:] - e[:-1]                           # recorded change: true change plus a level-error difference
    y = H_TRUE * x + SD_BASIS * rng.standard_normal(n)
    return {"x": x, "x_obs": xo, "y": y}


def attenuation(sd_fut: float = SD_FUT, sd_level: float = SD_LEVEL, horizon: int = 1) -> float:
    s2 = horizon * sd_fut**2
    return s2 / (s2 + 2 * sd_level**2)


def hedge(seed: int = 2036, n: int = 500) -> dict:
    d = hedge_data(seed, n)
    x, xo, y = d["x"], d["x_obs"], d["y"]
    X = np.column_stack([np.ones(n), xo])
    b_ols = float(ols(X, y)["beta"][1])
    g0 = float(np.var(xo))
    g1 = float(np.mean((xo[1:] - xo.mean()) * (xo[:-1] - xo.mean())))
    lam_hat = (g0 + 2 * g1) / g0                      # Roll: the level-error variance is -gamma(1)
    k = 5
    m = n // k
    xw, yw = xo[: m * k].reshape(m, k).sum(1), y[: m * k].reshape(m, k).sum(1)
    b_week = float(ols(np.column_stack([np.ones(m), xw]), yw)["beta"][1])
    b_tls = tls(xo, y)

    def resid_sd(h):
        return float(np.std(y - h * x))
    return {"b_ols": b_ols, "lam": attenuation(), "lam_hat": lam_hat, "b_corrected": b_ols / lam_hat,
            "b_week": b_week, "lam_week": attenuation(horizon=5), "b_tls": b_tls,
            "rho1": g1 / g0, "resid_true": resid_sd(H_TRUE), "resid_ols": resid_sd(b_ols),
            "resid_corrected": resid_sd(b_ols / lam_hat), "resid_week": resid_sd(b_week),
            "resid_unhedged": float(np.std(y))}


def hedge_mc(n_rep: int = 2000, n: int = 500, seed0: int = 30_000) -> dict:
    rows = np.array([[hedge(seed0 + s, n)[k] for k in ("b_ols", "b_corrected", "b_week")] for s in range(n_rep)])
    return {"mean": rows.mean(0), "sd": rows.std(0)}


# --- panels: Fama-MacBeth and clustered standard errors ----------------------------------------------------

def panel(seed: int, n_firms: int = 100, n_months: int = 60, firm_share: float = 0.5, slope: float = 1.0) -> dict:
    """Petersen-style panel: both the characteristic and the residual have a persistent firm component."""
    rng = np.random.default_rng(seed)
    gx, ge = rng.standard_normal(n_firms), rng.standard_normal(n_firms)
    a, b = math.sqrt(firm_share), math.sqrt(1 - firm_share)
    x = a * gx[:, None] + b * rng.standard_normal((n_firms, n_months))
    e = a * ge[:, None] + b * rng.standard_normal((n_firms, n_months))
    y = slope * x + 2 * e
    return {"x": x, "y": y}


def panel_ses(seed: int = 1, **kw) -> dict:
    p = panel(seed, **kw)
    x, y = p["x"], p["y"]
    nf, nt = x.shape
    X = np.column_stack([np.ones(x.size), x.ravel()])
    firms = np.repeat(np.arange(nf), nt)
    out = {"beta": float(ols(X, y.ravel())["beta"][1])}
    for c in ("classical", "hc", "cluster"):
        out[c] = float(ols(X, y.ravel(), cov=c, groups=firms)["se"][1])
    xs = [np.column_stack([np.ones(nf), x[:, t]]) for t in range(nt)]
    fm = fama_macbeth([y[:, t] for t in range(nt)], xs, lags=3)
    out["fm_beta"], out["fm"], out["fm_nw"] = float(fm["beta"][1]), float(fm["se"][1]), float(fm["se_nw"][1])
    return out


def panel_truth(n_rep: int = 500, seed0: int = 5000, **kw) -> dict:
    rows = [panel_ses(seed0 + s, **kw) for s in range(n_rep)]
    return {"sd_ols": float(np.std([r["beta"] for r in rows])), "sd_fm": float(np.std([r["fm_beta"] for r in rows])),
            **{k: float(np.mean([r[k] for r in rows])) for k in ("classical", "hc", "cluster", "fm", "fm_nw")}}


def flip(month: int = 20, seed: int = 16) -> dict:
    """Months `month` and `month + 1` (1-based): the two collinear betas, their sum, and how much the fitted
    returns of the second month change when the first month's betas are used instead of its own."""
    F = factor_months(seed=seed)
    b0, b1 = F["betas"][month - 1], F["betas"][month]
    s = slice(month * DAYS, (month + 1) * DAYS)
    f, r = F["f"][s], F["r"][s]
    X = np.column_stack([np.ones(DAYS), f])
    own = ols(X, r)["beta"]
    fit_own = X @ own
    fit_prev = own[0] + f @ b0
    return {"b_prev": b0[:2], "b_next": b1[:2], "sum_prev": float(b0[:2].sum()), "sum_next": float(b1[:2].sum()),
            "corr_fits": float(np.corrcoef(fit_own, fit_prev)[0, 1]),
            "rmse_change": float(np.sqrt(np.mean((fit_own - fit_prev) ** 2))), "sd_fit": float(fit_own.std()),
            "r2_next": float(F["r2"][month]), "vif_theory": 1 / (1 - RHO12**2)}
