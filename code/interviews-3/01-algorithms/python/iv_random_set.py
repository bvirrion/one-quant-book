import random


class RandomSet:
    def __init__(self):
        self.items, self.where = [], {}

    def insert(self, x):
        if x in self.where:
            return False
        self.where[x] = len(self.items)
        self.items.append(x)
        return True

    def remove(self, x):
        if x not in self.where:
            return False
        i, last = self.where.pop(x), self.items.pop()
        if last != x:                 # move the last element into the hole
            self.items[i] = last
            self.where[last] = i
        return True

    def pick(self, rng=random):
        return self.items[rng.randrange(len(self.items))]
