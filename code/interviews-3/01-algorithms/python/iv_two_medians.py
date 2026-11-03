from bisect import bisect_right
from math import inf


def median_two(a, b):
    if len(a) > len(b):
        a, b = b, a                   # search the shorter list
    m, n = len(a), len(b)
    half = (m + n + 1) // 2           # how many values the left side must hold
    lo, hi = 0, m
    while True:
        i = (lo + hi) // 2            # i values from a, j from b, on the left side
        j = half - i
        left_a = a[i - 1] if i else -inf
        right_a = a[i] if i < m else inf
        left_b = b[j - 1] if j else -inf
        right_b = b[j] if j < n else inf
        if left_a > right_b:
            hi = i - 1                # took too many from a
        elif left_b > right_a:
            lo = i + 1                # took too few from a
        elif (m + n) % 2:
            return max(left_a, left_b)
        else:
            return (max(left_a, left_b) + min(right_a, right_b)) / 2


def kth_of_two(a, b, k):
    """The k-th smallest, k from 1, of two sorted lists: about log k steps."""
    i = j = 0
    while True:
        if i == len(a):
            return b[j + k - 1]
        if j == len(b):
            return a[i + k - 1]
        if k == 1:
            return min(a[i], b[j])
        step = k // 2
        x = min(i + step, len(a)) - 1
        y = min(j + step, len(b)) - 1
        if a[x] <= b[y]:
            k -= x - i + 1
            i = x + 1
        else:
            k -= y - j + 1
            j = y + 1


def median_of_partitions(partitions, lo, hi):
    """Lower median of integers in lo..hi spread over sorted partitions: bisect on the value."""
    total = sum(len(p) for p in partitions)
    need = (total + 1) // 2
    while lo < hi:
        mid = (lo + hi) // 2
        if sum(bisect_right(p, mid) for p in partitions) >= need:
            hi = mid
        else:
            lo = mid + 1
    return lo
