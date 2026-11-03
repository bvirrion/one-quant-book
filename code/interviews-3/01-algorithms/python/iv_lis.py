from bisect import bisect_left


def longest_increasing(xs):
    tails = []                    # tails[n]: smallest last value of a run of length n + 1
    tail_at = []                  # the position of that value
    prev = [-1] * len(xs)         # the element before xs[i] in the best run ending at i
    for i, x in enumerate(xs):
        n = bisect_left(tails, x)
        if n:
            prev[i] = tail_at[n - 1]
        if n == len(tails):
            tails.append(x)
            tail_at.append(i)
        else:
            tails[n] = x
            tail_at[n] = i
    out = []
    i = tail_at[-1] if tail_at else -1
    while i != -1:
        out.append(xs[i])
        i = prev[i]
    return out[::-1]


def nested_boxes(boxes):
    """Longest chain of (w, h) with both strictly increasing: sort, then run the same scan."""
    order = sorted(boxes, key=lambda b: (b[0], -b[1]))
    return len(longest_increasing([h for _, h in order]))
