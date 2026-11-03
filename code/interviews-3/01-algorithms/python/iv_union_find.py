class Groups:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.count = n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # halve the path
            x = self.parent[x]
        return x

    def link(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a            # the smaller tree goes under the larger
        self.size[a] += self.size[b]
        self.count -= 1

    def same(self, a, b):
        return self.find(a) == self.find(b)
