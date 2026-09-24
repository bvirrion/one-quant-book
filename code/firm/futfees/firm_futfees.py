"""Futures fee engine (build of Book 1, Chapter 30).

What one side of one contract costs depends on who is trading: non-member, lessee of a
membership, owner. On top of the exchange fee come the regulator's fee, the clearing broker's
commission and, for a member, the fixed cost of the membership itself.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductFees:
    product: str
    exchange_fee: dict[str, float]          # status -> dollars per side: 'non_member', 'lessee', 'owner'
    regulatory_fee: dict[str, float]        # status -> dollars per side


@dataclass(frozen=True)
class Access:
    status: str                             # 'non_member', 'lessee' or 'owner'
    broker_commission: float                # clearing broker, dollars per side
    fixed_monthly: float = 0.0              # lease, or the cost of capital tied up in an owned membership


def per_side(p: ProductFees, a: Access) -> float:
    return p.exchange_fee[a.status] + p.regulatory_fee[a.status] + a.broker_commission


def monthly_cost(p: ProductFees, a: Access, sides: float) -> float:
    return sides * per_side(p, a) + a.fixed_monthly


def breakeven_sides(p: ProductFees, cheap: Access, dear: Access) -> float | None:
    """Monthly sides above which `cheap` (higher fixed cost, lower variable) beats `dear`."""
    saving = per_side(p, dear) - per_side(p, cheap)
    extra_fixed = cheap.fixed_monthly - dear.fixed_monthly
    if saving <= 0:
        return None
    return max(0.0, extra_fixed / saving)


@dataclass(frozen=True)
class IncentiveTier:
    min_sides: float                        # monthly volume from which the discount applies
    discount: float                         # dollars per side off the exchange fee, on ALL sides of the month


def with_incentive(p: ProductFees, a: Access, sides: float, tiers: tuple[IncentiveTier, ...]) -> float:
    ok = [t.discount for t in tiers if sides >= t.min_sides]
    return monthly_cost(p, a, sides) - sides * (max(ok) if ok else 0.0)


def cost_in_ticks(p: ProductFees, a: Access, tick_value: float) -> float:
    """A round trip's fees as a fraction of one tick: what a one-tick scalp must pay."""
    return 2.0 * per_side(p, a) / tick_value
