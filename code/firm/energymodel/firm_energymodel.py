"""Commodity forward-curve model, spread options, storage and swing (build of One Quant Book 6, ch. 16).

Two-factor forward-curve model (the forward-curve form of Schwartz-Smith): under the pricing measure
  dF(t,T) / F(t,T) = sigma_s e^{-kappa (T - t)} dW_1 + sigma_l dW_2,   d<W_1, W_2> = rho dt,
so ln F(t,T) = ln F(0,T) + e^{-kappa (T - t)} chi_t + xi_t - V(t,T) / 2, with chi an Ornstein-Uhlenbeck
factor (from 0) and xi a Brownian factor, both simulated exactly. Short-dated forwards are more volatile
(the Samuelson effect). Spread options: Margrabe (zero strike), Kirk's approximation, Monte Carlo.
Storage and swing: dynamic programming over an integer inventory (or rights) grid; intrinsic value on
today's forwards, rolling intrinsic by re-optimising on simulated forward curves, and least-squares Monte
Carlo on simulated spot (regression of continuation values on 1, S, S^2 per end inventory).
Prices per unit of energy; volumes in integer units; one period per delivery month.
"""
import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

ND = NormalDist()


@dataclass(frozen=True)
class TwoFactor:
    kappa: float
    sigma_s: float
    sigma_l: float
    rho: float

    def var(self, t: float, T: float) -> float:
        """Variance of ln F(t,T) accumulated from 0 to t."""
        k, a = self.kappa, math.exp(-self.kappa * (T - t))
        return (a * a * self.sigma_s ** 2 * (1 - math.exp(-2 * k * t)) / (2 * k) + self.sigma_l ** 2 * t
                + 2 * a * self.rho * self.sigma_s * self.sigma_l * (1 - math.exp(-k * t)) / k)

    def cov(self, t: float, T1: float, T2: float) -> float:
        k = self.kappa
        a1, a2 = math.exp(-k * (T1 - t)), math.exp(-k * (T2 - t))
        c = self.sigma_s * self.sigma_l * self.rho * (1 - math.exp(-k * t)) / k
        return (a1 * a2 * self.sigma_s ** 2 * (1 - math.exp(-2 * k * t)) / (2 * k) + self.sigma_l ** 2 * t
                + (a1 + a2) * c)

    def implied_vol(self, t_exp: float, T: float) -> float:
        return math.sqrt(self.var(t_exp, T) / t_exp)

    def simulate(self, times: list[float], paths: int, seed: int = 5) -> tuple[np.ndarray, np.ndarray]:
        """Factors (chi, xi) at each time, shape (paths, len(times)); antithetic pairs."""
        rng, k = np.random.default_rng(seed), self.kappa
        half = paths // 2
        chi, xi = np.zeros((2 * half, len(times))), np.zeros((2 * half, len(times)))
        c, x, prev = np.zeros(2 * half), np.zeros(2 * half), 0.0
        for j, t in enumerate(times):
            dt = t - prev
            e = math.exp(-k * dt)
            v1 = self.sigma_s ** 2 * (1 - e * e) / (2 * k)
            v2 = self.sigma_l ** 2 * dt
            c12 = self.rho * self.sigma_s * self.sigma_l * (1 - e) / k
            L = np.linalg.cholesky(np.array([[v1, c12], [c12, v2]]))
            z = rng.standard_normal((half, 2))
            z = np.concatenate([z, -z]) @ L.T
            c, x = e * c + z[:, 0], x + z[:, 1]
            chi[:, j], xi[:, j] = c, x
            prev = t
        return chi, xi

    def forward(self, F0T: float, t: float, T: float, chi, xi):
        return F0T * np.exp(math.exp(-self.kappa * (T - t)) * chi + xi - 0.5 * self.var(t, T))


def calibrate(quotes: list[tuple[float, float, float]], rho: float, guess=(1.0, 0.5, 0.2)) -> TwoFactor:
    """Fit kappa, sigma_s, sigma_l to (t_exp, T, implied vol) quotes by Levenberg-Marquardt."""
    p, lam = np.array(guess, float), 1e-3

    def res(q):
        m = TwoFactor(q[0], q[1], q[2], rho)
        return np.array([m.implied_vol(te, T) - v for te, T, v in quotes])

    r = res(p)
    for _ in range(200):
        J = np.column_stack([(res(p + h) - r) / 1e-6 for h in np.eye(3) * 1e-6])
        A = J.T @ J
        step = np.linalg.solve(A + lam * np.diag(np.diag(A)), -J.T @ r)
        q = np.maximum(p + step, 1e-4)
        rq = res(q)
        if rq @ rq < r @ r:
            p, r, lam = q, rq, lam / 3
            if np.max(np.abs(step)) < 1e-12:
                break
        else:
            lam *= 5
    return TwoFactor(float(p[0]), float(p[1]), float(p[2]), rho)


# ---- spread options ----------------------------------------------------------------------------------

def margrabe(F1: float, F2: float, T: float, s1: float, s2: float, rho: float, df: float = 1.0) -> float:
    """Option to receive F1 and pay F2 at T (zero strike), lognormal forwards."""
    s = math.sqrt(s1 * s1 + s2 * s2 - 2 * rho * s1 * s2)
    d1 = (math.log(F1 / F2) + 0.5 * s * s * T) / (s * math.sqrt(T))
    return df * (F1 * ND.cdf(d1) - F2 * ND.cdf(d1 - s * math.sqrt(T)))


def kirk(F1: float, F2: float, K: float, T: float, s1: float, s2: float, rho: float, df: float = 1.0) -> float:
    """Kirk's approximation to a call on F1 - F2 - K: F2 + K treated as lognormal with vol s2 F2 / (F2 + K)."""
    b = F2 / (F2 + K)
    s = math.sqrt(s1 * s1 - 2 * rho * s1 * s2 * b + (s2 * b) ** 2)
    d1 = (math.log(F1 / (F2 + K)) + 0.5 * s * s * T) / (s * math.sqrt(T))
    return df * (F1 * ND.cdf(d1) - (F2 + K) * ND.cdf(d1 - s * math.sqrt(T)))


def spread_mc(F1: float, F2: float, K: float, T: float, s1: float, s2: float, rho: float, df: float = 1.0,
              paths: int = 400_000, seed: int = 9) -> tuple[float, float]:
    """Monte Carlo price and standard error of the spread call (antithetic)."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((paths // 2, 2))
    z = np.concatenate([z, -z])
    w2 = rho * z[:, 0] + math.sqrt(1 - rho * rho) * z[:, 1]
    x1 = F1 * np.exp(s1 * math.sqrt(T) * z[:, 0] - 0.5 * s1 * s1 * T)
    x2 = F2 * np.exp(s2 * math.sqrt(T) * w2 - 0.5 * s2 * s2 * T)
    pay = df * np.maximum(x1 - x2 - K, 0.0)
    pair = 0.5 * (pay[: paths // 2] + pay[paths // 2:])
    return float(pay.mean()), float(pair.std(ddof=1) / math.sqrt(len(pair)))


# ---- storage and swing by dynamic programming -------------------------------------------------------

@dataclass(frozen=True)
class Facility:
    capacity: int            # units of working gas
    max_inject: int          # units per period
    max_withdraw: int        # units per period
    cost_in: float = 0.0     # per unit injected
    cost_out: float = 0.0    # per unit withdrawn
    start: int = 0
    end: int = 0             # inventory required at the end

    def actions(self, i: int) -> list[int]:
        return [a for a in range(-self.max_withdraw, self.max_inject + 1) if 0 <= i + a <= self.capacity]

    def cash(self, a: int, price):
        """Cash flow of changing inventory by a units at price (inject pays, withdraw receives)."""
        return -a * price - (self.cost_in * a if a > 0 else -self.cost_out * a)


def intrinsic(fac: Facility, prices: list[float], dfs: list[float],
              start: int | None = None) -> tuple[float, list[int]]:
    """Best deterministic schedule on one price per period (today's forwards) and its value."""
    n, cap = len(prices), fac.capacity
    V = np.full(cap + 1, -np.inf)
    V[fac.end if fac.end >= 0 else slice(None)] = 0.0
    policy = []
    for m in range(n - 1, -1, -1):
        W, best = np.full(cap + 1, -np.inf), np.zeros(cap + 1, int)
        for i in range(cap + 1):
            for a in fac.actions(i):
                v = dfs[m] * fac.cash(a, prices[m]) + V[i + a]
                if v > W[i]:
                    W[i], best[i] = v, a
        V = W
        policy.append(best)
    policy.reverse()
    i, plan = fac.start if start is None else start, []
    for m in range(n):
        a = int(policy[m][i])
        plan.append(a)
        i += a
    return float(V[fac.start if start is None else start]), plan


def lsm(fac: Facility, spot: np.ndarray, dfs: list[float], degree: int = 2) -> float:
    """Least-squares Monte Carlo value of the facility on simulated spot (paths x periods)."""
    npaths, n = spot.shape
    cap = fac.capacity
    V = np.full((npaths, cap + 1), -1e18)
    V[:, fac.end if fac.end >= 0 else slice(None)] = 0.0
    for m in range(n - 1, -1, -1):
        S = spot[:, m]
        X = np.column_stack([S ** d for d in range(degree + 1)])
        cont = np.empty_like(V)
        for j in range(cap + 1):
            if V[0, j] <= -1e17 and (V[:, j] <= -1e17).all():
                cont[:, j] = -1e18
            else:
                beta, *_ = np.linalg.lstsq(X, V[:, j], rcond=None)
                cont[:, j] = X @ beta
        W = np.full_like(V, -1e18)
        for i in range(cap + 1):
            best_est = np.full(npaths, -np.inf)
            chosen = np.zeros(npaths)
            for a in fac.actions(i):
                if (V[:, i + a] <= -1e17).all():
                    continue
                now = dfs[m] * fac.cash(a, S)
                est = now + cont[:, i + a]
                real = now + V[:, i + a]
                better = est > best_est
                best_est = np.where(better, est, best_est)
                chosen = np.where(better, real, chosen)
            W[:, i] = np.where(np.isfinite(best_est), chosen, -1e18)
        V = W
    return float(V[:, fac.start].mean())


def _first_actions(fac: Facility, prices: np.ndarray, dfs: list[float], inv: np.ndarray) -> np.ndarray:
    """First-period action of the intrinsic optimum on each row of forward prices (vectorised over rows)."""
    rows, n = prices.shape
    cap = fac.capacity
    V = np.full((rows, cap + 1), -np.inf)
    V[:, fac.end if fac.end >= 0 else slice(None)] = 0.0
    for m in range(n - 1, -1, -1):
        W = np.full_like(V, -np.inf)
        A = np.zeros((rows, cap + 1), int)
        for i in range(cap + 1):
            for a in fac.actions(i):
                v = dfs[m] * fac.cash(a, prices[:, m]) + V[:, i + a]
                better = v > W[:, i]
                W[:, i] = np.where(better, v, W[:, i])
                A[:, i] = np.where(better, a, A[:, i])
        V = W
    return A[np.arange(rows), inv]


def rolling_intrinsic(fac: Facility, model: TwoFactor, F0: list[float], T: list[float], dfs: list[float],
                      paths: int = 2000, seed: int = 5) -> float:
    """Re-optimise the intrinsic plan on each simulated forward curve at each period, act on the first
    period at spot; average discounted cash (forward hedges have zero expected P&L)."""
    chi, xi = model.simulate(T, paths, seed)
    total = np.zeros(chi.shape[0])
    inv = np.full(chi.shape[0], fac.start)
    n = len(T)
    for m in range(n):
        curves = np.column_stack([model.forward(F0[k], T[m], T[k], chi[:, m], xi[:, m]) for k in range(m, n)])
        a = _first_actions(fac, curves, [d / dfs[m] for d in dfs[m:]], inv)
        cash = np.where(a > 0, -a * curves[:, 0] - fac.cost_in * a, -a * curves[:, 0] + fac.cost_out * a)
        total += dfs[m] * cash
        inv = inv + a
    return float(total.mean())


def spot_paths(model: TwoFactor, F0: list[float], T: list[float], paths: int, seed: int = 5) -> np.ndarray:
    """Spot of each period = the forward for that period at its delivery time."""
    chi, xi = model.simulate(T, paths, seed)
    return np.column_stack([model.forward(F0[m], T[m], T[m], chi[:, m], xi[:, m]) for m in range(len(T))])


def swing_facility(total_rights: int, max_per_period: int, strike: float) -> Facility:
    """A swing contract as a facility: 'inventory' = rights used; taking a unit pays strike, receives spot.
    Expressed as withdrawals from a store that starts full of rights and may end anywhere."""
    return Facility(capacity=total_rights, max_inject=0, max_withdraw=max_per_period,
                    cost_out=strike, start=total_rights, end=-1)
