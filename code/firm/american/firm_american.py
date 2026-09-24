"""American options: quadratic approximation, exercise boundary, Bermudan exercise, and the
exercise decision before an ex-dividend date (build of Book 5, Chapter 6).

Continuous yield q (cost of carry b = r - q); discrete cash dividends go through the tree of
firm_binomial. The Barone-Adesi-Whaley approximation writes the early-exercise premium as a power
of spot with the exponent that solves the time-independent pricing equation, and finds the
critical price by Newton's method.
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import bs, ncdf  # noqa: E402


def _d1(s, k, t, b, vol):
    return (math.log(s / k) + (b + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))


def baw(spot: float, strike: float, t: float, r: float, q: float, vol: float, right: str = "P") -> tuple[float, float]:
    """Barone-Adesi-Whaley American price and critical spot (exercise boundary today)."""
    b = r - q
    m, n, kk = 2.0 * r / (vol * vol), 2.0 * b / (vol * vol), 1.0 - math.exp(-r * t)
    disc = math.exp((b - r) * t)
    if right == "C":
        if q <= 0.0:
            return bs(spot, strike, t, r, q, vol, "C"), math.inf       # never exercised early
        q2 = (-(n - 1) + math.sqrt((n - 1) ** 2 + 4 * m / kk)) / 2
        s = strike * 1.2
        for _ in range(100):                                        # S* - K = c(S*) + S*/q2 (1 - e^{(b-r)T} N(d1))
            d1 = _d1(s, strike, t, b, vol)
            f = s - strike - bs(s, strike, t, r, q, vol, "C") - s / q2 * (1 - disc * ncdf(d1))
            fp = 1 - disc * ncdf(d1) - (1 - disc * ncdf(d1)) / q2 + disc * math.exp(-0.5 * d1 * d1) / math.sqrt(
                2 * math.pi) / (vol * math.sqrt(t)) / q2
            step = f / fp
            s -= step
            if abs(step) < 1e-10:
                break
        a2 = s / q2 * (1 - disc * ncdf(_d1(s, strike, t, b, vol)))
        if spot >= s:
            return spot - strike, s
        return bs(spot, strike, t, r, q, vol, "C") + a2 * (spot / s) ** q2, s
    q1 = (-(n - 1) - math.sqrt((n - 1) ** 2 + 4 * m / kk)) / 2
    s = strike * 0.8
    for _ in range(100):                                            # K - S** = p(S**) - S**/q1 (1 - e^{(b-r)T} N(-d1))
        d1 = _d1(s, strike, t, b, vol)
        f = strike - s - bs(s, strike, t, r, q, vol, "P") + s / q1 * (1 - disc * ncdf(-d1))
        fp = -1 - (disc * ncdf(-d1) - 1) + (1 - disc * ncdf(-d1)) / q1 + disc * math.exp(-0.5 * d1 * d1) / math.sqrt(
            2 * math.pi) / (vol * math.sqrt(t)) / q1
        step = f / fp
        s -= step
        if abs(step) < 1e-10:
            break
    a1 = -s / q1 * (1 - disc * ncdf(-_d1(s, strike, t, b, vol)))
    if spot <= s:
        return strike - spot, s
    return bs(spot, strike, t, r, q, vol, "P") + a1 * (spot / s) ** q1, s


def put_boundary(strike: float, t: float, r: float, q: float, vol: float, n: int = 2000) -> list[tuple[float, float]]:
    """Exercise boundary of an American put from a Cox-Ross-Rubinstein tree: at each step, the highest
    node where exercising beats holding. Returns (time to expiry, boundary)."""
    dt = t / n
    u = math.exp(vol * math.sqrt(dt))
    d = 1 / u
    p = (math.exp((r - q) * dt) - d) / (u - d)
    disc = math.exp(-r * dt)
    j = np.arange(n + 1)
    s = strike * u ** (2 * j - n)
    v = np.maximum(strike - s, 0.0)
    out = []
    for step in range(n - 1, -1, -1):
        j = np.arange(step + 1)
        s = strike * u ** (2 * j - step)
        cont = disc * (p * v[1:] + (1 - p) * v[:-1])
        ex = strike - s
        v = np.maximum(cont, ex)
        mask = ex > cont + 1e-12
        if mask.any():
            out.append(((n - step) * dt, float(s[mask].max())))
    return out[::-1]


def bermudan_put(spot: float, strike: float, t: float, r: float, vol: float, n_ex: int, n: int = 1200) -> float:
    """Put exercisable only on n_ex equally spaced dates (the last one at expiry), on a CRR tree of n
    steps (n a multiple of n_ex)."""
    dt = t / n
    u = math.exp(vol * math.sqrt(dt))
    d = 1 / u
    p = (math.exp(r * dt) - d) / (u - d)
    disc = math.exp(-r * dt)
    every = n // n_ex
    j = np.arange(n + 1)
    v = np.maximum(strike - spot * u ** j * d ** (n - j), 0.0)
    for step in range(n - 1, -1, -1):
        v = disc * (p * v[1:] + (1 - p) * v[:-1])
        if step > 0 and step % every == 0:
            j = np.arange(step + 1)
            v = np.maximum(v, strike - spot * u ** j * d ** (step - j))
    return float(v[0])


def exercise_decision(spot: float, strike: float, dividend: float, t_left: float, r: float, vol: float) -> dict:
    """The night before an ex-date: exercise a call (and keep the dividend) or hold it through the drop.
    Holding is valued as a European call on the ex-dividend share (a lower bound if further dividends
    follow)."""
    ex = spot - strike
    hold = bs(spot - dividend, strike, t_left, r, 0.0, vol, "C")
    return {"exercise": ex, "hold": hold, "exercise_now": ex > hold}


def dividend_threshold(spot: float, strike: float, t_left: float, r: float, vol: float) -> float:
    """Smallest dividend for which exercising the call the night before the ex-date is optimal
    (bisection on the dividend)."""
    lo, hi = 0.0, spot - strike
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if exercise_decision(spot, strike, mid, t_left, r, vol)["exercise_now"]:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)
