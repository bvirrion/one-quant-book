def smallest_largest_day(sizes, days):
    def days_needed(cap):
        used, load = 1, 0
        for s in sizes:
            if load + s > cap:
                used, load = used + 1, 0
            load += s
        return used

    lo, hi = max(sizes), sum(sizes)   # no day can hold less than the largest slice
    while lo < hi:
        mid = (lo + hi) // 2
        if days_needed(mid) <= days:
            hi = mid
        else:
            lo = mid + 1
    return lo
