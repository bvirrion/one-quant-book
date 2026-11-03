import heapq
from collections import deque


class Engine:
    def __init__(self):
        self.levels = {"B": {}, "S": {}}  # side -> price -> queue of [id, remaining]
        self.heaps = {"B": [], "S": []}   # best price first; levels leave lazily
        self.live = {}                    # id -> its [id, remaining]

    def submit(self, oid, side, price, qty):
        other, sign = ("S", 1) if side == "B" else ("B", -1)
        trades = []
        while qty and self.heaps[other]:
            best = sign * self.heaps[other][0]
            queue = self.levels[other].get(best)
            if not queue:                 # an emptied level
                heapq.heappop(self.heaps[other])
                self.levels[other].pop(best, None)
            elif sign * (best - price) > 0:
                break
            elif queue[0][1] == 0:        # cancelled while queued
                queue.popleft()
            else:
                order = queue[0]
                done = min(qty, order[1])
                trades.append((order[0], oid, best, done))
                qty -= done
                order[1] -= done
                if order[1] == 0:
                    queue.popleft()
                    del self.live[order[0]]
        if qty:
            if price not in self.levels[side]:
                self.levels[side][price] = deque()
                heapq.heappush(self.heaps[side], -sign * price)
            self.live[oid] = [oid, qty]
            self.levels[side][price].append(self.live[oid])
        return trades

    def cancel(self, oid):
        order = self.live.pop(oid, None)
        if order:
            order[1] = 0
        return order is not None
