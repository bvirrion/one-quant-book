class Level:
    """One first-in, first-out level: a Fenwick tree of shares, by arrival number."""

    def __init__(self, max_orders):
        self.tree = [0] * (max_orders + 1)
        self.slot, self.size = {}, []        # id -> arrival number; arrival number -> shares
        self.front = 0

    def _add(self, i, delta):
        i += 1
        while i < len(self.tree):
            self.tree[i] += delta
            i += i & -i

    def add(self, oid, qty):
        self.slot[oid] = len(self.size)
        self.size.append(qty)
        self._add(self.slot[oid], qty)

    def cancel(self, oid):
        i = self.slot.pop(oid)
        self._add(i, -self.size[i])
        self.size[i] = 0

    def execute(self, qty):                  # the front of the queue trades first
        while qty and self.front < len(self.size):
            done = min(qty, self.size[self.front])
            self.size[self.front] -= done
            self._add(self.front, -done)
            qty -= done
            if self.size[self.front] == 0:
                self.front += 1

    def ahead(self, oid):                    # shares ahead of this order in the queue
        i, total = self.slot[oid], 0
        while i:
            total += self.tree[i]
            i -= i & -i
        return total
