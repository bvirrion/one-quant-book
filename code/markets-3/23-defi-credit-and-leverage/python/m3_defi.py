"""Book 3, Chapter 23: a kinked rate curve, a borrower's health through a price fall, a liquidation
funded by a flash loan and sold into a constant-product pool, and the oracle pump that borrows a pool dry."""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/lendpool"))
sys.path.insert(0, str(ROOT / "code/firm/amm"))
from firm_amm import cp_amount_out  # noqa: E402
from firm_lendpool import Account, Pool, RateModel, Reserve  # noqa: E402

MODEL = RateModel(base=0.0, slope1=0.04, slope2=0.60, optimal=0.90)     # illustrative, two slopes and a kink


def make_pool(eth_price: float = 3_000.0) -> Pool:
    p = Pool({"USDC": Reserve(MODEL), "ETH": Reserve(MODEL)}, {"USDC": 1.0, "ETH": eth_price},
             ltv={"ETH": 0.80, "USDC": 0.0}, threshold={"ETH": 0.825, "USDC": 0.0},
             bonus={"ETH": 0.05, "USDC": 0.0}, close_factor=0.5, flash_fee=0.0005)
    p.supply("USDC", 10_000_000)
    return p


def rate_curve() -> list[tuple[float, float, float]]:
    out = []
    for k in range(0, 101):
        u = k / 100
        rb = MODEL.borrow_rate(u)
        out.append((u, rb, rb * u * 0.9))
    return out


def health_path(eth: float = 100.0, debt: float = 240_000.0) -> list[tuple[float, float]]:
    """Health factor of a borrower with `eth` of collateral and `debt` dollars as the price falls."""
    return [(p, eth * p * 0.825 / debt) for p in range(3_300, 1_999, -50)]


def flash_liquidation(eth_price: float = 2_800.0, pool_eth: int = 5_000, fee_bps: int = 30) -> dict:
    """A liquidator with no capital: flash-borrow the repayment, liquidate half the debt, sell the seized ETH
    in a constant-product pool at the market price, repay the flash loan with its fee, keep the rest."""
    p = make_pool()
    acct = Account({"ETH": 100.0})
    p.borrow(acct, "USDC", 240_000.0)
    p.prices["ETH"] = eth_price
    result = {}

    def callback(amount: float) -> float:
        seized = p.liquidate(acct, "USDC", "ETH", amount)
        e18, e6 = 10**18, 10**6
        usdc = cp_amount_out(int(seized * e18), pool_eth * e18, int(pool_eth * eth_price * e6), fee_bps) / e6
        result.update(seized=seized, usdc=usdc)
        return min(usdc, amount * (1 + p.flash_fee))

    repay = 0.5 * p.owed(acct, "USDC")
    fee = p.flash_loan("USDC", repay, callback)
    result.update(repay=repay, fee=fee, profit=result["usdc"] - repay - fee, health_after=p.health(acct))
    return result


def pump_cost(depth_usd: float, k: float) -> tuple[float, float]:
    """To raise a constant-product pool's price by a factor k with depth_usd of dollars in it: the dollars to
    add, depth (sqrt(k) - 1), and the fraction of the pool's tokens bought, 1 - 1/sqrt(k)."""
    return depth_usd * (math.sqrt(k) - 1), 1 - 1 / math.sqrt(k)


def pump_needed(liquidity: float, collateral_usd: float, ltv: float) -> float:
    """Price multiple at which the collateral's borrowing power equals the pool's liquidity."""
    return liquidity / (ltv * collateral_usd)


def pump_attack(k: float, liquidity: float = 50e6, tokens: float = 5e6, price: float = 1.0, ltv: float = 0.6,
                depth_usd: float = 2e6, depth_tokens: float = 2e6, residual: float = 0.0) -> float:
    """Attacker's net gain from pumping the oracle's source by k and borrowing all it can (capped by the pool),
    abandoning the collateral; tokens bought during the pump are worth `residual` per token afterwards."""
    borrowed = min(liquidity, ltv * tokens * price * k)
    spent, frac = pump_cost(depth_usd, k)
    return borrowed - tokens * price - spent + frac * depth_tokens * residual
