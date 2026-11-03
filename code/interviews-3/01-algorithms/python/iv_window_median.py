import heapq


def window_medians(xs, k):
    low, high = [], []            # (-value, i) and (value, i): a max-heap and a min-heap
    in_low = [False] * len(xs)
    live = 0                      # entries of low still inside the window
    out = []

    def top(heap, i):             # drop entries that have left the window, lazily
        while heap and heap[0][1] <= i - k:
            heapq.heappop(heap)
        return heap[0]

    for i, x in enumerate(xs):
        if i >= k and in_low[i - k]:
            live -= 1
        if live and x <= -top(low, i)[0]:
            heapq.heappush(low, (-x, i))
            in_low[i], live = True, live + 1
        else:
            heapq.heappush(high, (x, i))
        want = (min(i + 1, k) + 1) // 2
        while live != want:
            a, b, step = (high, low, 1) if live < want else (low, high, -1)
            v, j = top(a, i)
            heapq.heappop(a)
            heapq.heappush(b, (-v, j))
            in_low[j], live = step > 0, live + step
        if i >= k - 1:
            m = -top(low, i)[0]
            out.append(m if k % 2 else (m + top(high, i)[0]) / 2)
    return out
