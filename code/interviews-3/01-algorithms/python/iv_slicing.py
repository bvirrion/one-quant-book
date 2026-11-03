import heapq


def cheapest_slicing(total, a, b):
    """Send total shares over len(a) periods; q shares in period t cost a[t]*q + b[t]*q*q."""
    def marginal(t, q):           # the cost of the q+1-th share in period t
        return a[t] + b[t] * (2 * q + 1)

    sent = [0] * len(a)
    heap = [(marginal(t, 0), t) for t in range(len(a))]
    heapq.heapify(heap)
    cost = 0
    for _ in range(total):
        m, t = heap[0]
        cost += m
        sent[t] += 1
        heapq.heapreplace(heap, (marginal(t, sent[t]), t))
    return cost, sent
