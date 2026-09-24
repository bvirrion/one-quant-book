"""Jump and Levy models behind one interface (build of Book 5, Chapter 13).

Every model gives the characteristic function phi(u, t) = E[exp(i u x_t)] of x_t = ln(S_t / F_t), already
martingale-corrected (E[e^x] = 1), for real or complex u. Chapter 24's transform engine consumes exactly
that; here calls are priced by Lewis's single integral on a grid long enough for short expiries, where
the characteristic functions of pure-jump models decay slowly.

    Merton          diffusion sigma + Poisson(lam) jumps, log-jump N(mu, delta^2)
    Kou             diffusion sigma + Poisson(lam) jumps, double exponential: up with probability p,
                    rate eta1 (> 1), down with rate eta2
    Bates           Heston (chapter 10) + Merton jumps
    VarianceGamma   Brownian motion with drift theta and volatility sigma run on a gamma clock of
                    variance rate nu (Madan, Carr and Chang)
    EventJump       diffusion sigma + one scheduled jump before expiry: log-jump a with probability p,
                    b otherwise
"""
import math
import pathlib
import sys
from dataclasses import astuple, dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("bs", "heston"):
    sys.path.insert(0, str(FIRM / comp))
from firm_bs import black, implied_vol  # noqa: E402
from firm_heston import Heston  # noqa: E402

_GL400 = np.polynomial.legendre.leggauss(400)
U = np.concatenate([np.linspace(1e-8, 2000.0, 40001), np.geomspace(2000.0, 1e6, 4001)[1:]])


def _gauss_jump(u, mu: float, delta: float):
    return np.exp(1j * u * mu - 0.5 * delta * delta * u * u)


@dataclass(frozen=True)
class Merton:
    sigma: float
    lam: float
    mu: float
    delta: float

    def cf(self, u, t: float):
        u = np.asarray(u, complex)
        kbar = math.exp(self.mu + 0.5 * self.delta ** 2) - 1
        drift = -0.5 * self.sigma ** 2 - self.lam * kbar
        return np.exp(t * (1j * u * drift - 0.5 * self.sigma ** 2 * u * u
                           + self.lam * (_gauss_jump(u, self.mu, self.delta) - 1)))

    def cumulants(self, t: float) -> tuple[float, float, float]:
        m, d, lam = self.mu, self.delta, self.lam
        return (t * (self.sigma ** 2 + lam * (m * m + d * d)), t * lam * (m ** 3 + 3 * m * d * d),
                t * lam * (m ** 4 + 6 * m * m * d * d + 3 * d ** 4))

    def series_call(self, fwd: float, strike: float, t: float, n_max: int = 60) -> float:
        """Merton's formula: a Poisson mixture of Black prices, conditioning on the number of jumps."""
        kbar = math.exp(self.mu + 0.5 * self.delta ** 2) - 1
        out, w = 0.0, math.exp(-self.lam * t)
        for n in range(n_max):
            if n:
                w *= self.lam * t / n
            f_n = fwd * math.exp(n * (self.mu + 0.5 * self.delta ** 2) - self.lam * kbar * t)
            vol_n = math.sqrt(self.sigma ** 2 + n * self.delta ** 2 / t)
            out += w * black(f_n, strike, t, 1.0, vol_n, "C")
        return out


@dataclass(frozen=True)
class Kou:
    sigma: float
    lam: float
    p: float
    eta1: float
    eta2: float

    def cf(self, u, t: float):
        u = np.asarray(u, complex)
        jump = self.p * self.eta1 / (self.eta1 - 1j * u) + (1 - self.p) * self.eta2 / (self.eta2 + 1j * u)
        kbar = self.p * self.eta1 / (self.eta1 - 1) + (1 - self.p) * self.eta2 / (self.eta2 + 1) - 1
        drift = -0.5 * self.sigma ** 2 - self.lam * kbar
        return np.exp(t * (1j * u * drift - 0.5 * self.sigma ** 2 * u * u + self.lam * (jump - 1)))

    def cumulants(self, t: float) -> tuple[float, float, float]:
        def m(n: int) -> float:
            return math.factorial(n) * (self.p / self.eta1 ** n + (1 - self.p) * (-1) ** n / self.eta2 ** n)
        return t * (self.sigma ** 2 + self.lam * m(2)), t * self.lam * m(3), t * self.lam * m(4)


@dataclass(frozen=True)
class Bates:
    v0: float
    kappa: float
    vbar: float
    eta: float
    rho: float
    lam: float
    mu: float
    delta: float

    def cf(self, u, t: float):
        u = np.asarray(u, complex)
        kbar = math.exp(self.mu + 0.5 * self.delta ** 2) - 1
        jumps = np.exp(t * self.lam * (_gauss_jump(u, self.mu, self.delta) - 1 - 1j * u * kbar))
        return Heston(self.v0, self.kappa, self.vbar, self.eta, self.rho).cf(u, t) * jumps


@dataclass(frozen=True)
class VarianceGamma:
    sigma: float
    nu: float
    theta: float

    def cf(self, u, t: float):
        u = np.asarray(u, complex)
        omega = math.log(1 - self.theta * self.nu - 0.5 * self.sigma ** 2 * self.nu) / self.nu
        return np.exp(1j * u * omega * t) * (1 - 1j * u * self.theta * self.nu
                                            + 0.5 * self.sigma ** 2 * self.nu * u * u) ** (-t / self.nu)

    def cumulants(self, t: float) -> tuple[float, float, float]:
        s, n, th = self.sigma, self.nu, self.theta
        return (t * (s * s + th * th * n), t * (2 * th ** 3 * n * n + 3 * s * s * th * n),
                t * (3 * s ** 4 * n + 12 * s * s * th * th * n * n + 6 * th ** 4 * n ** 3))

    def conditional_call(self, fwd: float, strike: float, t: float) -> float:
        """Condition on the gamma clock g ~ Gamma(t / nu, scale nu): x is then normal, so the call is a Black
        price with forward F e^(omega t + theta g + sigma^2 g / 2) and total variance sigma^2 g."""
        shape = t / self.nu
        omega = math.log(1 - self.theta * self.nu - 0.5 * self.sigma ** 2 * self.nu) / self.nu
        z, w = _GL400
        y, w = 0.5 * (z + 1), 0.5 * w
        if shape < 1:          # density singular at 0: g = gmax y^(1 / shape) makes the integrand smooth in y
            gmax = self.nu * (shape + 40 * math.sqrt(shape) + 60)
            g = gmax * y ** (1 / shape)
            weight = w * np.exp(-g / self.nu) * gmax ** shape / (self.nu ** shape * math.gamma(shape + 1))
        else:                  # plain quadrature on [0, mean + 12 standard deviations]
            gmax = self.nu * (shape + 12 * math.sqrt(shape) + 12)
            g = gmax * y
            weight = gmax * w * g ** (shape - 1) * np.exp(-g / self.nu) / (self.nu ** shape * math.gamma(shape))
        vals = np.array([black(fwd * math.exp(omega * t + self.theta * gi + 0.5 * self.sigma ** 2 * gi), strike,
                               1.0, 1.0, self.sigma * math.sqrt(gi), "C") if gi > 0 else max(fwd - strike, 0.0)
                         for gi in g])
        return float(np.sum(weight * vals))


@dataclass(frozen=True)
class EventJump:
    sigma: float
    p: float
    a: float
    b: float

    @classmethod
    def from_up(cls, sigma: float, p: float, a: float) -> "EventJump":
        """The down move that makes the event fair: p e^a + (1 - p) e^b = 1."""
        return cls(sigma, p, a, math.log((1 - p * math.exp(a)) / (1 - p)))

    def _norm(self) -> float:
        return self.p * math.exp(self.a) + (1 - self.p) * math.exp(self.b)

    def cf(self, u, t: float):
        u = np.asarray(u, complex)
        c = math.log(self._norm())
        jump = self.p * np.exp(1j * u * (self.a - c)) + (1 - self.p) * np.exp(1j * u * (self.b - c))
        return np.exp(-0.5 * self.sigma ** 2 * t * (1j * u + u * u)) * jump

    def mixture_call(self, fwd: float, strike: float, t: float) -> float:
        """Exact price: a two-point mixture of Black prices."""
        c = self._norm()
        return (self.p * black(fwd * math.exp(self.a) / c, strike, t, 1.0, self.sigma, "C")
                + (1 - self.p) * black(fwd * math.exp(self.b) / c, strike, t, 1.0, self.sigma, "C"))


def call_prices(model, fwd: float, strikes, t: float, df: float = 1.0) -> np.ndarray:
    """European calls by Lewis's integral: C = df [F - sqrt(F K) / pi int Re(e^(-i u k) phi(u - i/2)) /
    (u^2 + 1/4) du], k = ln(K / F), on a grid that reaches u = 10^6 for slowly decaying phi."""
    strikes = np.asarray(strikes, float)
    ks = np.log(strikes / fwd)
    phi = model.cf(U - 0.5j, t)
    integrand = np.real(np.exp(-1j * np.outer(ks, U)) * phi[None, :]) / (U * U + 0.25)
    return df * (fwd - np.sqrt(fwd * strikes) / math.pi * np.trapezoid(integrand, U, axis=1))


def implied_vols(model, fwd: float, strikes, t: float) -> np.ndarray:
    out = []
    for k, c in zip(strikes, call_prices(model, fwd, strikes, t), strict=True):
        right = "C" if k >= fwd else "P"
        price = c if right == "C" else c - (fwd - k)
        out.append(implied_vol(max(price, 1e-14), fwd, k, t, 1.0, right))
    return np.array(out)


def skew_kurtosis(model, t: float) -> tuple[float, float]:
    """Skewness and excess kurtosis of ln(S_t / F_t) from the model's cumulants."""
    c2, c3, c4 = model.cumulants(t)
    return c3 / c2 ** 1.5, c4 / c2 ** 2


def calibrate(make, z0, quotes, fwd: float, max_iter: int = 80, lam: float = 1e-2):
    """Levenberg-Marquardt on implied-volatility residuals for any model: make(z) builds the model from an
    unconstrained vector z (transforms inside make keep every step admissible); quotes are (t, strikes, vols).
    Returns (model, z, rmse)."""
    def residuals(z):
        m = make(z)
        return np.concatenate([implied_vols(m, fwd, ks, t) - vols for t, ks, vols in quotes])
    z = np.asarray(z0, float)
    r = residuals(z)
    cost = float(r @ r)
    for _ in range(max_iter):
        h = 1e-5
        jac = np.column_stack([(residuals(z + h * e) - r) / h for e in np.eye(len(z))])
        a, g = jac.T @ jac, jac.T @ r
        while True:
            step = np.linalg.solve(a + lam * np.diag(np.diag(a) + 1e-12), -g)
            try:
                r_new = residuals(z + step)
                c_new = float(r_new @ r_new)
            except (ValueError, FloatingPointError, OverflowError, ZeroDivisionError):
                c_new = math.inf
            if c_new < cost:
                z, r, cost, lam = z + step, r_new, c_new, max(lam / 3, 1e-9)
                break
            lam *= 4
            if lam > 1e8:
                return make(z), z, math.sqrt(cost / len(r))
        if float(np.max(np.abs(step))) < 1e-8:
            break
    return make(z), z, math.sqrt(cost / len(r))


def params(model) -> tuple[float, ...]:
    return astuple(model)
