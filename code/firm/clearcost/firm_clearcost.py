"""Access-cost model for cleared repo and swaps (build of Book 2, Chapter 28).

A route to the market has a fixed annual cost (membership, legal, operations, systems) and costs
proportional to the business: fees or spreads in basis points a year on the repo balance and on the
swap notional, margin that must be funded, and capital tied up in a clearing fund. The annual cost of
a book of repo balance B and swap notional N is linear in (B, N), so two routes cost the same at one
scale of a given mix: the break-even size.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    name: str
    fixed: float                 # USD a year
    repo_bp: float               # fees or spread, bp a year on the repo balance
    swap_bp: float               # clearing fees, bp a year on swap notional
    repo_margin: float = 0.0     # margin posted per unit of repo balance
    swap_margin: float = 0.0     # initial margin per unit of swap notional
    fund_share: float = 0.0      # clearing-fund contribution per unit of repo balance
    capital_rate: float = 0.10   # cost of the capital tied up in the clearing fund, a year


def annual_cost(route: Route, repo: float, swaps: float, funding: float) -> float:
    """Total cost a year, USD; margin is funded at `funding` (a spread over the cash it earns)."""
    return route.fixed + variable_cost(route, repo, swaps, funding)


def variable_cost(route: Route, repo: float, swaps: float, funding: float) -> float:
    variable = route.repo_bp * 1e-4 * repo + route.swap_bp * 1e-4 * swaps
    margin = funding * (route.repo_margin * repo + route.swap_margin * swaps)
    capital = route.capital_rate * route.fund_share * repo
    return variable + margin + capital


def unit_cost(route: Route, swaps_per_repo: float, funding: float) -> float:
    """Variable cost a year per USD of repo balance, for a book with a fixed swap-to-repo mix."""
    return variable_cost(route, 1.0, swaps_per_repo, funding)


def breakeven(a: Route, b: Route, swaps_per_repo: float, funding: float) -> float | None:
    """Repo balance at which routes a and b cost the same, or None if one is always cheaper."""
    du = unit_cost(a, swaps_per_repo, funding) - unit_cost(b, swaps_per_repo, funding)
    if du == 0:
        return None
    size = (b.fixed - a.fixed) / du
    return size if size > 0 else None


def cheapest(routes: list[Route], repo: float, swaps: float, funding: float) -> Route:
    return min(routes, key=lambda r: annual_cost(r, repo, swaps, funding))
