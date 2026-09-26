"""firm.searcher -- on-chain arbitrage, bundle auctions and hedged liquidity (One Quant Book 11, chapter 25).

Built on Book 3's firm.amm (constant-product swaps), firm.gasfee (transaction costs) and firm.sandwich (the sandwich
arithmetic, for the legal discussion only). A constant-product pool of token A against dollars is arbitraged
against a centralised exchange's price once per block; searchers compete for the arbitrage in a first-price auction
to the block builder; a liquidity provider hedges its pool position on the centralised exchange and loses to the
arbitrageurs what the literature calls loss-versus-rebalancing.

API (stable):
    optimal_arb(x, y, p, fee)                      input and profit of the arbitrage that moves the pool to price p
                                                   (x token A, y dollars, fee as a fraction; float arithmetic)
    arb_exact(x, y, p, fee_bps)                    the same trade through firm.amm's integer swap, for checking
    auction(value, n, spread, seed, trials)        first-price sealed-bid auction among n searchers whose values are
                                                   value x U[1 - spread, 1]: equilibrium bids, the builder's share
    Chain(blocks, seed, sigma_day, ...)            the centralised price per 12-second block and noise swaps
    run_pool(chain, x0, fee, hedge)                pool reserves, arbitrage profits per block, fees, the liquidity
                                                   provider's hedged P&L and the loss-versus-rebalancing estimate
    lvr_rate(sigma_day, value)                     sigma^2 / 8 x value a day (constant product)
    liquidation_value(debt, bonus, gas_usd)        the gross value of a lending-protocol liquidation
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("amm", "gasfee"):
    sys.path.insert(0, str(FIRM / comp))
import firm_amm as amm  # noqa: E402
import firm_gasfee as gas  # noqa: E402

BLOCK_S = 12.0


def optimal_arb(x: float, y: float, p: float, fee: float = 0.003) -> tuple[str, float, float]:
    """If the pool's price y/x is above p (A dear in the pool), sell A into it: input dx = (sqrt(g x y / p) - x) / g
    with g = 1 - fee, profit = out - p dx. If below, buy A from it with dollars: dy = (sqrt(g x y p) - y) / g,
    profit = p out_A - dy. Returns (direction, input, profit in dollars)."""
    g = 1.0 - fee
    if y / x > p / g:
        dx = (math.sqrt(g * x * y / p) - x) / g
        out = g * dx * y / (x + g * dx)
        return "sell_A", dx, out - p * dx
    if y / x < p * g:
        dy = (math.sqrt(g * x * y * p) - y) / g
        out = g * dy * x / (y + g * dy)
        return "buy_A", dy, p * out - dy
    return "none", 0.0, 0.0


def arb_exact(x: int, y: int, p: float, fee_bps: int = 30) -> int:
    """Dollar profit (integer units) of optimal_arb's trade executed with firm.amm.cp_amount_out."""
    d, amt, _ = optimal_arb(float(x), float(y), p, fee_bps / 1e4)
    if d == "sell_A":
        out = amm.cp_amount_out(int(amt), x, y, fee_bps)
        return int(out - p * int(amt))
    if d == "buy_A":
        out = amm.cp_amount_out(int(amt), y, x, fee_bps)
        return int(p * out - int(amt))
    return 0


def auction(value: float, n: int, spread: float = 0.2, seed: int = 0, trials: int = 20000) -> dict:
    """Values v_i = value x (1 - spread + spread U_i). With uniform private values on [a, b] the symmetric equilibrium
    of a first-price auction bids a + (n - 1) / n (v - a). The winner pays its bid to the builder."""
    rng = np.random.default_rng(seed)
    a = value * (1.0 - spread)
    v = a + value * spread * rng.random((trials, n))
    vmax = v.max(axis=1)
    bid = a + (n - 1) / n * (vmax - a) if n > 1 else np.zeros(trials)
    return {"builder": float(bid.mean()), "searcher": float((vmax - bid).mean()),
            "share": float(bid.mean() / vmax.mean())}


class Chain:
    """`blocks` twelve-second blocks: the centralised price of A (dollars) is a geometric random walk of daily
    volatility sigma_day from p0; noise traders swap `noise_usd` dollars a block in a random direction."""

    def __init__(self, blocks: int = 7200, seed: int = 0, sigma_day: float = 0.04, p0: float = 3000.0,
                 noise_usd: float = 2000.0):
        rng = np.random.default_rng(seed)
        per = sigma_day * math.sqrt(BLOCK_S / 86400.0)
        self.p = p0 * np.exp(np.cumsum(rng.standard_normal(blocks) * per - 0.5 * per * per))
        self.noise = rng.choice([-1.0, 1.0], blocks) * noise_usd
        self.blocks, self.sigma_day = blocks, sigma_day


def run_pool(ch: Chain, value0: float = 20e6, fee: float = 0.003, gas_usd: float = 5.0) -> dict:
    """A pool worth value0 at the first price. Each block: a noise swap, then the arbitrage if its profit exceeds gas.
    The liquidity provider holds the pool and hedges its A exposure on the centralised exchange at each block's price
    (no hedging costs), so its P&L is the value of every trade at that price: noise trades (their fees and their
    mispricing) plus the arbitrage trades' fees, less what the arbitrageurs take before fees. The arbitrageurs' take
    splits into reverting the noise trades' impact (back-running, paid for by the noise traders' mispricing) and
    loss-versus-rebalancing proper, the part due to the market price moving."""
    p = ch.p[0]
    x, y = value0 / 2 / p, value0 / 2
    g = 1.0 - fee
    noise_fees = arb_fees = arb_profit = lvr = noise_pnl = 0.0
    arbs = 0
    for t in range(ch.blocks):
        p = ch.p[t]
        dn = ch.noise[t]
        if dn > 0:                                   # a noise trader buys A with dollars
            out = g * dn * x / (y + g * dn)
            noise_pnl += dn - p * out
            noise_fees += dn * fee
            y, x = y + dn, x - out
        else:                                        # sells A worth |dn| at the pool price
            dx = -dn / (y / x)
            out = g * dx * y / (x + g * dx)
            noise_pnl += p * dx - out
            noise_fees += dx * fee * p
            x, y = x + dx, y - out
        d, amt, profit = optimal_arb(x, y, p, fee)
        if profit > gas_usd:
            arbs += 1
            if d == "sell_A":
                out = g * amt * y / (x + g * amt)
                arb_fees += amt * fee * p
                lvr += out - p * amt + amt * fee * p     # the pool's loss at the market price, before its fee
                x, y = x + amt, y - out
            else:
                out = g * amt * x / (y + g * amt)
                arb_fees += amt * fee
                lvr += p * out - amt + amt * fee
                x, y = x - out, y + amt
            arb_profit += profit - gas_usd
    mispricing = noise_pnl - noise_fees
    return {"noise_pnl": noise_pnl, "noise_fees": noise_fees, "arb_fees": arb_fees, "arb_take": lvr,
            "lvr": lvr - mispricing, "fees": noise_fees + arb_fees,
            "hedged_pnl": noise_pnl + arb_fees - lvr, "arb_profit": arb_profit, "arbs": arbs,
            "days": ch.blocks * BLOCK_S / 86400.0, "value0": value0}


def lvr_rate(sigma_day: float, value: float) -> float:
    return sigma_day ** 2 / 8.0 * value


def liquidation_value(debt: float, bonus: float, gas_usd: float) -> float:
    return debt * bonus - gas_usd


def gas_cost(gas_units: int = 150000, base_gwei: float = 10.0, prio_gwei: float = 1.0,
             eth_usd: float = 3000.0) -> float:
    return gas.tx_cost_usd(gas_units, base_gwei, prio_gwei, eth_usd)
