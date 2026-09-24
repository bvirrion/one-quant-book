"""Economics of venues and of market access (Chapter 4). All parameters illustrative."""
from dataclasses import dataclass

# ICE, Exchanges segment, full-year 2025 net revenues, USD million (ledger row F1)
ICE_EXCHANGES_2025 = {
    "Energy": 2182, "Ags and metals": 233, "Financials": 608,
    "Cash equities and equity options": 467, "OTC and other": 395,
    "Data and connectivity services": 1031, "Listings": 495,
}
ICE_TRANSACTION = ("Energy", "Ags and metals", "Financials", "Cash equities and equity options",
                   "OTC and other")
# CME Group, full-year 2025, USD million (ledger row F2)
CME_2025 = {"Clearing and transaction fees": 5281.1, "Market data and information services": 803.1}
CME_TOTAL_2025 = 6500.0
CME_RATE_PER_CONTRACT = 0.696


def shares(table: dict[str, float]) -> dict[str, float]:
    total = sum(table.values())
    return {k: v / total for k, v in table.items()}


@dataclass(frozen=True)
class AccessModel:
    name: str
    per_share: float      # USD per share, paid to the access provider
    fixed_month: float    # USD per month: connectivity, colocation, compliance, capital cost


ACCESS = (
    AccessModel("broker algorithm", 0.0030, 0.0),
    AccessModel("direct market access", 0.0010, 5_000.0),
    AccessModel("sponsored access", 0.0004, 25_000.0),
    AccessModel("own membership", 0.0, 150_000.0),
)


def monthly_cost(m: AccessModel, shares_month: float) -> float:
    return m.fixed_month + m.per_share * shares_month


def cheapest(shares_month: float) -> AccessModel:
    return min(ACCESS, key=lambda m: monthly_cost(m, shares_month))


def crossover(a: AccessModel, b: AccessModel) -> float:
    """Monthly volume at which b becomes cheaper than a (b has the higher fixed cost)."""
    return (b.fixed_month - a.fixed_month) / (a.per_share - b.per_share)


def venue_profit(share: float, market_shares_day: float, net_capture: float, data_rev_full: float,
                 fixed_cost: float, days: int = 252) -> float:
    """Annual profit of a venue with a given market share.

    net_capture: fee kept per share matched (after rebates), counted once per share.
    data_rev_full: annual market-data revenue the venue would earn with 100 % share.
    """
    return share * (market_shares_day * days * net_capture + data_rev_full) - fixed_cost


def breakeven_share(market_shares_day: float, net_capture: float, data_rev_full: float,
                    fixed_cost: float, days: int = 252) -> float:
    return fixed_cost / (market_shares_day * days * net_capture + data_rev_full)
