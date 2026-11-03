def missing(seqs, n):
    x = 0
    for i in range(1, n + 1):
        x ^= i
    for s in seqs:
        x ^= s
    return x


# Not printed: the follow-up.
def two_missing(seqs, n):
    x = 0
    for i in range(1, n + 1):
        x ^= i
    for s in seqs:
        x ^= s
    low = x & -x
    a = 0
    for i in range(1, n + 1):
        if i & low:
            a ^= i
    for s in seqs:
        if s & low:
            a ^= s
    return tuple(sorted((a, x ^ a)))
