"""firm.mlsynth -- synthetic learning tasks with a known best predictor (build of One Quant Book 12, chapter 1).

Machine learning on market data is judged against a truth nobody sees. This module plants one, so that every model of
Book 12 can be scored against the best predictor that exists for its data: the conditional expectation that generated
it.

Two kinds of data.

* A generic regression task: `task(n, p, snr, kind, seed)` draws features uniform on [-1, 1]^p, a signal f(x) (linear,
  or the nonlinear Friedman-style function below) scaled so that var(f) / var(y) = snr / (1 + snr), and Gaussian noise.
  The Bayes-optimal R-squared is snr / (1 + snr).
* A monthly cross-section of stocks: `panel(PanelConfig(...))`. Each stock has k characteristics, latent AR(1)
  processes with persistences from 0.60 to 0.99, published each month as cross-sectional ranks in [-1, 1] (as the
  empirical literature ranks them). The expected return of stock i for month t + 1, known at the end of month t, is
        mu_it = premium + scale * g(c_it)
  where g uses the first six characteristics: a linear part and a nonlinear part (an interaction, a square, a
  threshold and an absolute value) mixed in the share `nonlin`, the rest are pure noise; `scale` is set so that the
  predictability ceiling (the R-squared of mu against the realised return, below) equals `ceiling`. The realised
  return is
        r_i,t+1 = mu_it + beta_i m_t+1 + f_ind(i),t+1 + e_i,t+1 [+ sum_j c_ijt s_j,t+1]
  with a market factor m (monthly volatility mkt_vol), ten industry factors and Student-t specific shocks (and, when
  style_vol > 0, zero-mean factor returns s_j on every characteristic, so that a portfolio sorted on characteristics
  carries the factor risk real ones do): returns are
  correlated across stocks, so a month is one draw of the market, not n independent observations.
  Non-stationarity is optional: from month `decay_from` the linear coefficient of characteristic 0 decays with
  half-life `decay_half_life` months (a crowded signal), and from month `regime_at` the sign of the interaction flips.

R-squared is measured against a forecast of zero, as in the return-prediction literature:
    r2_oos(y, yhat) = 1 - sum (y - yhat)^2 / sum y^2.

API (stable):
    task(n, p, snr, kind='linear'|'friedman', seed) -> dict(X, y, f, bayes_r2)
    PanelConfig(n, months, k, seed, ceiling, nonlin, premium, mkt_vol, ind_vol, spec_vol, t_df, n_ind, style_vol,
                decay_from, decay_half_life, regime_at)
    panel(cfg) -> Panel     X (T, n, k) ranks in [-1, 1] known at month end t; r (T, n) the return of month t + 1;
                            mu (T, n) the truth; beta (n,), industry (n,), mkt (T,)
    Panel.flat(months)      (X (m*n, k), r (m*n,), mu (m*n,), month index (m*n,)) for a range of months
    r2_oos(y, yhat)         R-squared against zero
    ceiling(P, months)      r2_oos(r, mu) over those months: the best any model can do there
    months_to_detect(r2_by_month, z) months needed for the mean monthly R-squared to reach z standard errors
    SeriesConfig(...), series(cfg)     daily series of several assets (chapter 2; see the section at the end)
    FactorConfig(...), factor_panel(cfg) a panel with nonlinear conditional betas (chapter 9; section at the end)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def r2_oos(y, yhat) -> float:
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return float(1.0 - np.sum((y - yhat) ** 2) / np.sum(y**2))


def _friedman(X):
    """A smooth nonlinear function of the first five features (after Friedman, 1991), centred."""
    x = 0.5 * (X[:, :5] + 1.0)                                          # to [0, 1]
    return (10 * np.sin(np.pi * x[:, 0] * x[:, 1]) + 20 * (x[:, 2] - 0.5) ** 2 + 10 * x[:, 3] + 5 * x[:, 4])


def task(n: int, p: int = 10, snr: float = 1.0, kind: str = "linear", seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    X = rng.uniform(-1.0, 1.0, (n, p))
    if kind == "linear":
        w = np.zeros(p)
        w[: min(5, p)] = [1.0, -0.8, 0.6, 0.4, -0.3][: min(5, p)]
        f = X @ w
    elif kind == "friedman":
        f = _friedman(X)
    else:
        raise ValueError(kind)
    f = (f - f.mean()) / f.std()
    noise_sd = 1.0 / math.sqrt(snr)
    y = f + noise_sd * rng.standard_normal(n)
    return {"X": X, "y": y, "f": f, "bayes_r2": snr / (1.0 + snr)}


@dataclass(frozen=True)
class PanelConfig:
    n: int = 500
    months: int = 360
    k: int = 20
    seed: int = 1
    ceiling: float = 0.007            # R-squared of the truth against realised returns (vs zero)
    nonlin: float = 0.5               # share of the cross-sectional alpha variance that is nonlinear
    premium: float = 0.0              # monthly expected market excess return (0: all predictability is cross-sectional)
    mkt_vol: float = 0.045            # monthly volatility of the market factor
    ind_vol: float = 0.025            # monthly volatility of each industry factor
    spec_vol: float = 0.075           # median monthly specific volatility
    t_df: float = 5.0
    n_ind: int = 10
    style_vol: float = 0.0            # monthly volatility of a zero-mean factor return on every characteristic
    decay_from: int | None = None     # month from which characteristic 0's linear effect decays
    decay_half_life: float = 36.0
    regime_at: int | None = None      # month from which the interaction's sign flips


@dataclass
class Panel:
    cfg: PanelConfig
    X: np.ndarray
    r: np.ndarray
    mu: np.ndarray
    beta: np.ndarray
    industry: np.ndarray
    mkt: np.ndarray

    def flat(self, months):
        m = np.asarray(list(months) if not isinstance(months, np.ndarray) else months)
        T = len(m)
        n, k = self.X.shape[1], self.X.shape[2]
        return (self.X[m].reshape(T * n, k), self.r[m].reshape(-1), self.mu[m].reshape(-1),
                np.repeat(m, n))


def _ranks(Z):
    """Cross-sectional ranks mapped to [-1, 1] (row by row)."""
    n = Z.shape[-1]
    return 2.0 * (np.argsort(np.argsort(Z, axis=-1), axis=-1) + 0.5) / n - 1.0


def _alpha_shape(C, t, cfg):
    """Linear and nonlinear parts of g at month t, each cross-sectionally standardised."""
    w0 = 1.0
    if cfg.decay_from is not None and t >= cfg.decay_from:
        w0 = 0.5 ** ((t - cfg.decay_from) / cfg.decay_half_life)
    lin = w0 * C[:, 0] + 0.8 * C[:, 1] - 0.6 * C[:, 2]
    sgn = -1.0 if (cfg.regime_at is not None and t >= cfg.regime_at) else 1.0
    non = (sgn * 1.5 * C[:, 0] * C[:, 3] + 1.2 * (C[:, 4] ** 2 - 1 / 3) + 0.8 * ((C[:, 5] > 0.5) - 0.25)
           - 0.8 * (np.abs(C[:, 1]) - 0.5))
    return lin, non


def panel(cfg: PanelConfig | None = None) -> Panel:
    cfg = cfg or PanelConfig()
    rng = np.random.default_rng(cfg.seed)
    T, n, k = cfg.months, cfg.n, cfg.k
    phi = np.linspace(0.60, 0.99, k)
    rng.shuffle(phi[6:])                                                 # noise characteristics: mixed persistence
    phi[:6] = [0.95, 0.90, 0.80, 0.97, 0.85, 0.70]
    L = rng.standard_normal((n, k))
    X = np.empty((T, n, k))
    for t in range(T):
        L = phi * L + np.sqrt(1 - phi**2) * rng.standard_normal((n, k))
        X[t] = _ranks(L.T).T
    beta = np.clip(1.0 + 0.3 * rng.standard_normal(n), 0.2, 2.0)
    industry = rng.integers(0, cfg.n_ind, n)
    svol = cfg.spec_vol * np.exp(0.35 * rng.standard_normal(n) - 0.5 * 0.35**2)
    mkt = cfg.mkt_vol * rng.standard_normal(T)
    ind = cfg.ind_vol * rng.standard_normal((T, cfg.n_ind))
    tsc = math.sqrt((cfg.t_df - 2) / cfg.t_df)
    eps = svol * tsc * rng.standard_t(cfg.t_df, (T, n))
    noise = beta * mkt[:, None] + ind[:, industry] + eps
    if cfg.style_vol > 0:                                                # characteristic-sorted books carry factor risk
        fs = cfg.style_vol * rng.standard_normal((T, k))
        noise = noise + np.einsum("tnk,tk->tn", X, fs)
    g = np.empty((T, n))
    for t in range(T):
        lin, non = _alpha_shape(X[t], t, cfg)
        lz = lin / lin.std()
        nz = non / non.std()
        g[t] = math.sqrt(1 - cfg.nonlin) * lz + math.sqrt(cfg.nonlin) * nz
    # scale so that r2_oos(r, mu) hits the ceiling in expectation:
    #   1 - E(noise^2) / E((mu + noise)^2) = c  <=>  E(mu^2) = c / (1 - c) * E(noise^2)
    en2 = float(np.mean(noise**2))
    target = cfg.ceiling / (1 - cfg.ceiling) * en2 - cfg.premium**2
    scale = math.sqrt(max(target, 0.0) / float(np.mean(g**2)))
    mu = cfg.premium + scale * g
    return Panel(cfg, X, mu + noise, mu, beta, industry, mkt)


def ceiling(P: Panel, months) -> float:
    m = np.asarray(months)
    return r2_oos(P.r[m], P.mu[m])


def months_to_detect(r2_by_month, z: float = 2.0) -> float:
    """Months of monthly R-squared needed for the mean to sit z standard errors from zero (i.i.d. months)."""
    x = np.asarray(r2_by_month, float)
    m, s = x.mean(), x.std(ddof=1)
    return float((z * s / m) ** 2) if m > 0 else math.inf


# ---------------------------------------------------------------------------------------------------------------------
# Daily series (added for Book 12, chapter 2): several assets with GARCH volatility and a planted, persistent drift.
#     SeriesConfig(assets, days, seed, drift_ic, drift_half_life, signal_noise, vol, garch_alpha, garch_beta, t_df,
#                  k_noise, vol_break, vol_mult)
#     series(cfg) -> dict(r (T, A) daily log returns, sigma (T, A) conditional volatility of r[t], drift (T, A) the
#                    expected return of day t + 1 known at the close of day t (truth), F (T, A, k) features known at the
#                    close of day t, names)
# Features: a noisy reading of the drift (in volatility units), 5- and 20-day past returns, the ratio of short to long
# realised volatility, and k_noise pure-noise features. The drift is an AR(1) with the given half-life, scaled so that
# its correlation with the next day's return is drift_ic.
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SeriesConfig:
    assets: int = 20
    days: int = 2520
    seed: int = 1
    drift_ic: float = 0.04            # correlation of the true drift with the next day's return
    drift_half_life: float = 20.0     # days
    signal_noise: float = 1.5         # noise sd of the drift reading, in drift sds
    vol: float = 0.015                # unconditional daily volatility
    garch_alpha: float = 0.06
    garch_beta: float = 0.92
    t_df: float = 5.0
    k_noise: int = 3
    vol_break: int | None = None      # from this day on, every shock is multiplied by vol_mult (a volatility regime)
    vol_mult: float = 1.0


def series(cfg: SeriesConfig | None = None) -> dict:
    cfg = cfg or SeriesConfig()
    rng = np.random.default_rng(cfg.seed)
    T, A = cfg.days, cfg.assets
    phi = 0.5 ** (1.0 / cfg.drift_half_life)
    # drift sd d so that corr(d_t, r_t+1) = ic with r = d + sigma z:  d^2 / (d^2 + vol^2) = ic^2
    dsd = cfg.vol * cfg.drift_ic / math.sqrt(1 - cfg.drift_ic**2)
    omega = cfg.vol**2 * (1 - cfg.garch_alpha - cfg.garch_beta)
    tsc = math.sqrt((cfg.t_df - 2) / cfg.t_df)
    drift = np.zeros((T, A))
    r = np.zeros((T, A))
    sig = np.zeros((T, A))
    d = dsd * rng.standard_normal(A)
    h = np.full(A, cfg.vol**2)
    for t in range(T):
        mult = cfg.vol_mult if (cfg.vol_break is not None and t >= cfg.vol_break) else 1.0
        sig[t] = np.sqrt(h) * mult                                       # the shock's scale, known at t - 1
        z = tsc * rng.standard_t(cfg.t_df, A)
        r[t] = (drift[t - 1] if t > 0 else 0.0) + sig[t] * z
        h = omega + cfg.garch_alpha * (sig[t] / mult * z) ** 2 + cfg.garch_beta * h
        d = phi * d + math.sqrt(1 - phi**2) * dsd * rng.standard_normal(A)
        drift[t] = d
    reading = drift / dsd + cfg.signal_noise * rng.standard_normal((T, A))
    c = np.cumsum(r, axis=0)

    def past(w):
        out = np.full((T, A), np.nan)
        out[w:] = c[w:] - c[:-w]
        return out

    r2 = np.cumsum(r**2, axis=0)

    def rv(w):
        out = np.full((T, A), np.nan)
        out[w:] = np.sqrt((r2[w:] - r2[:-w]) / w)
        return out

    feats = [reading, past(5), past(20), rv(5) / rv(60)] + [rng.standard_normal((T, A)) for _ in range(cfg.k_noise)]
    names = ["signal", "ret_5", "ret_20", "vol_ratio"] + [f"noise_{i}" for i in range(cfg.k_noise)]
    return {"r": r, "sigma": sig, "drift": drift, "F": np.stack(feats, axis=-1), "names": names}


# ---------------------------------------------------------------------------------------------------------------------
# Conditional factor panel (added for Book 12, chapter 9): betas that are nonlinear functions of characteristics.
#     FactorConfig(n, months, L, K, seed, nonlin, premia, factor_vol, spec_vol)
#     factor_panel(cfg) -> dict(Z (T, n, L) ranked characteristics known at month end t, r (T, n) return of month t + 1,
#                           beta (T, n, K) true conditional betas, f (T, K) factor returns of month t + 1,
#                           mu (T, n) = beta . premia, the truth, lin_beta (T, n, K) the betas' linear part)
# Each beta_k(c) = a_k . c + nonlin-weighted quadratic and interaction terms of the first characteristics, scaled to
# unit cross-sectional variance and shifted to mean one for the first (market-like) factor.
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FactorConfig:
    n: int = 300
    months: int = 240
    L: int = 10
    K: int = 3
    seed: int = 1
    nonlin: float = 0.5               # share of each beta's cross-sectional variance that is nonlinear
    premia: tuple = (0.006, 0.004, 0.003)
    factor_vol: tuple = (0.045, 0.03, 0.025)
    spec_vol: float = 0.08


def factor_panel(cfg: FactorConfig | None = None) -> dict:
    cfg = cfg or FactorConfig()
    rng = np.random.default_rng(cfg.seed)
    T, n, L, K = cfg.months, cfg.n, cfg.L, cfg.K
    phi = np.linspace(0.8, 0.98, L)
    lat = rng.standard_normal((n, L))
    Z = np.empty((T, n, L))
    for t in range(T):
        lat = phi * lat + np.sqrt(1 - phi**2) * rng.standard_normal((n, L))
        Z[t] = _ranks(lat.T).T
    A = rng.standard_normal((K, L)) * (rng.random((K, L)) < 0.5)
    for k in range(K):
        A[k, k] = 1.5                                                    # each factor has one dominant characteristic
    beta = np.empty((T, n, K))
    lin = np.empty((T, n, K))
    for t in range(T):
        c = Z[t]
        for k in range(K):
            li = c @ A[k]
            nl = (c[:, (k + 1) % L] ** 2 - 1 / 3) + c[:, k] * c[:, (k + 2) % L] + np.abs(c[:, (k + 3) % L]) - 0.5
            li = (li - li.mean()) / li.std()
            nl = (nl - nl.mean()) / nl.std()
            b = np.sqrt(1 - cfg.nonlin) * li + np.sqrt(cfg.nonlin) * nl
            beta[t, :, k] = b * 0.5 + (1.0 if k == 0 else 0.0)
            lin[t, :, k] = np.sqrt(1 - cfg.nonlin) * li * 0.5 + (1.0 if k == 0 else 0.0)
    lam, vol = np.asarray(cfg.premia[:K]), np.asarray(cfg.factor_vol[:K])
    f = lam + vol * rng.standard_normal((T, K))
    e = cfg.spec_vol * rng.standard_normal((T, n))
    r = np.einsum("tnk,tk->tn", beta, f) + e
    return {"Z": Z, "r": r, "beta": beta, "f": f, "mu": beta @ lam, "lin_beta": lin, "premia": lam}
