def lower_bound(xs, target):
    lo, hi = 0, len(xs)               # the answer is always in [lo, hi]
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


# Not printed: the follow-up.
def upper_bound(xs, target):
    lo, hi = 0, len(xs)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if xs[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo
