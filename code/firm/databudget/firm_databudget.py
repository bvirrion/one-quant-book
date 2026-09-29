"""firm.databudget -- data products, fee rules and usage as data: the data budget, the enterprise break-even, audit
exposure with interest, a per-strategy allocation, and the break-even price of an alternative dataset (build of One
Quant Book 16, chapter 22). Fee levels are inputs: published schedules change by filing and contracts differ.

API (stable):
    Product(name, category, per_user, per_device, flat, enterprise) ; Usage(users, devices)
    annual_cost(product, usage, enterprise=False) ; budget(products, usage) -> {category: cost}
    enterprise_breakeven(product) -> users ; audit_exposure(annual_fees, under_share, years, monthly_rate)
    allocate(total, weights) ; alt_breakeven(annual, capital, cost, half_life, years)   (firm.vendoreval)
"""
import math
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendoreval"))
import firm_vendoreval as ve  # noqa: E402


@dataclass(frozen=True)
class Product:
    name: str
    category: str
    per_user: float = 0.0          # a year
    per_device: float = 0.0        # a year
    flat: float = 0.0              # a year (non-display category fees, feed fees, dataset prices)
    enterprise: float | None = None


@dataclass(frozen=True)
class Usage:
    users: int = 0
    devices: int = 0


def annual_cost(p, u, enterprise=False):
    if enterprise:
        if p.enterprise is None:
            raise ValueError(f"{p.name} has no enterprise licence")
        return p.enterprise + p.flat
    return p.per_user * u.users + p.per_device * u.devices + p.flat


def budget(products, usage):
    """Each product at its cheaper licence (per unit or enterprise); totals by category."""
    out = {}
    for p in products:
        c = annual_cost(p, usage[p.name])
        if p.enterprise is not None:
            c = min(c, annual_cost(p, usage[p.name], True))
        out[p.category] = out.get(p.category, 0.0) + c
    return out


def enterprise_breakeven(p):
    """The smallest number of users at which the enterprise licence costs no more than per-user fees."""
    return math.ceil(p.enterprise / p.per_user)


def audit_exposure(annual_fees, under_share, years, monthly_rate):
    """Back-billing when a share `under_share` of true usage went unreported for `years`: each month's unbilled fees
    (the reported fees scaled up to true usage) with interest from that month to the audit."""
    months = int(round(12 * years))
    unbilled = annual_fees / 12 * under_share / (1 - under_share)
    principal = unbilled * months
    total = sum(unbilled * (1 + monthly_rate) ** (months - m) for m in range(1, months + 1))
    return {"principal": principal, "interest": total - principal, "total": total}


def allocate(total, weights):
    s = sum(weights.values())
    return {k: total * w / s for k, w in weights.items()}


def alt_breakeven(annual, capital, cost, half_life, years):
    return ve.breakeven(annual, capital, cost, half_life, years)
