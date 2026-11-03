def best_stretch(xs):
    """Largest sum of a non-empty stretch, with its first and last positions."""
    best = (xs[0], 0, 0)
    here, start = xs[0], 0
    for i, x in enumerate(xs[1:], 1):
        if here < 0:                  # a negative past can only hurt
            here, start = x, i
        else:
            here += x
        best = max(best, (here, start, i), key=lambda t: t[0])
    return best
