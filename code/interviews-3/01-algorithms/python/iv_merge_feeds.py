import heapq


def merge_feeds(feeds):
    """feeds: iterators of (timestamp, message), each in time order. Yields the merge."""
    its = [iter(f) for f in feeds]
    heap = []
    for n, it in enumerate(its):
        head = next(it, None)
        if head is not None:
            heap.append((head[0], n, head[1]))   # n breaks ties: messages never compared
    heapq.heapify(heap)
    while heap:
        ts, n, message = heap[0]
        yield ts, message
        head = next(its[n], None)
        if head is None:
            heapq.heappop(heap)
        else:
            heapq.heapreplace(heap, (head[0], n, head[1]))
