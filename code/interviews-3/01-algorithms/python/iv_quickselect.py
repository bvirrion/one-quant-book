import random


def kth_smallest(xs, k, rng=random):
    """The value with k elements below it in sorted order, k from 0."""
    xs = list(xs)
    lo, hi = 0, len(xs)
    while True:
        pivot = xs[rng.randrange(lo, hi)]
        below = [x for x in xs[lo:hi] if x < pivot]
        equal = sum(1 for x in xs[lo:hi] if x == pivot)
        if k < lo + len(below):
            xs[lo:hi] = below
            hi = lo + len(below)
        elif k < lo + len(below) + equal:
            return pivot
        else:
            above = [x for x in xs[lo:hi] if x > pivot]
            lo += len(below) + equal
            xs[lo:hi] = above
            hi = lo + len(above)


# Not printed: comparison counts for the two failure modes, on a partition with one pivot.
def comparisons_first_pivot(xs, k):
    count = 0
    while True:
        pivot = xs[0]
        count += len(xs) - 1
        below = [x for x in xs[1:] if x < pivot]
        rest = [x for x in xs[1:] if x >= pivot]
        if k < len(below):
            xs = below
        elif k == len(below):
            return count
        else:
            k -= len(below) + 1
            xs = rest
