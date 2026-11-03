class Book:
    orders = []

    def __init__(self, name):
        self.name = name

    def add(self, order):
        self.orders.append(order)


a, b = Book("A"), Book("B")
a.add(1)
print(b.orders)
a.orders = [9]
print(a.orders, b.orders)
