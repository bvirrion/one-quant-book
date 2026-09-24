"""Who gets a customer's option order? Allocation at the quote and in an auction (Chapter 24). Illustrative."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/match"))
from firm_optmatch import Quote, customer_priority_pro_rata, price_improvement_auction

BOOK = [Quote("MM1", 100, "mm"), Quote("C1", 10, "customer"), Quote("DMM", 100, "mm", designated=True),
        Quote("F", 50, "firm"), Quote("C2", 5, "customer"), Quote("MM2", 250, "mm")]

OPRA_PROJECTIONS = (("10/2025", 253, 12.322), ("1/2026", 298, 12.887), ("7/2026", 311, 13.575),
                    ("1/2027", 327, 14.227), ("7/2027", 343, 14.964))   # bn messages a day; million msg / 100 ms


def simulate_auctions(n: int, mean_responders: float, p_improve: float, seed: int, order: int = 100, stop: int = 250):
    """Initiator's share of the order and the customer's improvement, in ticks, over n auctions.
    Each responder bids for the whole order, at one tick better than the stop with probability p_improve."""
    rng = np.random.default_rng(seed)
    share, improvement = np.empty(n), np.empty(n)
    for i in range(n):
        k = rng.poisson(mean_responders)
        resp = [(f"r{j}", stop - 1 if rng.random() < p_improve else stop, order) for j in range(k)]
        r = price_improvement_auction(order, stop, +1, resp)
        share[i] = r.initiator_qty / order
        improved_qty = sum(q for who, q in r.fills.items() if any(w == who and p < stop for w, p, _ in resp))
        improvement[i] = improved_qty / order
    return float(share.mean()), float(improvement.mean())


def compare_rules(qty: int) -> dict[str, dict[str, int]]:
    flat = [Quote(q.oid, q.qty, "mm") for q in BOOK]
    return {
        "pro_rata": customer_priority_pro_rata(flat, qty),
        "customer": customer_priority_pro_rata(BOOK, qty),
        "entitled": customer_priority_pro_rata(BOOK, qty, entitlement_pct=40),
    }
