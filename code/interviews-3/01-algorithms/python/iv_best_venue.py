class BestBid:
    """An indexed max-heap of venues: pos[v] says where venue v sits in the heap."""

    def __init__(self, n):
        self.bid = [0] * n
        self.heap = list(range(n))
        self.pos = list(range(n))

    def _swap(self, i, j):
        h = self.heap
        h[i], h[j] = h[j], h[i]
        self.pos[h[i]], self.pos[h[j]] = i, j

    def update(self, venue, price):
        self.bid[venue] = price
        i = self.pos[venue]
        while i and self.bid[self.heap[i]] > self.bid[self.heap[(i - 1) // 2]]:
            self._swap(i, (i - 1) // 2)
            i = (i - 1) // 2
        while (c := 2 * i + 1) < len(self.heap):
            if c + 1 < len(self.heap) and self.bid[self.heap[c + 1]] > self.bid[self.heap[c]]:
                c += 1
            if self.bid[self.heap[c]] <= self.bid[self.heap[i]]:
                break
            self._swap(i, c)
            i = c

    def best(self):
        return self.bid[self.heap[0]], self.heap[0]
