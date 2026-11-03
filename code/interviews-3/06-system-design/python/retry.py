class Gateway:
    def __init__(self):
        self.orders = []
        self.replies = {}

    def plain(self, qty):
        self.orders.append(qty)
        return len(self.orders)

    def keyed(self, client_id, qty):
        if client_id not in self.replies:
            self.orders.append(qty)
            self.replies[client_id] = len(self.orders)
        return self.replies[client_id]


a = Gateway()
a.plain(100)                                 # this reply is lost, so it sends again
print(a.plain(100), a.orders)
b = Gateway()
b.keyed("c1", 100)                           # so is this one
print(b.keyed("c1", 100), b.orders)
