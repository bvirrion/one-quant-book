class Book:
    def __init__(self):
        self.levels = {}          # price -> total quantity
        self.orders = {}          # id -> (price, qty)

    def add(self, oid, price, qty):
        self.orders[oid] = (price, qty)
        self.levels[price] = self.levels.get(price, 0) + qty

    def cancel(self, oid):
        price, qty = self.orders.pop(oid)
        self.levels[price] -= qty

    def best(self):
        return max(self.levels) if self.levels else None


def test_add_then_best():
    b = Book()
    b.add(1, 100, 5)
    b.add(2, 101, 5)
    assert b.best() == 101


def test_cancel_lower():
    b = Book()
    b.add(1, 100, 5)
    b.add(2, 101, 5)
    b.cancel(1)
    assert b.best() == 101
