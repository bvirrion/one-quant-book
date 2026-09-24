"""Parity checker and implied-volatility solver (build of Book 1, Chapter 25).

European options priced on the forward (Black 1976, discounted). Everything about dividends and
stock borrow enters through the forward, which put-call parity lets us read off the chain itself.
"""
import math


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def price(forward: float, strike: float, years: float, rate: float, vol: float, right: str) -> float:
    df = math.exp(-rate * years)
    if vol <= 0.0 or years <= 0.0:
        intrinsic = max(forward - strike, 0.0) if right == "C" else max(strike - forward, 0.0)
        return df * intrinsic
    s = vol * math.sqrt(years)
    d1 = math.log(forward / strike) / s + 0.5 * s
    call = df * (forward * _phi(d1) - strike * _phi(d1 - s))
    return call if right == "C" else call - df * (forward - strike)


def implied_vol(premium: float, forward: float, strike: float, years: float, rate: float, right: str,
                tol: float = 1e-10) -> float:
    """Bisection on [0, 5]. Raises if the premium is outside the no-arbitrage bounds."""
    lo_price, hi_price = (price(forward, strike, years, rate, v, right) for v in (0.0, 5.0))
    if not lo_price - 1e-12 <= premium <= hi_price:
        raise ValueError(f"premium {premium} outside [{lo_price:.6f}, {hi_price:.6f}]: no implied volatility")
    lo, hi = 0.0, 5.0
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if price(forward, strike, years, rate, mid, right) < premium:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def implied_forward(call: float, put: float, strike: float, years: float, rate: float) -> float:
    """Put-call parity for European options: C - P = DF (F - K)."""
    return strike + math.exp(rate * years) * (call - put)


def implied_dividends_pv(spot: float, forward: float, years: float, rate: float) -> float:
    """Present value of what the holder of the share receives (dividends) or pays (borrow fee)
    before expiry, as implied by the forward: S - DF * F."""
    return spot - math.exp(-rate * years) * forward


def conversion_edge(call_bid: float, put_ask: float, spot_ask: float, strike: float, years: float, rate: float,
                    dividends_pv: float) -> float:
    """Profit today of a conversion: buy the share, buy the put, sell the call; receive the strike
    at expiry and the dividends on the way. Positive = parity is violated beyond the quotes."""
    return call_bid - put_ask - spot_ask + dividends_pv + strike * math.exp(-rate * years)


def reversal_edge(call_ask: float, put_bid: float, spot_bid: float, strike: float, years: float, rate: float,
                  dividends_pv: float, borrow_cost_pv: float = 0.0) -> float:
    """Profit today of a reversal: short the share, sell the put, buy the call. The short pays the
    dividends and the borrow fee."""
    return put_bid - call_ask + spot_bid - dividends_pv - borrow_cost_pv - strike * math.exp(-rate * years)


def variance_strip(forward: float, years: float, rate: float, quotes: list[tuple[float, float]]) -> float:
    """Model-free implied variance from out-of-the-money option mid-quotes, in the form used by the
    best-known volatility index: (2/T) sum dK/K^2 e^{RT} Q(K) - (1/T) (F/K0 - 1)^2.
    `quotes` = (strike, mid) sorted by strike: puts below K0, calls above, their average at K0."""
    strikes = [k for k, _ in quotes]
    k0 = max(k for k in strikes if k <= forward)
    total = 0.0
    for i, (k, q) in enumerate(quotes):
        if i == 0:
            dk = strikes[1] - strikes[0]
        elif i == len(quotes) - 1:
            dk = strikes[-1] - strikes[-2]
        else:
            dk = 0.5 * (strikes[i + 1] - strikes[i - 1])
        total += dk / (k * k) * math.exp(rate * years) * q
    return 2.0 / years * total - (forward / k0 - 1.0) ** 2 / years
