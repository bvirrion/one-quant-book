"""An allowance lowered from N to M, while the spender watches the pending transaction."""


def most_taken(n, m):
    """The spender moves before or after the owner's change. Returns the most it can take."""
    best = 0
    for before in range(n + 1):              # taken while the old allowance stands
        allowance = m                        # the owner's change simply overwrites
        best = max(best, before + allowance)
    return best


def most_taken_with_compare(n, m):
    """The same, where the change only applies if the allowance is still n."""
    best = 0
    for before in range(n + 1):
        allowance = m if before == 0 else n - before
        best = max(best, before + allowance)
    return best
