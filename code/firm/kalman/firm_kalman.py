"""firm.kalman -- linear Gaussian state-space models (One Quant Book 4, chapter 19).

Model: y_t = Z_t a_t + e_t, e_t ~ N(0, H);  a_{t+1} = T a_t + u_t, u_t ~ N(0, Q), with a_1 ~ N(a0, P0). The
observation matrix may vary with t (a regression with time-varying coefficients has Z_t = x_t). Missing
observations (NaN) skip the update. Filter with the prediction-error likelihood, Rauch-Tung-Striebel smoother,
EM for H and Q, maximum likelihood by Nelder-Mead, the local-level steady-state gain, a bootstrap particle
filter, and a streaming hedge-ratio tracker. NumPy only.

API (stable):
    kalman_filter(y, Z, T, H, Q, a0, P0)       dict(a_pred, P_pred, a_filt, P_filt, v, F, K, loglik)
    rts_smoother(kf, T)                        dict(a_smooth, P_smooth, P_lag) (P_lag: Cov(a_t, a_{t-1} | all))
    em(y, Z, T, H, Q, a0, P0, n_iter)          (H, Q, logliks): EM for the noise variances
    fit_mle(y, Z, T, a0, P0, h0, q0)           (H, Q, loglik) with scalar H and diagonal Q by maximum likelihood
    local_level_gain(q)                        steady-state Kalman gain for signal-to-noise ratio q
    particle_filter(y, n, init, step, loglik_obs, rng)   dict(mean, loglik, ess)
    HedgeTracker(q, h, beta0, p0)              .update(x, y) -> (predicted ratio used, updated ratio)
"""
from __future__ import annotations

import math

import numpy as np


def _Zt(Z, t, m):
    Z = np.asarray(Z, dtype=float)
    if Z.ndim == 2 and Z.shape[1] == m and Z.shape[0] > 1:
        return Z[t]
    return Z.reshape(-1)


def kalman_filter(y, Z, T, H, Q, a0, P0) -> dict:
    """Univariate observations y_t (NaN = missing). Z: (m,) constant or (n, m) time-varying."""
    y = np.asarray(y, dtype=float)
    T, Q = np.atleast_2d(np.asarray(T, float)), np.atleast_2d(np.asarray(Q, float))
    m = T.shape[0]
    n = y.size
    a, P = np.asarray(a0, float).reshape(m).copy(), np.atleast_2d(np.asarray(P0, float)).copy()
    out = {k: np.zeros((n, m)) for k in ("a_pred", "a_filt", "K")}
    out.update({k: np.zeros((n, m, m)) for k in ("P_pred", "P_filt")})
    v, F = np.full(n, np.nan), np.full(n, np.nan)
    ll = 0.0
    for t in range(n):
        out["a_pred"][t], out["P_pred"][t] = a, P
        z = _Zt(Z, t, m)
        if not np.isnan(y[t]):
            v[t] = y[t] - z @ a
            F[t] = float(z @ P @ z) + float(H)
            K = P @ z / F[t]
            a = a + K * v[t]
            P = P - np.outer(K, z @ P)
            out["K"][t] = K
            ll += -0.5 * (math.log(2 * math.pi * F[t]) + v[t] ** 2 / F[t])
        out["a_filt"][t], out["P_filt"][t] = a, P
        a = T @ a
        P = T @ P @ T.T + Q
    out.update({"v": v, "F": F, "loglik": ll})
    return out


def rts_smoother(kf: dict, T) -> dict:
    T = np.atleast_2d(np.asarray(T, float))
    af, Pf, ap, Pp = kf["a_filt"], kf["P_filt"], kf["a_pred"], kf["P_pred"]
    n, m = af.shape
    a_s, P_s = af.copy(), Pf.copy()
    P_lag = np.zeros((n, m, m))
    for t in range(n - 2, -1, -1):
        J = Pf[t] @ T.T @ np.linalg.inv(Pp[t + 1])
        a_s[t] = af[t] + J @ (a_s[t + 1] - ap[t + 1])
        P_s[t] = Pf[t] + J @ (P_s[t + 1] - Pp[t + 1]) @ J.T
        P_lag[t + 1] = P_s[t + 1] @ J.T
    return {"a_smooth": a_s, "P_smooth": P_s, "P_lag": P_lag}


def em(y, Z, T, H, Q, a0, P0, n_iter: int = 50) -> tuple[float, np.ndarray, list[float]]:
    """Shumway-Stoffer EM for scalar H and full Q, with Z, T, a0, P0 fixed; the likelihood never decreases."""
    y = np.asarray(y, dtype=float)
    T = np.atleast_2d(np.asarray(T, float))
    Q = np.atleast_2d(np.asarray(Q, float)).copy()
    m = T.shape[0]
    lls = []
    obs = ~np.isnan(y)
    for _ in range(n_iter):
        kf = kalman_filter(y, Z, T, H, Q, a0, P0)
        lls.append(kf["loglik"])
        sm = rts_smoother(kf, T)
        a_s, P_s, P_lag = sm["a_smooth"], sm["P_smooth"], sm["P_lag"]
        n = y.size
        hs = 0.0
        for t in np.flatnonzero(obs):
            z = _Zt(Z, t, m)
            hs += (y[t] - z @ a_s[t]) ** 2 + float(z @ P_s[t] @ z)
        H = hs / int(obs.sum())
        S = np.zeros((m, m))
        for t in range(1, n):
            d = a_s[t] - T @ a_s[t - 1]
            S += np.outer(d, d) + P_s[t] - T @ P_lag[t].T - P_lag[t] @ T.T + T @ P_s[t - 1] @ T.T
        Q = S / (n - 1)
    return float(H), Q, lls


def _nm(f, x0, step=0.5, tol=1e-10, max_iter=4000):
    x0 = np.asarray(x0, dtype=float)
    k = x0.size
    pts = [x0] + [x0 + step * np.eye(k)[i] for i in range(k)]
    vals = [f(p) for p in pts]
    for _ in range(max_iter):
        o = np.argsort(vals)
        pts, vals = [pts[i] for i in o], [vals[i] for i in o]
        if abs(vals[-1] - vals[0]) <= tol * (abs(vals[0]) + 1e-12):
            break
        c = np.mean(pts[:-1], axis=0)
        xr = c + (c - pts[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1])
            fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c)
            fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    return pts[int(np.argmin(vals))]


def fit_mle(y, Z, T, a0, P0, h0: float, q0) -> tuple[float, np.ndarray, float]:
    """Maximum likelihood over log H and the logs of a diagonal Q, by the prediction-error decomposition."""
    q0 = np.atleast_1d(np.asarray(q0, float))

    def nll(th):
        return -kalman_filter(y, Z, T, math.exp(th[0]), np.diag(np.exp(th[1:])), a0, P0)["loglik"]
    th = _nm(nll, np.concatenate([[math.log(h0)], np.log(q0)]))
    th = _nm(nll, th, step=0.1)
    return math.exp(th[0]), np.diag(np.exp(th[1:])), -nll(th)


def local_level_gain(q: float) -> float:
    """Steady-state gain of y_t = mu_t + e_t, mu_{t+1} = mu_t + u_t with q = Var(u) / Var(e):
    the predicted variance ratio p solves p^2 - q p - q = 0 and the gain is p / (1 + p)."""
    p = (q + math.sqrt(q * q + 4 * q)) / 2
    return p / (1 + p)


def particle_filter(y, n: int, init, step, loglik_obs, rng: np.random.Generator) -> dict:
    """Bootstrap filter (sequential importance resampling): propagate particles through the transition, weight by
    the observation density, resample (systematic) every step. init(n, rng) -> particles; step(x, rng) -> particles;
    loglik_obs(y_t, x) -> log densities. Returns filtered means, the log-likelihood estimate and the effective
    sample sizes before resampling."""
    y = np.asarray(y, dtype=float)
    x = init(n, rng)
    means, ess = np.empty(y.size), np.empty(y.size)
    ll = 0.0
    for t in range(y.size):
        if t > 0:
            x = step(x, rng)
        lw = loglik_obs(y[t], x)
        c = lw.max()
        w = np.exp(lw - c)
        ll += c + math.log(w.mean())
        w /= w.sum()
        means[t] = float(w @ x)
        ess[t] = 1.0 / float(w @ w)
        u = (rng.random() + np.arange(n)) / n
        x = x[np.minimum(np.searchsorted(np.cumsum(w), u), n - 1)]
    return {"mean": means, "loglik": ll, "ess": ess}


class HedgeTracker:
    """Streaming time-varying regression y_t = beta_t x_t + e_t, beta_{t+1} = beta_t + u_t."""

    def __init__(self, q: float, h: float, beta0: float = 1.0, p0: float = 1.0):
        self.q, self.h, self.beta, self.p = q, h, beta0, p0

    def update(self, x: float, y: float) -> tuple[float, float]:
        used = self.beta
        if not (math.isnan(x) or math.isnan(y)):
            f = x * x * self.p + self.h
            k = self.p * x / f
            self.beta += k * (y - x * self.beta)
            self.p -= k * x * self.p
        self.p += self.q
        return used, self.beta
