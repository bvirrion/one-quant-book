class Order:
    def __init__(self, oid, qty):
        self.oid, self.qty = oid, qty

    def __eq__(self, other):
        return (self.oid, self.qty) == (other.oid, other.qty)

    def __hash__(self):
        return hash((self.oid, self.qty))


book = set()
o = Order(1, 100)
book.add(o)
o.qty = 50                # a partial fill
print(o in book, len(book), any(x is o for x in book))
