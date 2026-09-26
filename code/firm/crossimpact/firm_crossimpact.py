"""firm.crossimpact -- latent liquidity, fair pricing and cross-impact (build of One Quant Book 10, chapter 13).

API (stable):
    llob(q, horizon, L, D, dt, width, dx, after)   the latent order book of Donier, Bonart, Mastromatteo and Bouchaud,
                                                   deterministic (no deposition, no cancellation): a signed density
                                                   phi(x) of latent orders (asks positive) that diffuses with
                                                   coefficient D (bids and asks annihilate where they meet), starting
                                                   from phi = L x; a buy metaorder removes q / horizon a second from the
                                                   asks at the price. Returns (times, price), the price
                                                   being the zero of phi
    fair_pricing(times, price, horizon)            the average price paid during the execution against the price after
                                                   it: (peak, average paid, final, final / peak)
    estimate(r, q)                                 Lambda in r_t = Lambda q_t + noise, by least squares
    symmetric_psd(Lambda)                          the nearest symmetric positive semi-definite matrix (Frobenius)
    explained_by_other(r, q)                       for each asset, the share of its return variance explained by the
                                                   other assets' flows beyond its own (increase in R^2)
    liquidation(Lambda, rho, times, X, joint, rho_cross)   the cheapest schedule to sell the vector X under
                                                   transient impact: own impact Lambda_ii exp(-rho |t_i - t_j|),
                                                   cross-impact Lambda_ij exp(-rho_cross |t_i - t_j|); jointly, or
                                                   asset by asset ignoring the cross terms;
                                                   returns (schedule, true cost)
"""
from __future__ import annotations

import numpy as np


def _zero(x, phi) -> float:
    i = int(np.flatnonzero((phi[:-1] <= 0) & (phi[1:] > 0))[0])
    return float(x[i] - phi[i] * (x[i + 1] - x[i]) / (phi[i + 1] - phi[i]))


def llob(q: float, horizon: float, L: float = 1.0, D: float = 1.0, dt: float = 0.002,
         width: float = 40.0, dx: float = 0.1, after: float = 0.0):
    x = np.arange(-width, width + dx / 2, dx)
    phi = L * x
    rate = q / horizon
    times, price = [0.0], [0.0]
    steps = int(round((horizon + after) / dt))
    for k in range(steps):
        t = (k + 1) * dt
        lap = np.zeros_like(phi)
        lap[1:-1] = (phi[2:] - 2 * phi[1:-1] + phi[:-2]) / dx**2
        phi = phi + D * dt * lap
        phi[0], phi[-1] = L * x[0], L * x[-1]          # far ends stay on the linear profile
        if t <= horizon + 1e-12:
            need = rate * dt                             # shares taken from the nearest asks
            i = int(np.flatnonzero(phi > 0)[0])
            while need > 0 and i < len(phi):
                take = min(need, phi[i] * dx)
                phi[i] -= take / dx
                need -= take
                i += 1
        times.append(t)
        price.append(_zero(x, phi))
    return np.array(times), np.array(price)


def fair_pricing(times, price, horizon: float) -> dict:
    t, p = np.asarray(times), np.asarray(price)
    during = t <= horizon
    peak = float(p[during][-1])
    return {"peak": peak, "average": float(p[during].mean()), "final": float(p[-1]), "ratio": float(p[-1] / peak)}


def estimate(r, q) -> np.ndarray:
    r, q = np.asarray(r, float), np.asarray(q, float)
    b, *_ = np.linalg.lstsq(q, r, rcond=None)                # r = q B, B = Lambda'
    return b.T


def symmetric_psd(lam) -> np.ndarray:
    s = 0.5 * (np.asarray(lam, float) + np.asarray(lam, float).T)
    w, v = np.linalg.eigh(s)
    return (v * np.maximum(w, 0.0)) @ v.T


def explained_by_other(r, q) -> list[float]:
    r, q = np.asarray(r, float), np.asarray(q, float)
    out = []
    for i in range(r.shape[1]):
        y = r[:, i] - r[:, i].mean()

        def r2(cols, y=y):
            b, *_ = np.linalg.lstsq(q[:, cols], y, rcond=None)
            e = y - q[:, cols] @ b
            return 1 - e @ e / (y @ y)
        out.append(float(r2(list(range(q.shape[1]))) - r2([i])))
    return out


def liquidation(lam, rho: float, times, x_total, joint: bool = True,
                rho_cross: float | None = None):
    """Own impact decays at rho, cross-impact at rho_cross (default rho)."""
    lam = np.asarray(lam, float)
    t = np.asarray(times, float)
    dist = np.abs(t[:, None] - t[None, :])
    e = np.exp(-rho * dist)
    ec = np.exp(-(rho if rho_cross is None else rho_cross) * dist)
    n, k = len(t), len(lam)
    diag = np.diag(np.diag(lam))
    gamma = np.kron(diag, e) + np.kron(lam - diag, ec)       # asset-major blocks
    if joint:
        a = np.kron(np.eye(k), np.ones((1, n)))              # sum of each asset's trades
        m = np.block([[gamma, a.T], [a, np.zeros((k, k))]])
        sol = np.linalg.solve(m, np.concatenate([np.zeros(n * k), x_total]))
        q = sol[: n * k]
    else:
        w = np.linalg.solve(e, np.ones(n))
        q = np.concatenate([w * xi / w.sum() for xi in x_total])
    return q.reshape(k, n), float(0.5 * q @ gamma @ q)
