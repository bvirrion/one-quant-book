"""One Quant Book 16, chapter 6: the head of desk's plan (illustrative desk, $ millions a year).

Three businesses: client flow (expected revenue 30, volatility 25), inventory trading (15, 20) and structured
solutions (10, 12), correlated 0.3, 0.2 and 0.4. Last year the desk made its expected 55; the budget is 10 per cent
more. Direct costs 18, costs allocated by the firm 10, variable pay 20 per cent of the result after costs.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/deskplan"))
import firm_deskplan as dp  # noqa: E402

BUS = (dp.Business("client flow", 30.0, 25.0), dp.Business("inventory", 15.0, 20.0),
       dp.Business("structured", 10.0, 12.0))
CORR = ((1.0, 0.3, 0.2), (0.3, 1.0, 0.4), (0.2, 0.4, 1.0))
LAST = 55.0
PLAN = dp.Plan(BUS, CORR, 18.0, 10.0, 0.20, 1.10 * LAST)
N = 20_000


def plan(k=1.10):
    return dp.Plan(BUS, CORR, 18.0, 10.0, 0.20, k * LAST)


def headline():
    s = dp.plan_stats(PLAN)
    return {"mu": s["mu"], "sigma": s["sigma"], "sharpe": s["sharpe"], "p_meet": dp.p_meet(PLAN),
            "lam75": dp.risk_multiple(PLAN, 0.75), "p_loss_year": dp._phi(-(s["mu"] - 28.0) / s["sigma"]),
            "p_negative_revenue": dp._phi(-s["sharpe"])}


def p_meet_closed(sharpe, k):
    """P(revenue >= k * expected revenue) for a desk of Sharpe ratio `sharpe`: Phi(S (1 - k))."""
    return 0.5 * (1 + math.erf(sharpe * (1 - k) / math.sqrt(2)))


def simulated(n=N, seed=6):
    sim = dp.simulate(PLAN, n, np.random.default_rng(seed))
    return {"p_meet": float((sim["annual"] >= PLAN.budget).mean()), "mdd_median": float(np.median(sim["max_drawdown"])),
            "mdd_p90": float(np.quantile(sim["max_drawdown"], 0.9))}


def fan(n=5_000, seed=6, days=252):
    """Monthly percentiles (5, 25, 50, 75, 95) of cumulative revenue over the year."""
    s = dp.plan_stats(PLAN)
    rng = np.random.default_rng(seed)
    path = np.cumsum(rng.normal(s["mu"] / days, s["sigma"] / math.sqrt(days), (n, days)), axis=1)
    idx = [round(days * m / 12) - 1 for m in range(1, 13)]
    return {m + 1: np.percentile(path[:, i], [5, 25, 50, 75, 95]) for m, i in enumerate(idx)}


def cascade(loss_tolerance=20.0):
    return dp.cascade(PLAN, loss_tolerance)


def expected_pnl_after_costs(n=N, seed=6):
    sim = dp.simulate(PLAN, n, np.random.default_rng(seed))["annual"]
    pre = sim - PLAN.direct_cost - PLAN.allocated_cost
    return float(np.mean(pre - PLAN.var_pay * np.maximum(pre, 0.0)))
