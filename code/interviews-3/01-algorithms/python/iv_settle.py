def fewest_transfers(balances):
    """balances sum to 0. The answer is the non-zero count minus the most zero-sum groups."""
    xs = [b for b in balances if b]
    n = len(xs)
    total = [0] * (1 << n)
    for mask in range(1, 1 << n):
        low = mask & -mask
        total[mask] = total[mask ^ low] + xs[low.bit_length() - 1]
    groups = [0] * (1 << n)           # groups[mask]: most zero-sum groups inside mask
    for mask in range(1, 1 << n):
        best = max(groups[mask ^ (1 << i)] for i in range(n) if mask >> i & 1)
        groups[mask] = best + (total[mask] == 0)
    return n - groups[-1]
