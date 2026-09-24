"""Black-Scholes and Black kernels (build of Book 5, Chapter 3). Twins: cpp/firm_bs.hpp, rust/.

Everything is priced on the forward: black(F, K, T, df, vol, right) is Black's formula times the
discount factor df = P(0,T); bs(S, ...) builds F = S exp((r-q)T) and df = exp(-rT). Greeks are per
unit of the underlying and per unit of volatility (the pricing library converts to desk units).
The implied-volatility solver brackets the root by the no-arbitrage bounds, starts from a closed-form
guess and runs Newton's method safeguarded by bisection, so it never leaves the bracket.
"""
import math

SQRT2PI = math.sqrt(2.0 * math.pi)


def ncdf(x: float) -> float:
    """Standard normal cdf, accurate in both tails (erfc, not 1 + erf)."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def npdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT2PI


def black(fwd: float, strike: float, t: float, df: float, vol: float, right: str = "C") -> float:
    """Discounted Black price of a European call ("C") or put ("P") on a forward."""
    sign = 1.0 if right == "C" else -1.0
    if t <= 0.0 or vol <= 0.0:
        return df * max(sign * (fwd - strike), 0.0)
    s = vol * math.sqrt(t)
    d1 = math.log(fwd / strike) / s + 0.5 * s
    d2 = d1 - s
    return df * sign * (fwd * ncdf(sign * d1) - strike * ncdf(sign * d2))


def bs(spot: float, strike: float, t: float, r: float, q: float, vol: float, right: str = "C") -> float:
    """Black-Scholes price with a continuous dividend (or borrow) yield q."""
    return black(spot * math.exp((r - q) * t), strike, t, math.exp(-r * t), vol, right)


def greeks(spot: float, strike: float, t: float, r: float, q: float, vol: float, right: str = "C") -> dict:
    """Analytic Greeks: delta, gamma (per unit spot), vega (per unit vol), theta (per year, calendar
    time), rho (per unit rate), vanna (d delta / d vol), volga (d vega / d vol)."""
    sign = 1.0 if right == "C" else -1.0
    sq = math.sqrt(t)
    s = vol * sq
    d1 = (math.log(spot / strike) + (r - q) * t) / s + 0.5 * s
    d2 = d1 - s
    eq, er = math.exp(-q * t), math.exp(-r * t)
    pdf = npdf(d1)
    delta = sign * eq * ncdf(sign * d1)
    gamma = eq * pdf / (spot * s)
    vega = spot * eq * pdf * sq
    theta = (-spot * eq * pdf * vol / (2.0 * sq) - sign * r * strike * er * ncdf(sign * d2)
             + sign * q * spot * eq * ncdf(sign * d1))
    rho = sign * strike * t * er * ncdf(sign * d2)
    vanna = -eq * pdf * d2 / vol
    volga = vega * d1 * d2 / vol
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho,
            "vanna": vanna, "volga": volga}


def implied_vol(price: float, fwd: float, strike: float, t: float, df: float, right: str = "C",
                tol: float = 1e-12, max_iter: int = 100) -> float:
    """Volatility at which black(...) equals price. Raises ValueError outside the arbitrage bounds."""
    sign = 1.0 if right == "C" else -1.0
    lo_p = df * max(sign * (fwd - strike), 0.0)
    hi_p = df * (fwd if right == "C" else strike)
    if not lo_p <= price < hi_p:
        raise ValueError(f"price {price} outside ({lo_p}, {hi_p}): no implied volatility")
    if price - lo_p < 1e-15 * df * max(fwd, strike):
        return 0.0
    # Brenner-Subrahmanyam / Corrado-Miller style guess on the time value, clipped to the bracket
    x = math.log(fwd / strike)
    c = price / df - 0.5 * sign * (fwd - strike)
    disc = max(c * c - (fwd - strike) ** 2 / math.pi, 0.0)
    guess = math.sqrt(2.0 * math.pi) / (fwd + strike) * (c + math.sqrt(disc)) / math.sqrt(t)
    lo, hi = 0.0, 1.0
    while black(fwd, strike, t, df, hi, right) < price:
        hi *= 2.0
        if hi > 100.0:
            raise ValueError("no volatility below 10000%")
    v = min(max(guess, 1e-4), hi) if guess > 0 and abs(x) < 1.0 else 0.5 * hi
    for _ in range(max_iter):
        f = black(fwd, strike, t, df, v, right) - price
        if abs(f) < tol * max(price, 1e-300) or hi - lo < 1e-15:
            return v
        if f > 0:
            hi = v
        else:
            lo = v
        s = v * math.sqrt(t)
        vega = df * fwd * npdf(x / s + 0.5 * s) * math.sqrt(t)
        step = v - f / vega if vega > 0 else -1.0
        v = step if lo < step < hi else 0.5 * (lo + hi)
    return v
