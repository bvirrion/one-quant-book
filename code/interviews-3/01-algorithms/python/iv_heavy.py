def heavy_hitters(stream, k):
    """At most k - 1 counters. Every item seen more than n / k times is among the keys."""
    counts = {}
    for x in stream:
        if x in counts:
            counts[x] += 1
        elif len(counts) < k - 1:
            counts[x] = 1
        else:                     # x and k - 1 others each lose one: k units cancel
            for y in list(counts):
                counts[y] -= 1
                if counts[y] == 0:
                    del counts[y]
    return counts
