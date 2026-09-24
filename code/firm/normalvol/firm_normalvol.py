"""Bachelier and Black option prices on rates, and quote conversion (build of Book 2, Chapter 13).

Rates and volatilities are decimals: a normal volatility of 0.0085 is 85 basis points a year. An
option on a forward rate F with strike K and expiry T pays annuity x max(F_T - K, 0) (payer, call)
or annuity x max(K - F_T, 0) (receiver, put); for a caplet the annuity is accrual x discount factor.
"""
import math

SQRT_2PI = math.sqrt(2.0 * math.pi)


def _pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def _cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def bachelier(f: float, k: float, t: float, vol: float, annuity: float = 1.0, payer: bool = True) -> float:
    """Normal model: F_T = F + vol * W_T."""
    s = vol * math.sqrt(t)
    if s <= 0.0:
        return annuity * max(f - k if payer else k - f, 0.0)
    d = (f - k) / s
    call = (f - k) * _cdf(d) + s * _pdf(d)
    return annuity * (call if payer else call - (f - k))


def black(f: float, k: float, t: float, vol: float, annuity: float = 1.0, payer: bool = True) -> float:
    """Lognormal model: needs F > 0 and K > 0."""
    if f <= 0.0 or k <= 0.0:
        raise ValueError("Black's model needs a positive forward and strike")
    s = vol * math.sqrt(t)
    d1 = math.log(f / k) / s + 0.5 * s
    call = f * _cdf(d1) - k * _cdf(d1 - s)
    return annuity * (call if payer else call - (f - k))


def normal_vega(f: float, k: float, t: float, vol: float, annuity: float = 1.0) -> float:
    """Price change per unit of normal volatility (same for payer and receiver)."""
    s = vol * math.sqrt(t)
    return annuity * math.sqrt(t) * _pdf((f - k) / s)


def implied(price: float, f: float, k: float, t: float, annuity: float = 1.0, payer: bool = True,
            model: str = "normal", lo: float = 1e-8, hi: float = 20.0) -> float:
    """Implied volatility by bisection (prices increase with volatility in both models). Raises
    ValueError when no volatility in (lo, hi) reproduces the price: a Black call is worth less than
    the forward times the annuity, whatever the volatility."""
    pricer = bachelier if model == "normal" else black
    if not pricer(f, k, t, lo, annuity, payer) <= price <= pricer(f, k, t, hi, annuity, payer):
        raise ValueError("no volatility reproduces this price")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if pricer(f, k, t, mid, annuity, payer) < price:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def normal_to_black(f: float, k: float, t: float, vol_n: float) -> float:
    return implied(bachelier(f, k, t, vol_n), f, k, t, model="black")


def black_to_normal(f: float, k: float, t: float, vol_b: float) -> float:
    return implied(black(f, k, t, vol_b), f, k, t, model="normal")


def atm_straddle(t: float, vol: float, annuity: float = 1.0) -> float:
    """Payer plus receiver at the money: annuity * vol * sqrt(t) * sqrt(2/pi)."""
    return 2.0 * bachelier(0.0, 0.0, t, vol, annuity)


def bp_per_day(vol: float, days: int = 252) -> float:
    """Annual normal volatility (decimal) as basis points per business day."""
    return vol * 1e4 / math.sqrt(days)
