"""Chapter 14 of Book 3: blockchains for traders. The EIP-1559 base fee under full blocks and under
a demand shock, a transaction's cost, and when a time-sensitive arbitrage stops paying for its gas.
Demand, ether price and trade sizes are illustrative."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/gasfee"))
from firm_gasfee import GWEI, next_base_fee, project, tx_cost_usd

LIMIT = 30_000_000             # gas limit of a block (illustrative)
ETH_USD = 3000.0               # illustrative


def full_blocks(k: int, base_gwei: float = 10.0) -> float:
    """Base fee in gwei after k consecutive full blocks."""
    return project(int(base_gwei * GWEI), [1.0] * k, LIMIT)[-1] / GWEI


def demand_shock(blocks: int = 60, start: int = 5, end: int = 35, mult: float = 4.0,
                 base_gwei: float = 10.0) -> list[tuple[int, float, float]]:
    """(block, base fee in gwei, share of the gas limit used). Demand for gas at base fee b is
    LIMIT * min(1, a / b), with a set so that demand equals the target at the starting base fee;
    from `start` to `end` demand is `mult` times higher."""
    a0 = 0.5 * base_gwei
    b = int(base_gwei * GWEI)
    out = []
    for n in range(blocks):
        a = a0 * (mult if start <= n < end else 1.0)
        share = min(1.0, a / (b / GWEI))
        out.append((n, b / GWEI, share))
        b = next_base_fee(b, int(share * LIMIT), LIMIT)
    return out


def arbitrage_breakeven(gross_usd: float = 60.0, gas: int = 150_000, tip_gwei: float = 2.0,
                        base_gwei: float = 10.0) -> dict[str, float]:
    """Base fee at which an arbitrage worth `gross_usd` before gas stops paying, and the number of
    consecutive full blocks that take the base fee there from `base_gwei`."""
    b_star = gross_usd / (gas * 1e-9 * ETH_USD) - tip_gwei
    k = math.log(b_star / base_gwei) / math.log(1.125)
    return {"breakeven_gwei": b_star, "blocks": k, "cost_now": tx_cost_usd(gas, base_gwei, tip_gwei, ETH_USD)}
