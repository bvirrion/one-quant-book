"""A store that refuses writers with an old epoch, and a primary paused and replaced."""


class Store:
    def __init__(self, fenced=True):
        self.fenced = fenced
        self.highest = 0
        self.data = {}

    def write(self, epoch, key, value):
        if self.fenced and epoch < self.highest:
            return False
        self.highest = max(self.highest, epoch)
        self.data[key] = value
        return True


for fenced in (True, False):
    store = Store(fenced)
    store.write(1, "position", 100)      # epoch 1, and then this primary pauses
    store.write(2, "position", 250)      # the standby takes over with epoch 2
    late = store.write(1, "position", 90)  # the old primary wakes up, still believing
    print(late, store.data["position"])
