"""Orders for several venues, each taking a set time: one shared worker or one per venue."""


def simulate(orders, service, shared):
    """orders: (arrival, venue) in time order. Returns each venue's worst latency."""
    free_at = {}
    worst = {}
    for arrival, venue in orders:
        key = "all" if shared else venue
        start = max(arrival, free_at.get(key, 0.0))
        free_at[key] = start + service[venue]
        worst[venue] = max(worst.get(venue, 0.0), free_at[key] - arrival)
    return worst
