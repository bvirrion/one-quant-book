"""Book 3, Chapter 22: the sandwich of a USD 1 million swap in a constant-product pool as a function of the
victim's slippage tolerance, the attacker's profit against the size of its front-run, and a CEX-DEX
arbitrage after a price move."""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/sandwich"))
sys.path.insert(0, str(ROOT / "code/firm/amm"))
from firm_amm import cp_amount_out  # noqa: E402
from firm_sandwich import max_front_run, run, sandwich  # noqa: E402

E6, E18 = 10**6, 10**18
RA, RB = 15_000_000 * E6, 5_000 * E18          # a USDC-ETH pool at 3,000 dollars
SWAP = 1_000_000 * E6                            # the victim buys ETH with USD 1 million
GAS = 20 * E6                                     # two transactions' gas, in USDC (illustrative)


def by_tolerance(tols_bps=(0, 10, 25, 50, 100, 200), builder_share_bps: int = 0) -> list[tuple]:
    """(tolerance bp, front-run USD, attacker gross USD, net USD, victim loss ETH)."""
    rows = []
    for t in tols_bps:
        s = sandwich(RA, RB, SWAP, t, GAS, builder_share_bps)
        rows.append((t, s.front_in / E6, s.gross / E6, s.net / E6, s.victim_loss / E18))
    return rows


def profit_curve(tolerance_bps: int, points: int = 40) -> list[tuple[float, float, bool]]:
    """(front-run USD, attacker gross USD, victim still executes) up to twice the feasible maximum."""
    amax = max_front_run(RA, RB, SWAP, tolerance_bps)
    floor = cp_amount_out(SWAP, RA, RB) * (10_000 - tolerance_bps) // 10_000
    out = []
    for k in range(points + 1):
        a = 2 * amax * k // points
        b_v, g = run(RA, RB, SWAP, a)
        out.append((a / E6, g / E6, b_v >= floor))
    return out


def cex_dex_arbitrage(new_price: float, fee_bps: int = 30) -> tuple[float, float]:
    """After the centralised price of ETH moves to new_price, the trade that brings the pool's marginal price
    (net of fee) to it, and its profit in USDC valued at new_price. Returns (USDC in, profit USD)."""
    k, fee = (RA / E6) * (RB / E18), fee_bps / 1e4
    ra = RA / E6
    target_ra = math.sqrt(k * new_price * (1 - fee))       # buy ETH until the pool price net of fee meets the CEX
    if target_ra <= ra:
        return 0.0, 0.0
    dx = (target_ra - ra) / (1 - fee)
    dy = cp_amount_out(int(dx * E6), RA, RB) / E18
    return dx, dy * new_price - dx
