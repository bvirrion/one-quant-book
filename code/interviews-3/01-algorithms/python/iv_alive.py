import heapq


def peak_alive(orders):
    """orders: (open, close), alive for open <= t < close. Returns (peak, first time)."""
    events = []
    for start, end in orders:
        events.append((start, +1))
        events.append((end, -1))
    events.sort()                 # at equal times -1 sorts first: closes before opens
    alive = peak = 0
    when = None
    for t, delta in events:
        alive += delta
        if alive > peak:
            peak, when = alive, t
    return peak, when


def peak_alive_heap(orders):
    """The same count with a heap of closing times, for orders that arrive sorted by open."""
    closes, peak = [], 0
    for start, end in sorted(orders):
        while closes and closes[0] <= start:
            heapq.heappop(closes)
        heapq.heappush(closes, end)
        peak = max(peak, len(closes))
    return peak
