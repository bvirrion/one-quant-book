"""firm.blockbid -- risk-bid pricing service (build of Chapter 2, One Quant Book 1)."""
import math
from dataclasses import dataclass
from statistics import NormalDist

KAPPA = 0.70
MAX_PARTICIPATION = 0.30
MAX_DAYS_OF_VOLUME = 5.0


@dataclass(frozen=True)
class Quote:
    unwind_days: float
    impact: float      # fraction of value
    risk: float        # one standard deviation, fraction of value
    discount: float    # fraction of value
    bid: float         # price, rounded down to the cent


def quote(shares: float, price: float, adv: float, sigma: float, participation: float = 0.10,
          confidence: float = 0.95, hedge_ratio: float = 0.0) -> Quote:
    if not 0.0 < participation <= MAX_PARTICIPATION:
        raise ValueError("participation outside (0, 0.30]")
    if shares > MAX_DAYS_OF_VOLUME * adv:
        raise ValueError("block above five days of volume")
    if not 0.0 <= hedge_ratio <= 1.0:
        raise ValueError("hedge_ratio outside [0, 1]")
    days = shares / (participation * adv)
    impact = KAPPA * sigma * math.sqrt(shares / adv)
    risk = sigma * math.sqrt(1.0 - hedge_ratio) * math.sqrt(days / 3.0)
    discount = impact + NormalDist().inv_cdf(confidence) * risk
    bid = math.floor(price * (1.0 - discount) * 100.0 + 1e-9) / 100.0
    return Quote(days, impact, risk, discount, bid)
