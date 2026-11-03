class MinHeap:
    def __init__(self, items=()):
        self.a = list(items)
        for i in range(len(self.a) // 2 - 1, -1, -1):
            self._down(i)             # from the last parent up to the root

    def push(self, x):
        self.a.append(x)
        i = len(self.a) - 1
        while i and self.a[i] < self.a[(i - 1) // 2]:
            self.a[i], self.a[(i - 1) // 2] = self.a[(i - 1) // 2], self.a[i]
            i = (i - 1) // 2

    def pop(self):
        top, last = self.a[0], self.a.pop()
        if self.a:
            self.a[0] = last
            self._down(0)
        return top

    def _down(self, i):
        while (child := 2 * i + 1) < len(self.a):
            if child + 1 < len(self.a) and self.a[child + 1] < self.a[child]:
                child += 1
            if self.a[i] <= self.a[child]:
                return
            self.a[i], self.a[child] = self.a[child], self.a[i]
            i = child
