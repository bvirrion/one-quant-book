"""Short-rate models (build of One Quant Book 6, chapter 7).

Hull-White one-factor model in its Gaussian form, fitted exactly to an initial discount curve:
  r_t = f(0, t) + x_t,  dx = (y(t) - kappa x) dt + sigma(t) dW,  x_0 = 0,
  y(t) = int_0^t exp(-2 kappa (t - u)) sigma(u)^2 du,
  P(t, T) = P(0, T) / P(0, t) * exp(-B(t, T) x_t - B(t, T)^2 y(t) / 2),  B = (1 - exp(-kappa (T - t))) / kappa.
sigma(t) is piecewise constant. Zero-coupon bond options in closed form, European swaptions by
Jamshidian's decomposition, co-terminal calibration of sigma, and a Hull-White trinomial tree (constant
sigma) fitted to the curve by forward induction. Also: Vasicek bond prices, and the correlation of
zero-rate changes in the two-factor Gaussian (G2++) model. Times in years; the curve is any object with
`df_t(t)`. Swaps: annual fixed leg paying K on unit accruals, floating leg worth P(T0) - P(Tn).
"""
import math
from collections.abc import Callable, Sequence

import numpy as np

SQRT2 = math.sqrt(2.0)


def _cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / SQRT2)


def B(kappa: float, tau: float) -> float:
    return tau if abs(kappa) < 1e-12 else (1 - math.exp(-kappa * tau)) / kappa


class HullWhite:
    """Hull-White model on a discount curve, with sigma piecewise constant on [knots[i-1], knots[i])."""

    def __init__(self, curve, kappa: float, sigmas: Sequence[float], knots: Sequence[float] = ()):
        if len(sigmas) != len(knots) + 1:
            raise ValueError("need one more sigma than knots")
        self.curve, self.kappa, self.sigmas, self.knots = curve, kappa, list(sigmas), list(knots)

    def P0(self, t: float) -> float:
        return 1.0 if t <= 0 else self.curve.df_t(t)

    def _pieces(self, t: float):
        edges = [0.0] + [k for k in self.knots if k < t] + [t]
        for i in range(len(edges) - 1):
            yield edges[i], edges[i + 1], self.sigmas[min(i, len(self.sigmas) - 1)]

    def y(self, t: float) -> float:
        """int_0^t exp(-2 kappa (t - u)) sigma(u)^2 du."""
        k = self.kappa
        tot = 0.0
        for a, b, s in self._pieces(t):
            if abs(k) < 1e-12:
                tot += s * s * (b - a)
            else:
                tot += s * s * (math.exp(-2 * k * (t - b)) - math.exp(-2 * k * (t - a))) / (2 * k)
        return tot

    def bond(self, t: float, T: float, x: float, yt: float | None = None) -> float:
        b = B(self.kappa, T - t)
        yt = self.y(t) if yt is None else yt
        return self.P0(T) / self.P0(t) * math.exp(-b * x - 0.5 * b * b * yt)

    def bond_vol(self, T: float, S: float) -> float:
        """Standard deviation of ln P(T, S) seen from 0: B(T, S) sqrt(y(T))."""
        return B(self.kappa, S - T) * math.sqrt(self.y(T))

    def zbo(self, T: float, S: float, K: float, call: bool = True) -> float:
        """Option at T on the zero-coupon bond maturing at S, strike K."""
        v = self.bond_vol(T, S)
        ps, pt = self.P0(S), self.P0(T)
        h = math.log(ps / (K * pt)) / v + v / 2
        c = ps * _cdf(h) - K * pt * _cdf(h - v)
        return c if call else c - ps + K * pt

    def swaption(self, T: float, tenor: int, K: float, payer: bool = True) -> float:
        """European swaption (annual unit accruals) by Jamshidian's decomposition: the receiver is a
        call on a coupon bond, i.e. a portfolio of calls on zero-coupon bonds struck at P(T, t_i; x*)."""
        pay = [T + i for i in range(1, tenor + 1)]
        cf = [K] * tenor
        cf[-1] += 1.0

        yt = self.y(T)

        def bond_value(x):
            return sum(c * self.bond(T, t, x, yt) for c, t in zip(cf, pay, strict=True))
        lo, hi = -1.0, 1.0
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if bond_value(mid) > 1.0 else (lo, mid)
        xs = 0.5 * (lo + hi)
        return sum(c * self.zbo(T, t, self.bond(T, t, xs, yt), call=not payer) for c, t in zip(cf, pay, strict=True))

    def annuity_forward(self, T: float, tenor: int) -> tuple[float, float]:
        ann = sum(self.P0(T + i) for i in range(1, tenor + 1))
        return ann, (self.P0(T) - self.P0(T + tenor)) / ann


def normal_price(f: float, k: float, t: float, vol: float, annuity: float, payer: bool = True) -> float:
    s = vol * math.sqrt(t)
    d = (f - k) / s
    call = (f - k) * _cdf(d) + s * math.exp(-0.5 * d * d) / math.sqrt(2 * math.pi)
    return annuity * (call if payer else call - (f - k))


def implied_normal(model_price: float, f: float, k: float, t: float, annuity: float, payer: bool = True) -> float:
    lo, hi = 1e-7, 0.05
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if normal_price(f, k, t, mid, annuity, payer) < model_price else (lo, mid)
    return 0.5 * (lo + hi)


def calibrate_coterminal(curve, kappa: float, expiries: Sequence[int], final: int,
                         vols: Callable[[int], float], constant: bool = False) -> HullWhite:
    """Fit sigma (one level, or one per interval between expiries, bootstrapped in order) so that the
    at-the-money payer swaptions expiring at each e into the swap ending at `final` reprice at the
    normal volatility vols(e)."""
    def targets(model_curve):
        out = []
        for e in expiries:
            ann, f = HullWhite(model_curve, kappa, [0.01]).annuity_forward(e, final - e)
            out.append((e, f, ann, normal_price(f, f, e, vols(e), ann)))
        return out
    tg = targets(curve)
    if constant:
        def err(s):
            m = HullWhite(curve, kappa, [s])
            return sum((m.swaption(e, final - e, f) - p) ** 2 for e, f, _, p in tg)
        lo, hi = 1e-4, 0.05
        for _ in range(60):                      # golden-section search on a unimodal error
            a, b = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
            lo, hi = (lo, b) if err(a) < err(b) else (a, hi)
        return HullWhite(curve, kappa, [0.5 * (lo + hi)])
    sig: list[float] = []
    for e, f, _, p in tg:
        lo, hi = 1e-5, 0.05
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            m = HullWhite(curve, kappa, sig + [mid], list(expiries[:len(sig)]))
            lo, hi = (mid, hi) if m.swaption(e, final - e, f) < p else (lo, mid)
        sig.append(0.5 * (lo + hi))
    return HullWhite(curve, kappa, sig, list(expiries[:-1]))


# ---- the trinomial tree (constant sigma) ------------------------------------------------------------------
class HWTree:
    """Hull-White (1994) trinomial tree for x = r - alpha(t), dx = -kappa x dt + sigma dW, with alpha(t)
    fitted step by step so that the tree reprices the curve's discount factors."""

    def __init__(self, curve, kappa: float, sigma: float, horizon: float, dt: float):
        self.kappa, self.sigma, self.dt = kappa, sigma, dt
        n = int(round(horizon / dt))
        self.n = n
        dx = sigma * math.sqrt(3 * dt)
        jmax = max(1, math.ceil(0.184 / (kappa * dt)))
        self.dx, self.jmax = dx, jmax
        js = np.arange(-jmax, jmax + 1)
        m = -kappa * js * dt                                         # E[dx] / dx in units of j
        k = np.where(js == jmax, -1, np.where(js == -jmax, 1, 0))   # branching shift at the edges
        mk = m + (-k)                                                 # expected move relative to j + k
        self.pu = 1 / 6 + (mk * mk + mk) / 2
        self.pm = 2 / 3 - mk * mk
        self.pd = 1 / 6 + (mk * mk - mk) / 2
        self.k = k
        self.alpha = np.zeros(n + 1)
        q = np.zeros(2 * jmax + 1)
        q[jmax] = 1.0
        width = [min(i, jmax) for i in range(n + 1)]
        for i in range(n + 1):
            p_next = curve.df_t((i + 1) * dt)
            ws = width[i]
            idx = np.arange(jmax - ws, jmax + ws + 1)
            s = np.sum(q[idx] * np.exp(-js[idx] * dx * dt))
            self.alpha[i] = math.log(s / p_next) / dt
            if i == n:
                break
            disc = np.exp(-(self.alpha[i] + js * dx) * dt)
            qn = np.zeros_like(q)
            for jj in idx:
                c = jj + k[jj]
                w = q[jj] * disc[jj]
                qn[c + 1] += w * self.pu[jj]
                qn[c] += w * self.pm[jj]
                qn[c - 1] += w * self.pd[jj]
            q = qn
        self.js, self.width = js, width

    def rates(self, i: int) -> np.ndarray:
        return self.alpha[i] + self.js * self.dx

    def step_back(self, v: np.ndarray, i: int) -> np.ndarray:
        """Values at step i from values at step i + 1."""
        c = np.arange(len(v)) + self.k
        up, mid, dn = np.clip(c + 1, 0, len(v) - 1), np.clip(c, 0, len(v) - 1), np.clip(c - 1, 0, len(v) - 1)
        cont = self.pu * v[up] + self.pm * v[mid] + self.pd * v[dn]
        return np.exp(-self.rates(i) * self.dt) * cont

    def zero_bonds_at(self, i_start: int, i_pay: int) -> np.ndarray:
        v = np.ones(2 * self.jmax + 1)
        for i in range(i_pay - 1, i_start - 1, -1):
            v = self.step_back(v, i)
        return v

    def european_swaption(self, T: float, tenor: int, K: float, payer: bool = True) -> float:
        it = int(round(T / self.dt))
        per = int(round(1.0 / self.dt))
        bonds = [self.zero_bonds_at(it, it + per * i) for i in range(1, tenor + 1)]
        swap = 1.0 - bonds[-1] - K * sum(bonds)                    # payer swap value at T
        v = np.maximum(swap if payer else -swap, 0.0)
        for i in range(it - 1, -1, -1):
            v = self.step_back(v, i)
        return float(v[self.jmax])


# ---- Vasicek and two-factor Gaussian ------------------------------------------------------------------------
def vasicek_bond(r: float, tau: float, kappa: float, xbar: float, sigma: float) -> float:
    """Zero-coupon bond price in Vasicek: A(tau) exp(-B(tau) r)."""
    b = B(kappa, tau)
    ln_a = (xbar - sigma * sigma / (2 * kappa * kappa)) * (b - tau) - sigma * sigma * b * b / (4 * kappa)
    return math.exp(ln_a - b * r)


def zero_rate_vol(kappa: float, sigma: float, tau: float) -> float:
    """Instantaneous normal volatility of the tau-maturity zero rate in a one-factor Gaussian model."""
    return sigma * B(kappa, tau) / tau


def g2_correlation(tau1: float, tau2: float, k1: float, k2: float, s1: float, s2: float, rho: float) -> float:
    """Correlation of instantaneous changes of two zero rates in G2++ (it is 1 in any one-factor model)."""
    b = [(B(k1, t) / t, B(k2, t) / t) for t in (tau1, tau2)]

    def cov(u, v):
        return u[0] * v[0] * s1 * s1 + u[1] * v[1] * s2 * s2 + rho * s1 * s2 * (u[0] * v[1] + u[1] * v[0])
    return cov(b[0], b[1]) / math.sqrt(cov(b[0], b[0]) * cov(b[1], b[1]))
