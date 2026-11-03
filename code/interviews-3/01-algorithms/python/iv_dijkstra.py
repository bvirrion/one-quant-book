import heapq


def fastest(links, source):
    """links: {venue: [(next_venue, cost >= 0), ...]}. Returns distances, predecessors."""
    dist, before = {source: 0}, {}
    heap = [(0, source)]
    while heap:
        d, v = heapq.heappop(heap)
        if d > dist[v]:               # a stale entry: v was reached faster since
            continue
        for w, cost in links.get(v, ()):
            if d + cost < dist.get(w, float("inf")):
                dist[w], before[w] = d + cost, v
                heapq.heappush(heap, (d + cost, w))
    return dist, before


# Not printed: the wrong answer with a closed set.
def closed_set_version(links, source):
    dist, closed = {source: 0}, set()
    heap = [(0, source)]
    while heap:
        d, v = heapq.heappop(heap)
        if v in closed:
            continue
        closed.add(v)
        for w, cost in links.get(v, ()):
            if w not in closed and d + cost < dist.get(w, float("inf")):
                dist[w] = d + cost
                heapq.heappush(heap, (d + cost, w))
    return dist
