"""firm.multimm -- extensions of the inventory framework (One Quant Book 11, chapter 4).

Built on firm.invmm's running-penalty model (fill intensity A exp(-k delta), penalty phi q^2 per unit time):

* inventory bounds and the long horizon: as T - t grows, omega(t) = expm(M (T - t)) z tends to the eigenvector of M's
  largest eigenvalue, so the depths stop depending on time; with a Gaussian eigenvector exp(-beta (q - q0)^2 / 2),
  beta^2 = phi k e / A, they have the closed form
      delta_b(q) = 1/k + eps + (2 (q - q0) + 1) c / 2,   delta_a(q) = 1/k + eps - (2 (q - q0) - 1) c / 2,
  c = beta / k = sqrt(phi e / (A k)), accurate while c is small;
* a drift mu of the mid adds k mu q to M's diagonal: the market maker quotes as if its inventory were q - q0,
  q0 = mu / (2 phi), i.e. it targets the position q0;
* an expected adverse move eps per fill multiplies the off-diagonal of M by exp(-k eps) and adds eps to both depths; a
  permanent move xi of the mid against the market maker after each fill is the same problem with eps = xi / 2 (the
  substitution h -> h - xi q^2 / 2);
* several assets sharing A and k with a joint penalty phi q' cov q: the same linearisation on the grid
  {-qmax..qmax}^d, solved for the long horizon by the Perron eigenvector.

API (stable):
    stationary(A, k, phi, qmax, mu=0, eps=0)       bid and ask depth arrays over q = -qmax..qmax (nan: not quoted)
    asymptotic(A, k, phi, q, mu=0, eps=0)          the closed form above (bid, ask)
    MultiStationary(A, k, phi, cov, qmax)          .depths(q (paths, d)) -> (bid, ask), each (paths, d)
    simulate_multi(policy, T, dt, cov, A, k, paths, seed, qmax)
                                                   correlated mids; returns {'pnl', 'q_T', 'risk' (time-average of
                                                   q' cov q), 'fills'} per path
    table_policy(bid, ask, qmax)                   a (t, q) -> depths policy for firm.invmm.simulate from depth arrays
"""
from __future__ import annotations

import math

import numpy as np


def table_policy(bid, ask, qmax: int):
    def policy(t, q):
        j = np.clip(q, -qmax, qmax) + qmax
        return bid[j], ask[j]
    return policy


def _tridiag(A: float, k: float, phi: float, qmax: int, mu: float, eps: float):
    qs = np.arange(-qmax, qmax + 1).astype(float)
    off = A * math.exp(-1.0 - k * eps)
    band = np.full(len(qs) - 1, off)
    M = np.diag(k * (mu * qs - phi * qs**2)) + np.diag(band, 1) + np.diag(band, -1)
    return M, qs


def stationary(A: float, k: float, phi: float, qmax: int, mu: float = 0.0, eps: float = 0.0):
    """Long-horizon depths: omega(t) tends to the eigenvector of the largest eigenvalue of M (symmetric), so the depths
    stop depending on time."""
    M, qs = _tridiag(A, k, phi, qmax, mu, eps)
    w, V = np.linalg.eigh(M)
    v = np.abs(V[:, -1])
    h = np.log(np.maximum(v / v.max(), 1e-300)) / k
    bid = np.full(len(qs), np.nan)
    ask = np.full(len(qs), np.nan)
    ask[1:] = 1.0 / k + eps + h[1:] - h[:-1]
    bid[:-1] = 1.0 / k + eps + h[:-1] - h[1:]
    return bid, ask


def asymptotic(A: float, k: float, phi: float, q, mu: float = 0.0, eps: float = 0.0):
    """Closed form of the stationary depths from a Gaussian eigenvector exp(-beta (q - q0)^2 / 2),
    beta^2 = phi k e / A."""
    q = np.asarray(q, float)
    c = math.sqrt(phi * math.e / (A * k))
    q0 = mu / (2.0 * phi) if phi > 0 else 0.0
    return 1.0 / k + eps + (2 * (q - q0) + 1) / 2 * c, 1.0 / k + eps - (2 * (q - q0) - 1) / 2 * c


class MultiStationary:
    """d assets sharing A and k: the long-horizon solution of the running-penalty problem with penalty phi q' cov q on
    the grid {-qmax..qmax}^d, from the Perron eigenvector of the (2 qmax + 1)^d linear system."""

    def __init__(self, A: float, k: float, phi: float, cov, qmax: int):
        cov = np.asarray(cov, float)
        d = cov.shape[0]
        side = 2 * qmax + 1
        grid = np.array(np.meshgrid(*[np.arange(-qmax, qmax + 1)] * d, indexing="ij")).reshape(d, -1).T
        n = len(grid)
        M = np.zeros((n, n))
        M[np.arange(n), np.arange(n)] = -phi * k * np.einsum("ni,ij,nj->n", grid, cov, grid)
        off = A * math.exp(-1.0)
        strides = [side ** (d - 1 - i) for i in range(d)]
        for i in range(d):
            ok = grid[:, i] < qmax
            src = np.flatnonzero(ok)
            M[src, src + strides[i]] = off
            M[src + strides[i], src] = off
        w, V = np.linalg.eigh(M)
        v = np.abs(V[:, -1])
        self.h = (np.log(np.maximum(v / v.max(), 1e-300)) / k).reshape([side] * d)
        self.k, self.qmax, self.d = k, qmax, d

    def depths(self, q):
        """q: (paths, d) integer inventories; returns (bid, ask), each (paths, d), nan where a side is not quoted."""
        q = np.asarray(q, int)
        idx = q + self.qmax
        here = self.h[tuple(idx.T)]
        bid = np.full(q.shape, np.nan)
        ask = np.full(q.shape, np.nan)
        for i in range(self.d):
            up, dn = idx.copy(), idx.copy()
            up[:, i] += 1
            dn[:, i] -= 1
            can_up, can_dn = idx[:, i] < 2 * self.qmax, idx[:, i] > 0
            hu = np.where(can_up, self.h[tuple(np.minimum(up, 2 * self.qmax).T)], np.nan)
            hd = np.where(can_dn, self.h[tuple(np.maximum(dn, 0).T)], np.nan)
            bid[:, i] = 1.0 / self.k + here - hu
            ask[:, i] = 1.0 / self.k + here - hd
        return bid, ask


def simulate_multi(policy, T: float, dt: float, cov, A: float, k: float, paths: int, seed: int,
                   qmax: int) -> dict:
    """d assets with correlated Gaussian mids (covariance cov per unit time); each side of each asset fills with
    probability A exp(-k delta) dt. P&L is summed over assets."""
    cov = np.asarray(cov, float)
    d = cov.shape[0]
    L = np.linalg.cholesky(cov)
    rng = np.random.default_rng(seed)
    n = int(round(T / dt))
    s = np.zeros((paths, d))
    x = np.zeros(paths)
    q = np.zeros((paths, d), int)
    risk = np.zeros(paths)
    fills = np.zeros(paths, int)
    for _ in range(n):
        db, da = policy(q)
        ub, ua, z = rng.random((paths, d)), rng.random((paths, d)), rng.standard_normal((paths, d))
        buy = np.isfinite(db) & (ub < A * np.exp(-k * np.nan_to_num(db)) * dt) & (q < qmax)
        sell = np.isfinite(da) & (ua < A * np.exp(-k * np.nan_to_num(da)) * dt) & (q > -qmax)
        x += (np.where(buy, -(s - np.nan_to_num(db)), 0.0) + np.where(sell, s + np.nan_to_num(da), 0.0)).sum(axis=1)
        q += buy.astype(int) - sell.astype(int)
        fills += (buy.astype(int) + sell.astype(int)).sum(axis=1)
        s += math.sqrt(dt) * z @ L.T
        risk += np.einsum("pi,ij,pj->p", q, cov, q) * dt
    return {"pnl": x + (q * s).sum(axis=1), "q_T": q.copy(), "risk": risk / T, "fills": fills}
