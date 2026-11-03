class Ladder:
    """Sizes at integer price levels 0..n-1, with sums over the top of the book."""

    def __init__(self, n):
        self.n, self.tree = n, [0] * (n + 1)

    def update(self, price, delta):
        i = price + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def below(self, price):           # total size at prices 0..price-1
        i, total = price, 0
        while i:
            total += self.tree[i]
            i -= i & -i
        return total

    def depth(self, price):           # total size at or above price
        return self.below(self.n) - self.below(price)


# Not printed: the follow-up, as a function, for sizes that are never negative.
def highest_with_depth(lad, q):
    left = lad.below(lad.n) - q
    if left < 0:
        return None
    pos, bit = 0, 1 << lad.n.bit_length()
    while bit:
        if pos + bit <= lad.n and lad.tree[pos + bit] <= left:
            pos += bit
            left -= lad.tree[pos]
        bit >>= 1
    return pos
