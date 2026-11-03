def sweep(asks, qty):
    """asks: (price, size) from the lowest price up. Returns fills, unfilled size, cost."""
    fills, cost = [], 0
    for price, size in asks:
        if qty == 0:
            break
        take = min(size, qty)
        fills.append((price, take))
        cost += price * take
        qty -= take
    return fills, qty, cost


def size_within(asks, limit):
    """How much a buyer can take at or below a limit price."""
    total = 0
    for price, size in asks:
        if price > limit:
            break
        total += size
    return total
