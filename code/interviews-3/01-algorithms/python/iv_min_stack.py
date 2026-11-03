class MinStack:
    def __init__(self):
        self.items = []
        self.mins = []                # the minimum at each depth where it changed

    def push(self, x):
        self.items.append(x)
        if not self.mins or x <= self.mins[-1]:
            self.mins.append(x)

    def pop(self):
        x = self.items.pop()
        if x == self.mins[-1]:
            self.mins.pop()
        return x

    def min(self):
        return self.mins[-1]
