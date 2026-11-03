from math import sqrt


def sort_count(a):
    """A sorted copy of a, and how many pairs were out of order."""
    if len(a) < 2:
        return a, 0
    mid = len(a) // 2
    left, inv_left = sort_count(a[:mid])
    right, inv_right = sort_count(a[mid:])
    merged, i, j = [], 0, 0
    inversions = inv_left + inv_right
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
            inversions += len(left) - i   # right[j] is below everything left in `left`
    return merged + left[i:] + right[j:], inversions


def kendall_tau(xs, ys):
    order = sorted(range(len(xs)), key=xs.__getitem__)
    _, discordant = sort_count([ys[i] for i in order])
    pairs = len(xs) * (len(xs) - 1) // 2
    return (pairs - 2 * discordant) / pairs


def tied_pairs(values):
    """How many pairs of equal entries a list holds."""
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return sum(c * (c - 1) // 2 for c in counts.values())


def kendall_tau_b(xs, ys):
    """With ties: sort by (x, y), so a pair tied in x is never counted as discordant."""
    pairs = sorted(zip(xs, ys, strict=True))
    _, discordant = sort_count([y for _, y in pairs])
    total = len(xs) * (len(xs) - 1) // 2
    tx, ty, txy = tied_pairs(xs), tied_pairs(ys), tied_pairs(pairs)
    concordant = total - tx - ty + txy - discordant
    return (concordant - discordant) / sqrt((total - tx) * (total - ty))
