def best_mean(xs, k, tol=1e-9):
    """The largest mean over stretches of length at least k, to within tol; None if k > n."""
    if k > len(xs):
        return None

    def reachable(m):             # is some stretch of length >= k at a mean of at least m?
        total, low, before = 0.0, 0.0, 0.0
        for i, x in enumerate(xs):
            total += x - m
            if i >= k:
                before += xs[i - k] - m
                low = min(low, before)
            if i >= k - 1 and total >= low:
                return True
        return False

    lo, hi = min(xs), max(xs)
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if reachable(mid):
            lo = mid
        else:
            hi = mid
    return lo
