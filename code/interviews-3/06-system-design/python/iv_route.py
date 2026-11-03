"""Split a buy across venues by price after fees, cheapest displayed level first."""
import heapq


def route(venues, qty):
    """venues maps a name to (fee per share, [(price, size), ...]). Returns (plan, cost)."""
    heap = [(price + fee, name, price, size)
            for name, (fee, levels) in venues.items() for price, size in levels]
    heapq.heapify(heap)
    plan, cost = {}, 0.0
    while qty > 0 and heap:
        net, name, _, size = heapq.heappop(heap)
        take = min(qty, size)
        plan[name] = plan.get(name, 0) + take
        cost += take * net
        qty -= take
    if qty:
        raise ValueError("not enough displayed")
    return plan, cost
