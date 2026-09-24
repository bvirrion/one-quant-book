"""ETF arbitrage bands, stale net asset values and leveraged funds (Chapter 14). Illustrative."""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ArbCosts:
    basket_half_spread_bp: float     # cost of trading the basket, one way
    etf_half_spread_bp: float        # cost of trading the ETF, one way
    creation_fee_bp: float           # fixed creation/redemption fee spread over one unit
    financing_bp: float              # carrying both legs until settlement

    @property
    def band_bp(self) -> float:
        """Premium (or discount) beyond which creating (redeeming) is profitable."""
        return (self.basket_half_spread_bp + self.etf_half_spread_bp + self.creation_fee_bp
                + self.financing_bp)


def premium_bp(etf_price: float, nav: float) -> float:
    return (etf_price / nav - 1.0) * 1e4


def simulate_premium(costs: ArbCosts, n: int, seed: int, shock_bp: float = 6.0):
    """Premium pushed around by order flow and pulled back by arbitrage outside the band."""
    rng = np.random.default_rng(seed)
    prem, out, creations = 0.0, [], 0
    for _ in range(n):
        prem += rng.normal(0.0, shock_bp)
        if abs(prem) > costs.band_bp:                       # an authorised participant acts
            creations += 1 if prem > 0 else -1
            prem = math.copysign(costs.band_bp * 0.5, prem)  # and leaves half the band
        out.append(prem)
    return np.array(out), creations


def stale_nav(true_value: np.ndarray, staleness: float) -> np.ndarray:
    """NAV computed from quotes that adjust only partly each day: an exponential lag."""
    nav = np.empty_like(true_value)
    nav[0] = true_value[0]
    for t in range(1, len(true_value)):
        nav[t] = nav[t - 1] + (1.0 - staleness) * (true_value[t] - nav[t - 1])
    return nav


def rebalance_trade(beta: float, nav: float, index_return: float) -> float:
    """Exposure the fund must add at the close to be `beta` times leveraged again:
    beta (beta - 1) N r."""
    return beta * (beta - 1.0) * nav * index_return


def leveraged_path(index_returns: np.ndarray, beta: float) -> np.ndarray:
    return np.cumprod(1.0 + beta * index_returns)


def decay_factor(beta: float, sigma_annual: float, years: float) -> float:
    """exp(-beta (beta - 1) sigma^2 T / 2): leveraged fund versus (index ratio)^beta."""
    return math.exp(-0.5 * beta * (beta - 1.0) * sigma_annual**2 * years)
