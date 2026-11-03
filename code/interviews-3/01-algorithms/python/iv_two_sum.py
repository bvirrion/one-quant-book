def two_sum(xs, target):
    seen = {}                     # value -> a position where it occurred
    for j, x in enumerate(xs):
        i = seen.get(target - x)
        if i is not None:         # looked up before inserting, so i != j
            return i, j
        seen[x] = j
    return None


def two_sum_sorted(xs, target):
    """On a sorted list: two pointers, constant extra memory."""
    i, j = 0, len(xs) - 1
    while i < j:
        s = xs[i] + xs[j]
        if s == target:
            return i, j
        if s < target:
            i += 1
        else:
            j -= 1
    return None
