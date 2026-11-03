def three_sum(xs, target=0):
    xs = sorted(xs)
    out = []
    for i, a in enumerate(xs):
        if i and xs[i - 1] == a:
            continue                  # the same first value gives the same triples
        lo, hi = i + 1, len(xs) - 1
        while lo < hi:
            s = a + xs[lo] + xs[hi]
            if s < target:
                lo += 1
            elif s > target:
                hi -= 1
            else:
                out.append((a, xs[lo], xs[hi]))
                lo += 1
                while lo < hi and xs[lo] == xs[lo - 1]:
                    lo += 1
    return out
