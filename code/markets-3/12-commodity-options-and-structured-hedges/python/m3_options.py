"""Chapter 12 of Book 3: commodity options and structured hedges. A vanilla option on a future
against an average-price option, a producer's collar and three-way collar, and a sovereign's put
programme; all inputs illustrative (forward 60, volatility 35%, rate 4%, one year, monthly fixings)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/hedgeprog"))
from firm_hedgeprog import Leg, black76, cash_flow_at_risk, hedged_revenue, simulate_averages, three_way, value

F0, SIGMA, R, T, STEPS, PATHS = 60.0, 0.35, 0.04, 1.0, 12, 200_000
VOLUME = 250e6                                           # barrels hedged by the sovereign (illustrative)


def averages() -> np.ndarray:
    return simulate_averages(F0, SIGMA, T, STEPS, PATHS, seed=11)


def vanilla_vs_average(strike: float = 55.0) -> dict[str, float]:
    return {"vanilla": black76(F0, strike, T, SIGMA, R, False), "apo": value([Leg("put", strike)], averages(), R, T)}


def solve_call(legs_fixed: list[Leg], target: float, lo: float = 60.0, hi: float = 200.0) -> float:
    """Call strike K such that legs_fixed plus a short call at K cost `target` per barrel (bisection)."""
    avg = averages()
    for _ in range(60):
        mid = (lo + hi) / 2
        v = value(legs_fixed + [Leg("call", mid, -1)], avg, R, T)
        if v > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def sovereign() -> dict[str, float]:
    """The weekend problem: an average-price put at 55 on 250 million barrels, against a three-way
    (buy 60 put, sell 45 put, sell a call) costing the same premium."""
    put = value([Leg("put", 55.0)], averages(), R, T)
    k3 = solve_call([Leg("put", 60.0), Leg("put", 45.0, -1)], put)
    tw = three_way(60.0, 45.0, k3)
    pay = {}
    for avg in (45.0, 30.0, 90.0):
        x = np.array([avg])
        pay[avg] = (float(Leg("put", 55.0).payoff(x)[0]) * VOLUME, float(sum(leg.payoff(x) for leg in tw)[0]) * VOLUME)
    return {"premium": put, "cost_usd": put * VOLUME, "revenue_usd": F0 * VOLUME, "share": put / F0,
            "call_strike": k3, "pay45": pay[45.0], "pay30": pay[30.0], "pay90": pay[90.0]}


def producer_car(budget: float = 50.0) -> dict[str, float]:
    """Cash flow at risk (5%) of a producer's average realised price: unhedged, with a zero-cost
    collar 50/75 (illustrative strikes, not solved), and with a 55 put bought at its premium."""
    avg = averages()
    put = value([Leg("put", 55.0)], avg, R, T)
    return {"unhedged": cash_flow_at_risk(avg, budget),
            "collar": cash_flow_at_risk(hedged_revenue(avg, [Leg("put", 50.0), Leg("call", 75.0, -1)], 0.0), budget),
            "put": cash_flow_at_risk(hedged_revenue(avg, [Leg("put", 55.0)], put), budget),
            "collar_cost": value([Leg("put", 50.0), Leg("call", 75.0, -1)], avg, R, T), "put_cost": put}


def swing_example(contract: float = 40.0, market: tuple[float, ...] = (30.0, 50.0, 40.0), dcq: float = 100.0,
                  swing: float = 20.0) -> float:
    """Value, against taking the DCQ every day, of a three-day swing contract whose total must equal three
    times the DCQ: take the minimum on the cheapest day and the maximum on the dearest (prices known)."""
    lo, hi = market.index(min(market)), market.index(max(market))
    take = [dcq] * len(market)
    take[lo], take[hi] = dcq - swing, dcq + swing
    return sum((m - contract) * (t - dcq) for m, t in zip(market, take, strict=True))
