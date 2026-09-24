"""Barriers and digitals (build of Book 5, Chapter 15): digitals with and without a smile, the call-spread
overhedge, single-barrier closed forms with rebates (the reflection formulas in the form of Reiner and
Rubinstein), touch options, double no-touch by a sine series, the discrete-monitoring shift of Broadie,
Glasserman and Kou, static hedges (put-call symmetry and a calendar strip in the manner of Derman, Ergener and
Kani), and a Monte Carlo of discretely monitored barriers for checking.

Black-Scholes with rate r, dividend yield q, carry b = r - q, volatility sigma.
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import bs, ncdf, npdf  # noqa: E402

BGK_BETA = 0.5826                      # -zeta(1/2) / sqrt(2 pi), Broadie, Glasserman and Kou (1997)


# ---------------------------------------------------------------- digitals
def digital(s: float, k: float, t: float, r: float, q: float, vol: float, right: str = "C") -> float:
    """Cash-or-nothing digital paying 1: e^(-rT) N(+-d2)."""
    d2 = (math.log(s / k) + (r - q - 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
    return math.exp(-r * t) * ncdf(d2 if right == "C" else -d2)


def digital_delta(s: float, k: float, t: float, r: float, q: float, vol: float) -> float:
    """dDigital/dS for the call: e^(-rT) phi(d2) / (S sigma sqrt T)."""
    d2 = (math.log(s / k) + (r - q - 0.5 * vol * vol) * t) / (vol * math.sqrt(t))
    return math.exp(-r * t) * npdf(d2) / (s * vol * math.sqrt(t))


def digital_smile(s: float, k: float, t: float, r: float, q: float, vol_of_k, h: float | None = None) -> float:
    """Digital call under a smile: minus the strike derivative of the call price, which is the flat-volatility
    digital minus vega times the smile's slope in strike."""
    h = 1e-4 * k if h is None else h
    return -(bs(s, k + h, t, r, q, vol_of_k(k + h), "C") - bs(s, k - h, t, r, q, vol_of_k(k - h), "C")) / (2 * h)


def call_spread(s: float, k: float, t: float, r: float, q: float, vol_of_k, width: float, notional: float = 1.0,
                below: bool = True) -> float:
    """notional / width call spreads struck at (k - width, k) if below (the overhedge that dominates the digital),
    else at (k, k + width)."""
    lo, hi = (k - width, k) if below else (k, k + width)
    return notional / width * (bs(s, lo, t, r, q, vol_of_k(lo), "C") - bs(s, hi, t, r, q, vol_of_k(hi), "C"))


# ---------------------------------------------------------------- single barriers
def barrier(s: float, k: float, h: float, t: float, r: float, q: float, vol: float, kind: str, right: str = "C",
            rebate: float = 0.0) -> float:
    """Continuously monitored single barrier. kind in {'down-out', 'down-in', 'up-out', 'up-in'}; rebate paid at
    the hit for knock-outs and at expiry for knock-ins that never knock in."""
    b = r - q
    sv = vol * math.sqrt(t)
    mu = (b - 0.5 * vol * vol) / (vol * vol)
    lam = math.sqrt(mu * mu + 2 * r / (vol * vol))
    eta = 1 if kind.startswith("down") else -1
    phi = 1 if right == "C" else -1
    x1 = math.log(s / k) / sv + (1 + mu) * sv
    x2 = math.log(s / h) / sv + (1 + mu) * sv
    y1 = math.log(h * h / (s * k)) / sv + (1 + mu) * sv
    y2 = math.log(h / s) / sv + (1 + mu) * sv
    z = math.log(h / s) / sv + lam * sv
    dq, dr = math.exp((b - r) * t), math.exp(-r * t)
    hs = h / s
    a = phi * s * dq * ncdf(phi * x1) - phi * k * dr * ncdf(phi * x1 - phi * sv)
    bb = phi * s * dq * ncdf(phi * x2) - phi * k * dr * ncdf(phi * x2 - phi * sv)
    c = phi * s * dq * hs ** (2 * (mu + 1)) * ncdf(eta * y1) - phi * k * dr * hs ** (2 * mu) * ncdf(eta * y1 - eta * sv)
    d = phi * s * dq * hs ** (2 * (mu + 1)) * ncdf(eta * y2) - phi * k * dr * hs ** (2 * mu) * ncdf(eta * y2 - eta * sv)
    e = rebate * dr * (ncdf(eta * x2 - eta * sv) - hs ** (2 * mu) * ncdf(eta * y2 - eta * sv))
    f = rebate * (hs ** (mu + lam) * ncdf(eta * z) + hs ** (mu - lam) * ncdf(eta * z - 2 * eta * lam * sv))
    above = k > h
    table = {
        ("down-in", "C"): c + e if above else a - bb + d + e,
        ("up-in", "C"): a + e if above else bb - c + d + e,
        ("down-in", "P"): bb - c + d + e if above else a + e,
        ("up-in", "P"): a - bb + d + e if above else c + e,
        ("down-out", "C"): a - c + f if above else bb - d + f,
        ("up-out", "C"): f if above else a - bb + c - d + f,
        ("down-out", "P"): a - bb + c - d + f if above else f,
        ("up-out", "P"): bb - d + f if above else a - c + f,
    }
    return table[(kind, right)]


def hit_probability(s: float, h: float, t: float, r: float, q: float, vol: float) -> float:
    """Probability, under the pricing measure, that the price touches h before t (reflection principle)."""
    nu = r - q - 0.5 * vol * vol
    sv = vol * math.sqrt(t)
    x = math.log(h / s)
    if h < s:
        return ncdf((x - nu * t) / sv) + math.exp(2 * nu * x / (vol * vol)) * ncdf((x + nu * t) / sv)
    return ncdf((-x + nu * t) / sv) + math.exp(2 * nu * x / (vol * vol)) * ncdf((-x - nu * t) / sv)


def one_touch(s: float, h: float, t: float, r: float, q: float, vol: float, at_hit: bool = True) -> float:
    """Pays 1 if the barrier is touched: at the hit (the rebate formula) or at expiry."""
    if at_hit:
        kind = "down-out" if h < s else "up-out"
        return barrier(s, s, h, t, r, q, vol, kind, "C", rebate=1.0) - barrier(s, s, h, t, r, q, vol, kind, "C")
    return math.exp(-r * t) * hit_probability(s, h, t, r, q, vol)


def no_touch(s: float, h: float, t: float, r: float, q: float, vol: float) -> float:
    """Pays 1 at expiry if the barrier is never touched."""
    return math.exp(-r * t) * (1 - hit_probability(s, h, t, r, q, vol))


def double_no_touch(s: float, lo: float, hi: float, t: float, r: float, q: float, vol: float,
                    terms: int = 200) -> float:
    """Pays 1 at expiry if the price stays strictly inside (lo, hi): the killed transition density of the log price
    expanded in sines, p(y) = (2/a) sum_k sin(k pi y0 / a) sin(k pi y / a) e^(c (y - y0) - (mu^2 / (2 sigma^2) +
    k^2 pi^2 sigma^2 / (2 a^2)) T), integrated over y in closed form."""
    mu = r - q - 0.5 * vol * vol
    a = math.log(hi / lo)
    y0 = math.log(s / lo)
    c = mu / (vol * vol)
    total = 0.0
    for k in range(1, terms + 1):
        bk = k * math.pi / a
        integral = bk * (1 - (-1) ** k * math.exp(c * a)) / (c * c + bk * bk)
        total += (2 / a) * math.sin(bk * y0) * integral * math.exp(
            -c * y0 - (mu * mu / (2 * vol * vol) + 0.5 * bk * bk * vol * vol) * t)
    return math.exp(-r * t) * total


# ---------------------------------------------------------------- discrete monitoring
def bgk_shift(h: float, s: float, vol: float, dt: float) -> float:
    """The continuous barrier that prices a barrier monitored every dt: moved away from the spot by
    exp(beta sigma sqrt(dt))."""
    return h * math.exp((1 if h > s else -1) * BGK_BETA * vol * math.sqrt(dt))


def mc_barrier(s: float, k: float, h: float, t: float, r: float, q: float, vol: float, kind: str, right: str,
               steps: int, n_paths: int = 200_000, seed: int = 15) -> tuple[float, float]:
    """Monte Carlo of a barrier monitored at `steps` equally spaced dates (exact lognormal steps, antithetic).
    Returns (price, standard error)."""
    rng = np.random.default_rng(seed)
    dt = t / steps
    z = rng.standard_normal((n_paths // 2, steps))
    z = np.vstack([z, -z])
    logs = math.log(s) + np.cumsum((r - q - 0.5 * vol * vol) * dt + vol * math.sqrt(dt) * z, axis=1)
    paths = np.exp(logs)
    hit = (paths.min(axis=1) <= h) if kind.startswith("down") else (paths.max(axis=1) >= h)
    alive = ~hit if kind.endswith("out") else hit
    st = paths[:, -1]
    pay = np.maximum(st - k, 0.0) if right == "C" else np.maximum(k - st, 0.0)
    x = math.exp(-r * t) * pay * alive
    return float(x.mean()), float(x.std() / math.sqrt(len(x)))


# ---------------------------------------------------------------- static hedges
def symmetry_down_in_call(k: float, h: float, s: float, t: float, vol: float) -> float:
    """Put-call symmetry (zero carry, no smile): a down-and-in call with barrier h below strike k is worth
    (k / h) puts struck at h^2 / k, and the puts are its static hedge (swap them for calls at the hit)."""
    return k / h * bs(s, h * h / k, t, 0.0, 0.0, vol, "P")


def calendar_hedge(s: float, k: float, h: float, t: float, r: float, q: float, vol: float,
                   n: int) -> tuple[list[tuple[float, float, float]], float]:
    """Static hedge of an up-and-out call (h > k) in the manner of Derman, Ergener and Kani: the terminal payoff
    (S - k)^+ below h is a call at k less a call at h less (h - k) digitals at h; then, working back over n
    equally spaced dates t_i, a call struck at h expiring at t_(i+1) is added in the amount that makes the
    portfolio worth zero on the barrier at t_i. Returns the positions (weight, strike, expiry; strike 'digital'
    encoded as -h) and the hedge's price today."""
    book: list[tuple[float, float, float]] = [(1.0, k, t), (-1.0, h, t), (-(h - k), -h, t)]

    def value(spot: float, now: float) -> float:
        v = 0.0
        for w, kk, tt in book:
            tau = tt - now
            if tau <= 1e-12:
                continue
            v += w * (digital(spot, -kk, tau, r, q, vol) if kk < 0 else bs(spot, kk, tau, r, q, vol, "C"))
        return v

    times = [t * i / n for i in range(n)]
    for i in range(n - 1, -1, -1):
        ti, expiry = times[i], t * (i + 1) / n
        if i == n - 1:
            continue                                     # the terminal payoff is already zero at the barrier
        unit = bs(h, h, expiry - ti, r, q, vol, "C")
        book.append((-value(h, ti) / unit, h, expiry))
    return book, value(s, 0.0)


def calendar_hedge_on_barrier(book, h: float, r: float, q: float, vol: float, times) -> np.ndarray:
    """Value of a calendar hedge on the barrier at the given times (zero at its nodes)."""
    out = []
    for now in times:
        v = 0.0
        for w, kk, tt in book:
            tau = tt - now
            if tau <= 1e-12:
                continue
            v += w * (digital(h, -kk, tau, r, q, vol) if kk < 0 else bs(h, kk, tau, r, q, vol, "C"))
        out.append(v)
    return np.array(out)
