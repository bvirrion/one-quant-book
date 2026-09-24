"""Fourier pricing and a calibration pipeline (build of Book 5, Chapter 24).

Any model with a characteristic function phi(u, t) = E[exp(i u x_t)], x_t = ln(S_t / F_t), martingale-corrected,
is priced here by the Carr-Madan FFT (a whole log-strike grid at once) or by the COS method (Fang and Oosterlee:
a cosine expansion of the density on a truncated range), and calibrated by a pipeline: filter the quotes,
weight the price errors by vega, fit by Levenberg-Marquardt from yesterday's parameters with an optional
penalty on the change, report diagnostics and raise an alarm on parameter jumps.
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("bs", "heston"):
    sys.path.insert(0, str(FIRM / comp))
from firm_bs import black, implied_vol  # noqa: E402
from firm_heston import Heston  # noqa: E402


# ---------------------------------------------------------------- transform pricing
def cumulants(model, t: float, h: float = 1e-3) -> tuple[float, float]:
    """First two cumulants of x_t from ln phi by central differences: ln phi(u) = i c1 u - c2 u^2 / 2 + ..."""
    lp, lm = np.log(model.cf(np.array([h]), t))[0], np.log(model.cf(np.array([-h]), t))[0]
    return float(np.imag(lp - lm) / (2 * h)), float(-np.real(lp + lm) / (h * h))


def cos_calls(model, fwd: float, strikes, t: float, n: int = 160, width: float = 16.0, df: float = 1.0) -> np.ndarray:
    """European calls by the COS method: puts from the cosine coefficients of the density of y = ln(S_T / K) on
    [a, b] = c1 + ln(F / K) +- width sqrt(c2), then calls by parity. n terms, one cf evaluation per term and strike."""
    strikes = np.asarray(strikes, float)
    x0 = np.log(fwd / strikes)
    c1, c2 = cumulants(model, t)
    a = x0 + c1 - width * math.sqrt(c2)
    b = x0 + c1 + width * math.sqrt(c2)
    w = np.outer(math.pi / (b - a), np.arange(n))                   # u_k = k pi / (b - a), one row per strike
    phi = model.cf(w, t)
    aa = a[:, None]
    chi = (np.cos(-w * aa) - np.cos(0 * w) * np.exp(aa) + w * np.sin(-w * aa)) / (1 + w * w)
    with np.errstate(divide="ignore", invalid="ignore"):
        psi = np.where(w == 0, -aa, np.sin(-w * aa) / np.where(w == 0, 1.0, w))
    coef = 2 / (b - a)[:, None] * (psi - chi)                       # put payoff (1 - e^y)^+ on [a, 0]
    terms = np.real(phi * np.exp(1j * w * (x0 - a)[:, None])) * coef
    terms[:, 0] *= 0.5
    puts = df * strikes * terms.sum(axis=1)
    return puts + df * (fwd - strikes)


def lewis_calls(model, fwd: float, strikes, t: float, cuts=(0.0, 50.0, 200.0, 1000.0), nodes: int = 2000,
                df: float = 1.0) -> np.ndarray:
    """Reference calls by Lewis's integral with Gauss-Legendre panels (slow, accurate to about 1e-9 for Heston)."""
    strikes = np.asarray(strikes, float)
    ks = np.log(strikes / fwd)
    x, wts = np.polynomial.legendre.leggauss(nodes)
    total = np.zeros(len(strikes))
    for lo, hi in zip(cuts[:-1], cuts[1:], strict=True):
        u, w = 0.5 * (hi - lo) * x + 0.5 * (hi + lo), 0.5 * (hi - lo) * wts
        total += (np.real(np.exp(-1j * np.outer(ks, u)) * model.cf(u - 0.5j, t)[None, :]) / (u * u + 0.25)) @ w
    return df * (fwd - np.sqrt(fwd * strikes) / math.pi * total)


def carr_madan(model, fwd: float, t: float, n: int = 4096, eta: float = 0.25, alpha: float = 1.5,
               df: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Carr-Madan FFT: calls on the log-strike grid k_m = -b + m lam, lam = 2 pi / (n eta), b = n lam / 2, from the
    damped call transform psi(v) = df phi(v - (alpha + 1) i) / (alpha^2 + alpha - v^2 + i (2 alpha + 1) v),
    Simpson weights on the v grid. Returns (strikes, calls)."""
    lam = 2 * math.pi / (n * eta)
    b = n * lam / 2
    j = np.arange(n)
    v = eta * j
    psi = df * model.cf(v - (alpha + 1) * 1j, t) / (alpha * alpha + alpha - v * v + 1j * (2 * alpha + 1) * v)
    simpson = eta / 3 * (3 + (-1.0) ** (j + 1) - (j == 0))
    y = np.fft.fft(np.exp(1j * b * v) * psi * simpson)
    k = -b + lam * j
    return fwd * np.exp(k), fwd * np.exp(-alpha * k) / math.pi * np.real(y)


def carr_madan_at(model, fwd: float, strikes, t: float, **kw) -> np.ndarray:
    """Carr-Madan calls interpolated (cubic in log-strike, on the four nearest grid points) at given strikes."""
    ks, cs = carr_madan(model, fwd, t, **kw)
    x, target = np.log(ks), np.log(np.asarray(strikes, float))
    out = []
    for z in target:
        i = int(np.searchsorted(x, z)) - 2
        xs, ys = x[i:i + 4], cs[i:i + 4]
        out.append(sum(ys[m] * np.prod([(z - xs[q]) / (xs[m] - xs[q]) for q in range(4) if q != m]) for m in range(4)))
    return np.array(out)


# ---------------------------------------------------------------- quotes, weights, filter
@dataclass(frozen=True)
class QuoteSet:
    """Option quotes on one underlying, in implied volatility: expiry t, strike, bid and ask."""
    t: np.ndarray
    strike: np.ndarray
    bid: np.ndarray
    ask: np.ndarray
    fwd: float

    def mid(self) -> np.ndarray:
        return 0.5 * (self.bid + self.ask)

    def subset(self, mask) -> "QuoteSet":
        return QuoteSet(self.t[mask], self.strike[mask], self.bid[mask], self.ask[mask], self.fwd)


def black_vega(fwd: float, strike, t, vol) -> np.ndarray:
    strike, t, vol = (np.asarray(x, float) for x in (strike, t, vol))
    d1 = (np.log(fwd / strike) + 0.5 * vol * vol * t) / (vol * np.sqrt(t))
    return fwd * np.sqrt(t) * np.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)


def mid_prices(q: QuoteSet) -> np.ndarray:
    return np.array([black(q.fwd, k, t, 1.0, v, "C") for t, k, v in zip(q.t, q.strike, q.mid(), strict=True)])


def filter_quotes(q: QuoteSet, max_spread: float = 0.04, max_sd: float = 3.0) -> tuple[np.ndarray, dict]:
    """Keep quotes that are two-sided, not crossed, not too wide (in volatility) and within max_sd standard
    deviations of the forward; returns the mask and the count dropped for each reason (first reason wins)."""
    reasons = {
        "no bid": q.bid <= 0,
        "crossed": q.bid > q.ask,
        "wide": q.ask - q.bid > max_spread,
        "far": np.abs(np.log(q.strike / q.fwd)) > max_sd * np.maximum(q.mid(), 1e-6) * np.sqrt(q.t),
    }
    keep = np.ones(len(q.t), bool)
    counts = {}
    for name, bad in reasons.items():
        counts[name] = int((keep & bad).sum())
        keep &= ~bad
    return keep, counts


# ---------------------------------------------------------------- the calibration
def heston_from(z) -> Heston:
    """Unconstrained z = (ln v0, ln kappa, ln vbar, ln eta, artanh rho) -> Heston."""
    return Heston(math.exp(z[0]), math.exp(z[1]), math.exp(z[2]), math.exp(z[3]), math.tanh(z[4]))


def heston_to(m: Heston) -> np.ndarray:
    return np.array([math.log(m.v0), math.log(m.kappa), math.log(m.vbar), math.log(m.eta), math.atanh(m.rho)])


def model_prices(model, q: QuoteSet, pricer=cos_calls) -> np.ndarray:
    out = np.empty(len(q.t))
    for t in np.unique(q.t):
        m = q.t == t
        out[m] = pricer(model, q.fwd, q.strike[m], float(t))
    return out


@dataclass(frozen=True)
class Fit:
    model: object
    z: np.ndarray
    rmse: float           # of the weighted residuals (volatility units under vega weights)
    penalty: float
    iterations: int
    condition: float      # condition number of the weighted Jacobian at the solution


def calibrate(q: QuoteSet, z0, make=heston_from, weights=None, prior=None, reg: float = 0.0,
              max_iter: int = 100, pricer=cos_calls) -> Fit:
    """Levenberg-Marquardt on weighted price errors w_i (model_i - mid_i), plus sqrt(reg) (z - prior) when a prior
    (yesterday's z) is given. Default weights 1 / vega turn price errors into volatility errors."""
    target = mid_prices(q)
    w = 1 / black_vega(q.fwd, q.strike, q.t, q.mid()) if weights is None else np.asarray(weights, float)
    z = np.asarray(z0, float).copy()
    prior = None if prior is None else np.asarray(prior, float)

    def residuals(zz):
        r = w * (model_prices(make(zz), q, pricer) - target)
        if prior is not None and reg > 0:
            r = np.concatenate([r, math.sqrt(reg) * (zz - prior)])
        return r
    r = residuals(z)
    cost, lam, it, going = float(r @ r), 1e-3, 0, True
    while going and it < max_iter:
        it += 1
        jac = np.column_stack([(residuals(z + 1e-6 * e) - r) / 1e-6 for e in np.eye(len(z))])
        a, g = jac.T @ jac, jac.T @ r
        going = False
        while lam < 1e10:
            step = np.linalg.solve(a + lam * np.diag(np.diag(a) + 1e-14), -g)
            with np.errstate(all="ignore"):
                r_new = residuals(z + step)
            c_new = float(r_new @ r_new) if np.all(np.isfinite(r_new)) else math.inf
            if c_new < cost:
                going = cost - c_new >= 1e-12 * cost and float(np.max(np.abs(step))) >= 1e-9
                z, r, cost, lam = z + step, r_new, c_new, max(lam / 3, 1e-12)
                break
            lam *= 4
    n_q = len(q.t)
    fit_part = r[:n_q]
    sv = np.linalg.svd(jac[:n_q], compute_uv=False)
    return Fit(make(z), z, float(math.sqrt(fit_part @ fit_part / n_q)), float(r[n_q:] @ r[n_q:]), it,
               float(sv[0] / sv[-1]) if sv[-1] > 0 else math.inf)


def vol_errors(model, q: QuoteSet, pricer=cos_calls) -> np.ndarray:
    """Model implied volatility minus mid volatility, quote by quote (out-of-the-money side)."""
    prices = model_prices(model, q, pricer)
    out = []
    for c, t, k, v in zip(prices, q.t, q.strike, q.mid(), strict=True):
        right = "C" if k >= q.fwd else "P"
        p = c if right == "C" else c - (q.fwd - k)
        out.append(implied_vol(max(p, 1e-14), q.fwd, k, float(t), 1.0, right) - v)
    return np.array(out)


def jump_alarm(z_new, z_old, limits) -> list[int]:
    """Indices of the parameters whose change in z exceeds its limit."""
    d = np.abs(np.asarray(z_new) - np.asarray(z_old))
    return [i for i, (x, lim) in enumerate(zip(d, limits, strict=True)) if x > lim]

