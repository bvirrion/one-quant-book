import heapq


def best_bid_changes(bids):
    """bids: (open, close, price). Returns (time, best price or None) at each change."""
    events = sorted({t for o, c, _ in bids for t in (o, c)})
    bids = sorted(bids)
    alive, out, i = [], [], 0         # alive: a heap of (-price, close)
    for t in events:
        while i < len(bids) and bids[i][0] == t:
            heapq.heappush(alive, (-bids[i][2], bids[i][1]))
            i += 1
        while alive and alive[0][1] <= t:
            heapq.heappop(alive)      # gone
        best = -alive[0][0] if alive else None
        if not out or out[-1][1] != best:
            out.append((t, best))
    return out
