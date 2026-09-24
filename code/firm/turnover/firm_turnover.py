"""Turnover normaliser (build of Book 1, Chapter 27).

Exchanges report contracts. A contract is not a unit of anything: this module converts counts into
notional and premium turnover in one currency so that markets can be compared.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class MarketStats:
    name: str
    kind: str                       # 'option' or 'future'
    contracts: float                # contracts traded in the period
    multiplier: float               # units of underlying per contract (the lot size, for Indian contracts)
    underlying: float               # average level of the underlying, local currency
    avg_premium: float              # average option premium per unit of underlying, local currency (0 for futures)
    fx_to_usd: float                # US dollars per unit of local currency

    @property
    def notional_usd(self) -> float:
        return self.contracts * self.multiplier * self.underlying * self.fx_to_usd

    @property
    def premium_usd(self) -> float:
        """Money that actually changed hands for options. For futures there is no premium: None-like 0."""
        return self.contracts * self.multiplier * self.avg_premium * self.fx_to_usd

    @property
    def premium_to_notional_bp(self) -> float:
        return self.avg_premium / self.underlying * 1e4


def shares(markets: list[MarketStats], measure: str) -> dict[str, float]:
    """Each market's share of the total, by 'contracts', 'notional_usd' or 'premium_usd'."""
    values = {m.name: float(getattr(m, measure)) for m in markets}
    total = sum(values.values())
    if total <= 0:
        raise ValueError(f"no {measure} to share out")
    return {k: v / total for k, v in values.items()}


def ranking(markets: list[MarketStats], measure: str) -> list[str]:
    return [k for k, _ in sorted(shares(markets, measure).items(), key=lambda kv: (-kv[1], kv[0]))]


def contracts_after_lot_change(contracts: float, old_lot: float, new_lot: float, activity_kept: float = 1.0) -> float:
    """Contracts one should expect after a lot-size change if traders keep `activity_kept` of their
    NOTIONAL activity: a tripled lot with unchanged activity divides the count by three."""
    return contracts * old_lot / new_lot * activity_kept


def activity_kept(contracts_before: float, contracts_after: float, old_lot: float, new_lot: float) -> float:
    """Inverse question: what happened to notional activity, given the counts before and after?"""
    return contracts_after * new_lot / (contracts_before * old_lot)
