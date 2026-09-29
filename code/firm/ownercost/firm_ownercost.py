"""firm.ownercost -- what an asset owner pays to manage its assets, inside or outside (build of One Quant Book 17,
chapter 8).

An owner can run a mandate with its own team or pay an external manager a fee on the assets. The internal cost is the
team's headcount times the staff cost per head, plus systems and data; the external cost is a fee rate (basis points of
assets, with any performance fee as an expected rate). The mandate size above which the internal team is cheaper is the
break-even. Published totals give each owner's cost in basis points, overall and split between the internal and the
external parts. All amounts in one currency (the caller converts).

API (stable):
    Owner(name, assets, internal_costs, external_base, external_perf, external_assets)
    cost_bp(owner) -> total management cost in basis points of assets
    split_bp(owner) -> (internal bp on internally managed assets, external bp on externally managed assets)
    internal_cost(heads, cost_per_head, systems) ; external_cost(assets, fee_bp)
    breakeven_assets(heads, cost_per_head, systems, fee_bp) -> assets at which the two are equal
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Owner:
    name: str
    assets: float
    internal_costs: float
    external_base: float
    external_perf: float
    external_assets: float | None = None


def cost_bp(o):
    return 1e4 * (o.internal_costs + o.external_base + o.external_perf) / o.assets


def split_bp(o):
    if o.external_assets is None:
        raise ValueError("the owner does not publish its externally managed assets")
    internal_assets = o.assets - o.external_assets
    return 1e4 * o.internal_costs / internal_assets, 1e4 * (o.external_base + o.external_perf) / o.external_assets


def internal_cost(heads, cost_per_head, systems=0.0):
    return heads * cost_per_head + systems


def external_cost(assets, fee_bp):
    return assets * fee_bp / 1e4


def breakeven_assets(heads, cost_per_head, systems, fee_bp):
    return internal_cost(heads, cost_per_head, systems) * 1e4 / fee_bp
