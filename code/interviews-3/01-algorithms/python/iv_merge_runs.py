import heapq


def merge_cost(sizes):
    heap = list(sizes)
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        merged = heapq.heappop(heap) + heapq.heappop(heap)
        total += merged
        heapq.heappush(heap, merged)
    return total


def merge_cost_k(sizes, k):
    heap = list(sizes)
    while (len(heap) - 1) % (k - 1):
        heap.append(0)                # empty runs, so that the last merge is a full one
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        merged = sum(heapq.heappop(heap) for _ in range(k))
        total += merged
        heapq.heappush(heap, merged)
    return total
