class Queue:
    def __init__(self):
        self.inbox, self.outbox = [], []
        self.moves = 0

    def push(self, x):
        self.inbox.append(x)

    def pop(self):
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())
                self.moves += 1
        return self.outbox.pop()
