"""What one contract costs by membership status, and when a lease pays (Chapter 30).
Exchange and regulatory fees are those published by a futures broker (see the chapter's ledger);
commissions, the lease and the cost of owning are illustrative."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/futfees"))
from firm_futfees import Access, ProductFees, breakeven_sides, monthly_cost

ES = ProductFees("ES", {"non_member": 1.18, "lessee": 0.47, "owner": 0.35},
                 {"non_member": 0.02, "lessee": 0.0, "owner": 0.0})
MICRO = ProductFees("micro", {"non_member": 0.20, "lessee": 0.07, "owner": 0.04},
                    {"non_member": 0.02, "lessee": 0.0, "owner": 0.0})

OUTSIDE = Access("non_member", 0.25)
LESSEE = Access("lessee", 0.10, 1_500.0)
OWNER = Access("owner", 0.10, 4_000.0)                # cost of capital on a purchased membership, illustrative
ROUTES = (OUTSIDE, LESSEE, OWNER)


def breakevens() -> tuple[float, float]:
    """Sides a month from which leasing beats staying outside, and owning beats leasing."""
    return breakeven_sides(ES, LESSEE, OUTSIDE), breakeven_sides(ES, OWNER, LESSEE)


def exchange_round_trip_in_ticks(p: ProductFees, tick_value: float) -> dict[str, float]:
    return {k: 2.0 * (p.exchange_fee[k] + p.regulatory_fee[k]) / tick_value for k in p.exchange_fee}


def cost_curve(sides: list[float]) -> list[tuple[float, float, float, float]]:
    return [(s, *(monthly_cost(ES, a, s) for a in ROUTES)) for s in sides]
