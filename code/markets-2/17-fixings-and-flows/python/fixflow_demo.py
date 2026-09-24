"""Chapter 17 of Book 2: fixings and flows. A month-end hedge rebalance, a fund's regional
rebalance, and the price path and dealer profit of a EUR 1 billion fixing order with and without
pre-hedging. Impact, holdings and returns are illustrative."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fixflow"))
from firm_fixflow import dealer_pnl, fix_and_cost, hedge_rebalance, simulate_pnl, weight_rebalance

Q = 1e9                  # EUR bought at the fix for the client
LAM = 0.3 / 1e8          # permanent impact: 0.3 pips per EUR 100 million
PIP_USD = 1e-4           # dollars per euro per pip of EURUSD
SIGMA_PRE = 2.0          # pips: random move between the pre-hedge and the window


def month_end() -> dict[str, float]:
    hedge = hedge_rebalance(2e12, 0.04, 0.5)
    fund = weight_rebalance({"US": 60e9 * 1.05, "EU": 40e9 * 0.99}, {"US": 0.6, "EU": 0.4})
    return {"hedge_sale": hedge, "fund_us": fund["US"], "fund_eu": fund["EU"]}


def fixing_order(p: float) -> dict[str, float]:
    fix, cost = fix_and_cost(Q, LAM, p)
    mean, sd = simulate_pnl(Q, LAM, p, SIGMA_PRE, seed=3)
    return {"fix": fix, "cost": cost, "pnl": dealer_pnl(Q, LAM, p) * PIP_USD, "sim_mean": mean * PIP_USD,
            "sim_sd": sd * PIP_USD, "client_extra": Q * (fix - fix_and_cost(Q, LAM, 0.0)[0]) * PIP_USD}


def price_path(p: float, steps: int = 150) -> list[tuple[float, float]]:
    """(minutes relative to 16:00, price in pips above the start) for pre-hedging from 15:50 to
    15:57:30 and the rest evenly in the window 15:57:30-16:02:30."""
    out = []
    for k in range(steps + 1):
        t = -10.0 + 15.0 * k / steps
        if t < -2.5:
            bought = p * Q * (t + 10.0) / 7.5
        elif t <= 2.5:
            bought = p * Q + (1 - p) * Q * (t + 2.5) / 5.0
        else:
            bought = Q
        out.append((t, LAM * bought))
    return out


def hedge_flow_grid(holdings: float = 2e12) -> list[tuple[float, float, float, float]]:
    """(US equity return %, dollar sales USD bn at hedge ratios 25%, 50%, 75%)."""
    return [(r, *(hedge_rebalance(holdings, r / 100, h) / 1e9 for h in (0.25, 0.5, 0.75))) for r in range(-6, 7)]
