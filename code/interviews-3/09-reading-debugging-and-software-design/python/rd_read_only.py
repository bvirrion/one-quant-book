class Book:
    def __init__(self):
        self.orders = {}

    def add(self, oid, qty):
        self.orders[oid] = qty

    def total(self):
        return sum(self.orders.values())


class ReplayBook(Book):
    """A book rebuilt from history. Nothing may be added to it."""

    def add(self, oid, qty):
        raise NotImplementedError("read-only")


def top_up(book, oid, qty):
    book.add(oid, qty)
    return book.total()
