"""Month-end flow estimates and the economics of a fixing order (build of Book 2, Chapter 17).

Flows are in dollars, positive for dollar sales. A foreign investor that hedges a share h of its
dollar assets must, when their dollar value changes, sell (or buy back) that share of the change
at the next rebalancing. A dealer that guarantees a client the fix buys the client's amount Q
itself; with linear permanent impact lam per unit, buying a share p before the window and the rest
evenly during it, the fix (the average price in the window) and the dealer's average cost follow
in closed form.
"""
import math
import random


def hedge_rebalance(value_usd: float, asset_return: float, hedge_ratio: float) -> float:
    """Dollars to sell forward so the hedge again covers `hedge_ratio` of the assets' dollar value."""
    return hedge_ratio * value_usd * asset_return


def weight_rebalance(values: dict[str, float], targets: dict[str, float]) -> dict[str, float]:
    """Amounts (in the portfolio's base currency) to buy in each region to restore target weights;
    negative numbers are sales."""
    total = sum(values.values())
    return {k: targets[k] * total - v for k, v in values.items()}


def fix_and_cost(q: float, lam: float, p: float, p0: float = 0.0) -> tuple[float, float]:
    """(fix, dealer's average purchase price) when it buys q with permanent impact lam, a share p
    before the window and the rest evenly inside it; the fix is the window's average price."""
    fix = p0 + lam * q * (1.0 + p) / 2.0
    cost = p0 + lam * q / 2.0
    return fix, cost


def dealer_pnl(q: float, lam: float, p: float) -> float:
    """Expected profit of guaranteeing the fix: q * (fix - average cost) = lam q^2 p / 2."""
    fix, cost = fix_and_cost(q, lam, p)
    return q * (fix - cost)


def simulate_pnl(q: float, lam: float, p: float, sigma_pre: float, n: int = 20_000,
                 seed: int = 1) -> tuple[float, float]:
    """Mean and standard deviation of the dealer's profit when the price also moves randomly, by a
    normal amount with standard deviation `sigma_pre`, between the pre-hedge and the window."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        move = rng.gauss(0.0, sigma_pre)            # affects the window, not the pre-hedge
        fix, cost = fix_and_cost(q, lam, p)
        out.append(q * (fix + move - (cost + (1.0 - p) * move)))
    m = sum(out) / n
    return m, math.sqrt(sum((x - m) ** 2 for x in out) / (n - 1))
