import heapq


class StreamMedian:
    def __init__(self):
        self.low = []             # the smaller half, negated: a max-heap
        self.high = []            # the larger half: a min-heap

    def add(self, x):
        heapq.heappush(self.low, -heapq.heappushpop(self.high, x))
        if len(self.low) > len(self.high):
            heapq.heappush(self.high, -heapq.heappop(self.low))

    def median(self):
        if len(self.high) > len(self.low):
            return self.high[0]
        return (self.high[0] - self.low[0]) / 2
