"""firm.invmm -- inventory models for market making (One Quant Book 11, chapter 3).

The model. The mid is S_t = S_0 + sigma W_t. The market maker quotes S - delta_b and S + delta_a; market sell orders
hit its bid at intensity A exp(-k delta_b), market buys lift its ask at intensity A exp(-k delta_a) (the fill
intensity). Cash X and inventory q follow the fills.

* Avellaneda-Stoikov (exponential utility, risk aversion gamma, horizon T): the reservation price and the total
  spread of their approximate solution,
      r = S - q gamma sigma^2 (T - t),     delta_a + delta_b = gamma sigma^2 (T - t) + (2 / gamma) ln(1 + gamma / k),
  quotes r -/+ half the spread.
* Cartea-Jaimungal (risk-neutral, running inventory penalty phi q^2, terminal penalty alpha q^2, inventory in
  [-qmax, qmax]): with h(t, q) = ln(omega(t, q)) / k, omega(t) = expm(M (T - t)) z, z_q = exp(-alpha k q^2),
  M tridiagonal with M[q, q] = -phi k q^2 and A e^{-1} next to the diagonal; the optimal depths are
      delta_a(t, q) = 1/k + h(t, q) - h(t, q - 1),    delta_b(t, q) = 1/k + h(t, q) - h(t, q + 1),
  and a side is not quoted at the inventory bound it would breach.
* Fill intensity estimation: from the time a quoter spent at each depth and the fills it got there, a log-linear
  fit ln(fills / time) = ln A - k delta.
* A vectorised simulator of the model (many paths at once, common random numbers across policies).

Units are whatever the caller uses (the chapter uses ticks and seconds).

API (stable):
    as_quotes(s, q, tau, gamma, sigma, k)          (reservation price, half-spread, bid, ask)
    CJSolution(A, k, phi, alpha, qmax, T, n)       .depths(t, q) -> (delta_b, delta_a) (nan when not quoted);
                                                   .table: arrays (n + 1, 2 qmax + 1) for bid and ask on a time grid
    estimate_intensity(depth, time, fills)         (A, k) by weighted least squares on log rates
    simulate(policy, T, dt, sigma, A, k, paths, seed, qmax)
                                                   policy(t, q) -> (delta_b, delta_a) arrays (nan: no quote);
                                                   returns {'pnl', 'q_T', 'q_abs_mean', 'q2_int' (integral of q^2),
                                                   'fills', 'spread_paid'} per path
    symmetric(half)                                a policy quoting half on both sides, whatever the inventory
    as_policy(gamma, sigma, k, T)                  the Avellaneda-Stoikov quotes as depths from the mid
    cj_policy(sol)                                 a CJSolution's depths as a policy
    TouchSolution(lam, c, phi, alpha, qmax, T, n)  the large-tick version: on each side the only choice is to rest at
                                                   the touch (filled at intensity lam, earning c per fill net of
                                                   adverse selection) or not; .post(t, q) -> (bid?, ask?) booleans
    simulate(..., mid='gauss'|'binomial', jump=0)  the mid step: sigma sqrt(dt) Z, or +/- sigma sqrt(dt) (the paper's);
                                                   jump: the mid moves by that much against the market maker after each
                                                   of its fills (adverse selection)
    CJSolution(..., mu=0, eps=0)                   with a drift mu of the mid and an expected adverse move eps per fill
                                                   (chapter 4; the long-horizon and multi-asset versions are in
                                                   firm.multimm)
"""
from __future__ import annotations

import math

import numpy as np
from scipy.linalg import expm


def as_quotes(s: float, q: float, tau: float, gamma: float, sigma: float, k: float):
    r = s - q * gamma * sigma**2 * tau
    half = 0.5 * (gamma * sigma**2 * tau + (2.0 / gamma) * math.log(1.0 + gamma / k))
    return r, half, r - half, r + half


class CJSolution:
    """Cartea-Jaimungal market making with a running inventory penalty, solved exactly on a time grid."""

    def __init__(self, A: float, k: float, phi: float, alpha: float, qmax: int, T: float, n: int = 200,
                 mu: float = 0.0, eps: float = 0.0):
        self.A, self.k, self.phi, self.alpha, self.qmax, self.T, self.n = A, k, phi, alpha, qmax, T, n
        qs = np.arange(-qmax, qmax + 1)
        m = len(qs)
        M = np.diag(k * (mu * qs - phi * qs.astype(float) ** 2))
        off = A * math.exp(-1.0 - k * eps)
        M += np.diag(np.full(m - 1, off), 1) + np.diag(np.full(m - 1, off), -1)
        z = np.exp(-alpha * k * qs.astype(float) ** 2)
        self.times = np.linspace(0.0, T, n + 1)
        step = expm(M * (T / n))
        omega = np.empty((n + 1, m))
        omega[n] = z / z.max()
        for i in range(n - 1, -1, -1):
            w = step @ omega[i + 1]
            omega[i] = w / w.max()                  # a constant per time drops out of every depth (differences in q)
        h = np.log(np.maximum(omega, 1e-300)) / k
        bid = np.full((n + 1, m), np.nan)
        ask = np.full((n + 1, m), np.nan)
        ask[:, 1:] = 1.0 / k + eps + h[:, 1:] - h[:, :-1]      # selling takes q to q - 1
        bid[:, :-1] = 1.0 / k + eps + h[:, :-1] - h[:, 1:]     # buying takes q to q + 1
        self.h, self.bid, self.ask, self.qs = h, bid, ask, qs

    def depths(self, t, q):
        i = np.clip(np.rint(np.asarray(t, float) / self.T * self.n).astype(int), 0, self.n)
        j = np.asarray(q, int) + self.qmax
        return self.bid[i, j], self.ask[i, j]


class TouchSolution:
    """Market making when the only price is the touch (a large-tick book): h(t, q) solves, backwards from
    h(T, q) = -alpha q^2 on an explicit time grid,
        dh/dt = phi q^2 - lam max(0, c + h(q - 1) - h(q)) [q > -qmax] - lam max(0, c + h(q + 1) - h(q)) [q < qmax],
    and the policy rests on a side exactly when the bracket of that side is positive."""

    def __init__(self, lam: float, c: float, phi: float, alpha: float, qmax: int, T: float, n: int = 2000):
        self.qmax, self.T, self.n = qmax, T, n
        qs = np.arange(-qmax, qmax + 1).astype(float)
        m = len(qs)
        dt = T / n
        if lam * dt > 0.5:
            raise ValueError("time step too coarse for the explicit scheme")
        h = -alpha * qs**2
        post_b = np.zeros((n + 1, m), bool)
        post_a = np.zeros((n + 1, m), bool)
        H = np.empty((n + 1, m))
        H[n] = h
        for i in range(n, 0, -1):
            gain_a = np.full(m, -np.inf)
            gain_b = np.full(m, -np.inf)
            gain_a[1:] = c + h[:-1] - h[1:]
            gain_b[:-1] = c + h[1:] - h[:-1]
            post_a[i], post_b[i] = gain_a > 0, gain_b > 0
            h = h + dt * (-phi * qs**2 + lam * np.maximum(gain_a, 0.0) + lam * np.maximum(gain_b, 0.0))
            H[i - 1] = h
        post_a[0], post_b[0] = post_a[1], post_b[1]
        self.h, self.post_bid, self.post_ask, self.qs = H, post_b, post_a, qs

    def post(self, t: float, q: int) -> tuple[bool, bool]:
        i = min(max(int(round(t / self.T * self.n)), 0), self.n)
        j = min(max(int(q), -self.qmax), self.qmax) + self.qmax
        return bool(self.post_bid[i, j]), bool(self.post_ask[i, j])


def estimate_intensity(depth, time, fills) -> tuple[float, float]:
    """ln(fills / time) = ln A - k depth, weighted by the number of fills (depths with no fill are skipped)."""
    d, t, f = (np.asarray(a, float) for a in (depth, time, fills))
    ok = (f > 0) & (t > 0)
    w = np.sqrt(f[ok])
    X = np.column_stack([np.ones(ok.sum()), -d[ok]]) * w[:, None]
    y = np.log(f[ok] / t[ok]) * w
    (lna, k), *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(math.exp(lna)), float(k)


def symmetric(half: float):
    def policy(t, q):
        h = np.full(np.shape(q), half, float)
        return h, h.copy()
    return policy


def as_policy(gamma: float, sigma: float, k: float, T: float):
    def policy(t, q):
        tau = T - t
        half = 0.5 * (gamma * sigma**2 * tau + (2.0 / gamma) * math.log(1.0 + gamma / k))
        shift = np.asarray(q, float) * gamma * sigma**2 * tau
        return half + shift, half - shift
    return policy


def cj_policy(sol: CJSolution):
    def policy(t, q):
        return sol.depths(t, np.clip(q, -sol.qmax, sol.qmax))
    return policy


def simulate(policy, T: float, dt: float, sigma: float, A: float, k: float, paths: int, seed: int,
             qmax: int | None = None, mid: str = "gauss", jump: float = 0.0) -> dict:
    """Euler steps of the model: the mid moves sigma sqrt(dt) Z; each side fills with probability A exp(-k delta) dt.
    The random numbers depend only on (seed, step), so different policies see the same mid and the same uniforms."""
    rng = np.random.default_rng(seed)
    n = int(round(T / dt))
    s = np.zeros(paths)
    x = np.zeros(paths)
    q = np.zeros(paths, int)
    qabs = np.zeros(paths)
    q2 = np.zeros(paths)
    fills = np.zeros(paths, int)
    spread = np.zeros(paths)
    for i in range(n):
        t = i * dt
        db, da = policy(t, q)
        db, da = np.asarray(db, float), np.asarray(da, float)
        ub, ua, z = rng.random(paths), rng.random(paths), rng.standard_normal(paths)
        if mid == "binomial":
            z = np.where(z >= 0.0, 1.0, -1.0)
        buy = np.isfinite(db) & (ub < A * np.exp(-k * np.nan_to_num(db, nan=0.0)) * dt)
        sell = np.isfinite(da) & (ua < A * np.exp(-k * np.nan_to_num(da, nan=0.0)) * dt)
        if qmax is not None:
            buy &= q < qmax
            sell &= q > -qmax
        x += np.where(buy, -(s - np.nan_to_num(db)), 0.0) + np.where(sell, s + np.nan_to_num(da), 0.0)
        spread += np.where(buy, np.nan_to_num(db), 0.0) + np.where(sell, np.nan_to_num(da), 0.0)
        q += buy.astype(int) - sell.astype(int)
        fills += buy.astype(int) + sell.astype(int)
        s += sigma * math.sqrt(dt) * z - jump * (buy.astype(float) - sell.astype(float))
        qabs += np.abs(q) * dt
        q2 += q.astype(float) ** 2 * dt
    return {"pnl": x + q * s, "q_T": q.copy(), "q_abs_mean": qabs / T, "q2_int": q2, "fills": fills,
            "spread_paid": spread}

