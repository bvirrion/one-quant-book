"""One Quant Book 16, chapter 22: a trading firm's data inventory, priced ($ thousand a year, illustrative inputs).

Fee levels are not any venue's or vendor's actual schedule: the structure (per user, per device, non-display category
fees, feed fees, enterprise terms) is what matters here. The alternative dataset's break-even price uses Book 7's
firm.vendoreval.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/databudget"))
import firm_databudget as db  # noqa: E402

PRODUCTS = [
    db.Product("exchange real-time display", "market data", per_user=0.6),
    db.Product("exchange non-display (automated trading)", "market data", flat=180.0),
    db.Product("direct feeds (6)", "market data", flat=360.0),
    db.Product("vendor terminals", "terminals", per_user=25.0),
    db.Product("reference data", "reference data", per_user=8.0, enterprise=400.0),
    db.Product("news analytics", "reference data", per_device=15.0),
    db.Product("alternative dataset", "alternative data", flat=300.0),
]
USAGE = {"exchange real-time display": db.Usage(users=40), "exchange non-display (automated trading)": db.Usage(),
         "direct feeds (6)": db.Usage(), "vendor terminals": db.Usage(users=30), "reference data": db.Usage(users=60),
         "news analytics": db.Usage(devices=4), "alternative dataset": db.Usage()}
STRATEGY_WEIGHTS = {"market making": 0.45, "statistical arbitrage": 0.30, "event-driven": 0.15, "macro": 0.10}


def the_budget():
    return db.budget(PRODUCTS, USAGE)


def reference_curve(max_users=100):
    p = PRODUCTS[4]
    return [(n, db.annual_cost(p, db.Usage(users=n)), db.annual_cost(p, db.Usage(users=n), True))
            for n in range(0, max_users + 1, 5)]


def audit(under=0.15, years=3.0, monthly_rate=0.01):
    """An audit of per-user fees (display and terminals) finds `under` of true users unreported for `years`."""
    fees = db.annual_cost(PRODUCTS[0], USAGE["exchange real-time display"]) + db.annual_cost(
        PRODUCTS[3], USAGE["vendor terminals"])
    return fees, db.audit_exposure(fees, under, years, monthly_rate)


def allocation():
    return db.allocate(sum(the_budget().values()), STRATEGY_WEIGHTS)


def alt_value():
    """The dataset feeds a strategy on $50 million that earns 2 per cent gross in year one from it, costs 0.5 per
    cent a year to trade, and loses half its edge every two years; over a three-year contract."""
    return db.alt_breakeven(0.02, 50_000.0, 0.005, 2.0, 3)
