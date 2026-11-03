import random


def check(make_book, runs=500, steps=30, seed=1):
    """Random operations against the plain truth. Returns a short failing list, or None."""
    rng = random.Random(seed)
    for _ in range(runs):
        ops = [(rng.choice("ac"), rng.randint(1, 5), rng.randint(99, 101), rng.randint(1, 9))
               for _ in range(steps)]
        if failure(make_book, ops):
            return shrink(make_book, ops)
    return None


def failure(make_book, ops):
    """Run the operations and check every invariant after each one. True if any fails."""
    book, live = make_book(), {}
    for kind, oid, price, qty in ops:
        if kind == "a" and oid not in live:
            book.add(oid, price, qty)
            live[oid] = (price, qty)
        elif kind == "c" and oid in live:
            book.cancel(oid)
            del live[oid]
        if book.best() != max((p for p, _ in live.values()), default=None):
            return True
        if sum(book.levels.values()) != sum(q for _, q in live.values()):
            return True
    return False


def shrink(make_book, ops):
    """Drop operations one at a time for as long as the failure survives."""
    i = 0
    while i < len(ops):
        shorter = ops[:i] + ops[i + 1:]
        if failure(make_book, shorter):
            ops = shorter
        else:
            i += 1
    return ops
